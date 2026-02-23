import uuid
from django.db import models
from django.conf import settings


class Report(models.Model):
    uuid = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
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
    description = models.TextField(default='')
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='reports',
    )
    report_type = models.CharField(max_length=20, choices=REPORT_TYPES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')

    date_from = models.DateField(null=True, blank=True)
    date_to = models.DateField(null=True, blank=True)
    generated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='generated_reports',
    )
    file = models.FileField(upload_to='reports/', null=True, blank=True)
    file_url = models.URLField(max_length=500, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title


class ActivityLog(models.Model):
    """
    General-purpose activity log used across the entire app.

    The `action` field uses free text (max_length=100) rather than
    a restricted choices list, because many apps write domain-specific
    action strings such as 'beneficiary_added', 'deposit_created', etc.
    If you want an audit trail with strict choices, add a separate
    AuditLog model and keep this one flexible.
    """
    uuid = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='activity_logs',
    )
    report = models.ForeignKey(
        Report,
        on_delete=models.CASCADE,
        related_name='activities',
        null=True,
        blank=True,
    )

    # Free text — no choices restriction so domain actions like
    # 'beneficiary_added', 'deposit_created' are all valid.
    action = models.CharField(max_length=100)

    description = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user} - {self.action}'