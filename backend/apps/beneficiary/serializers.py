from rest_framework import serializers
from .models import Beneficiary

class BeneficiarySerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.full_name', read_only=True)
    
    class Meta:
        model = Beneficiary
        fields = '__all__'
        read_only_fields = ['user', 'verification_status', 'created_at', 'updated_at']

