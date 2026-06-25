from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import User, BiometricDevice, BiometricAuthLog

class UserSerializer(serializers.ModelSerializer):
    has_biometric = serializers.SerializerMethodField()
    biometric_devices_count = serializers.SerializerMethodField()
    profile_photo_url = serializers.SerializerMethodField()
    identity_document_url = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'uuid', 'email', 'phone_number', 'full_name', 'role', 'age', 'gender',
            'marital_status', 'number_of_kids', 'profession', 'salary_range',
            'spouse_name', 'spouse_age', 'spouse_profession', 'profile_photo',
            'profile_photo_url', 'identity_document', 'identity_document_url',
            'activity_status', 'created_at', 'updated_at',
            'biometric_enabled', 'fingerprint_enabled', 'face_id_enabled',
            'has_biometric', 'biometric_devices_count'
        ]
        read_only_fields = ['uuid', 'created_at', 'updated_at']

    def get_profile_photo_url(self, obj):
        """Return full URL for profile photo"""
        if obj.profile_photo:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.profile_photo.url)
        return None

    def get_identity_document_url(self, obj):
        request = self.context.get('request')
        if obj.identity_document:
            if request:
                return request.build_absolute_uri(obj.identity_document.url)
            return obj.identity_document.url
        return None
    
    def get_has_biometric(self, obj):
        return obj.biometric_devices.filter(is_active=True).exists()
    
    def get_biometric_devices_count(self, obj):
        return obj.biometric_devices.filter(is_active=True).count()


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True, 
        min_length=12,
        style={'input_type': 'password'},
        help_text='Must be at least 12 characters with uppercase, lowercase, digits, and special characters'
    )
    password_confirm = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'}
    )
    
    class Meta:
        model = User
        fields = ['email', 'phone_number', 'full_name', 'password', 'password_confirm', 'role']
    
    def validate_password(self, value):
        """Validate password strength"""
        from django.contrib.auth.password_validation import validate_password
        from django.core.exceptions import ValidationError as DjangoValidationError
        
        try:
            validate_password(value)
        except DjangoValidationError as e:
            raise serializers.ValidationError(list(e.messages))
        
        return value
    
    def validate(self, data):
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError({
                'password_confirm': "Passwords don't match"
            })
        return data
    
    def create(self, validated_data):
        validated_data.pop('password_confirm')
        user = User.objects.create_user(**validated_data)
        return user


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    
    def validate(self, data):
        user = authenticate(username=data['email'], password=data['password'])
        if not user:
            raise serializers.ValidationError("Invalid credentials")
        if not user.is_active:
            raise serializers.ValidationError("Account is inactive")
        data['user'] = user
        return data


class BiometricDeviceSerializer(serializers.ModelSerializer):
    class Meta:
        model = BiometricDevice
        fields = [
            'uuid', 'device_type', 'device_id', 'device_name', 
            'credential_id', 'is_active', 'registered_at', 'last_used'
        ]
        read_only_fields = ['credential_id', 'registered_at', 'last_used']


class BiometricRegistrationSerializer(serializers.Serializer):
    """
    Serializer for registering a new biometric device.
    The actual biometric data is verified on the device.
    """
    device_type = serializers.ChoiceField(choices=['fingerprint', 'face_id'])
    device_id = serializers.CharField(max_length=255)
    device_name = serializers.CharField(max_length=255)
    public_key = serializers.CharField()
    
    # Verification token from device (proves biometric was captured)
    verification_token = serializers.CharField(write_only=True)
    
    def validate_device_id(self, value):
        """Ensure device isn't already registered for this user."""
        user = self.context['request'].user
        device_type = self.initial_data.get('device_type')
        
        if BiometricDevice.objects.filter(
            user=user, 
            device_id=value, 
            device_type=device_type,
            is_active=True
        ).exists():
            raise serializers.ValidationError(
                "This device is already registered for biometric authentication"
            )
        return value


class BiometricAuthSerializer(serializers.Serializer):
    """
    Serializer for biometric authentication.
    The device handles the actual biometric verification and sends proof.
    """
    email = serializers.EmailField()
    credential_id = serializers.CharField()
    device_id = serializers.CharField()
    
    # Signature/proof from device that biometric was verified
    auth_signature = serializers.CharField(write_only=True)
    challenge_response = serializers.CharField(write_only=True)
    
    def validate(self, data):
        try:
            user = User.objects.get(email=data['email'], is_active=True)
        except User.DoesNotExist:
            raise serializers.ValidationError("Invalid credentials")
        
        try:
            device = BiometricDevice.objects.get(
                user=user,
                credential_id=data['credential_id'],
                device_id=data['device_id'],
                is_active=True
            )
        except BiometricDevice.DoesNotExist:
            raise serializers.ValidationError("Device not registered")
        
        # Here you would verify the auth_signature and challenge_response
        # 1. Verifying the signature using the stored public_key
        # 2. Checking the challenge_response matches what was sent
        # For simplicity, we'll assume verification is successful
        
        data['user'] = user
        data['device'] = device
        return data


class BiometricAuthLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = BiometricAuthLog
        fields = ['uuid', 'status', 'ip_address', 'timestamp', 'error_message']
        read_only_fields = fields

class TwoFactorSetupSerializer(serializers.Serializer):
    """Serializer for 2FA setup"""
    code = serializers.CharField(max_length=6, min_length=6)
    
    def validate_code(self, value):
        if not value.isdigit():
            raise serializers.ValidationError("Code must be 6 digits")
        return value


class TwoFactorVerifySerializer(serializers.Serializer):
    """Serializer for 2FA verification during login"""
    email = serializers.EmailField()
    code = serializers.CharField(max_length=8)
    is_backup_code = serializers.BooleanField(default=False)
       