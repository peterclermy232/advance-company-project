import uuid
from django.db import models
from apps.accounts.models import User


class Application(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    APPLICATION_TYPE_CHOICES = [
        # Membership
        ('new_membership', 'New Membership Application'),
        ('membership_withdrawal', 'Membership Withdrawal'),
        ('membership_transfer', 'Membership Transfer'),

        # Loans
        ('loan', 'Loan Application'),
        ('loan_top_up', 'Loan Top-Up'),
        ('loan_restructure', 'Loan Restructuring'),

        # Savings / Contributions
        ('withdrawal', 'Savings Withdrawal'),
        ('contribution_change', 'Contribution Amount Change'),

        # Personal Details
        ('beneficiary_update', 'Beneficiary Update'),
        ('personal_details_change', 'Personal Details Change'),
        ('next_of_kin_update', 'Next of Kin Update'),

        # Other
        ('statement_request', 'Account Statement Request'),
        ('other', 'Other'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('under_review', 'Under Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    user = models.ForeignKey(
        User,
        to_field='uuid',            # User PK is named 'uuid', not 'id'
        db_column='user_id',
        on_delete=models.CASCADE,
        related_name='applications'
    )
    application_type = models.CharField(max_length=50, choices=APPLICATION_TYPE_CHOICES)
    reason = models.TextField()
    supporting_document = models.FileField(
        upload_to='applications/',
        null=True,
        blank=True
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    admin_comments = models.TextField(null=True, blank=True)

    # Approval workflow
    submitted_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(
        User,
        to_field='uuid',            # same here
        db_column='reviewed_by_id',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_applications'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.full_name} - {self.application_type} - {self.status}"


class ApplicationActivity(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    application = models.ForeignKey(
        Application,
        on_delete=models.CASCADE,
        related_name='activities'
        # Application.id IS named 'id' — no to_field needed
    )
    user = models.ForeignKey(
        User,
        to_field='uuid',            # User PK is named 'uuid', not 'id'
        db_column='user_id',
        on_delete=models.CASCADE,
        related_name='application_activities'
    )
    action = models.CharField(max_length=50)
    notes = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'Application Activities'

    def __str__(self):
        return f"{self.application} - {self.action}"