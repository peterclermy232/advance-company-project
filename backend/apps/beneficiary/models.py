import uuid
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from apps.accounts.models import User

class Beneficiary(models.Model):
    uuid = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    RELATION_CHOICES = [
        ('spouse', 'Spouse'),
        ('child', 'Child'),
        ('parent', 'Parent'),
        ('sibling', 'Sibling'),
        ('other', 'Other'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('deceased', 'Deceased'),
        ('removed', 'Removed'),
    ]
    
    VERIFICATION_CHOICES = [
        ('verified', 'Verified'),
        ('pending', 'Pending'),
        ('rejected', 'Rejected')
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='beneficiaries')
    name = models.CharField(max_length=255)
    relation = models.CharField(max_length=20, choices=RELATION_CHOICES)
    age = models.IntegerField()
    gender = models.CharField(max_length=1, choices=User.GENDER_CHOICES)
    phone_number = models.CharField(max_length=15, null=True, blank=True)
    profession = models.CharField(max_length=255, null=True, blank=True)
    salary_range = models.CharField(max_length=50, null=True, blank=True)
    
    # Allocation percentage (0-100)
    percentage_allocation = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0.00,
        validators=[
            MinValueValidator(0.00),
            MaxValueValidator(100.00)
        ],
        help_text="Percentage of contributions allocated to this beneficiary (0-100)"
    )
    
    # Documents
    identity_document = models.FileField(upload_to='beneficiary_docs/')
    birth_certificate = models.FileField(upload_to='beneficiary_docs/', null=True, blank=True)
    death_certificate = models.FileField(upload_to='beneficiary_docs/', null=True, blank=True)
    death_certificate_number = models.CharField(max_length=100, null=True, blank=True)
    additional_documents = models.FileField(upload_to='beneficiary_docs/', null=True, blank=True)
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    verification_status = models.CharField(
        max_length=20,
        choices=VERIFICATION_CHOICES,
        default='pending'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = 'Beneficiaries'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} ({self.relation}) - {self.user.full_name} - {self.percentage_allocation}%"
    
    def clean(self):
        """Validate that total allocation for user doesn't exceed 100%"""
        if self.percentage_allocation is not None:
            # Get all other active beneficiaries for this user
            other_beneficiaries = Beneficiary.objects.filter(
                user=self.user,
                status='active'
            ).exclude(pk=self.pk)
            
            # Calculate total allocation
            total_allocation = sum(
                b.percentage_allocation for b in other_beneficiaries
                if b.percentage_allocation is not None
            )
            total_allocation += self.percentage_allocation
            
            if total_allocation > 100:
                raise ValidationError({
                    'percentage_allocation': f'Total allocation cannot exceed 100%. '
                    f'Current total: {total_allocation}%'
                })
    
    def save(self, *args, **kwargs):
        """Override save to run validation"""
        self.clean()
        super().save(*args, **kwargs)