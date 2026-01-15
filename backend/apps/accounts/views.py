import logging
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from .models import User, BiometricDevice
from .serializers import (
    UserSerializer,
    BiometricRegistrationSerializer,
    TwoFactorSetupSerializer,
)

logger = logging.getLogger(__name__)


class UserViewSet(viewsets.ModelViewSet):
    """ViewSet for protected user management endpoints."""
    
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['post'])
    def enable_2fa(self, request):
        """Enable two-factor authentication for user."""
        logger.info("🔐 Enable 2FA endpoint called")
        secret = request.user.generate_2fa_secret()
        return Response({
            'secret': secret,
            'qr_code': request.user.get_2fa_qr_code()
        })

    @action(detail=False, methods=['post'])
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

    @action(detail=False, methods=['post'])
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