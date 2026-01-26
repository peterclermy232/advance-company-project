from django.db import models
from apps.accounts.models import User
from .validators import validate_document_file
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
    
    # File field with validator
    file = models.FileField(
        upload_to='documents/%Y/%m/',
        validators=[validate_document_file]
    )
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    rejection_reason = models.TextField(null=True, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-uploaded_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['category']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.user.full_name}"
    
    def save(self, *args, **kwargs):
        """Sanitize filename before saving"""
        if self.file:
            from .validators import SecureFileValidator
            self.file.name = SecureFileValidator.sanitize_filename(self.file.name)
            logger.info(f"Saving document: {self.title} - {self.file.name}")
        
        super().save(*args, **kwargs)
    
    def delete(self, *args, **kwargs):
        """Delete file from Cloudinary when model is deleted"""
        if self.file:
            try:
                self.file.delete(save=False)
                logger.info(f"Deleted file from Cloudinary: {self.file.name}")
            except Exception as e:
                logger.error(f"Error deleting file from Cloudinary: {str(e)}")
        
        super().delete(*args, **kwargs)