from rest_framework import serializers
from .models import FinancialAccount, Deposit, InterestCalculation

class FinancialAccountSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.full_name', read_only=True)
    
    class Meta:
        model = FinancialAccount
        fields = '__all__'
        read_only_fields = ['user', 'total_contributions', 'interest_earned']

class DepositSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.full_name', read_only=True)
    
    class Meta:
        model = Deposit
        fields = '__all__'
        read_only_fields = ['user', 'transaction_reference', 'created_at', 'updated_at']

class InterestCalculationSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.full_name', read_only=True)
    
    class Meta:
        model = InterestCalculation
        fields = '__all__'

