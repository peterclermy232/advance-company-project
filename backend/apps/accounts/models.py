from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils import timezone
import secrets

class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Email is required')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', 'admin')
        return self.create_user(email, password, **extra_fields)

class User(AbstractUser):
    ROLE_CHOICES = [
        ('user', 'User'),
        ('admin', 'Administrator'),
    ]
    
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    ]
    
    MARITAL_STATUS_CHOICES = [
        ('single', 'Single'),
        ('married', 'Married'),
        ('divorced', 'Divorced'),
        ('widowed', 'Widowed'),
    ]
    
    username = None
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=15, unique=True)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='user')
    
    # Profile fields
    full_name = models.CharField(max_length=255)
    age = models.IntegerField(null=True, blank=True)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, null=True, blank=True)
    marital_status = models.CharField(max_length=10, choices=MARITAL_STATUS_CHOICES, null=True, blank=True)
    number_of_kids = models.IntegerField(default=0)
    profession = models.CharField(max_length=255, null=True, blank=True)
    salary_range = models.CharField(max_length=50, null=True, blank=True)
    
    # Spouse details
    spouse_name = models.CharField(max_length=255, null=True, blank=True)
    spouse_age = models.IntegerField(null=True, blank=True)
    spouse_profession = models.CharField(max_length=255, null=True, blank=True)
    
    # Documents
    profile_photo = models.ImageField(upload_to='profiles/', null=True, blank=True)
    identity_document = models.FileField(upload_to='identity_docs/', null=True, blank=True)
    
    # Biometric authentication flags
    biometric_enabled = models.BooleanField(default=False)
    fingerprint_enabled = models.BooleanField(default=False)
    face_id_enabled = models.BooleanField(default=False)
    
    # Account status
    is_active = models.BooleanField(default=True)
    activity_status = models.CharField(max_length=20, default='Active')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    objects = UserManager()
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['phone_number', 'full_name']
    
    def __str__(self):
        return self.email


class BiometricDevice(models.Model):
    """
    Stores registered devices for biometric authentication.
    Each device gets a unique credential that's used for verification.
    """
    DEVICE_TYPE_CHOICES = [
        ('fingerprint', 'Fingerprint'),
        ('face_id', 'Face ID'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='biometric_devices')
    device_type = models.CharField(max_length=20, choices=DEVICE_TYPE_CHOICES)
    device_id = models.CharField(max_length=255, help_text="Unique device identifier")
    device_name = models.CharField(max_length=255, help_text="User-friendly device name")
    
    # Credential for this device (not the actual biometric data)
    credential_id = models.CharField(max_length=255, unique=True, editable=False)
    public_key = models.TextField(help_text="Public key for credential verification")
    
    is_active = models.BooleanField(default=True)
    registered_at = models.DateTimeField(auto_now_add=True)
    last_used = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        unique_together = ['user', 'device_id', 'device_type']
        ordering = ['-registered_at']
    
    def __str__(self):
        return f"{self.user.email} - {self.device_name} ({self.device_type})"
    
    def save(self, *args, **kwargs):
        if not self.credential_id:
            self.credential_id = secrets.token_urlsafe(32)
        super().save(*args, **kwargs)


class BiometricAuthLog(models.Model):
    """
    Logs all biometric authentication attempts for security auditing.
    """
    STATUS_CHOICES = [
        ('success', 'Success'),
        ('failed', 'Failed'),
        ('error', 'Error'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='biometric_logs')
    device = models.ForeignKey(BiometricDevice, on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    error_message = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.user.email} - {self.status} at {self.timestamp}"