from django.contrib import admin
from django.utils import timezone
from django.contrib import messages
from decimal import Decimal
from .models import FinancialAccount, Deposit, InterestCalculation

@admin.register(FinancialAccount)
class FinancialAccountAdmin(admin.ModelAdmin):
    list_display = ['user', 'total_contributions', 'interest_earned', 'interest_rate', 'updated_at']
    search_fields = ['user__full_name', 'user__email']
    readonly_fields = ['created_at', 'updated_at']
    list_filter = ['created_at']


@admin.register(Deposit)
class DepositAdmin(admin.ModelAdmin):
    list_display = [
        'transaction_reference', 
        'user', 
        'amount', 
        'payment_method', 
        'status', 
        'approved_by',
        'created_at'
    ]
    list_filter = ['status', 'payment_method', 'created_at', 'approved_at']
    search_fields = ['user__full_name', 'transaction_reference', 'user__email']
    readonly_fields = [
        'transaction_reference', 
        'created_at', 
        'updated_at',
        'approved_by',
        'approved_at',
        'rejected_by',
        'rejected_at'
    ]
    
    fieldsets = (
        ('Deposit Information', {
            'fields': ('user', 'amount', 'payment_method', 'status', 'transaction_reference')
        }),
        ('Payment Details', {
            'fields': ('mpesa_phone', 'notes')
        }),
        ('Approval Information', {
            'fields': ('approved_by', 'approved_at', 'rejected_by', 'rejected_at', 'rejection_reason'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['approve_deposits', 'reject_deposits']
    
    def approve_deposits(self, request, queryset):
        """Bulk approve selected deposits"""
        pending_deposits = queryset.filter(status='pending')
        approved_count = 0
        
        for deposit in pending_deposits:
            # Update deposit status
            deposit.status = 'completed'
            deposit.approved_by = request.user
            deposit.approved_at = timezone.now()
            deposit.save()
            
            # Get or create financial account
            account, created = FinancialAccount.objects.get_or_create(user=deposit.user)
            
            # Update total contributions
            account.total_contributions += deposit.amount
            
            # Calculate and update interest (5% annual = 0.4167% monthly)
            monthly_interest_rate = Decimal('0.004167')
            interest_earned = deposit.amount * monthly_interest_rate
            account.interest_earned += interest_earned
            
            account.save()
            
            # Create interest calculation record
            InterestCalculation.objects.create(
                user=deposit.user,
                principal_amount=deposit.amount,
                interest_rate=account.interest_rate,
                interest_amount=interest_earned,
                calculation_date=timezone.now().date(),
                period_start=timezone.now().date().replace(day=1),
                period_end=timezone.now().date()
            )
            
            approved_count += 1
        
        self.message_user(
            request,
            f'{approved_count} deposit(s) approved successfully.',
            messages.SUCCESS
        )
    
    approve_deposits.short_description = "Approve selected deposits"
    
    def reject_deposits(self, request, queryset):
        """Bulk reject selected deposits"""
        pending_deposits = queryset.filter(status='pending')
        
        updated = pending_deposits.update(
            status='failed',
            rejected_by=request.user,
            rejected_at=timezone.now(),
            rejection_reason='Rejected by admin via bulk action'
        )
        
        self.message_user(
            request,
            f'{updated} deposit(s) rejected.',
            messages.WARNING
        )
    
    reject_deposits.short_description = "Reject selected deposits"


@admin.register(InterestCalculation)
class InterestCalculationAdmin(admin.ModelAdmin):
    list_display = [
        'user', 
        'principal_amount',
        'interest_amount', 
        'interest_rate',
        'calculation_date',
        'period_start',
        'period_end'
    ]
    list_filter = ['calculation_date', 'created_at']
    search_fields = ['user__full_name', 'user__email']
    readonly_fields = ['created_at']
    date_hierarchy = 'calculation_date'