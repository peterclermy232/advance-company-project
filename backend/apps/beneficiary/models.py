from django.db import models
from apps.accounts.models import User

class Beneficiary(models.Model):
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
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='beneficiaries')
    name = models.CharField(max_length=255)
    relation = models.CharField(max_length=20, choices=RELATION_CHOICES)
    age = models.IntegerField()
    gender = models.CharField(max_length=1, choices=User.GENDER_CHOICES)
    phone_number = models.CharField(max_length=15, null=True, blank=True)
    profession = models.CharField(max_length=255, null=True, blank=True)
    salary_range = models.CharField(max_length=50, null=True, blank=True)
    
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
        choices=[('verified', 'Verified'), ('pending', 'Pending'), ('rejected', 'Rejected')],
        default='pending'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = 'Beneficiaries'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} ({self.relation}) - {self.user.full_name}"
