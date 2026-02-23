import logging
import secrets

from django.conf import settings
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.tokens import default_token_generator
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode

from rest_framework import status
from rest_framework.decorators import (
    api_view,
    permission_classes,
    throttle_classes,
    parser_classes,
)
from rest_framework.permissions import AllowAny
from rest_framework.parsers import JSONParser, MultiPartParser, FormParser
from rest_framework_simplejwt.tokens import RefreshToken

from .models import User
from .serializers import (
    UserSerializer,
    UserRegistrationSerializer,
    LoginSerializer,
)
from .emails import send_verification_email, send_password_reset_email
from .throttles import (
    LoginRateThrottle,
    RegisterRateThrottle,
    TwoFactorRateThrottle,
    EmailVerificationRateThrottle,
    PasswordResetRateThrottle,
)
from .response_utils import APIResponse, Messages
from .utils.cache_utils import (
    safe_cache_get,
    safe_cache_set,
    safe_cache_delete,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------
# REGISTER
# ---------------------------------------------------------------------
@api_view(['POST'])
@permission_classes([AllowAny])
@throttle_classes([RegisterRateThrottle])
@parser_classes([JSONParser, MultiPartParser, FormParser])
def register(request):
    """Register a new user."""
    logger.info('Register endpoint called')

    serializer = UserRegistrationSerializer(data=request.data)

    if not serializer.is_valid():
        return APIResponse.validation_error(
            message=Messages.REGISTER_FAILED,
            errors=serializer.errors,
        )

    try:
        user = serializer.save(is_active=True, email_verified=False)

        try:
            send_verification_email(user)
        except Exception as e:
            logger.error(f'Verification email failed: {e}')

        refresh = RefreshToken.for_user(user)

        return APIResponse.created(
            message=Messages.REGISTER_SUCCESS,
            data={
                'user': UserSerializer(user, context={'request': request}).data,
                'tokens': {
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                },
            },
        )

    except Exception:
        logger.error('Registration error', exc_info=True)
        return APIResponse.server_error(message=Messages.REGISTER_FAILED)


# ---------------------------------------------------------------------
# EMAIL VERIFICATION
# ---------------------------------------------------------------------
@api_view(['POST'])
@permission_classes([AllowAny])
@throttle_classes([EmailVerificationRateThrottle])
def verify_email(request):
    """Verify a user's email address using a token (email NOT required in URL)."""
    token = request.data.get('token')
    email = request.data.get('email')

    if not token or not email:
        return APIResponse.validation_error(
            message='Token and email are required',
            errors={'token': ['Required'], 'email': ['Required']},
        )

    try:
        user = User.objects.get(email=email)

        if user.email_verified:
            return APIResponse.info(message='Email already verified')

        if user.verify_email(token):
            return APIResponse.success(message=Messages.EMAIL_VERIFIED)

        return APIResponse.error(
            message=Messages.EMAIL_VERIFICATION_FAILED,
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    except User.DoesNotExist:
        return APIResponse.error(
            message='Invalid email',
            status_code=status.HTTP_404_NOT_FOUND,
        )


@api_view(['POST'])
@permission_classes([AllowAny])
@throttle_classes([EmailVerificationRateThrottle])
def resend_verification(request):
    email = request.data.get('email')

    if not email:
        return APIResponse.validation_error(
            message='Email is required',
            errors={'email': ['Required']},
        )

    try:
        user = User.objects.get(email=email)

        if user.email_verified:
            return APIResponse.info(message='Email already verified')

        send_verification_email(user)
        return APIResponse.success(message=Messages.EMAIL_VERIFICATION_SENT)

    except User.DoesNotExist:
        # Return 200 to prevent email enumeration
        return APIResponse.success(
            message='If the email exists, a verification link was sent.'
        )


# ---------------------------------------------------------------------
# LOGIN
# ---------------------------------------------------------------------
@api_view(['POST'])
@permission_classes([AllowAny])
@throttle_classes([LoginRateThrottle])
def login(request):
    serializer = LoginSerializer(data=request.data)

    if not serializer.is_valid():
        return APIResponse.unauthorized(message=Messages.AUTH_FAILED)

    user = serializer.validated_data['user']

    if not user.is_active:
        return APIResponse.forbidden(message=Messages.AUTH_INACTIVE)

    # 2FA check
    if user.two_factor_enabled:
        temp_token = secrets.token_urlsafe(32)
        cache_key = f'2fa_{temp_token}'

        if not safe_cache_set(cache_key, user.uuid, timeout=300):
            return APIResponse.server_error(message='2FA service unavailable')

        return APIResponse.info(
            message=Messages.TWO_FA_REQUIRED,
            data={
                'requires_2fa': True,
                'temp_token': temp_token,
                'email': user.email,
            },
        )

    user.last_login = timezone.now()
    user.save(update_fields=['last_login'])

    refresh = RefreshToken.for_user(user)

    return APIResponse.success(
        message=Messages.AUTH_SUCCESS,
        data={
            'user': UserSerializer(user).data,
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            },
        },
    )


# ---------------------------------------------------------------------
# VERIFY 2FA
# ---------------------------------------------------------------------
@api_view(['POST'])
@permission_classes([AllowAny])
@throttle_classes([TwoFactorRateThrottle])
def verify_2fa(request):
    temp_token = request.data.get('temp_token')
    code = request.data.get('code')
    email = request.data.get('email')
    is_backup_code = request.data.get('is_backup_code', False)

    if not all([temp_token, code, email]):
        return APIResponse.validation_error(
            message='Missing fields',
            errors={'fields': ['temp_token, code, email required']},
        )

    cache_key = f'2fa_{temp_token}'
    user_id = safe_cache_get(cache_key)

    if not user_id:
        return APIResponse.unauthorized(message='Session expired')

    try:
        user = User.objects.get(uuid=user_id, email=email)
    except User.DoesNotExist:
        return APIResponse.unauthorized(message=Messages.AUTH_FAILED)

    # FIX 7: use verify_backup_code (defined in models.py) correctly
    if is_backup_code:
        valid = user.verify_backup_code(code)
    else:
        valid = user.verify_2fa_code(code)

    if not valid:
        return APIResponse.unauthorized(message=Messages.TWO_FA_INVALID)

    safe_cache_delete(cache_key)

    user.last_login = timezone.now()
    user.save(update_fields=['last_login'])

    refresh = RefreshToken.for_user(user)

    return APIResponse.success(
        message=Messages.AUTH_SUCCESS,
        data={
            'user': UserSerializer(user).data,
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            },
        },
    )


# ---------------------------------------------------------------------
# PASSWORD RESET
# ---------------------------------------------------------------------
@api_view(['POST'])
@permission_classes([AllowAny])
@throttle_classes([PasswordResetRateThrottle])
def forgot_password(request):
    """
    Send a branded HTML password reset email.
    Always returns 200 to prevent email enumeration.
    FIX 4: uses send_password_reset_email() (branded HTML).
    FIX 11: email is NOT included in the reset URL.
    """
    email = request.data.get('email', '').strip().lower()

    if not email:
        return APIResponse.validation_error(
            message='Email is required',
            errors={'email': ['Required']},
        )

    try:
        user = User.objects.get(email=email, is_active=True)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)

        frontend_url = getattr(settings, 'FRONTEND_URL', '').rstrip('/')
        # FIX 11: email is NOT in the URL — looked up server-side via uid
        reset_url = f'{frontend_url}/reset-password?uid={uid}&token={token}'

        send_password_reset_email(user, reset_url)

    except User.DoesNotExist:
        pass  # Intentional: prevent email enumeration
    except Exception:
        logger.error('Password reset email failed', exc_info=True)

    return APIResponse.success(message=Messages.PASSWORD_RESET_SENT)


@api_view(['POST'])
@permission_classes([AllowAny])
@throttle_classes([PasswordResetRateThrottle])
def reset_password_confirm(request):
    """
    Confirm password reset and invalidate all existing JWT refresh tokens.
    FIX 8: outstanding refresh tokens are blacklisted after a successful reset.
    """
    uid = request.data.get('uid')
    token = request.data.get('token')
    new_password = request.data.get('new_password')

    if not all([uid, token, new_password]):
        return APIResponse.validation_error(
            message='Missing fields',
            errors={'fields': ['uid, token, new_password required']},
        )

    try:
        user_id = force_str(urlsafe_base64_decode(uid))
        user = User.objects.get(pk=user_id)

        if not default_token_generator.check_token(user, token):
            return APIResponse.error(
                message='Invalid or expired token',
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        validate_password(new_password, user)
        user.set_password(new_password)
        user.save()

        # FIX 8: blacklist all outstanding refresh tokens for this user
        _blacklist_user_tokens(user)

        return APIResponse.success(message=Messages.PASSWORD_RESET_SUCCESS)

    except (User.DoesNotExist, ValidationError):
        return APIResponse.error(
            message=Messages.PASSWORD_RESET_FAILED,
            status_code=status.HTTP_400_BAD_REQUEST,
        )


def _blacklist_user_tokens(user):
    """
    Blacklist all outstanding SimpleJWT refresh tokens for a user.
    Requires INSTALLED_APPS to include 'rest_framework_simplejwt.token_blacklist'.
    Fails silently if the token blacklist app is not installed.
    """
    try:
        from rest_framework_simplejwt.token_blacklist.models import (
            OutstandingToken,
            BlacklistedToken,
        )
        tokens = OutstandingToken.objects.filter(user=user)
        for token in tokens:
            BlacklistedToken.objects.get_or_create(token=token)
        logger.info(f'Blacklisted {tokens.count()} token(s) for user {user.email}')
    except ImportError:
        logger.warning(
            'rest_framework_simplejwt.token_blacklist is not installed. '
            'Add it to INSTALLED_APPS to invalidate tokens on password reset.'
        )
    except Exception:
        logger.error('Failed to blacklist tokens', exc_info=True)


# ---------------------------------------------------------------------
# TEST
# ---------------------------------------------------------------------
@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
def test_endpoint(request):
    return APIResponse.success(
        message='API is working',
        data={'method': request.method, 'time': timezone.now()},
    )