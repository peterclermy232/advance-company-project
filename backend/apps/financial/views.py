"""
backend/apps/financial/views.py
Fixed version with proper error handling and notification sending
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.utils import timezone
from django.db.models import Sum, Q
from django.db import transaction
from datetime import datetime, timedelta
import uuid
import logging

from .models import FinancialAccount, Deposit, InterestCalculation
from .serializers import (
    FinancialAccountSerializer, 
    DepositSerializer, 
    InterestCalculationSerializer
)

logger = logging.getLogger(__name__)


class FinancialAccountViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing financial accounts
    Users can only view their own account
    Admins can view all accounts
    """
    serializer_class = FinancialAccountSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if self.request.user.role == 'admin':
            return FinancialAccount.objects.all()
        return FinancialAccount.objects.filter(user=self.request.user)

    @action(detail=False, methods=['get'])
    def my_account(self, request):
        """Get current user's financial account"""
        account, created = FinancialAccount.objects.get_or_create(user=request.user)
        serializer = self.get_serializer(account)
        return Response(serializer.data)


class DepositViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing deposits
    Users can create and view their own deposits
    Admins can view and approve all deposits
    """
    serializer_class = DepositSerializer
    permission_classes = [IsAuthenticated]
    MONTHLY_DEPOSIT_AMOUNT = 20000

    def get_queryset(self):
        if self.request.user.role == 'admin':
            return Deposit.objects.all().order_by('-created_at')
        return Deposit.objects.filter(user=self.request.user).order_by('-created_at')

    def perform_create(self, serializer):
        """
        Create deposit with auto-generated transaction reference
        Notifications are sent automatically by signals
        """
        # Generate unique transaction reference
        transaction_ref = f"DEP{datetime.now().strftime('%Y%m%d')}{uuid.uuid4().hex[:6].upper()}"
        
        # Force the amount to be 20,000
        serializer.save(
            user=self.request.user, 
            transaction_reference=transaction_ref,
            amount=self.MONTHLY_DEPOSIT_AMOUNT
        )

    @action(detail=False, methods=['get'])
    def can_deposit(self, request):
        """
        Check if user can make a deposit this month
        Users can only make one deposit per month
        """
        current_month = timezone.now().month
        current_year = timezone.now().year
        
        existing_deposit = Deposit.objects.filter(
            user=request.user,
            created_at__month=current_month,
            created_at__year=current_year,
            status__in=['pending', 'completed']
        ).exists()
        
        return Response({
            'can_deposit': not existing_deposit,
            'message': 'You have already made a deposit this month' if existing_deposit else 'You can make a deposit'
        })

    @action(detail=False, methods=['get'])
    def monthly_summary(self, request):
        """Get monthly deposit summary for current user"""
        deposits = self.get_queryset().filter(status='completed')
        
        monthly_data = deposits.values(
            'created_at__month', 
            'created_at__year'
        ).annotate(
            total=Sum('amount'),
            count=Sum(1)
        ).order_by('-created_at__year', '-created_at__month')[:12]
        
        return Response({
            'results': [
                {
                    'month': item['created_at__month'],
                    'year': item['created_at__year'],
                    'total_deposits': float(item['total']),
                    'count': item['count']
                }
                for item in monthly_data
            ]
        })

    @action(detail=False, methods=['get'], permission_classes=[IsAdminUser])
    def pending_approvals(self, request):
        """Admin endpoint to get all pending deposits"""
        pending = Deposit.objects.filter(status='pending').order_by('-created_at')
        serializer = self.get_serializer(pending, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def approve_deposit(self, request, pk=None):
        """
        Admin endpoint to approve a deposit and update financial account
        Fixed: Better error handling and transaction management
        """
        deposit = self.get_object()
        
        if deposit.status != 'pending':
            return Response(
                {'error': 'Deposit is not pending'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            with transaction.atomic():
                # Update deposit status
                deposit.status = 'completed'
                deposit.approved_by = request.user
                deposit.approved_at = timezone.now()
                deposit.save()
                
                # Update financial account
                account, created = FinancialAccount.objects.get_or_create(
                    user=deposit.user
                )
                account.total_contributions += deposit.amount
                
                # Calculate and add interest (e.g., 5% per deposit)
                interest = deposit.amount * (account.interest_rate / 100)
                account.interest_earned += interest
                account.save()
                
                # Record interest calculation
                InterestCalculation.objects.create(
                    user=deposit.user,
                    principal_amount=deposit.amount,
                    interest_rate=account.interest_rate,
                    interest_amount=interest,
                    calculation_date=timezone.now().date(),
                    period_start=timezone.now().date(),
                    period_end=timezone.now().date()
                )
                
                logger.info(f"Deposit {deposit.id} approved by admin {request.user.id}")
                
                serializer = self.get_serializer(deposit)
                return Response({
                    'message': 'Deposit approved successfully',
                    'deposit': serializer.data
                })
                
        except Exception as e:
            logger.error(f"Error approving deposit {deposit.id}: {str(e)}", exc_info=True)
            return Response(
                {'error': f'Failed to approve deposit: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def reject_deposit(self, request, pk=None):
        """
        Admin endpoint to reject a deposit
        Fixed: Better error handling
        """
        deposit = self.get_object()
        
        if deposit.status != 'pending':
            return Response(
                {'error': 'Deposit is not pending'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            reason = request.data.get('reason', 'No reason provided')
            
            # Update deposit status
            deposit.status = 'failed'
            deposit.rejection_reason = reason
            deposit.rejected_by = request.user
            deposit.rejected_at = timezone.now()
            deposit.notes = f"Rejected: {reason}"
            deposit.save()
            
            logger.info(f"Deposit {deposit.id} rejected by admin {request.user.id}")
            
            serializer = self.get_serializer(deposit)
            return Response({
                'message': 'Deposit rejected',
                'deposit': serializer.data
            })
            
        except Exception as e:
            logger.error(f"Error rejecting deposit {deposit.id}: {str(e)}", exc_info=True)
            return Response(
                {'error': f'Failed to reject deposit: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class InterestCalculationViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing interest calculations
    Users can only view their own calculations
    """
    serializer_class = InterestCalculationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if self.request.user.role == 'admin':
            return InterestCalculation.objects.all().order_by('-calculation_date')
        
        return InterestCalculation.objects.filter(
            user=self.request.user
        ).order_by('-calculation_date')