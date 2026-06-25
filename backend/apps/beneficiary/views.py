from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from django.db import transaction
from .models import Beneficiary
from .serializers import BeneficiarySerializer, BeneficiaryVerificationSerializer
from apps.notifications.services import NotificationService
import logging

logger = logging.getLogger(__name__)


class BeneficiaryViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing beneficiaries
    Users can create and view their own beneficiaries
    Admins can verify/reject all beneficiaries
    """
    queryset = Beneficiary.objects.all()
    serializer_class = BeneficiarySerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['status', 'relation', 'verification_status']
    search_fields = ['name', 'phone_number']
    ordering_fields = ['created_at', 'name', 'age']
    
    def get_queryset(self):
        """Users see their active/deceased beneficiaries; admins see all."""
        if self.request.user.role == 'admin':
            return Beneficiary.objects.all().select_related('user').order_by('-created_at')
        return Beneficiary.objects.filter(
            user=self.request.user
        ).exclude(status='removed').order_by('-created_at')
    
    def perform_create(self, serializer):
        """Create beneficiary for current user"""
        beneficiary = serializer.save(user=self.request.user)
        
        # Log activity (removed ip_address parameter)
        from apps.reports.models import ActivityLog
        ActivityLog.objects.create(
            user=self.request.user,
            action='beneficiary_added',
            description=f'Added beneficiary: {beneficiary.name} ({beneficiary.get_relation_display()})'
        )
        
        logger.info(f"Beneficiary {beneficiary.uuid} created by user {self.request.user.uuid}")
    
    def perform_update(self, serializer):
        """Update beneficiary"""
        beneficiary = serializer.save()
        
        # Log activity (removed ip_address parameter)
        from apps.reports.models import ActivityLog
        ActivityLog.objects.create(
            user=self.request.user,
            action='beneficiary_updated',
            description=f'Updated beneficiary: {beneficiary.name}'
        )
        
        logger.info(f"Beneficiary {beneficiary.uuid} updated by user {self.request.user.uuid}")
    
    def perform_destroy(self, instance):
        """Soft delete - mark as removed instead of deleting"""
        instance.status = 'removed'
        instance.save()
        
        # Log activity (removed ip_address parameter)
        from apps.reports.models import ActivityLog
        ActivityLog.objects.create(
            user=self.request.user,
            action='beneficiary_removed',
            description=f'Removed beneficiary: {instance.name}'
        )
        
        logger.info(f"Beneficiary {instance.uuid} removed by user {self.request.user.uuid}")
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def pending_verification(self, request):
        """
        Admin endpoint: Get all beneficiaries pending verification
        GET /api/beneficiary/pending_verification/
        """
        if request.user.role != 'admin':
            return Response(
                {'error': 'Admin access required'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        pending = Beneficiary.objects.filter(
            verification_status='pending'
        ).select_related('user').order_by('-created_at')
        
        serializer = self.get_serializer(pending, many=True)
        return Response({
            'count': pending.count(),
            'results': serializer.data
        })
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def verify(self, request, pk=None):
        """
        Admin endpoint: Verify a beneficiary
        POST /api/beneficiary/{id}/verify/
        Body: {
            "notes": "Verification notes (optional)"
        }
        """
        if request.user.role != 'admin':
            return Response(
                {'error': 'Only admins can verify beneficiaries'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        beneficiary = self.get_object()
        
        if beneficiary.verification_status == 'verified':
            return Response(
                {'message': 'Beneficiary is already verified'},
                status=status.HTTP_200_OK
            )
        
        try:
            with transaction.atomic():
                # Update verification status
                beneficiary.verification_status = 'verified'
                beneficiary.save()
                
                # Create notification for user
                NotificationService.create_notification(
                    user=beneficiary.user,
                    notification_type='beneficiary_verified',
                    title='Beneficiary Verified',
                    message=f'Your beneficiary "{beneficiary.name}" has been verified and approved.',
                )
                
                # Log activity (removed ip_address parameter)
                from apps.reports.models import ActivityLog
                ActivityLog.objects.create(
                    user=request.user,
                    action='beneficiary_verified',
                    description=f'Verified beneficiary: {beneficiary.name} for user {beneficiary.user.full_name}'
                )
                
                logger.info(f"Beneficiary {beneficiary.uuid} verified by admin {request.user.uuid}")
                
                serializer = self.get_serializer(beneficiary)
                return Response({
                    'message': 'Beneficiary verified successfully',
                    'beneficiary': serializer.data
                })
                
        except Exception as e:
            logger.error(f"Error verifying beneficiary {beneficiary.uuid}: {str(e)}", exc_info=True)
            return Response(
                {'error': f'Failed to verify beneficiary: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def reject(self, request, pk=None):
        """
        Admin endpoint: Reject a beneficiary
        POST /api/beneficiary/{id}/reject/
        Body: {
            "reason": "Rejection reason (required)"
        }
        """
        if request.user.role != 'admin':
            return Response(
                {'error': 'Only admins can reject beneficiaries'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        beneficiary = self.get_object()
        reason = request.data.get('reason', '')
        
        if not reason:
            return Response(
                {'error': 'Rejection reason is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            with transaction.atomic():
                # Update verification status
                beneficiary.verification_status = 'rejected'
                beneficiary.save()
                
                # Create notification for user
                NotificationService.create_notification(
                    user=beneficiary.user,
                    notification_type='beneficiary_rejected',
                    title='Beneficiary Rejected',
                    message=f'Your beneficiary "{beneficiary.name}" was rejected. Reason: {reason}',
                )
                
                # Log activity (removed ip_address parameter)
                from apps.reports.models import ActivityLog
                ActivityLog.objects.create(
                    user=request.user,
                    action='beneficiary_rejected',
                    description=f'Rejected beneficiary: {beneficiary.name} for user {beneficiary.user.full_name}. Reason: {reason}'
                )
                
                logger.info(f"Beneficiary {beneficiary.uuid} rejected by admin {request.user.uuid}")
                
                serializer = self.get_serializer(beneficiary)
                return Response({
                    'message': 'Beneficiary rejected',
                    'beneficiary': serializer.data
                })
                
        except Exception as e:
            logger.error(f"Error rejecting beneficiary {beneficiary.uuid}: {str(e)}", exc_info=True)
            return Response(
                {'error': f'Failed to reject beneficiary: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def mark_deceased(self, request, pk=None):
        """
        Mark a beneficiary as deceased
        POST /api/beneficiary/{id}/mark_deceased/
        Body: {
            "death_certificate": <file>,
            "death_certificate_number": "DC123456"
        }
        """
        beneficiary = self.get_object()
        
        # Only admin or beneficiary owner can mark as deceased
        if request.user.role != 'admin' and beneficiary.user != request.user:
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            with transaction.atomic():
                beneficiary.status = 'deceased'
                
                # Update death certificate if provided
                if 'death_certificate' in request.FILES:
                    beneficiary.death_certificate = request.FILES['death_certificate']
                
                if 'death_certificate_number' in request.data:
                    beneficiary.death_certificate_number = request.data['death_certificate_number']
                
                beneficiary.save()
                
                # Create notification
                NotificationService.create_notification(
                    user=beneficiary.user,
                    notification_type='beneficiary_deceased',
                    title='Beneficiary Status Updated',
                    message=f'Beneficiary "{beneficiary.name}" has been marked as deceased.',
                )
                
                # Log activity (removed ip_address parameter)
                from apps.reports.models import ActivityLog
                ActivityLog.objects.create(
                    user=request.user,
                    action='beneficiary_deceased',
                    description=f'Marked beneficiary as deceased: {beneficiary.name}'
                )
                
                logger.info(f"Beneficiary {beneficiary.uuid} marked deceased by user {request.user.uuid}")
                
                serializer = self.get_serializer(beneficiary)
                return Response({
                    'message': 'Beneficiary marked as deceased',
                    'beneficiary': serializer.data
                })
                
        except Exception as e:
            logger.error(f"Error marking beneficiary deceased: {str(e)}", exc_info=True)
            return Response(
                {'error': f'Failed to update beneficiary: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """
        Get beneficiary statistics for current user or all (admin)
        GET /api/beneficiary/statistics/
        """
        if request.user.role == 'admin':
            queryset = Beneficiary.objects.all()
        else:
            queryset = Beneficiary.objects.filter(user=request.user)
        
        stats = {
            'total': queryset.count(),
            'active': queryset.filter(status='active').count(),
            'deceased': queryset.filter(status='deceased').count(),
            'removed': queryset.filter(status='removed').count(),
            'verified': queryset.filter(verification_status='verified').count(),
            'pending': queryset.filter(verification_status='pending').count(),
            'rejected': queryset.filter(verification_status='rejected').count(),
            'by_relation': {
                'spouse': queryset.filter(relation='spouse').count(),
                'child': queryset.filter(relation='child').count(),
                'parent': queryset.filter(relation='parent').count(),
                'sibling': queryset.filter(relation='sibling').count(),
                'other': queryset.filter(relation='other').count(),
            }
        }
        
        return Response(stats)
    
    def get_client_ip(self):
        """Get client IP address from request"""
        x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = self.request.META.get('REMOTE_ADDR')
        return ip