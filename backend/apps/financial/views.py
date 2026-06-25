from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from django.utils import timezone
from django.db.models import Sum, Count, Q
from django.db import transaction
from django.views.decorators.csrf import csrf_exempt
from datetime import datetime, timedelta
from decimal import Decimal
import uuid
import logging
import json

from .models import FinancialAccount, Deposit, InterestCalculation
from .serializers import (
    FinancialAccountSerializer, 
    DepositSerializer, 
    InterestCalculationSerializer
)
from .mpesa_utils import initiate_stk_push
from django_ratelimit.decorators import ratelimit
from django.utils.decorators import method_decorator

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

    @method_decorator(ratelimit(key='user', rate='5/h', method='POST'))
    def create(self, request, *args, **kwargs):
        """
        Create deposit and initiate M-Pesa payment if payment method is M-Pesa
        Limit deposit creation to 5 per hour per user
        """
        if getattr(request, 'limited', False):
            return Response(
                {'error': 'You have reached the maximum number of deposit attempts. Please try again later.'},
                status=status.HTTP_429_TOO_MANY_REQUESTS
            )
        
        # Check if user can deposit this month
        current_month = timezone.now().month
        current_year = timezone.now().year
        
        existing_deposit = Deposit.objects.filter(
            user=request.user,
            created_at__month=current_month,
            created_at__year=current_year,
            status__in=['pending', 'processing', 'completed']
        ).exists()
        
        if existing_deposit:
            return Response(
                {'error': 'You have already made a deposit this month'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get payment method and phone number
        payment_method = request.data.get('payment_method')
        mpesa_phone = request.data.get('mpesa_phone')
        
        # Validate M-Pesa requirements
        if payment_method == 'mpesa' and not mpesa_phone:
            return Response(
                {'error': 'Phone number is required for M-Pesa payments'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            with transaction.atomic():
                # Generate unique transaction reference
                transaction_ref = f"DEP{datetime.now().strftime('%Y%m%d')}{uuid.uuid4().hex[:6].upper()}"
                
                # Create deposit
                deposit = Deposit.objects.create(
                    user=request.user,
                    amount=self.MONTHLY_DEPOSIT_AMOUNT,
                    payment_method=payment_method,
                    transaction_reference=transaction_ref,
                    mpesa_phone=mpesa_phone,
                    status='pending' if payment_method != 'mpesa' else 'processing',
                    notes=request.data.get('notes', '')
                )
                
                # Initiate M-Pesa STK Push if payment method is M-Pesa
                if payment_method == 'mpesa':
                    result = initiate_stk_push(
                        phone_number=mpesa_phone,
                        amount=self.MONTHLY_DEPOSIT_AMOUNT,
                        account_reference=transaction_ref,
                        transaction_desc='Deposit'
                    )
                    
                    if result.get('success'):
                        mpesa_data = result.get('data', {})
                        deposit.mpesa_checkout_request_id = mpesa_data.get('CheckoutRequestID')
                        deposit.mpesa_merchant_request_id = mpesa_data.get('MerchantRequestID')
                        deposit.mpesa_response_code = mpesa_data.get('ResponseCode')
                        deposit.mpesa_response_description = mpesa_data.get('ResponseDescription')
                        deposit.save()
                        
                        logger.info(f"STK Push initiated for deposit {deposit.uuid}")
                    else:
                        # STK Push failed
                        deposit.status = 'failed'
                        deposit.notes = f"M-Pesa error: {result.get('error', 'Unknown error')}"
                        deposit.save()
                        
                        return Response(
                            {
                                'error': 'Failed to initiate M-Pesa payment',
                                'details': result.get('error')
                            },
                            status=status.HTTP_400_BAD_REQUEST
                        )
                
                serializer = self.get_serializer(deposit)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
                
        except Exception as e:
            logger.error(f"Error creating deposit: {str(e)}", exc_info=True)
            return Response(
                {'error': f'Failed to create deposit: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
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
            status__in=['pending', 'processing', 'completed']
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
            count=Count('uuid')
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
        """
        deposit = self.get_object()
        
        if deposit.status not in ['pending', 'processing']:
            return Response(
                {'error': 'Deposit is not in a state that can be approved'},
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
                
                # Calculate and add interest
                interest_rate = Decimal(str(account.interest_rate))
                deposit_amount = Decimal(str(deposit.amount))
                interest = deposit_amount * (interest_rate / Decimal('100'))
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
                
                logger.info(f"Deposit {deposit.uuid} approved by admin {request.user.uuid}")
                
                serializer = self.get_serializer(deposit)
                return Response({
                    'message': 'Deposit approved successfully',
                    'deposit': serializer.data
                })
                
        except Exception as e:
            logger.error(f"Error approving deposit {deposit.uuid}: {str(e)}", exc_info=True)
            return Response(
                {'error': f'Failed to approve deposit: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def reject_deposit(self, request, pk=None):
        """Admin endpoint to reject a deposit"""
        deposit = self.get_object()
        
        if deposit.status not in ['pending', 'processing']:
            return Response(
                {'error': 'Deposit is not in a state that can be rejected'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            reason = request.data.get('reason', 'No reason provided')
            
            deposit.status = 'failed'
            deposit.rejection_reason = reason
            deposit.rejected_by = request.user
            deposit.rejected_at = timezone.now()
            deposit.notes = f"Rejected: {reason}"
            deposit.save()
            
            logger.info(f"Deposit {deposit.uuid} rejected by admin {request.user.uuid}")
            
            serializer = self.get_serializer(deposit)
            return Response({
                'message': 'Deposit rejected',
                'deposit': serializer.data
            })
            
        except Exception as e:
            logger.error(f"Error rejecting deposit {deposit.uuid}: {str(e)}", exc_info=True)
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


# M-Pesa Callback View
@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
def mpesa_callback(request):
    """
    M-Pesa callback endpoint to receive payment notifications
    """
    try:
        data = json.loads(request.body)
        logger.info(f"M-Pesa Callback received: {data}")
        
        # Extract callback data
        callback_body = data.get('Body', {}).get('stkCallback', {})
        result_code = callback_body.get('ResultCode')
        checkout_request_id = callback_body.get('CheckoutRequestID')
        
        # Find the deposit
        try:
            deposit = Deposit.objects.get(mpesa_checkout_request_id=checkout_request_id)
        except Deposit.DoesNotExist:
            logger.error(f"Deposit not found for CheckoutRequestID: {checkout_request_id}")
            return Response({'ResultCode': 0, 'ResultDesc': 'Accepted'})
        
        if result_code == 0:
            # Payment successful
            callback_metadata = callback_body.get('CallbackMetadata', {}).get('Item', [])
            
            # Extract transaction details
            for item in callback_metadata:
                if item.get('Name') == 'MpesaReceiptNumber':
                    deposit.mpesa_receipt_number = item.get('Value')
                elif item.get('Name') == 'TransactionDate':
                    # Convert timestamp to datetime (format: 20220101123456)
                    trans_date = str(item.get('Value'))
                    deposit.mpesa_transaction_date = datetime.strptime(
                        trans_date, '%Y%m%d%H%M%S'
                    )
            
            deposit.status = 'pending'  # Pending admin approval
            deposit.mpesa_response_code = str(result_code)
            deposit.mpesa_response_description = callback_body.get('ResultDesc', 'Success')
            deposit.save()
            
            logger.info(f"M-Pesa payment successful for deposit {deposit.uuid}")
            
        else:
            # Payment failed
            deposit.status = 'failed'
            deposit.mpesa_response_code = str(result_code)
            deposit.mpesa_response_description = callback_body.get('ResultDesc', 'Failed')
            deposit.save()
            
            logger.warning(f"M-Pesa payment failed for deposit {deposit.uuid}: {result_code}")
        
        return Response({'ResultCode': 0, 'ResultDesc': 'Accepted'})
        
    except Exception as e:
        logger.error(f"Error processing M-Pesa callback: {str(e)}", exc_info=True)
        return Response({'ResultCode': 1, 'ResultDesc': 'Failed'})