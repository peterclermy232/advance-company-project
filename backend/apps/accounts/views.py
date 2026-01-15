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


def safe_cache_get(key, default=None):
    """Safely get value from cache with exception handling."""
    try:
        return cache.get(key, default)
    except Exception as e:
        logger.warning(f"Cache get failed for key {key}: {e}")
        return default


def safe_cache_set(key, value, timeout=None):
    """Safely set value in cache with exception handling."""
    try:
        cache.set(key, value, timeout=timeout)
        return True
    except Exception as e:
        logger.warning(f"Cache set failed for key {key}: {e}")
        return False


def safe_cache_delete(key):
    """Safely delete value from cache with exception handling."""
    try:
        cache.delete(key)
        return True
    except Exception as e:
        logger.warning(f"Cache delete failed for key {key}: {e}")
        return False


class UserViewSet(viewsets.ModelViewSet):
    """ViewSet for user management and authentication."""
    
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]  # Default permission

    def get_client_ip(self, request):
        """Get client IP address from request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR')

    @method_decorator(ratelimit(key='ip', rate='5/m', method='POST'))
    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def register(self, request):
        """Register a new user."""
        logger.info("📝 Register endpoint called")
        
        if getattr(request, 'limited', False):
            return Response(
                {'error': 'Too many registration attempts. Please try again later.'},
                status=status.HTTP_429_TOO_MANY_REQUESTS
            )

        serializer = UserRegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save(is_active=True, email_verified=False)

        try:
            send_verification_email(user)
            message = 'Registration successful. Please check your email to verify your account.'
        except Exception as e:
            logger.error(f"Failed to send verification email: {e}")
            message = 'Registration successful. You can now log in.'

        refresh = RefreshToken.for_user(user)
        return Response({
            'message': message,
            'user': UserSerializer(user).data,
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }
        }, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def verify_email(self, request):
        """Verify user email address."""
        logger.info("📧 Verify email endpoint called")
        
        token = request.data.get('token')
        email = request.data.get('email')
        
        if not token or not email:
            return Response(
                {'error': 'Token and email are required.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            user = User.objects.get(email=email)
            if user.email_verified:
                return Response({'message': 'Email already verified.'})
            
            if user.verify_email(token):
                return Response({'message': 'Email verified successfully.'})
            
            return Response(
                {'error': 'Invalid or expired token.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        except User.DoesNotExist:
            return Response(
                {'error': 'Invalid credentials.'},
                status=status.HTTP_401_UNAUTHORIZED
            )

    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def resend_verification(self, request):
        """Resend email verification link."""
        logger.info("🔄 Resend verification endpoint called")
        
        email = request.data.get('email')
        
        if not email:
            return Response(
                {'error': 'Email is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            user = User.objects.get(email=email)
            if user.email_verified:
                return Response({'message': 'Email already verified.'})
            
            send_verification_email(user)
            return Response({'message': 'Verification email sent.'})
        except User.DoesNotExist:
            # Don't reveal if user exists
            return Response({'message': 'If the email exists, a verification link has been sent.'})

    @method_decorator(ratelimit(key='ip', rate='10/m', method='POST'))
    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def login(self, request):
        """Authenticate user and return tokens."""
        logger.info(f"🔐 Login endpoint called - IP: {self.get_client_ip(request)}")
        logger.info(f"🔐 Request data keys: {request.data.keys()}")
        
        if getattr(request, 'limited', False):
            logger.warning(f"⚠️ Rate limit exceeded for IP: {self.get_client_ip(request)}")
            return Response(
                {'error': 'Too many login attempts. Please try again later.'},
                status=status.HTTP_429_TOO_MANY_REQUESTS
            )

        serializer = LoginSerializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
        except Exception as e:
            logger.error(f"❌ Login validation failed: {str(e)}")
            raise
            
        user = serializer.validated_data['user']
        logger.info(f"✅ User authenticated: {user.email}, 2FA: {user.two_factor_enabled}")

        if not user.is_active:
            logger.warning(f"⚠️ Inactive user login attempt: {user.email}")
            return Response(
                {'error': 'Account is disabled. Please contact support.'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Check if 2FA is enabled
        if user.two_factor_enabled:
            temp_token = secrets.token_urlsafe(32)
            cache_key = f'2fa_{temp_token}'
            
            if not safe_cache_set(cache_key, user.id, timeout=300):
                logger.error(f"❌ Cache unavailable, cannot process 2FA for {user.email}")
                return Response(
                    {'error': 'Authentication service temporarily unavailable. Please try again.'},
                    status=status.HTTP_503_SERVICE_UNAVAILABLE
                )
            
            logger.info(f"🔐 2FA required for user {user.email}")
            return Response({
                'requires_2fa': True,
                'temp_token': temp_token,
                'email': user.email
            }, status=status.HTTP_202_ACCEPTED)

        # Update last login
        try:
            user.last_login = timezone.now()
            user.save(update_fields=['last_login'])
        except Exception as e:
            logger.error(f"❌ Failed to update last_login: {str(e)}")

        # Generate tokens
        try:
            refresh = RefreshToken.for_user(user)
            logger.info(f"✅ Login successful for user {user.email}")
            return Response({
                'user': UserSerializer(user).data,
                'tokens': {
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                }
            })
        except Exception as e:
            logger.error(f"❌ Token generation failed: {str(e)}")
            return Response(
                {'error': 'Authentication successful but token generation failed.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def enable_2fa(self, request):
        """Enable two-factor authentication for user."""
        logger.info("🔐 Enable 2FA endpoint called")
        secret = request.user.generate_2fa_secret()
        return Response({
            'secret': secret,
            'qr_code': request.user.get_2fa_qr_code()
        })

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def confirm_2fa(self, request):
        """Confirm 2FA setup with verification code."""
        logger.info("✅ Confirm 2FA endpoint called")
        serializer = TwoFactorSetupSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        if not request.user.verify_2fa_code(serializer.validated_data['code']):
            return Response(
                {'error': 'Invalid verification code.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        request.user.two_factor_enabled = True
        backup_codes = request.user.generate_backup_codes()
        request.user.save()
        
        return Response({
            'message': 'Two-factor authentication enabled successfully.',
            'backup_codes': backup_codes
        })

    @method_decorator(ratelimit(key='ip', rate='5/5m', method='POST'))
    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def verify_2fa(self, request):
        """Verify 2FA code and complete login."""
        logger.info("🔐 Verify 2FA endpoint called")
        
        if getattr(request, 'limited', False):
            return Response(
                {'error': 'Too many verification attempts. Please try again later.'},
                status=status.HTTP_429_TOO_MANY_REQUESTS
            )
        
        serializer = TwoFactorVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        temp_token = request.data.get('temp_token')
        if not temp_token:
            return Response(
                {'error': 'Invalid request.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        cache_key = f'2fa_{temp_token}'
        user_id = safe_cache_get(cache_key)
        
        if not user_id:
            return Response(
                {'error': 'Session expired. Please login again.'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        try:
            user = User.objects.get(id=user_id, email=serializer.validated_data['email'])
        except User.DoesNotExist:
            return Response(
                {'error': 'Invalid credentials.'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        is_valid = (
            user.verify_backup_code(serializer.validated_data['code'])
            if serializer.validated_data.get('is_backup_code')
            else user.verify_2fa_code(serializer.validated_data['code'])
        )
        
        if not is_valid:
            return Response(
                {'error': 'Invalid verification code.'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        safe_cache_delete(cache_key)
        
        try:
            user.last_login = timezone.now()
            user.save(update_fields=['last_login'])
        except Exception as e:
            logger.error(f"Failed to update last_login: {str(e)}")
        
        refresh = RefreshToken.for_user(user)
        return Response({
            'user': UserSerializer(user).data,
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token)
            }
        })

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def register_biometric(self, request):
        """Register biometric device for user."""
        logger.info("👆 Register biometric endpoint called")
        serializer = BiometricRegistrationSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        
        device = BiometricDevice.objects.create(
            user=request.user,
            device_type=serializer.validated_data['device_type'],
            device_id=serializer.validated_data['device_id'],
            device_name=serializer.validated_data['device_name'],
            public_key=serializer.validated_data['public_key']
        )
        
        request.user.biometric_enabled = True
        request.user.save(update_fields=['biometric_enabled'])
        
        from .serializers import BiometricDeviceSerializer
        return Response(
            BiometricDeviceSerializer(device).data, 
            status=status.HTTP_201_CREATED
        )

    @method_decorator(ratelimit(key='ip', rate='10/m', method='POST'))
    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def biometric_challenge(self, request):
        """Generate biometric authentication challenge."""
        logger.info("👆 Biometric challenge endpoint called")
        
        if getattr(request, 'limited', False):
            return Response(
                {'error': 'Too many attempts. Please try again later.'},
                status=status.HTTP_429_TOO_MANY_REQUESTS
            )
        
        email = request.data.get('email')
        device_id = request.data.get('device_id')
        
        try:
            user = User.objects.get(email=email, is_active=True)
            device = BiometricDevice.objects.get(
                user=user,
                device_id=device_id,
                is_active=True
            )
        except (User.DoesNotExist, BiometricDevice.DoesNotExist):
            return Response(
                {'error': 'Invalid credentials.'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        return Response({
            'challenge': BiometricVerifier.generate_challenge(email),
            'credential_id': device.credential_id
        })

    @method_decorator(ratelimit(key='ip', rate='10/m', method='POST'))
    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def biometric_login(self, request):
        """Authenticate user with biometric data."""
        logger.info("👆 Biometric login endpoint called")
        
        if getattr(request, 'limited', False):
            return Response(
                {'error': 'Too many attempts. Please try again later.'},
                status=status.HTTP_429_TOO_MANY_REQUESTS
            )
        
        try:
            device = BiometricDevice.objects.get(
                credential_id=request.data['credential_id']
            )
            
            is_valid = BiometricVerifier.verify_signature(
                email=request.data['email'],
                public_key_pem=device.public_key,
                signature=request.data['auth_signature'],
                challenge_response=request.data['challenge_response']
            )
        except BiometricDevice.DoesNotExist:
            return Response(
                {'error': 'Device not found.'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        if not is_valid:
            return Response(
                {'error': 'Authentication failed.'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        user = User.objects.get(email=request.data['email'])
        
        try:
            user.last_login = timezone.now()
            user.save(update_fields=['last_login'])
        except Exception as e:
            logger.error(f"Failed to update last_login: {str(e)}")
        
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'user': UserSerializer(user).data,
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token)
            }
        })

    @method_decorator(ratelimit(key='ip', rate='3/h', method='POST'))
    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def forgot_password(self, request):
        """Send password reset email."""
        logger.info("🔑 Forgot password endpoint called")
        
        if getattr(request, 'limited', False):
            return Response(
                {'error': 'Too many password reset attempts.'},
                status=status.HTTP_429_TOO_MANY_REQUESTS
            )
        
        email = request.data.get('email', '').lower()
        
        if not email:
            return Response(
                {'error': 'Email is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            user = User.objects.get(email=email, is_active=True)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            reset_url = f"{settings.FRONTEND_URL}/reset-password?uid={uid}&token={token}"
            
            send_mail(
                subject='Password Reset Request',
                message=f'Click the link to reset your password: {reset_url}',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                fail_silently=False,
            )
        except User.DoesNotExist:
            pass
        except Exception as e:
            logger.error(f"Failed to send password reset email: {e}")
        
        return Response({
            'message': 'If your email exists in our system, you will receive a password reset link.'
        })

    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def reset_password_confirm(self, request):
        """Confirm password reset with new password."""
        logger.info("🔑 Reset password confirm endpoint called")
        
        uid = request.data.get('uid')
        token = request.data.get('token')
        new_password = request.data.get('new_password')
        
        if not all([uid, token, new_password]):
            return Response(
                {'error': 'Missing required fields.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            user_id = force_str(urlsafe_base64_decode(uid))
            user = User.objects.get(pk=user_id)
        except (User.DoesNotExist, ValueError, TypeError):
            return Response(
                {'error': 'Invalid reset link.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not default_token_generator.check_token(user, token):
            return Response(
                {'error': 'Invalid or expired token.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            validate_password(new_password, user)
        except ValidationError as e:
            return Response(
                {'error': e.messages},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user.set_password(new_password)
        user.save()
        
        return Response({'message': 'Password has been reset successfully.'})