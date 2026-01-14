import logging
import secrets
from datetime import timedelta

from django.conf import settings
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.tokens import default_token_generator
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.utils.encoding import force_bytes, force_str
from django.utils.http import (
    urlsafe_base64_decode,
    urlsafe_base64_encode,
)

from django_ratelimit.decorators import ratelimit
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.tokens import RefreshToken

from .models import User, BiometricDevice
from .serializers import (
    UserSerializer,
    UserRegistrationSerializer,
    LoginSerializer,
    BiometricRegistrationSerializer,
    TwoFactorSetupSerializer,
    TwoFactorVerifySerializer,
)
from .emails import send_verification_email
from .utils.biometric_verification import BiometricVerifier

logger = logging.getLogger(__name__)


# -------------------------------------------------------------------
# Safe cache helpers
# -------------------------------------------------------------------

def safe_cache_get(key, default=None):
    try:
        return cache.get(key, default)
    except Exception as e:
        logger.warning(f"Cache get failed [{key}]: {e}")
        return default


def safe_cache_set(key, value, timeout=None):
    try:
        cache.set(key, value, timeout=timeout)
        return True
    except Exception as e:
        logger.warning(f"Cache set failed [{key}]: {e}")
        return False


def safe_cache_delete(key):
    try:
        cache.delete(key)
        return True
    except Exception as e:
        logger.warning(f"Cache delete failed [{key}]: {e}")
        return False


# -------------------------------------------------------------------
# ViewSet
# -------------------------------------------------------------------

class UserViewSet(viewsets.ModelViewSet):
    """
    User authentication & account management ViewSet
    """

    queryset = User.objects.all()
    serializer_class = UserSerializer

    # IMPORTANT: override defaults
    authentication_classes = []
    permission_classes = []

    # -------------------------------------------------------------------
    # Permissions (SAFE to use self.action here)
    # -------------------------------------------------------------------
    def get_permissions(self):
        public_actions = {
            'register',
            'login',
            'verify_email',
            'resend_verification',
            'forgot_password',
            'reset_password_confirm',
            'verify_2fa',
            'biometric_challenge',
            'biometric_login',
        }

        action = getattr(self, 'action', None)
        logger.info(f"Permissions check - action={action}")

        if action in public_actions:
            return [AllowAny()]

        return [IsAuthenticated()]

    # -------------------------------------------------------------------
    # Authentication (DO NOT use self.action here)
    # -------------------------------------------------------------------
    def get_authenticators(self):
        """
        self.action DOES NOT exist here.
        Use resolver_match.url_name instead.
        """

        public_url_names = {
            'user-register',
            'user-login',
            'user-verify-email',
            'user-resend-verification',
            'user-forgot-password',
            'user-reset-password-confirm',
            'user-verify-2fa',
            'user-biometric-challenge',
            'user-biometric-login',
        }

        resolver_match = self.request.resolver_match
        url_name = resolver_match.url_name if resolver_match else None

        logger.info(
            f"Authenticator check - url_name={url_name}, "
            f"public={url_name in public_url_names}"
        )

        if url_name in public_url_names:
            return []

        return [JWTAuthentication()]

    # -------------------------------------------------------------------
    # Helpers
    # -------------------------------------------------------------------
    def get_client_ip(self, request):
        xff = request.META.get("HTTP_X_FORWARDED_FOR")
        if xff:
            return xff.split(",")[0].strip()
        return request.META.get("REMOTE_ADDR")

    # -------------------------------------------------------------------
    # AUTH ENDPOINTS
    # -------------------------------------------------------------------

    @method_decorator(ratelimit(key="ip", rate="5/m", method="POST"))
    @action(detail=False, methods=["post"], permission_classes=[AllowAny])
    def register(self, request):
        if getattr(request, "limited", False):
            return Response(
                {"error": "Too many registration attempts."},
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )

        serializer = UserRegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.save(is_active=True, email_verified=False)

        try:
            send_verification_email(user)
            message = "Registration successful. Check your email."
        except Exception as e:
            logger.error(f"Verification email failed: {e}")
            message = "Registration successful."

        refresh = RefreshToken.for_user(user)

        return Response(
            {
                "message": message,
                "user": UserSerializer(user).data,
                "tokens": {
                    "refresh": str(refresh),
                    "access": str(refresh.access_token),
                },
            },
            status=status.HTTP_201_CREATED,
        )

    @method_decorator(ratelimit(key="ip", rate="5/m", method="POST"))
    @action(detail=False, methods=["post"], permission_classes=[AllowAny])
    def login(self, request):
        if getattr(request, "limited", False):
            return Response(
                {"error": "Too many login attempts."},
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )

        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]

        if not user.is_active:
            return Response(
                {"error": "Account disabled."},
                status=status.HTTP_403_FORBIDDEN,
            )

        if user.two_factor_enabled:
            temp_token = secrets.token_urlsafe(32)
            safe_cache_set(f"2fa_{temp_token}", user.id, timeout=300)

            return Response(
                {
                    "requires_2fa": True,
                    "temp_token": temp_token,
                    "email": user.email,
                },
                status=status.HTTP_202_ACCEPTED,
            )

        user.last_login = timezone.now()
        user.save(update_fields=["last_login"])

        refresh = RefreshToken.for_user(user)

        return Response(
            {
                "user": UserSerializer(user).data,
                "tokens": {
                    "refresh": str(refresh),
                    "access": str(refresh.access_token),
                },
            }
        )

    @action(detail=False, methods=["post"], permission_classes=[AllowAny])
    def verify_email(self, request):
        token = request.data.get("token")
        email = request.data.get("email")

        if not token or not email:
            return Response(
                {"error": "Token and email required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response(
                {"error": "User not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if user.email_verified:
            return Response({"message": "Email already verified."})

        if not user.verify_email(token):
            return Response(
                {"error": "Invalid or expired token."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response({"message": "Email verified successfully."})

    @action(detail=False, methods=["post"], permission_classes=[AllowAny])
    def resend_verification(self, request):
        email = request.data.get("email")
        if not email:
            return Response(
                {"error": "Email required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            user = User.objects.get(email=email)
            if not user.email_verified:
                send_verification_email(user)
        except User.DoesNotExist:
            pass

        return Response({"message": "If the email exists, a link was sent."})

    @action(detail=False, methods=["post"], permission_classes=[AllowAny])
    def forgot_password(self, request):
        email = request.data.get("email", "").lower()
        if not email:
            return Response(
                {"error": "Email required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            user = User.objects.get(email=email, is_active=True)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)

            reset_url = (
                f"{settings.FRONTEND_URL}/reset-password"
                f"?uid={uid}&token={token}"
            )

            send_mail(
                "Password Reset",
                f"Reset your password: {reset_url}",
                settings.DEFAULT_FROM_EMAIL,
                [email],
            )
        except User.DoesNotExist:
            pass

        return Response(
            {"message": "If the email exists, a reset link was sent."}
        )

    @action(detail=False, methods=["post"], permission_classes=[AllowAny])
    def reset_password_confirm(self, request):
        uid = request.data.get("uid")
        token = request.data.get("token")
        new_password = request.data.get("new_password")

        if not all([uid, token, new_password]):
            return Response(
                {"error": "Missing fields."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            user_id = force_str(urlsafe_base64_decode(uid))
            user = User.objects.get(pk=user_id)
        except Exception:
            return Response(
                {"error": "Invalid reset link."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not default_token_generator.check_token(user, token):
            return Response(
                {"error": "Invalid or expired token."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            validate_password(new_password, user)
        except ValidationError as e:
            return Response(
                {"error": e.messages},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user.set_password(new_password)
        user.save()

        return Response({"message": "Password reset successful."})
