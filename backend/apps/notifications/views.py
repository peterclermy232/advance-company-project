from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from .models import Notification
from .serializers import NotificationSerializer

class NotificationViewSet(viewsets.ModelViewSet):
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Return notifications for the current user"""
        return Notification.objects.filter(user=self.request.user)
    
    @action(detail=False, methods=['get'])
    def unread(self, request):
        """Get all unread notifications"""
        notifications = self.get_queryset().filter(is_read=False)
        serializer = self.get_serializer(notifications, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def unread_count(self, request):
        """Get count of unread notifications"""
        count = self.get_queryset().filter(is_read=False).count()
        return Response({'count': count})
    
    @action(detail=True, methods=['post'])
    def mark_as_read(self, request, pk=None):
        """Mark a single notification as read"""
        notification = self.get_object()
        notification.mark_as_read()
        serializer = self.get_serializer(notification)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def mark_all_as_read(self, request):
        """Mark all notifications as read"""
        notifications = self.get_queryset().filter(is_read=False)
        updated = notifications.update(
            is_read=True,
            read_at=timezone.now()
        )
        return Response({
            'message': f'{updated} notifications marked as read',
            'count': updated
        })
    
    @action(detail=False, methods=['delete'])
    def clear_all(self, request):
        """Delete all read notifications"""
        deleted = self.get_queryset().filter(is_read=True).delete()
        return Response({
            'message': 'All read notifications cleared',
            'count': deleted[0]
        })
    
    @action(detail=False, methods=['get'])
    def recent(self, request):
        """Get recent notifications (last 20)"""
        notifications = self.get_queryset()[:20]
        serializer = self.get_serializer(notifications, many=True)
        return Response(serializer.data)