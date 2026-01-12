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

    email_verified = models.BooleanField(default=False)
    email_verification_token = models.CharField(max_length=64, blank=True, null=True)
    email_verification_sent_at = models.DateTimeField(blank=True, null=True)
    
    def generate_verification_token(self):
        """Generate email verification token"""
        self.email_verification_token = secrets.token_urlsafe(32)
        self.email_verification_sent_at = timezone.now()
        self.save(update_fields=['email_verification_token', 'email_verification_sent_at'])
        return self.email_verification_token
    
    def verify_email(self, token):
        """Verify email with token"""
        if not self.email_verification_token:
            return False
        
        # Check token validity (24 hours)
        if self.email_verification_sent_at:
            expiry = self.email_verification_sent_at + timedelta(hours=24)
            if timezone.now() > expiry:
                return False
        
        if self.email_verification_token == token:
            self.email_verified = True
            self.email_verification_token = None
            self.email_verification_sent_at = None
            self.save(update_fields=['email_verified', 'email_verification_token', 'email_verification_sent_at'])
            return True
        
        return False 
    
    two_factor_enabled = models.BooleanField(default=False)
    two_factor_secret = models.CharField(max_length=32, blank=True, null=True)
    backup_codes = models.JSONField(default=list, blank=True)
    
    def generate_2fa_secret(self):
        """Generate TOTP secret for 2FA"""
        import pyotp
        secret = pyotp.random_base32()
        self.two_factor_secret = secret
        self.save(update_fields=['two_factor_secret'])
        return secret
    
    def get_2fa_qr_code(self):
        """Generate QR code for 2FA setup"""
        import pyotp
        import qrcode
        from io import BytesIO
        import base64
        
        if not self.two_factor_secret:
            self.generate_2fa_secret()
        
        totp = pyotp.TOTP(self.two_factor_secret)
        uri = totp.provisioning_uri(
            name=self.email,
            issuer_name='Advance Company'
        )
        
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(uri)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        
        return base64.b64encode(buffer.getvalue()).decode()
    
    def verify_2fa_code(self, code):
        """Verify TOTP code"""
        import pyotp
        
        if not self.two_factor_enabled or not self.two_factor_secret:
            return False
        
        totp = pyotp.TOTP(self.two_factor_secret)
        return totp.verify(code, valid_window=1)  # Allow 30 seconds before/after
    
    def generate_backup_codes(self):
        """Generate backup codes for 2FA"""
        import secrets
        codes = [secrets.token_hex(4).upper() for _ in range(10)]
        self.backup_codes = codes
        self.save(update_fields=['backup_codes'])
        return codes
    
    def verify_backup_code(self, code):
        """Verify and consume backup code"""
        if code.upper() in self.backup_codes:
            self.backup_codes.remove(code.upper())
            self.save(update_fields=['backup_codes'])
            return True
        return False

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