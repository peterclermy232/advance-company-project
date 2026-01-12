from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.utils import timezone
from django.utils.decorators import method_decorator
from django_ratelimit.decorators import ratelimit

from .models import User, BiometricDevice, BiometricAuthLog
from .serializers import (
    UserSerializer,
    UserRegistrationSerializer,
    LoginSerializer,
    BiometricDeviceSerializer,
    BiometricRegistrationSerializer,
    BiometricAuthLogSerializer,
)
from .emails import send_verification_email
from .utils.biometric_verification import BiometricVerifier

import secrets
import logging
from datetime import timedelta

logger = logging.getLogger(__name__)


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    # ---------------- PERMISSIONS ----------------

    def get_permissions(self):
        if self.action in [
            'register',
            'login',
            'verify_email',
            'resend_verification',
            'biometric_challenge',
            'biometric_login',
        ]:
            return [AllowAny()]
        return [IsAuthenticated()]

    # ---------------- UTILITIES ----------------

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        return x_forwarded_for.split(',')[0] if x_forwarded_for else request.META.get('REMOTE_ADDR')

    # ================= AUTH =================

    @method_decorator(ratelimit(key='ip', rate='5/m', method='POST'))
    @action(detail=False, methods=['post'])
    def register(self, request):
        if getattr(request, 'limited', False):
            return Response({'error': 'Too many attempts'}, status=429)

        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save(is_active=False)
            try:
                send_verification_email(user)
            except Exception as e:
                logger.error(e)
                return Response({'error': 'Email failed'}, status=500)

            return Response(
                {'message': 'Check your email to verify your account'},
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=400)


    
    @action(detail=False, methods=['post'])
    def enable_2fa(self, request):
        """Enable 2FA for user account"""
        user = request.user
        
        # Generate secret and QR code
        secret = user.generate_2fa_secret()
        qr_code = user.get_2fa_qr_code()
        
        return Response({
            'secret': secret,
            'qr_code': qr_code,
            'message': 'Scan the QR code with your authenticator app (Google Authenticator, Authy, etc.)'
        })
    
    @action(detail=False, methods=['post'])
    def confirm_2fa(self, request):
        """Confirm and activate 2FA"""
        serializer = TwoFactorSetupSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = request.user
        code = serializer.validated_data['code']
        
        if not user.two_factor_secret:
            return Response({
                'error': 'Please enable 2FA first'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Verify the code
        import pyotp
        totp = pyotp.TOTP(user.two_factor_secret)
        
        if not totp.verify(code, valid_window=1):
            return Response({
                'error': 'Invalid verification code'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Activate 2FA and generate backup codes
        user.two_factor_enabled = True
        backup_codes = user.generate_backup_codes()
        user.save()
        
        return Response({
            'message': '2FA enabled successfully',
            'backup_codes': backup_codes,
            'warning': 'Save these backup codes in a secure location. You will need them if you lose access to your authenticator app.'
        })
    
    @action(detail=False, methods=['post'])
    def disable_2fa(self, request):
        """Disable 2FA (requires current password)"""
        password = request.data.get('password')
        
        if not password:
            return Response({
                'error': 'Password is required to disable 2FA'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        user = request.user
        
        if not user.check_password(password):
            return Response({
                'error': 'Invalid password'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        user.two_factor_enabled = False
        user.two_factor_secret = None
        user.backup_codes = []
        user.save()
        
        return Response({
            'message': '2FA disabled successfully'
        })
    
    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def verify_2fa(self, request):
        """Verify 2FA code during login"""
        serializer = TwoFactorVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        email = serializer.validated_data['email']
        code = serializer.validated_data['code']
        is_backup = serializer.validated_data['is_backup_code']
        
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({
                'error': 'Invalid credentials'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        # Verify code
        if is_backup:
            verified = user.verify_backup_code(code)
        else:
            verified = user.verify_2fa_code(code)
        
        if not verified:
            return Response({
                'error': 'Invalid verification code'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        # Generate tokens
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'user': UserSerializer(user).data,
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }
        })
    
    @method_decorator(ratelimit(key='ip', rate='10/m', method='POST'))
    @action(detail=False, methods=['post'])
    def login(self, request):
        if getattr(request, 'limited', False):
            return Response({'error': 'Too many attempts'}, status=429)

        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            # Check if 2FA is enabled
            if user.two_factor_enabled:
                return Response({
                    'requires_2fa': True,
                    'email': user.email,
                    'message': 'Please enter your 2FA code'
                }, status=status.HTTP_202_ACCEPTED)
            
            # No 2FA, proceed with login
            refresh = RefreshToken.for_user(user)
            return Response({
                'user': UserSerializer(user).data,
                'tokens': {
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                }
            })

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # ================= BIOMETRIC =================

    @method_decorator(ratelimit(key='ip', rate='3/m', method='POST'))
    @action(detail=False, methods=['post'])
    def biometric_challenge(self, request):
        """
        Step 1: Generate cryptographic challenge
        """
        email = request.data.get('email')
        device_id = request.data.get('device_id')

        if not email or not device_id:
            return Response({'error': 'email and device_id required'}, status=400)

        try:
            user = User.objects.get(email=email, is_active=True)
            device = BiometricDevice.objects.get(
                user=user,
                device_id=device_id,
                is_active=True
            )
        except (User.DoesNotExist, BiometricDevice.DoesNotExist):
            return Response({'error': 'Invalid credentials'}, status=401)

        challenge = BiometricVerifier.generate_challenge(email)

        return Response({
            'challenge': challenge,
            'credential_id': device.credential_id
        })

    @method_decorator(ratelimit(key='ip', rate='3/m', method='POST'))
    @action(detail=False, methods=['post'])
    def biometric_login(self, request):
        """
        Step 2: Verify biometric signature
        """
        email = request.data.get('email')
        device_id = request.data.get('device_id')
        credential_id = request.data.get('credential_id')
        auth_signature = request.data.get('auth_signature')
        challenge_response = request.data.get('challenge_response')

        if not all([email, device_id, credential_id, auth_signature, challenge_response]):
            return Response({'error': 'Missing fields'}, status=400)

        try:
            user = User.objects.get(email=email, is_active=True)
            device = BiometricDevice.objects.get(
                user=user,
                device_id=device_id,
                credential_id=credential_id,
                is_active=True
            )
        except (User.DoesNotExist, BiometricDevice.DoesNotExist):
            BiometricAuthLog.objects.create(
                status='failed',
                ip_address=self.get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                error_message='Invalid credentials'
            )
            return Response({'error': 'Authentication failed'}, status=401)

        is_valid = BiometricVerifier.verify_signature(
            email=email,
            public_key=device.public_key,
            signature=auth_signature,
            challenge_response=challenge_response
        )

        if not is_valid:
            BiometricAuthLog.objects.create(
                user=user,
                device=device,
                status='failed',
                ip_address=self.get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                error_message='Signature verification failed'
            )
            return Response({'error': 'Authentication failed'}, status=401)

        device.last_used = timezone.now()
        device.save(update_fields=['last_used'])

        BiometricAuthLog.objects.create(
            user=user,
            device=device,
            status='success',
            ip_address=self.get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )

        refresh = RefreshToken.for_user(user)

        return Response({
            'user': UserSerializer(user).data,
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            },
            'message': 'Biometric authentication successful'
        })

    # ================= BIOMETRIC MANAGEMENT =================

    @action(detail=False, methods=['post'])
    def register_biometric(self, request):
        serializer = BiometricRegistrationSerializer(
            data=request.data,
            context={'request': request}
        )

        if serializer.is_valid():
            device = serializer.save(user=request.user)

            request.user.biometric_enabled = True
            request.user.save(update_fields=['biometric_enabled'])

            return Response(
                BiometricDeviceSerializer(device).data,
                status=201
            )

        return Response(serializer.errors, status=400)

    @action(detail=False, methods=['get'])
    def biometric_devices(self, request):
        devices = request.user.biometric_devices.filter(is_active=True)
        return Response(BiometricDeviceSerializer(devices, many=True).data)

    @action(detail=False, methods=['get'])
    def biometric_logs(self, request):
        logs = request.user.biometric_logs.order_by('-created_at')[:20]
        return Response(BiometricAuthLogSerializer(logs, many=True).data)
