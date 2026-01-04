from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from django.http import HttpResponse
from django.db.models import Sum, Count
from datetime import datetime, timedelta
from .models import Report, ActivityLog
from .serializers import ReportSerializer, ActivityLogSerializer
from apps.financial.models import Deposit, FinancialAccount
from apps.beneficiary.models import Beneficiary

class ReportViewSet(viewsets.ModelViewSet):
    queryset = Report.objects.all()
    serializer_class = ReportSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['report_type', 'status']
    
    def get_queryset(self):
        if self.request.user.role == 'admin':
            return Report.objects.all()
        return Report.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user, generated_by=self.request.user)
    
    @action(detail=False, methods=['post'])
    def generate_financial_report(self, request):
        date_from = request.data.get('date_from')
        date_to = request.data.get('date_to')
        
        report = Report.objects.create(
            user=request.user,
            report_type='financial',
            title=f'Financial Report {datetime.now().strftime("%Y-%m-%d")}',
            date_from=date_from,
            date_to=date_to,
            generated_by=request.user,
            status='ready'
        )
        
        # Generate report data
        deposits = Deposit.objects.filter(
            user=request.user,
            status='completed'
        )
        
        if date_from:
            deposits = deposits.filter(created_at__gte=date_from)
        if date_to:
            deposits = deposits.filter(created_at__lte=date_to)
        
        total_deposits = deposits.aggregate(total=Sum('amount'))['total'] or 0
        
        return Response({
            'report': ReportSerializer(report, context={'request': request}).data,
            'summary': {
                'total_deposits': total_deposits,
                'deposit_count': deposits.count(),
                'date_from': date_from,
                'date_to': date_to
            }
        })
    
    @action(detail=False, methods=['get'])
    def dashboard_summary(self, request):
        user = request.user
        
        # Financial summary
        account = FinancialAccount.objects.filter(user=user).first()
        deposits = Deposit.objects.filter(user=user, status='completed')
        
        # Current month deposits
        current_month_deposits = deposits.filter(
            created_at__month=datetime.now().month,
            created_at__year=datetime.now().year
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        # Beneficiaries
        active_beneficiaries = Beneficiary.objects.filter(
            user=user,
            status='active'
        ).count()
        
        return Response({
            'total_contributions': account.total_contributions if account else 0,
            'interest_earned': account.interest_earned if account else 0,
            'monthly_deposits': current_month_deposits,
            'active_beneficiaries': active_beneficiaries,
            'total_deposits': deposits.count()
        })

class ActivityLogViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ActivityLog.objects.all()
    serializer_class = ActivityLogSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['action']
    search_fields = ['action', 'description']
    
    def get_queryset(self):
        if self.request.user.role == 'admin':
            return ActivityLog.objects.all()
        return ActivityLog.objects.filter(user=self.request.user)

