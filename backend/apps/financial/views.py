from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Sum
from datetime import datetime
import uuid
from .models import FinancialAccount, Deposit, InterestCalculation
from .serializers import FinancialAccountSerializer, DepositSerializer, InterestCalculationSerializer

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
        account, created = FinancialAccount.objects.get_or_create(user=request.user)
        serializer = self.get_serializer(account)
        return Response(serializer.data)

class DepositViewSet(viewsets.ModelViewSet):
    queryset = Deposit.objects.all()
    serializer_class = DepositSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['status', 'payment_method']
    search_fields = ['transaction_reference', 'user__full_name']
    ordering_fields = ['created_at', 'amount']
    
    def get_queryset(self):
        if self.request.user.role == 'admin':
            return Deposit.objects.all()
        return Deposit.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        transaction_ref = f"TXN{uuid.uuid4().hex[:12].upper()}"
        serializer.save(user=self.request.user, transaction_reference=transaction_ref)
    
    @action(detail=True, methods=['post'])
    def confirm_payment(self, request, pk=None):
        deposit = self.get_object()
        if deposit.status != 'pending':
            return Response(
                {'error': 'Deposit already processed'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        deposit.status = 'completed'
        deposit.save()
        
        # Update financial account
        account, created = FinancialAccount.objects.get_or_create(user=deposit.user)
        account.total_contributions += deposit.amount
        account.save()
        
        return Response({'message': 'Payment confirmed successfully'})
    
    @action(detail=False, methods=['get'])
    def monthly_summary(self, request):
        user = request.user
        current_month = datetime.now().month
        current_year = datetime.now().year
        
        deposits = Deposit.objects.filter(
            user=user,
            created_at__month=current_month,
            created_at__year=current_year,
            status='completed'
        )
        
        total = deposits.aggregate(total=Sum('amount'))['total'] or 0
        
        return Response({
            'month': current_month,
            'year': current_year,
            'total_deposits': total,
            'count': deposits.count()
        })

class InterestCalculationViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = InterestCalculation.objects.all()
    serializer_class = InterestCalculationSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        if self.request.user.role == 'admin':
            return InterestCalculation.objects.all()
        return InterestCalculation.objects.filter(user=self.request.user)

