from django.db import models
from apps.accounts.models import User
from .validators import SecureFileValidator
import logging

logger = logging.getLogger(__name__)


def validate_document_file(file):
    """
    Wrapper for file validation
    Returns the file if valid, raises ValidationError if invalid
    """
    try:
        return SecureFileValidator.validate_file(file)
    except Exception as e:
        logger.error(f"File validation error: {str(e)}")
        raise


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
    
    def __str__(self):
        return f"{self.title} - {self.user.full_name}"
    
    def save(self, *args, **kwargs):
        """Override save to sanitize filename before saving"""
        try:
            if self.file:
                self.file.name = SecureFileValidator.sanitize_filename(self.file.name)
                logger.info(f"Saving document: {self.file.name} for user {self.user.email}")
            super().save(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error saving document: {str(e)}", exc_info=True)
            raise