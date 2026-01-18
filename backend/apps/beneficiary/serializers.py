from rest_framework import serializers
from .models import Beneficiary


class BeneficiarySerializer(serializers.ModelSerializer):
    """Serializer for beneficiary management"""
    
    user_name = serializers.CharField(source='user.full_name', read_only=True)
    user_email = serializers.EmailField(source='user.email', read_only=True)
    user_phone = serializers.CharField(source='user.phone_number', read_only=True)
    
    # File URLs
    identity_document_url = serializers.SerializerMethodField()
    birth_certificate_url = serializers.SerializerMethodField()
    death_certificate_url = serializers.SerializerMethodField()
    additional_documents_url = serializers.SerializerMethodField()
    
    # Display values
    relation_display = serializers.CharField(source='get_relation_display', read_only=True)
    gender_display = serializers.CharField(source='get_gender_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    verification_status_display = serializers.CharField(source='get_verification_status_display', read_only=True)
    
    class Meta:
        model = Beneficiary
        fields = [
            'id', 'user', 'user_name', 'user_email', 'user_phone',
            'name', 'relation', 'relation_display', 'age', 'gender', 'gender_display',
            'phone_number', 'profession', 'salary_range',
            'identity_document', 'identity_document_url',
            'birth_certificate', 'birth_certificate_url',
            'death_certificate', 'death_certificate_url',
            'death_certificate_number',
            'additional_documents', 'additional_documents_url',
            'status', 'status_display',
            'verification_status', 'verification_status_display',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['user', 'verification_status', 'created_at', 'updated_at']
    
    def get_identity_document_url(self, obj):
        if obj.identity_document:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.identity_document.url)
            return obj.identity_document.url
        return None
    
    def get_birth_certificate_url(self, obj):
        if obj.birth_certificate:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.birth_certificate.url)
            return obj.birth_certificate.url
        return None
    
    def get_death_certificate_url(self, obj):
        if obj.death_certificate:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.death_certificate.url)
            return obj.death_certificate.url
        return None
    
    def get_additional_documents_url(self, obj):
        if obj.additional_documents:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.additional_documents.url)
            return obj.additional_documents.url
        return None
    
    def validate_age(self, value):
        """Validate age is reasonable"""
        if value < 0 or value > 150:
            raise serializers.ValidationError("Age must be between 0 and 150")
        return value
    
    def validate_phone_number(self, value):
        """Validate phone number format if provided"""
        if value:
            # Remove spaces and special characters
            cleaned = value.replace(' ', '').replace('-', '').replace('+', '')
            if not cleaned.isdigit():
                raise serializers.ValidationError("Phone number must contain only digits")
            if len(cleaned) < 10 or len(cleaned) > 15:
                raise serializers.ValidationError("Phone number must be between 10 and 15 digits")
        return value


class BeneficiaryVerificationSerializer(serializers.Serializer):
    """Serializer for beneficiary verification actions"""
    
    action = serializers.ChoiceField(choices=['verify', 'reject'])
    reason = serializers.CharField(required=False, allow_blank=True, max_length=500)
    notes = serializers.CharField(required=False, allow_blank=True, max_length=1000)
    
    def validate(self, data):
        """Ensure reason is provided for rejection"""
        if data.get('action') == 'reject' and not data.get('reason'):
            raise serializers.ValidationError({
                'reason': 'Rejection reason is required when rejecting a beneficiary'
            })
        return data


class BeneficiarySummarySerializer(serializers.ModelSerializer):
    """Lightweight serializer for beneficiary lists"""
    
    relation_display = serializers.CharField(source='get_relation_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    verification_status_display = serializers.CharField(source='get_verification_status_display', read_only=True)
    
    class Meta:
        model = Beneficiary
        fields = [
            'id', 'name', 'relation', 'relation_display', 'age', 'gender',
            'status', 'status_display',
            'verification_status', 'verification_status_display',
            'created_at'
        ]
        read_only_fields = fields