from rest_framework import serializers
from .models import Notification

class NotificationSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.full_name', read_only=True)
    time_ago = serializers.SerializerMethodField()
    
    class Meta:
        model = Notification
        fields = [
            'id', 'user', 'user_name', 'notification_type', 'title', 
            'message', 'related_deposit_id', 'related_application_id',
            'related_user_name', 'is_read', 'read_at', 'created_at', 'time_ago'
        ]
        read_only_fields = ['user', 'created_at', 'read_at']
    
    def get_time_ago(self, obj):
        """Calculate time elapsed since notification creation"""
        from django.utils import timezone
        now = timezone.now()
        diff = now - obj.created_at
        
        if diff.days > 0:
            return f"{diff.days}d ago"
        elif diff.seconds >= 3600:
            return f"{diff.seconds // 3600}h ago"
        elif diff.seconds >= 60:
            return f"{diff.seconds // 60}m ago"
        else:
            return "Just now"