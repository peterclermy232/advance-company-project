from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.utils import timezone
from .models import Application, ApplicationActivity
from .serializers import ApplicationSerializer, ApplicationActivitySerializer
from apps.notifications.services import NotificationService

TYPE_DESCRIPTIONS = {
    # Membership
    'new_membership': 'Apply to become a new member of the SACCO',
    'membership_withdrawal': 'Request to withdraw your membership from the SACCO',
    'membership_transfer': 'Transfer your membership to another branch or category',
    
    # Loans
    'loan': 'Apply for a loan against your contributions',
    'loan_top_up': 'Request an additional amount on top of your existing loan',
    'loan_restructure': 'Request to restructure your existing loan repayment terms',
    
    # Savings / Contributions
    'withdrawal': 'Request to withdraw from your savings account',
    'contribution_change': 'Request to change your monthly contribution amount',
    
    # Personal Details
    'beneficiary_update': 'Update or change your beneficiary information',
    'personal_details_change': 'Update your personal details such as name or contact',
    'next_of_kin_update': 'Update your next of kin information',
    
    # Other
    'statement_request': 'Request an account statement for a specific period',
    'other': 'Any other application or request not listed above',
}

class ApplicationViewSet(viewsets.ModelViewSet):
    queryset = Application.objects.all()
    serializer_class = ApplicationSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['application_type', 'status']
    search_fields = ['user__full_name', 'reason']
    ordering_fields = ['created_at', 'updated_at']
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    
    def get_queryset(self):
        if self.request.user.role == 'admin':
            return Application.objects.all()
        return Application.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        application = serializer.save(user=self.request.user)
        ApplicationActivity.objects.create(
            application=application,
            user=self.request.user,
            action='submitted',
            notes='Application submitted'
        )
        NotificationService.notify_application_submitted(application)

    # ---- NEW ----
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def choices(self, request):
        return Response({
            'application_types': [
                {
                    'value': value,
                    'label': label,
                    'description': TYPE_DESCRIPTIONS.get(value, ''),
                }
                for value, label in Application.APPLICATION_TYPE_CHOICES
            ],
            'status_choices': [
                {'value': value, 'label': label}
                for value, label in Application.STATUS_CHOICES
            ]
        })
    # ---- END NEW ----
        
    @action(detail=True, methods=['post'], parser_classes=[JSONParser, MultiPartParser, FormParser])
    def approve(self, request, pk=None):
        if request.user.role != 'admin':
            return Response(
                {'error': 'Only admins can approve applications'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        application = self.get_object()
        application.status = 'approved'
        application.reviewed_by = request.user
        application.approved_at = timezone.now()
        application.admin_comments = request.data.get('comments', '')
        application.save()
        
        ApplicationActivity.objects.create(
            application=application,
            user=request.user,
            action='approved',
            notes=request.data.get('comments', '')
        )
        NotificationService.notify_application_approved(application)
        
        return Response({'message': 'Application approved successfully'})
    
    @action(detail=True, methods=['post'], parser_classes=[JSONParser, MultiPartParser, FormParser])
    def reject(self, request, pk=None):
        if request.user.role != 'admin':
            return Response(
                {'error': 'Only admins can reject applications'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        application = self.get_object()
        application.status = 'rejected'
        application.reviewed_by = request.user
        application.reviewed_at = timezone.now()
        application.admin_comments = request.data.get('comments', '')
        application.save()
        
        ApplicationActivity.objects.create(
            application=application,
            user=request.user,
            action='rejected',
            notes=request.data.get('comments', '')
        )
        NotificationService.notify_application_rejected(application, request.data.get('comments', ''))

        return Response({'message': 'Application rejected'})
    
    @action(detail=True, methods=['post'], parser_classes=[JSONParser, MultiPartParser, FormParser])
    def review(self, request, pk=None):
        if request.user.role != 'admin':
            return Response(
                {'error': 'Only admins can review applications'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        application = self.get_object()
        application.status = 'under_review'
        application.reviewed_by = request.user
        application.reviewed_at = timezone.now()
        application.save()
        
        ApplicationActivity.objects.create(
            application=application,
            user=request.user,
            action='under_review',
            notes='Application under review'
        )
        
        return Response({'message': 'Application marked as under review'})