"""
apps/notifications/models.py - Add NotificationPreferences Model
"""
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db.models.signals import post_save
from django.dispatch import receiver

User = get_user_model()


class Notification(models.Model):
    """Existing Notification model - keep as is"""
    NOTIFICATION_TYPES = (
        ('deposit_created', 'Deposit Created'),
        ('deposit_approved', 'Deposit Approved'),
        ('deposit_rejected', 'Deposit Rejected'),
        ('application_submitted', 'Application Submitted'),
        ('application_approved', 'Application Approved'),
        ('application_rejected', 'Application Rejected'),
        ('document_uploaded', 'Document Uploaded'),
        ('document_verified', 'Document Verified'),
        ('document_rejected', 'Document Rejected'),
        ('beneficiary_added', 'Beneficiary Added'),
        ('beneficiary_verified', 'Beneficiary Verified'),
        ('beneficiary_deceased', 'Beneficiary Deceased'),
        ('system', 'System Notification'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=50, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=255)
    message = models.TextField()
    
    related_deposit_id = models.IntegerField(null=True, blank=True)
    related_application_id = models.IntegerField(null=True, blank=True)
    related_user_name = models.CharField(max_length=255, null=True, blank=True)
    
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['user', 'is_read']),
        ]

    def __str__(self):
        return f"{self.user.full_name} - {self.title}"

    @property
    def time_ago(self):
        now = timezone.now()
        diff = now - self.created_at
        
        if diff.days > 30:
            return f"{diff.days // 30} month{'s' if diff.days // 30 > 1 else ''} ago"
        elif diff.days > 0:
            return f"{diff.days} day{'s' if diff.days > 1 else ''} ago"
        elif diff.seconds > 3600:
            return f"{diff.seconds // 3600} hour{'s' if diff.seconds // 3600 > 1 else ''} ago"
        elif diff.seconds > 60:
            return f"{diff.seconds // 60} minute{'s' if diff.seconds // 60 > 1 else ''} ago"
        else:
            return "just now"


class NotificationPreferences(models.Model):
    """
    User notification preferences for different channels
    Auto-created for each user with default settings
    """
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE, 
        related_name='notification_preferences'
    )
    
    # Channel preferences
    email_enabled = models.BooleanField(
        default=True,
        help_text="Receive notifications via email"
    )
    sms_enabled = models.BooleanField(
        default=True,
        help_text="Receive notifications via SMS"
    )
    push_enabled = models.BooleanField(
        default=True,
        help_text="Receive push notifications in-app"
    )
    
    # Specific notification types
    deposit_notifications = models.BooleanField(
        default=True,
        help_text="Notifications about deposits"
    )
    application_notifications = models.BooleanField(
        default=True,
        help_text="Notifications about applications"
    )
    document_notifications = models.BooleanField(
        default=True,
        help_text="Notifications about documents"
    )
    beneficiary_notifications = models.BooleanField(
        default=True,
        help_text="Notifications about beneficiaries"
    )
    
    # Reports
    monthly_reports = models.BooleanField(
        default=True,
        help_text="Receive monthly financial reports"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Notification Preference"
        verbose_name_plural = "Notification Preferences"

    def __str__(self):
        return f"{self.user.full_name}'s Preferences"

    def should_notify(self, notification_type, channel='push'):
        """
        Check if user should receive a notification
        
        Args:
            notification_type: Type of notification (e.g., 'deposit_created')
            channel: Notification channel ('email', 'sms', 'push')
        
        Returns:
            bool: True if notification should be sent
        """
        # Check channel preference
        if channel == 'email' and not self.email_enabled:
            return False
        if channel == 'sms' and not self.sms_enabled:
            return False
        if channel == 'push' and not self.push_enabled:
            return False
        
        # Check notification type preference
        if 'deposit' in notification_type and not self.deposit_notifications:
            return False
        if 'application' in notification_type and not self.application_notifications:
            return False
        if 'document' in notification_type and not self.document_notifications:
            return False
        if 'beneficiary' in notification_type and not self.beneficiary_notifications:
            return False
        
        return True


@receiver(post_save, sender=User)
def create_notification_preferences(sender, instance, created, **kwargs):
    """
    Automatically create notification preferences when a new user is created
    """
    if created:
        NotificationPreferences.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_notification_preferences(sender, instance, **kwargs):
    """
    Ensure preferences are saved when user is saved
    """
    if hasattr(instance, 'notification_preferences'):
        instance.notification_preferences.save()