from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from .models import Application, ApplicationActivity
from .serializers import ApplicationSerializer, ApplicationActivitySerializer

class ApplicationViewSet(viewsets.ModelViewSet):
    queryset = Application.objects.all()
    serializer_class = ApplicationSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['application_type', 'status']
    search_fields = ['user__full_name', 'reason']
    ordering_fields = ['created_at', 'updated_at']
    
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
    
    @action(detail=True, methods=['post'])
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
        
        return Response({'message': 'Application approved successfully'})
    
    @action(detail=True, methods=['post'])
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
        
        return Response({'message': 'Application rejected'})
    
    @action(detail=True, methods=['post'])
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
