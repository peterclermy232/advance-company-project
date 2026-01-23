from django.db import models
from apps.accounts.models import User
import logging

logger = logging.getLogger(__name__)


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
    
    # NO VALIDATORS - rely on view-level validation only
    file = models.FileField(upload_to='documents/%Y/%m/')
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    rejection_reason = models.TextField(null=True, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-uploaded_at']
    
    def __str__(self):
        return f"{self.title} - {self.user.full_name}"
    
    def save(self, *args, **kwargs):
        """
        OPTIMIZED: No validation on save
        Just sanitize filename and save
        """
        try:
            if self.file:
                # Only sanitize filename - no validation
                from .validators import SecureFileValidator
                self.file.name = SecureFileValidator.sanitize_filename(self.file.name)
                logger.info(f"Saving document: {self.file.name}")
            
            super().save(*args, **kwargs)
            
        except Exception as e:
            logger.error(f"Error saving document: {str(e)}", exc_info=True)
            raise