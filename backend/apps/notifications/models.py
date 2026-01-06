from django.db import models
from apps.accounts.models import User

class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ('deposit_created', 'Deposit Created'),
        ('deposit_approved', 'Deposit Approved'),
        ('deposit_rejected', 'Deposit Rejected'),
        ('application_submitted', 'Application Submitted'),
        ('application_approved', 'Application Approved'),
        ('application_rejected', 'Application Rejected'),
        ('beneficiary_verified', 'Beneficiary Verified'),
        ('document_verified', 'Document Verified'),
        ('document_rejected', 'Document Rejected'),
        ('system', 'System Notification'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=50, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=255)
    message = models.TextField()
    
    # Related objects
    related_deposit_id = models.IntegerField(null=True, blank=True)
    related_application_id = models.IntegerField(null=True, blank=True)
    related_user_name = models.CharField(max_length=255, null=True, blank=True)
    
    # Status
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['user', 'is_read']),
        ]
    
    def __str__(self):
        return f"{self.user.full_name} - {self.title}"
    
    def mark_as_read(self):
        if not self.is_read:
            from django.utils import timezone
            self.is_read = True
            self.read_at = timezone.now()
            self.save()