from django.db import models
from django.conf import settings


class Report(models.Model):
    REPORT_TYPES = (
        ('BUG', 'Bug'),
        ('FEEDBACK', 'Feedback'),
        ('COMPLAINT', 'Complaint'),
        ('REQUEST', 'Request'),
        ('FINANCIAL', 'Financial Report'),
        ('COMPENSATORY', 'Compensatory Report'),  
        ('ACTIVITY', 'Activity Log'),  
    )

    STATUS_CHOICES = (
        ('PENDING', 'Pending'),
        ('IN_PROGRESS', 'In Progress'),
        ('RESOLVED', 'Resolved'),
        ('REJECTED', 'Rejected'),
    )

    title = models.CharField(max_length=255)
    # Add permanent default here
    description = models.TextField(default='')  

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='reports'
    )

    report_type = models.CharField(
        max_length=20,
        choices=REPORT_TYPES
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='PENDING'
    )
    # Added fields
    date_from = models.DateField(null=True, blank=True)
    date_to = models.DateField(null=True, blank=True)
    generated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='generated_reports'
    )

# Add this for storing generated report files
    file = models.FileField(upload_to='reports/', null=True, blank=True)

    # New field to store Cloudinary URL
    file_url = models.URLField(max_length=500, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title


class ActivityLog(models.Model):
    ACTION_CHOICES = (
        ('CREATED', 'Created'),
        ('UPDATED', 'Updated'),
        ('STATUS_CHANGED', 'Status Changed'),
        ('DELETED', 'Deleted'),
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='activity_logs'
    )

    report = models.ForeignKey(
        Report,
        on_delete=models.CASCADE,
        related_name='activities',
        null=True,
        blank=True
    )

    action = models.CharField(
        max_length=50,
        choices=ACTION_CHOICES
    )

    description = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user} - {self.action}"
