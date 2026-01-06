from rest_framework import serializers
from decimal import Decimal
from django.utils import timezone
from .models import FinancialAccount, Deposit, InterestCalculation

# Simple serializers
class FinancialAccountSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.full_name', read_only=True)
    
    class Meta:
        model = FinancialAccount
        fields = '__all__'
        read_only_fields = ['user', 'total_contributions', 'interest_earned']


class InterestCalculationSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.full_name', read_only=True)
    
    class Meta:
        model = InterestCalculation
        fields = '__all__'


# Complex serializer with business logic
class DepositSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.full_name', read_only=True)
    
    # Fixed monthly deposit amount
    MONTHLY_DEPOSIT_AMOUNT = Decimal('20000.00')
    
    class Meta:
        model = Deposit
        fields = '__all__'
        read_only_fields = ['user', 'transaction_reference', 'created_at', 'updated_at', 'amount']
    
    def validate_amount(self, value):
        """Ensure deposit amount is exactly KES 20,000"""
        if value != self.MONTHLY_DEPOSIT_AMOUNT:
            raise serializers.ValidationError(
                f'Deposit amount must be exactly KES {self.MONTHLY_DEPOSIT_AMOUNT:,.2f}. '
                f'You entered KES {value:,.2f}.'
            )
        return value
    
    def validate(self, data):
        """Ensure user doesn't exceed monthly deposit limit"""
        user = self.context['request'].user
        current_month = timezone.now().month
        current_year = timezone.now().year
        
        existing_deposits = Deposit.objects.filter(
            user=user,
            status='completed',
            created_at__month=current_month,
            created_at__year=current_year
        )
        
        # If editing, exclude current deposit
        if self.instance:
            existing_deposits = existing_deposits.exclude(id=self.instance.id)
        
        if existing_deposits.exists():
            raise serializers.ValidationError(
                'You have already made your monthly deposit of KES 20,000 for this month. '
                'You can only make one deposit per month.'
            )
        
        return data