import os
import secrets
from datetime import timedelta
import uuid

from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils import timezone


# ==========================
# Upload path helpers
# ==========================
def user_profile_photo_path(instance, filename):
    ext = filename.split('.')[-1]
    filename = f"user_{instance.uuid}_{timezone.now().strftime('%Y%m%d_%H%M%S')}.{ext}"
    return os.path.join('profiles', filename)


# ==========================
# Custom User Manager
# ==========================
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


# ==========================
# Custom User Model
# ==========================
class User(AbstractUser):
    username = None

    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

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

    # Auth
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=15, unique=True)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='user')

    # Profile
    full_name = models.CharField(max_length=255)
    age = models.IntegerField(null=True, blank=True)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, null=True, blank=True)
    marital_status = models.CharField(
        max_length=10, choices=MARITAL_STATUS_CHOICES, null=True, blank=True
    )
    number_of_kids = models.IntegerField(default=0)
    profession = models.CharField(max_length=255, null=True, blank=True)
    salary_range = models.CharField(max_length=50, null=True, blank=True)

    # Spouse
    spouse_name = models.CharField(max_length=255, null=True, blank=True)
    spouse_age = models.IntegerField(null=True, blank=True)
    spouse_profession = models.CharField(max_length=255, null=True, blank=True)

    # Files
    profile_photo = models.ImageField(
        upload_to=user_profile_photo_path,
        null=True,
        blank=True,
        help_text='JPEG, PNG, GIF (Max 5MB)',
    )
    identity_document = models.FileField(upload_to='identity_docs/', null=True, blank=True)

    # Biometric
    biometric_enabled = models.BooleanField(default=False)
    fingerprint_enabled = models.BooleanField(default=False)
    face_id_enabled = models.BooleanField(default=False)

    # Status
    is_active = models.BooleanField(default=True)
    activity_status = models.CharField(max_length=20, default='Active')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Email verification
    email_verified = models.BooleanField(default=False)
    email_verification_token = models.CharField(max_length=64, blank=True, null=True)
    email_verification_sent_at = models.DateTimeField(blank=True, null=True)

    # 2FA
    two_factor_enabled = models.BooleanField(default=False)
    two_factor_secret = models.CharField(max_length=32, blank=True, null=True)
    backup_codes = models.JSONField(default=list, blank=True)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['phone_number', 'full_name']

    def __str__(self):
        return self.email

    # ==========================
    # Email verification
    # ==========================
    def generate_verification_token(self):
        self.email_verification_token = secrets.token_urlsafe(32)
        self.email_verification_sent_at = timezone.now()
        self.save(update_fields=['email_verification_token', 'email_verification_sent_at'])
        return self.email_verification_token

    def verify_email(self, token):
        if not self.email_verification_token:
            return False

        expiry = self.email_verification_sent_at + timedelta(hours=24)
        if timezone.now() > expiry:
            return False

        if token == self.email_verification_token:
            self.email_verified = True
            self.email_verification_token = None
            self.email_verification_sent_at = None
            self.save()
            return True

        return False

    # ==========================
    # Two-Factor Auth
    # ==========================
    def generate_2fa_secret(self):
        import pyotp
        self.two_factor_secret = pyotp.random_base32()
        self.save(update_fields=['two_factor_secret'])
        return self.two_factor_secret

    def get_2fa_qr_code(self):
        import pyotp
        import qrcode
        import base64
        from io import BytesIO

        totp = pyotp.TOTP(self.two_factor_secret)
        uri = totp.provisioning_uri(name=self.email, issuer_name='Advance Company')

        qr = qrcode.make(uri)
        buffer = BytesIO()
        qr.save(buffer, format='PNG')
        return base64.b64encode(buffer.getvalue()).decode()

    def verify_2fa_code(self, code):
        import pyotp
        if not self.two_factor_secret:
            return False
        return pyotp.TOTP(self.two_factor_secret).verify(code, valid_window=1)

    def generate_backup_codes(self):
        codes = [secrets.token_hex(4).upper() for _ in range(10)]
        self.backup_codes = codes
        self.save(update_fields=['backup_codes'])
        return codes

    def verify_backup_code(self, code: str) -> bool:
        """
        FIX 7: Verify a single-use backup code.
        The matching code is removed from the list after successful use.
        Returns True if the code was valid, False otherwise.
        """
        if not self.backup_codes:
            return False

        code = code.strip().upper()
        codes = list(self.backup_codes)

        if code in codes:
            codes.remove(code)
            self.backup_codes = codes
            self.save(update_fields=['backup_codes'])
            return True

        return False

    # ==========================
    # Cleanup files on delete
    # ==========================
    def delete(self, *args, **kwargs):
        if self.profile_photo:
            try:
                self.profile_photo.delete(save=False)
            except Exception:
                pass
        super().delete(*args, **kwargs)


# ==========================
# Biometric Device
# ==========================
class BiometricDevice(models.Model):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    DEVICE_TYPE_CHOICES = [
        ('fingerprint', 'Fingerprint'),
        ('face_id', 'Face ID'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='biometric_devices')
    device_type = models.CharField(max_length=20, choices=DEVICE_TYPE_CHOICES)
    device_id = models.CharField(max_length=255)
    device_name = models.CharField(max_length=255)
    credential_id = models.CharField(max_length=255, unique=True, editable=False)
    public_key = models.TextField()
    is_active = models.BooleanField(default=True)
    registered_at = models.DateTimeField(auto_now_add=True)
    last_used = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('user', 'device_id', 'device_type')
        ordering = ['-registered_at']

    def save(self, *args, **kwargs):
        if not self.credential_id:
            self.credential_id = secrets.token_urlsafe(32)
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.user.email} - {self.device_name}'


# ==========================
# Biometric Auth Logs
# ==========================
class BiometricAuthLog(models.Model):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    STATUS_CHOICES = [
        ('success', 'Success'),
        ('failed', 'Failed'),
        ('error', 'Error'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='biometric_logs')
    device = models.ForeignKey(
        BiometricDevice, on_delete=models.SET_NULL, null=True, blank=True
    )
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    error_message = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f'{self.user.email} - {self.status}'