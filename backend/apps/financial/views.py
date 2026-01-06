from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Sum, Q
from django.utils import timezone
from datetime import datetime
from decimal import Decimal
import uuid
from .models import FinancialAccount, Deposit, InterestCalculation
from .serializers import FinancialAccountSerializer, DepositSerializer, InterestCalculationSerializer
from .permissions import IsAdminUser
from apps.notifications.services import NotificationService
class DepositViewSet(viewsets.ModelViewSet):
    queryset = Deposit.objects.all()
    serializer_class = DepositSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['status', 'payment_method']
    search_fields = ['transaction_reference', 'user__full_name']
    ordering_fields = ['created_at', 'amount']
    
    # Fixed monthly deposit amount
    MONTHLY_DEPOSIT_AMOUNT = Decimal('20000.00')
    
    def get_queryset(self):
        if self.request.user.role == 'admin':
            return Deposit.objects.all()
        return Deposit.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        transaction_ref = f"TXN{uuid.uuid4().hex[:12].upper()}"
        
        # Force the amount to be 20,000
        serializer.save(
            user=self.request.user, 
            transaction_reference=transaction_ref,
            amount=self.MONTHLY_DEPOSIT_AMOUNT
        )
        NotificationService.notify_deposit_submitted(serializer.instance)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def approve_deposit(self, request, pk=None):
        """
        Admin endpoint to approve a deposit and update financial account
        """
        deposit = self.get_object()
        
        if deposit.status == 'completed':
            return Response(
                {'error': 'Deposit already approved and processed'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if deposit.status == 'failed' or deposit.status == 'cancelled':
            return Response(
                {'error': f'Cannot approve a {deposit.status} deposit'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Update deposit status
        deposit.status = 'completed'
        deposit.approved_by = request.user
        deposit.approved_at = timezone.now()
        deposit.save()

        # Notify user about approval
        NotificationService.notify_deposit_approved(deposit, approved_by=request.user)
        
        # Get or create financial account
        account, created = FinancialAccount.objects.get_or_create(user=deposit.user)
        
        # Update total contributions
        account.total_contributions += deposit.amount
        
        # Calculate and update interest (5% annual = 0.4167% monthly)
        monthly_interest_rate = Decimal('0.004167')  # 5% / 12 months
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
        
        return Response({
            'message': 'Deposit approved successfully',
            'deposit': DepositSerializer(deposit).data,
            'account': {
                'total_contributions': str(account.total_contributions),
                'interest_earned': str(account.interest_earned),
                'interest_amount_added': str(interest_earned)
            }
        })
    
    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def reject_deposit(self, request, pk=None):
        """
        Admin endpoint to reject a deposit
        """
        deposit = self.get_object()
        
        if deposit.status == 'completed':
            return Response(
                {'error': 'Cannot reject an already completed deposit'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        reason = request.data.get('reason', 'No reason provided')
        
        deposit.status = 'failed'
        deposit.rejection_reason = reason
        deposit.rejected_by = request.user
        deposit.rejected_at = timezone.now()
        deposit.save()
        NotificationService.notify_deposit_rejected(deposit, rejected_by=request.user, reason=reason)
        
        return Response({
            'message': 'Deposit rejected',
            'deposit': DepositSerializer(deposit).data
        })
    
    @action(detail=False, methods=['get'], permission_classes=[IsAdminUser])
    def pending_approvals(self, request):
        """
        Get all pending deposits that need admin approval
        """
        pending_deposits = Deposit.objects.filter(status='pending').order_by('-created_at')
        
        serializer = self.get_serializer(pending_deposits, many=True)
        
        return Response({
            'count': pending_deposits.count(),
            'results': serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def monthly_summary(self, request):
        """
        Get current month's deposit summary
        """
        user = request.user
        current_month = datetime.now().month
        current_year = datetime.now().year
        
        # Get completed deposits for current month
        deposits = Deposit.objects.filter(
            user=user,
            created_at__month=current_month,
            created_at__year=current_year,
            status='completed'
        )
        
        total = deposits.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        has_paid_this_month = deposits.exists()
        
        return Response({
            'month': current_month,
            'year': current_year,
            'total_deposits': str(total),
            'count': deposits.count(),
            'has_paid_this_month': has_paid_this_month,
            'monthly_required': str(self.MONTHLY_DEPOSIT_AMOUNT),
            'remaining': str(self.MONTHLY_DEPOSIT_AMOUNT - total) if total < self.MONTHLY_DEPOSIT_AMOUNT else '0.00'
        })
    
    @action(detail=False, methods=['get'])
    def can_deposit(self, request):
        """
        Check if user can make a deposit this month
        """
        user = request.user
        current_month = datetime.now().month
        current_year = datetime.now().year
        
        existing_deposits = Deposit.objects.filter(
            user=user,
            status__in=['completed', 'pending'],  # Include pending to prevent duplicate submissions
            created_at__month=current_month,
            created_at__year=current_year
        )
        
        can_deposit = not existing_deposits.exists()
        
        return Response({
            'can_deposit': can_deposit,
            'monthly_amount': str(self.MONTHLY_DEPOSIT_AMOUNT),
            'message': 'You can make your monthly deposit' if can_deposit else 'You have already submitted a deposit this month'
        })


class FinancialAccountViewSet(viewsets.ModelViewSet):
    queryset = FinancialAccount.objects.all()
    serializer_class = FinancialAccountSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        if self.request.user.role == 'admin':
            return FinancialAccount.objects.all()
        return FinancialAccount.objects.filter(user=self.request.user)
    
    @action(detail=False, methods=['get'])
    def my_account(self, request):
        """
        Get current user's financial account with real-time data
        """
        account, created = FinancialAccount.objects.get_or_create(user=request.user)
        
        # Get current month's deposit info
        current_month = datetime.now().month
        current_year = datetime.now().year
        
        monthly_deposits = Deposit.objects.filter(
            user=request.user,
            created_at__month=current_month,
            created_at__year=current_year,
            status='completed'
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        
        serializer = self.get_serializer(account)
        data = serializer.data
        
        # Add monthly deposit info
        data['monthly_deposits'] = str(monthly_deposits)
        data['has_paid_this_month'] = monthly_deposits >= Decimal('20000.00')
        
        return Response(data)


class InterestCalculationViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = InterestCalculation.objects.all()
    serializer_class = InterestCalculationSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        if self.request.user.role == 'admin':
            return InterestCalculation.objects.all()
        return InterestCalculation.objects.filter(user=self.request.user)