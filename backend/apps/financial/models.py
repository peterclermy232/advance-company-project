from django.db import models
from apps.accounts.models import User


class FinancialAccount(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='financial_account')
    total_contributions = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    interest_earned = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    interest_rate = models.DecimalField(max_digits=5, decimal_places=2, default=5.00)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.full_name} - Account"
    
    @property
    def total_balance(self):
        """Total balance including contributions and interest"""
        return self.total_contributions + self.interest_earned


class Deposit(models.Model):
    PAYMENT_METHOD_CHOICES = [
        ('mpesa', 'M-Pesa'),
        ('bank', 'Bank Transfer'),
        ('mansa_x', 'Mansa-X'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),  # Added for M-Pesa pending state
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='deposits')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    transaction_reference = models.CharField(max_length=100, unique=True)
    mpesa_phone = models.CharField(max_length=15, null=True, blank=True)
    notes = models.TextField(null=True, blank=True)
    
    # M-Pesa specific fields
    mpesa_checkout_request_id = models.CharField(max_length=100, null=True, blank=True)
    mpesa_merchant_request_id = models.CharField(max_length=100, null=True, blank=True)
    mpesa_receipt_number = models.CharField(max_length=50, null=True, blank=True)
    mpesa_transaction_date = models.DateTimeField(null=True, blank=True)
    mpesa_response_code = models.CharField(max_length=10, null=True, blank=True)
    mpesa_response_description = models.TextField(null=True, blank=True)
    
    # Admin approval fields
    approved_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='approved_deposits'
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    rejected_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='rejected_deposits'
    )
    rejected_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['mpesa_checkout_request_id']),
            models.Index(fields=['transaction_reference']),
        ]
    
    def __str__(self):
        return f"{self.user.full_name} - KES {self.amount} ({self.status})"


class InterestCalculation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='interest_calculations')
    principal_amount = models.DecimalField(max_digits=12, decimal_places=2)
    interest_rate = models.DecimalField(max_digits=5, decimal_places=2)
    interest_amount = models.DecimalField(max_digits=10, decimal_places=2)
    calculation_date = models.DateField()
    period_start = models.DateField()
    period_end = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-calculation_date']
    
    def __str__(self):
        return f"{self.user.full_name} - Interest: KES {self.interest_amount}"