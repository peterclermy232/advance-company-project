from django.db import models
from apps.accounts.models import User

class Document(models.Model):
    CATEGORY_CHOICES = [
        ('identity', 'Identity'),
        ('beneficiary', 'Beneficiary'),
        ('birth_certificate', 'Birth Certificate'),
        ('death_certificate', 'Death Certificate'),
        ('additional', 'Additional'),
    ]
    
    STATUS_CHOICES = [
        ('verified', 'Verified'),
        ('pending', 'Pending'),
        ('rejected', 'Rejected'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='documents')
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    title = models.CharField(max_length=255)
    file = models.FileField(upload_to='documents/%Y/%m/')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    rejection_reason = models.TextField(null=True, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-uploaded_at']
    
    def __str__(self):
        return f"{self.title} - {self.user.full_name}"
