from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.utils import timezone
from .models import User, BiometricDevice, BiometricAuthLog
from .serializers import (
    UserSerializer, UserRegistrationSerializer, LoginSerializer,
    BiometricDeviceSerializer, BiometricRegistrationSerializer,
    BiometricAuthSerializer, BiometricAuthLogSerializer
)
import secrets

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    
    def get_permissions(self):
        if self.action in ['register', 'login', 'biometric_login']:
            return [AllowAny()]
        return [IsAuthenticated()]
    
    def get_client_ip(self, request):
        """Get client IP address from request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def register(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            refresh = RefreshToken.for_user(user)
            return Response({
                'user': UserSerializer(user).data,
                'tokens': {
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                }
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def login(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            refresh = RefreshToken.for_user(user)
            return Response({
                'user': UserSerializer(user).data,
                'tokens': {
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                }
            })
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def me(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)
    
    @action(detail=False, methods=['put', 'patch'])
    def update_profile(self, request):
        serializer = UserSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    # ==================== BIOMETRIC AUTHENTICATION ====================
    
    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def biometric_challenge(self, request):
        """
        Generate a challenge for biometric authentication.
        The client device will sign this challenge after biometric verification.
        """
        email = request.data.get('email')
        device_id = request.data.get('device_id')
        
        if not email or not device_id:
            return Response(
                {'error': 'Email and device_id are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            user = User.objects.get(email=email, is_active=True)
            device = BiometricDevice.objects.get(
                user=user,
                device_id=device_id,
                is_active=True
            )
        except (User.DoesNotExist, BiometricDevice.DoesNotExist):
            return Response(
                {'error': 'Invalid credentials'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        # Generate a random challenge
        challenge = secrets.token_urlsafe(32)
        
        # In production, store this challenge in cache (Redis) with expiration
        # request.session['biometric_challenge'] = challenge
        
        return Response({
            'challenge': challenge,
            'credential_id': device.credential_id
        })
    
    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def biometric_login(self, request):
        """
        Authenticate user using biometric credentials.
        The device verifies the biometric and sends proof of verification.
        """
        serializer = BiometricAuthSerializer(data=request.data)
        
        if serializer.is_valid():
            user = serializer.validated_data['user']
            device = serializer.validated_data['device']
            
            # Update device last used time
            device.last_used = timezone.now()
            device.save(update_fields=['last_used'])
            
            # Log successful authentication
            BiometricAuthLog.objects.create(
                user=user,
                device=device,
                status='success',
                ip_address=self.get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            # Generate tokens
            refresh = RefreshToken.for_user(user)
            
            return Response({
                'user': UserSerializer(user).data,
                'tokens': {
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                },
                'message': 'Biometric authentication successful'
            })
        
        # Log failed authentication attempt
        email = request.data.get('email')
        if email:
            try:
                user = User.objects.get(email=email)
                BiometricAuthLog.objects.create(
                    user=user,
                    status='failed',
                    ip_address=self.get_client_ip(request),
                    user_agent=request.META.get('HTTP_USER_AGENT', ''),
                    error_message=str(serializer.errors)
                )
            except User.DoesNotExist:
                pass
        
        return Response(serializer.errors, status=status.HTTP_401_UNAUTHORIZED)
    
    @action(detail=False, methods=['post'])
    def register_biometric(self, request):
        """
        Register a new biometric device for the authenticated user.
        """
        serializer = BiometricRegistrationSerializer(
            data=request.data,
            context={'request': request}
        )
        
        if serializer.is_valid():
            device = BiometricDevice.objects.create(
                user=request.user,
                device_type=serializer.validated_data['device_type'],
                device_id=serializer.validated_data['device_id'],
                device_name=serializer.validated_data['device_name'],
                public_key=serializer.validated_data['public_key']
            )
            
            # Update user's biometric flags
            if device.device_type == 'fingerprint':
                request.user.fingerprint_enabled = True
            elif device.device_type == 'face_id':
                request.user.face_id_enabled = True
            
            request.user.biometric_enabled = True
            request.user.save(update_fields=[
                'biometric_enabled', 'fingerprint_enabled', 'face_id_enabled'
            ])
            
            return Response(
                BiometricDeviceSerializer(device).data,
                status=status.HTTP_201_CREATED
            )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def biometric_devices(self, request):
        """Get all registered biometric devices for the current user."""
        devices = request.user.biometric_devices.filter(is_active=True)
        serializer = BiometricDeviceSerializer(devices, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['delete'])
    def remove_biometric(self, request):
        """Remove a biometric device."""
        device_id = request.data.get('device_id')
        
        if not device_id:
            return Response(
                {'error': 'device_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            device = BiometricDevice.objects.get(
                user=request.user,
                device_id=device_id,
                is_active=True
            )
            device.is_active = False
            device.save(update_fields=['is_active'])
            
            # Update user's biometric flags if no devices of this type remain
            active_devices = request.user.biometric_devices.filter(is_active=True)
            
            if not active_devices.filter(device_type='fingerprint').exists():
                request.user.fingerprint_enabled = False
            
            if not active_devices.filter(device_type='face_id').exists():
                request.user.face_id_enabled = False
            
            if not active_devices.exists():
                request.user.biometric_enabled = False
            
            request.user.save(update_fields=[
                'biometric_enabled', 'fingerprint_enabled', 'face_id_enabled'
            ])
            
            return Response({'message': 'Biometric device removed successfully'})
        
        except BiometricDevice.DoesNotExist:
            return Response(
                {'error': 'Device not found'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=False, methods=['get'])
    def biometric_logs(self, request):
        """Get biometric authentication logs for the current user."""
        logs = request.user.biometric_logs.all()[:20]  # Last 20 attempts
        serializer = BiometricAuthLogSerializer(logs, many=True)
        return Response(serializer.data)