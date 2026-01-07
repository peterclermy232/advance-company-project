"""
apps/notifications/views.py
Complete notification system with all processes
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.db.models import Q
from .models import Notification
from .serializers import NotificationSerializer


class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for managing user notifications
    Includes: list, retrieve, mark_as_read, mark_all_as_read, unread_count, recent, clear_all
    """
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Return notifications for the current user, ordered by creation date"""
        return Notification.objects.filter(
            user=self.request.user
        ).select_related('user').order_by('-created_at')

    def list(self, request, *args, **kwargs):
        """
        GET /api/notifications/
        Returns paginated list of all notifications for the user
        """
        queryset = self.get_queryset()
        page = self.paginate_queryset(queryset)
        
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def retrieve(self, request, *args, **kwargs):
        """
        GET /api/notifications/{id}/
        Returns a single notification detail
        """
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def unread(self, request):
        """
        GET /api/notifications/unread/
        Returns only unread notifications
        """
        queryset = self.get_queryset().filter(is_read=False)
        page = self.paginate_queryset(queryset)
        
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def unread_count(self, request):
        """
        GET /api/notifications/unread_count/
        Returns count of unread notifications
        """
        count = self.get_queryset().filter(is_read=False).count()
        return Response({'count': count})

    @action(detail=False, methods=['get'])
    def recent(self, request):
        """
        GET /api/notifications/recent/
        Returns the 10 most recent notifications (for dropdown)
        """
        queryset = self.get_queryset()[:10]
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def mark_as_read(self, request, pk=None):
        """
        POST /api/notifications/{id}/mark_as_read/
        Marks a single notification as read
        """
        notification = self.get_object()
        
        if notification.is_read:
            return Response(
                {'message': 'Notification already marked as read'},
                status=status.HTTP_200_OK
            )
        
        notification.is_read = True
        notification.read_at = timezone.now()
        notification.save()
        
        serializer = self.get_serializer(notification)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def mark_all_as_read(self, request):
        """
        POST /api/notifications/mark_all_as_read/
        Marks all user notifications as read
        """
        updated_count = self.get_queryset().filter(
            is_read=False
        ).update(
            is_read=True,
            read_at=timezone.now()
        )
        
        return Response({
            'message': f'{updated_count} notifications marked as read',
            'count': updated_count
        })

    @action(detail=False, methods=['delete'])
    def clear_all(self, request):
        """
        DELETE /api/notifications/clear_all/
        Deletes all READ notifications for the user
        Only removes notifications that have been read
        """
        deleted_count, _ = self.get_queryset().filter(
            is_read=True
        ).delete()
        
        return Response({
            'message': f'{deleted_count} read notifications cleared',
            'count': deleted_count
        })

    @action(detail=True, methods=['delete'])
    def delete_notification(self, request, pk=None):
        """
        DELETE /api/notifications/{id}/
        Deletes a specific notification
        """
        notification = self.get_object()
        notification.delete()
        
        return Response(
            {'message': 'Notification deleted successfully'},
            status=status.HTTP_204_NO_CONTENT
        )