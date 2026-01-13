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
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode

from django_ratelimit.decorators import ratelimit
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
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

# ---------------- Safe Cache Helpers ---------------- #

def safe_cache_get(key, default=None):
    try:
        return cache.get(key, default)
    except Exception as e:
        logger.warning(f"Cache get failed for key {key}: {e}")
        return default

def safe_cache_set(key, value, timeout=None):
    try:
        cache.set(key, value, timeout=timeout)
        return True
    except Exception as e:
        logger.warning(f"Cache set failed for key {key}: {e}")
        return False

def safe_cache_delete(key):
    try:
        cache.delete(key)
        return True
    except Exception as e:
        logger.warning(f"Cache delete failed for key {key}: {e}")
        return False

# ---------------- User ViewSet ---------------- #

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    # ---------- Permissions ----------
    def get_permissions(self):
        public_actions = [
            'register', 'login', 'verify_email', 'resend_verification',
            'forgot_password', 'reset_password_confirm',
            'verify_2fa', 'biometric_challenge', 'biometric_login'
        ]
        return [AllowAny()] if self.action in public_actions else [IsAuthenticated()]

    # ---------- Utilities ----------
    def get_client_ip(self, request):
        xff = request.META.get('HTTP_X_FORWARDED_FOR')
        return xff.split(',')[0] if xff else request.META.get('REMOTE_ADDR')

    # ---------- Registration ----------
    @method_decorator(ratelimit(key='ip', rate='5/m', method='POST'))
    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def register(self, request):
        if getattr(request, 'limited', False):
            return Response({'error': 'Too many attempts'}, status=429)

        serializer = UserRegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save(is_active=True, email_verified=False)

        # Send verification email
        try:
            send_verification_email(user)
            message = 'Registration successful! Check your email to verify your account.'
        except Exception as e:
            logger.error(f"Failed to send verification email: {e}")
            message = 'Registration successful! You can now login.'

        # Auto-login after registration
        refresh = RefreshToken.for_user(user)
        return Response({
            'message': message,
            'user': UserSerializer(user).data,
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }
        }, status=status.HTTP_201_CREATED)

    # ---------- Email Verification ----------
    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def verify_email(self, request):
        token = request.data.get('token')
        email = request.data.get('email')
        if not token or not email:
            return Response({'error': 'Token and email are required'}, status=400)
        try:
            user = User.objects.get(email=email)
            if user.email_verified:
                return Response({'message': 'Email already verified'}, status=200)
            if user.verify_email(token):
                return Response({'message': 'Email verified successfully'}, status=200)
            return Response({'error': 'Invalid or expired token'}, status=400)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=404)

    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def resend_verification(self, request):
        email = request.data.get('email')
        if not email:
            return Response({'error': 'Email is required'}, status=400)
        try:
            user = User.objects.get(email=email)
            if user.email_verified:
                return Response({'message': 'Email already verified'}, status=200)
            send_verification_email(user)
            return Response({'message': 'Verification email sent'}, status=200)
        except User.DoesNotExist:
            return Response({'message': 'If the email exists, a verification link has been sent'}, status=200)

    # ---------- Login ----------
    @method_decorator(ratelimit(key='ip', rate='5/m', method='POST'))
    @action(detail=False, methods=['post'])
    def login(self, request):
        if getattr(request, 'limited', False):
            return Response({'error': 'Too many login attempts'}, status=429)

        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']

        if not user.is_active:
            return Response({'error': 'Account disabled'}, status=403)

        # 2FA check
        if user.two_factor_enabled:
            temp_token = secrets.token_urlsafe(32)
            safe_cache_set(f'2fa_{temp_token}', user.id, timeout=300)
            return Response({
                'requires_2fa': True,
                'temp_token': temp_token,
                'email': user.email
            }, status=202)

        refresh = RefreshToken.for_user(user)
        user.last_login = timezone.now()
        user.save(update_fields=['last_login'])
        return Response({
            'user': UserSerializer(user).data,
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }
        })

    # ---------- 2FA ----------
    @action(detail=False, methods=['post'])
    def enable_2fa(self, request):
        secret = request.user.generate_2fa_secret()
        return Response({'secret': secret, 'qr_code': request.user.get_2fa_qr_code()})

    @action(detail=False, methods=['post'])
    def confirm_2fa(self, request):
        serializer = TwoFactorSetupSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        if not request.user.verify_2fa_code(serializer.validated_data['code']):
            return Response({'error': 'Invalid code'}, status=400)
        request.user.two_factor_enabled = True
        backup_codes = request.user.generate_backup_codes()
        request.user.save()
        return Response({'message': '2FA enabled', 'backup_codes': backup_codes})

    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def verify_2fa(self, request):
        serializer = TwoFactorVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            user = User.objects.get(email=serializer.validated_data['email'])
        except User.DoesNotExist:
            return Response({'error': 'Invalid credentials'}, status=401)
        valid = (
            user.verify_backup_code(serializer.validated_data['code'])
            if serializer.validated_data['is_backup_code']
            else user.verify_2fa_code(serializer.validated_data['code'])
        )
        if not valid:
            return Response({'error': 'Invalid code'}, status=401)
        refresh = RefreshToken.for_user(user)
        return Response({
            'user': UserSerializer(user).data,
            'tokens': {'refresh': str(refresh), 'access': str(refresh.access_token)}
        })

    # ---------- Biometric ----------
    @action(detail=False, methods=['post'])
    def register_biometric(self, request):
        serializer = BiometricRegistrationSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        device = serializer.save(user=request.user)
        request.user.biometric_enabled = True
        request.user.save(update_fields=['biometric_enabled'])
        return Response(device.serialized, status=201)

    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def biometric_challenge(self, request):
        email = request.data.get('email')
        device_id = request.data.get('device_id')
        try:
            user = User.objects.get(email=email, is_active=True)
            device = BiometricDevice.objects.get(user=user, device_id=device_id, is_active=True)
        except (User.DoesNotExist, BiometricDevice.DoesNotExist):
            return Response({'error': 'Invalid credentials'}, status=404)
        return Response({
            'challenge': BiometricVerifier.generate_challenge(email),
            'credential_id': device.credential_id
        })

    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def biometric_login(self, request):
        try:
            device = BiometricDevice.objects.get(credential_id=request.data['credential_id'])
            valid = BiometricVerifier.verify_signature(
                email=request.data['email'],
                public_key=device.public_key,
                signature=request.data['auth_signature'],
                challenge_response=request.data['challenge_response']
            )
        except BiometricDevice.DoesNotExist:
            return Response({'error': 'Device not found'}, status=404)
        if not valid:
            return Response({'error': 'Authentication failed'}, status=401)
        user = User.objects.get(email=request.data['email'])
        refresh = RefreshToken.for_user(user)
        return Response({
            'user': UserSerializer(user).data,
            'tokens': {'refresh': str(refresh), 'access': str(refresh.access_token)}
        })

    # ---------- Password Reset ----------
    @method_decorator(ratelimit(key='ip', rate='3/h', method='POST'))
    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def forgot_password(self, request):
        if getattr(request, 'limited', False):
            return Response({'error': 'Too many attempts'}, status=429)
        email = request.data.get('email', '').lower()
        if not email:
            return Response({'error': 'Email required'}, status=400)
        try:
            user = User.objects.get(email=email, is_active=True)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            reset_url = f"{settings.FRONTEND_URL}/reset-password?uid={uid}&token={token}"
            send_mail('Password Reset', f'Reset your password: {reset_url}', settings.DEFAULT_FROM_EMAIL, [email])
        except User.DoesNotExist:
            pass
        except Exception as e:
            logger.error(f"Failed to send password reset email: {e}")
        return Response({'message': 'If account exists, email sent'})

    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def reset_password_confirm(self, request):
        uid = request.data.get('uid')
        token = request.data.get('token')
        password = request.data.get('new_password')
        if not all([uid, token, password]):
            return Response({'error': 'Missing required fields'}, status=400)
        try:
            user_id = force_str(urlsafe_base64_decode(uid))
            user = User.objects.get(pk=user_id)
        except (User.DoesNotExist, ValueError, TypeError):
            return Response({'error': 'Invalid reset link'}, status=400)
        if not default_token_generator.check_token(user, token):
            return Response({'error': 'Invalid or expired token'}, status=400)
        try:
            validate_password(password, user)
        except ValidationError as e:
            return Response({'error': e.messages}, status=400)
        user.set_password(password)
        user.save()
        return Response({'message': 'Password reset successful'})
