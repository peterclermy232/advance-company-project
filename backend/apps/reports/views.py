from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from django.core.files.base import ContentFile
from django.db.models import Sum, Count
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from datetime import datetime
import cloudinary.uploader
import traceback
import logging

from .models import Report, ActivityLog
from .serializers import ReportSerializer, ActivityLogSerializer
from apps.financial.models import Deposit, FinancialAccount
from apps.beneficiary.models import Beneficiary
from .utils import (
    generate_financial_pdf_report,
    generate_compensatory_pdf_report,
    generate_activity_pdf_report
)

logger = logging.getLogger(__name__)


def upload_report_to_cloudinary(pdf_buffer, folder, filename):
    """
    Upload PDF to Cloudinary - type='upload' is NOT restricted in your settings
    
    Args:
        pdf_buffer: BytesIO buffer containing PDF data
        folder: Cloudinary folder path (e.g., 'reports/financial')
        filename: File name without extension
    
    Returns:
        str: Direct secure URL to the PDF
    """
    pdf_buffer.seek(0)
    
    # Upload with type='upload' (this is NOT in your restricted list)
    result = cloudinary.uploader.upload(
        pdf_buffer,
        resource_type='raw',
        folder=folder,
        public_id=filename,
        format='pdf',
        # Don't specify type - it defaults to 'upload' which is allowed
        overwrite=True,
        invalidate=True
    )
    
    logger.info(f"Upload successful: {result.get('secure_url')}")
    logger.info(f"Public ID: {result.get('public_id')}")
    
    # Return the direct secure_url (no signing needed since 'upload' is not restricted)
    return result.get('secure_url')


class ReportViewSet(viewsets.ModelViewSet):
    queryset = Report.objects.all()
    serializer_class = ReportSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['report_type', 'status']
    ordering_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']

    def get_queryset(self):
        if self.request.user.role == 'admin':
            return Report.objects.all()
        return Report.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user, generated_by=self.request.user)

    # ---------------------- FINANCIAL REPORT ----------------------
    @action(detail=False, methods=['post'])
    def generate_financial_report(self, request):
        date_from = request.data.get('date_from') or None
        date_to = request.data.get('date_to') or None

        report = Report.objects.create(
            user=request.user,
            report_type='FINANCIAL',
            title=f'Financial Report {datetime.now().strftime("%Y-%m-%d")}',
            date_from=date_from,
            date_to=date_to,
            generated_by=request.user,
            status='PENDING',
            description='Generating financial report...'
        )

        try:
            logger.info(f"Generating financial report for user {request.user.id}")
            
            account = FinancialAccount.objects.filter(user=request.user).first()
            deposits = Deposit.objects.filter(user=request.user, status='completed')
            if date_from:
                deposits = deposits.filter(created_at__gte=date_from)
            if date_to:
                deposits = deposits.filter(created_at__lte=date_to)

            total_deposits = deposits.aggregate(total=Sum('amount'))['total'] or 0
            deposit_count = deposits.count()

            # Monthly breakdown
            monthly_deposits = []
            if deposits.exists():
                from django.db.models.functions import TruncMonth
                monthly_data = deposits.annotate(
                    month=TruncMonth('created_at')
                ).values('month').annotate(
                    total=Sum('amount'),
                    count=Count('id')
                ).order_by('month')

                for item in monthly_data:
                    monthly_deposits.append({
                        'month': item['month'].strftime('%B %Y'),
                        'total_amount': float(item['total']),
                        'transaction_count': item['count']
                    })

            # Recent deposits
            recent_deposits = deposits.order_by('-created_at')[:10].values(
                'id', 'amount', 'payment_method', 'created_at', 'status'
            )
            recent_deposits_list = [
                {
                    'id': d['id'],
                    'amount': float(d['amount']),
                    'payment_method': d['payment_method'],
                    'created_at': d['created_at'],
                    'status': d['status']
                } for d in recent_deposits
            ]

            financial_data = {
                'account_summary': {
                    'total_contributions': float(account.total_contributions) if account else 0,
                    'interest_earned': float(account.interest_earned) if account else 0,
                    'account_balance': float(account.total_contributions + (account.interest_earned if account else 0)) if account else 0,
                },
                'period_summary': {
                    'total_deposits': float(total_deposits),
                    'deposit_count': deposit_count,
                    'average_deposit': float(total_deposits / deposit_count) if deposit_count else 0,
                    'date_from': date_from,
                    'date_to': date_to
                },
                'monthly_breakdown': monthly_deposits,
                'recent_transactions': recent_deposits_list
            }

            # Generate PDF
            logger.info("Generating PDF...")
            pdf_buffer = generate_financial_pdf_report(
                user=request.user,
                report=report,
                financial_data=financial_data,
                deposits=deposits,
                account=account
            )

            # Upload to Cloudinary
            logger.info("Uploading to Cloudinary...")
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"financial_report_user{request.user.id}_{timestamp}"
            
            file_url = upload_report_to_cloudinary(
                pdf_buffer,
                'reports/financial',
                filename
            )
            
            report.file_url = file_url
            report.status = 'RESOLVED'
            report.description = 'Financial report generated successfully'
            report.save()

            return Response({
                'success': True,
                'message': 'Report generated successfully',
                'report': ReportSerializer(report, context={'request': request}).data,
                'financial_data': financial_data
            })

        except Exception as e:
            error_details = traceback.format_exc()
            logger.error(f"Report generation error: {error_details}")
            
            report.status = 'REJECTED'
            report.description = f"Error: {str(e)}"
            report.save()
            
            return Response({
                'success': False,
                'error': str(e),
                'message': 'Failed to generate report'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # ---------------------- COMPENSATORY REPORT ----------------------
    @action(detail=False, methods=['post'])
    def generate_compensatory_report(self, request):
        date_from = request.data.get('date_from') or None
        date_to = request.data.get('date_to') or None

        report = Report.objects.create(
            user=request.user,
            report_type='COMPENSATORY',
            title=f'Compensatory Report {datetime.now().strftime("%Y-%m-%d")}',
            date_from=date_from,
            date_to=date_to,
            generated_by=request.user,
            status='PENDING',
            description='Generating compensatory report...'
        )

        try:
            beneficiaries = Beneficiary.objects.filter(user=request.user)
            deposits = Deposit.objects.filter(user=request.user, status='completed')
            if date_from:
                deposits = deposits.filter(created_at__gte=date_from)
            if date_to:
                deposits = deposits.filter(created_at__lte=date_to)

            total_contributions = deposits.aggregate(total=Sum('amount'))['total'] or 0

            active_beneficiaries = beneficiaries.filter(status='active')
            total_percentage = active_beneficiaries.aggregate(total=Sum('percentage_allocation'))['total'] or 0

            beneficiary_data = []
            for ben in active_beneficiaries:
                allocated_amount = (float(ben.percentage_allocation) / 100) * float(total_contributions)
                beneficiary_data.append({
                    'id': ben.id,
                    'name': ben.name,
                    'relationship': ben.relation,
                    'percentage': float(ben.percentage_allocation),
                    'allocated_amount': round(allocated_amount, 2),
                    'status': ben.status,
                    'age': ben.age,
                    'profession': ben.profession,
                    'verification_status': ben.verification_status
                })

            unallocated_percentage = 100 - float(total_percentage)
            unallocated_amount = (unallocated_percentage / 100) * float(total_contributions)

            compensatory_data = {
                'summary': {
                    'total_beneficiaries': beneficiaries.count(),
                    'active_beneficiaries': active_beneficiaries.count(),
                    'inactive_beneficiaries': beneficiaries.exclude(status='active').count(),
                    'total_contributions': float(total_contributions),
                    'total_allocated_percentage': float(total_percentage),
                    'unallocated_percentage': round(unallocated_percentage, 2),
                    'unallocated_amount': round(unallocated_amount, 2),
                    'date_from': date_from,
                    'date_to': date_to
                },
                'beneficiaries': beneficiary_data,
                'allocation_chart': [
                    {'name': b['name'], 'value': b['percentage']} for b in beneficiary_data
                ]
            }

            pdf_buffer = generate_compensatory_pdf_report(
                user=request.user,
                report=report,
                compensatory_data=compensatory_data
            )

            # Upload to Cloudinary
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"compensatory_report_user{request.user.id}_{timestamp}"
            
            file_url = upload_report_to_cloudinary(
                pdf_buffer,
                'reports/compensatory',
                filename
            )
            
            report.file_url = file_url
            report.status = 'RESOLVED'
            report.description = 'Compensatory report generated successfully'
            report.save()

            return Response({
                'success': True,
                'message': 'Report generated successfully',
                'report': ReportSerializer(report, context={'request': request}).data,
                'compensatory_data': compensatory_data
            })

        except Exception as e:
            error_details = traceback.format_exc()
            logger.error(f"Report generation error: {error_details}")
            
            report.status = 'REJECTED'
            report.description = f"Error: {str(e)}"
            report.save()
            
            return Response({
                'success': False,
                'error': str(e),
                'message': 'Failed to generate report'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # ---------------------- ACTIVITY REPORT ----------------------
    @action(detail=False, methods=['post'])
    def generate_activity_report(self, request):
        date_from = request.data.get('date_from') or None
        date_to = request.data.get('date_to') or None

        report = Report.objects.create(
            user=request.user,
            report_type='ACTIVITY',
            title=f'Activity Report {datetime.now().strftime("%Y-%m-%d")}',
            date_from=date_from,
            date_to=date_to,
            generated_by=request.user,
            status='PENDING',
            description='Generating activity report...'
        )

        try:
            activities = ActivityLog.objects.filter(user=request.user)
            if date_from:
                activities = activities.filter(created_at__gte=date_from)
            if date_to:
                activities = activities.filter(created_at__lte=date_to)

            action_summary = activities.values('action').annotate(count=Count('id')).order_by('-count')
            recent_activities = activities.order_by('-created_at')[:20].values(
                'id', 'action', 'description', 'created_at'
            )

            from django.db.models.functions import TruncDate
            daily_activities = activities.annotate(date=TruncDate('created_at')).values('date').annotate(count=Count('id')).order_by('date')
            daily_chart = [{'date': item['date'].strftime('%Y-%m-%d'), 'activities': item['count']} for item in daily_activities]

            activity_data = {
                'summary': {
                    'total_activities': activities.count(),
                    'unique_actions': activities.values('action').distinct().count(),
                    'date_from': date_from,
                    'date_to': date_to,
                    'most_common_action': action_summary.first()['action'] if action_summary else None
                },
                'action_breakdown': list(action_summary),
                'recent_activities': list(recent_activities),
                'daily_activity_chart': daily_chart
            }

            pdf_buffer = generate_activity_pdf_report(
                user=request.user,
                report=report,
                activity_data=activity_data
            )

            # Upload to Cloudinary
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"activity_report_user{request.user.id}_{timestamp}"
            
            file_url = upload_report_to_cloudinary(
                pdf_buffer,
                'reports/activity',
                filename
            )
            
            report.file_url = file_url
            report.status = 'RESOLVED'
            report.description = 'Activity report generated successfully'
            report.save()

            return Response({
                'success': True,
                'message': 'Report generated successfully',
                'report': ReportSerializer(report, context={'request': request}).data,
                'activity_data': activity_data
            })

        except Exception as e:
            error_details = traceback.format_exc()
            logger.error(f"Report generation error: {error_details}")
            
            report.status = 'REJECTED'
            report.description = f"Error: {str(e)}"
            report.save()
            
            return Response({
                'success': False,
                'error': str(e),
                'message': 'Failed to generate report'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # ---------------------- DASHBOARD SUMMARY ----------------------
    @action(detail=False, methods=['get'])
    def dashboard_summary(self, request):
        user = request.user
        account = FinancialAccount.objects.filter(user=user).first()
        deposits = Deposit.objects.filter(user=user, status='completed')

        current_month_deposits = deposits.filter(
            created_at__month=datetime.now().month,
            created_at__year=datetime.now().year
        ).aggregate(total=Sum('amount'))['total'] or 0

        active_beneficiaries = Beneficiary.objects.filter(user=user, status='active').count()

        return Response({
            'total_contributions': float(account.total_contributions) if account else 0,
            'interest_earned': float(account.interest_earned) if account else 0,
            'monthly_deposits': float(current_month_deposits),
            'active_beneficiaries': active_beneficiaries,
            'total_deposits': deposits.count()
        })


class ActivityLogViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ActivityLog.objects.all()
    serializer_class = ActivityLogSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['action']
    search_fields = ['action', 'description']

    def get_queryset(self):
        if self.request.user.role == 'admin':
            return ActivityLog.objects.all()
        return ActivityLog.objects.filter(user=self.request.user)