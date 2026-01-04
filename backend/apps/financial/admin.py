from django.contrib import admin
from .models import FinancialAccount, Deposit, InterestCalculation

@admin.register(FinancialAccount)
class FinancialAccountAdmin(admin.ModelAdmin):
    list_display = ['user', 'total_contributions', 'interest_earned', 'interest_rate']
    search_fields = ['user__full_name', 'user__email']

@admin.register(Deposit)
class DepositAdmin(admin.ModelAdmin):
    list_display = ['user', 'amount', 'payment_method', 'status', 'created_at']
    list_filter = ['status', 'payment_method', 'created_at']
    search_fields = ['user__full_name', 'transaction_reference']

@admin.register(InterestCalculation)
class InterestCalculationAdmin(admin.ModelAdmin):
    list_display = ['user', 'interest_amount', 'calculation_date']
    list_filter = ['calculation_date']

