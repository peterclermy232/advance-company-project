import logging
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.contrib.auth import authenticate

from .models import User, BiometricDevice
from .serializers import (
    UserSerializer,
    BiometricRegistrationSerializer,
    TwoFactorSetupSerializer,
    BiometricDeviceSerializer,
)
from .response_utils import APIResponse, Messages

logger = logging.getLogger(__name__)


class UserViewSet(viewsets.ModelViewSet):
    """ViewSet for protected user management endpoints."""
    
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_queryset(self):
        """Users can only access their own data unless admin."""
        if self.request.user.is_staff or self.request.user.role == 'admin':
            return User.objects.all()
        return User.objects.filter(id=self.request.user.uuid)

    def update(self, request, *args, **kwargs):
        """Override update to handle profile photo upload."""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        
        # Ensure user can only update their own profile unless admin
        if instance.uuid != request.user.uuid and not (request.user.is_staff or request.user.role == 'admin'):
            return Response(
                {'error': 'You do not have permission to update this profile.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        
        logger.info(f"✅ Profile updated for user {instance.email}")
        return APIResponse.success(Messages.PROFILE_UPDATED, data=serializer.data)

    def partial_update(self, request, *args, **kwargs):
        """Handle PATCH requests."""
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)

    @action(detail=False, methods=['post'])
    def change_password(self, request):
        """Change user password."""
        logger.info(f"🔑 Change password endpoint called for user {request.user.email}")
        
        current_password = request.data.get('current_password')
        new_password = request.data.get('new_password')
        confirm_password = request.data.get('confirm_password')
        
        # Validate required fields
        if not all([current_password, new_password, confirm_password]):
            return Response(
                {'error': 'All fields are required.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Verify current password
        if not request.user.check_password(current_password):
            return Response(
                {'error': 'Current password is incorrect.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if new password matches confirmation
        if new_password != confirm_password:
            return Response(
                {'error': 'New passwords do not match.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if new password is same as current
        if current_password == new_password:
            return Response(
                {'error': 'New password must be different from current password.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate password strength
        try:
            validate_password(new_password, request.user)
        except DjangoValidationError as e:
            return Response(
                {'error': list(e.messages)},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Set new password
        request.user.set_password(new_password)
        request.user.save()
        
        logger.info(f"✅ Password changed successfully for user {request.user.email}")
        
        return Response({
            'message': 'Password changed successfully. Please login with your new password.'
        })

    @action(detail=False, methods=['post'])
    def enable_2fa(self, request):
        """Enable two-factor authentication for user."""
        logger.info(f"🔐 Enable 2FA endpoint called for user {request.user.email}")
        
        if request.user.two_factor_enabled:
            return Response(
                {'error': 'Two-factor authentication is already enabled.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        secret = request.user.generate_2fa_secret()
        qr_code = request.user.get_2fa_qr_code()
        
        return APIResponse.success(
            'Scan the QR code with your authenticator app and enter the code to confirm.',
            data={'secret': secret, 'qr_code': qr_code}
        )

    @action(detail=False, methods=['post'])
    def confirm_2fa(self, request):
        """Confirm 2FA setup with verification code."""
        logger.info(f"✅ Confirm 2FA endpoint called for user {request.user.email}")
        
        serializer = TwoFactorSetupSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        if not request.user.verify_2fa_code(serializer.validated_data['code']):
            return Response(
                {'error': 'Invalid verification code. Please try again.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        request.user.two_factor_enabled = True
        backup_codes = request.user.generate_backup_codes()
        request.user.save(update_fields=['two_factor_enabled', 'backup_codes'])
        
        logger.info(f"✅ 2FA enabled successfully for user {request.user.email}")
        
        return Response({
            'message': 'Two-factor authentication enabled successfully.',
            'backup_codes': backup_codes,
            'note': 'Save these backup codes in a safe place. Each code can only be used once.'
        })

    @action(detail=False, methods=['post'])
    def disable_2fa(self, request):
        """Disable two-factor authentication."""
        logger.info(f"🔐 Disable 2FA endpoint called for user {request.user.email}")
        
        password = request.data.get('password')
        
        if not password:
            return Response(
                {'error': 'Password is required to disable 2FA.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not request.user.check_password(password):
            return Response(
                {'error': 'Invalid password.'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        request.user.two_factor_enabled = False
        request.user.two_factor_secret = None
        request.user.backup_codes = None
        request.user.save(update_fields=['two_factor_enabled', 'two_factor_secret', 'backup_codes'])
        
        logger.info(f"✅ 2FA disabled for user {request.user.email}")
        
        return Response({
            'message': 'Two-factor authentication has been disabled.'
        })

    @action(detail=False, methods=['get'])
    def regenerate_backup_codes(self, request):
        """Regenerate backup codes for 2FA."""
        logger.info(f"🔄 Regenerate backup codes called for user {request.user.email}")
        
        if not request.user.two_factor_enabled:
            return Response(
                {'error': 'Two-factor authentication is not enabled.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        backup_codes = request.user.generate_backup_codes()
        request.user.save(update_fields=['backup_codes'])
        
        return Response({
            'message': 'New backup codes generated successfully.',
            'backup_codes': backup_codes,
            'note': 'Old backup codes are no longer valid. Save these new codes in a safe place.'
        })

    @action(detail=False, methods=['post'])
    def register_biometric(self, request):
        """Register biometric device for user."""
        logger.info(f"👆 Register biometric endpoint called for user {request.user.email}")
        
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
        
        # Update user's biometric enabled status
        if not request.user.biometric_enabled:
            request.user.biometric_enabled = True
            request.user.save(update_fields=['biometric_enabled'])
        
        logger.info(f"✅ Biometric device registered for user {request.user.email}")
        
        return Response(
            BiometricDeviceSerializer(device).data, 
            status=status.HTTP_201_CREATED
        )

    @action(detail=False, methods=['get'])
    def biometric_devices(self, request):
        """Get list of registered biometric devices."""
        devices = BiometricDevice.objects.filter(user=request.user, is_active=True)
        serializer = BiometricDeviceSerializer(devices, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['delete'], url_path='biometric-devices/(?P<device_id>[^/.]+)')
    def remove_biometric_device(self, request, pk=None, device_id=None):
        """Remove a biometric device."""
        try:
            device = BiometricDevice.objects.get(
                user=request.user,
                id=device_id,
                is_active=True
            )
            device.is_active = False
            device.save()
            
            # Check if user has any active biometric devices left
            active_devices = BiometricDevice.objects.filter(
                user=request.user,
                is_active=True
            ).exists()
            
            if not active_devices:
                request.user.biometric_enabled = False
                request.user.save(update_fields=['biometric_enabled'])
            
            logger.info(f"✅ Biometric device removed for user {request.user.email}")
            
            return Response({
                'message': 'Biometric device removed successfully.'
            })
        except BiometricDevice.DoesNotExist:
            return Response(
                {'error': 'Device not found.'},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=False, methods=['get'])
    def profile(self, request):
        """Get current user's profile."""
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    @action(detail=False, methods=['delete'])
    def delete_account(self, request):
        """Delete user account."""
        logger.info(f"🗑️ Delete account endpoint called for user {request.user.email}")
        
        password = request.data.get('password')
        confirmation = request.data.get('confirmation')
        
        if not password:
            return Response(
                {'error': 'Password is required to delete account.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if confirmation != 'DELETE':
            return Response(
                {'error': 'Please type DELETE to confirm account deletion.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not request.user.check_password(password):
            return Response(
                {'error': 'Invalid password.'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        # Soft delete - deactivate account
        request.user.is_active = False
        request.user.save()
        
        logger.info(f"✅ Account deleted for user {request.user.email}")
        
        return Response({
            'message': 'Your account has been deleted successfully.'
        })
    
    @action(detail=False, methods=['post'], parser_classes=[MultiPartParser, FormParser])
    def upload_profile_photo(self, request):
        """
        Upload profile photo for current user
        POST /api/auth/users/upload_profile_photo/
        """
        logger.info(f"📸 Upload profile photo called for user {request.user.email}")

        if 'profile_photo' not in request.FILES:
            return Response(
                {'error': 'No profile photo provided'},
                status=status.HTTP_400_BAD_REQUEST
            )

        profile_photo = request.FILES['profile_photo']

        # Validate file size (max 5MB)
        if profile_photo.size > 5 * 1024 * 1024:
            return Response(
                {'error': 'File size too large. Maximum size is 5MB'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Validate file type
        allowed_types = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif']
        if profile_photo.content_type not in allowed_types:
            return Response(
                {'error': 'Invalid file type. Only JPEG, PNG, and GIF are allowed'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            if request.user.profile_photo:
                try:
                    request.user.profile_photo.delete(save=False)
                except Exception:
                    pass  # don't block upload if old file removal fails

            request.user.profile_photo = profile_photo
            request.user.save(update_fields=['profile_photo'])

            serializer = self.get_serializer(request.user)
            return APIResponse.success(
                Messages.PROFILE_PHOTO_UPLOADED,
                data={'user': serializer.data}
            )

        except Exception as e:
            logger.error(f"❌ Error uploading profile photo: {str(e)}", exc_info=True)
            return Response(
                {'error': 'Failed to upload profile photo'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['delete'])
    def delete_profile_photo(self, request):
        """
        Delete profile photo for current user
        DELETE /api/auth/users/delete_profile_photo/
        """
        logger.info(f"🗑️ Delete profile photo called for user {request.user.email}")

        try:
            if not request.user.profile_photo:
                return Response(
                    {'error': 'No profile photo to delete'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            request.user.profile_photo.delete(save=False)
            request.user.profile_photo = None
            request.user.save(update_fields=['profile_photo'])

            return APIResponse.success(Messages.PROFILE_PHOTO_DELETED)

        except Exception as e:
            logger.error(f"❌ Error deleting profile photo: {str(e)}", exc_info=True)
            return Response(
                {'error': 'Failed to delete profile photo'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
