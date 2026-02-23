from datetime import date, datetime

from django.db.models import Count, Sum
from django.db.models.functions import TruncMonth, TruncDate
from django.conf import settings
from django.core.mail import send_mail

from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from django_filters.rest_framework import DjangoFilterBackend

from supabase import create_client, Client
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

# Signed URL expiry — 24 hours in seconds
SIGNED_URL_EXPIRES_IN = 60 * 60 * 24


def get_supabase_client() -> Client:
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)


def upload_report_to_supabase(pdf_buffer, folder, filename):
    """
    Upload PDF to private Supabase Storage bucket.

    Args:
        pdf_buffer: BytesIO buffer containing PDF data
        folder: Folder path inside the bucket (e.g., 'financial')
        filename: File name without extension

    Returns:
        str: Internal file path (used later to generate signed URLs)
    """
    try:
        supabase = get_supabase_client()
        pdf_buffer.seek(0)
        file_data = pdf_buffer.read()

        # Full path inside the bucket e.g. financial/report_xyz.pdf
        file_path = f"{folder}/{filename}.pdf"

        supabase.storage.from_(settings.SUPABASE_BUCKET).upload(
            path=file_path,
            file=file_data,
            file_options={"content-type": "application/pdf", "upsert": "true"}
        )

        logger.info(f"Upload successful: {file_path}")
        return file_path  # return path, not public URL (bucket is private)

    except Exception as e:
        logger.error(f"Supabase upload error: {traceback.format_exc()}")
        raise Exception(f"Failed to upload file to Supabase: {str(e)}")


def generate_signed_url(file_path, expires_in=SIGNED_URL_EXPIRES_IN):
    """
    Generate a temporary signed URL for a private Supabase file.

    Args:
        file_path: Path inside the bucket (e.g., 'financial/report_xyz.pdf')
        expires_in: Expiry in seconds (default 24 hours)

    Returns:
        str: Signed URL valid for the given duration
    """
    try:
        supabase = get_supabase_client()
        result = supabase.storage.from_(settings.SUPABASE_BUCKET).create_signed_url(
            path=file_path,
            expires_in=expires_in
        )
        signed_url = result.get('signedURL') or result.get('signed_url')
        logger.info(f"Signed URL generated for: {file_path}")
        return signed_url

    except Exception as e:
        logger.error(f"Signed URL error: {traceback.format_exc()}")
        raise Exception(f"Failed to generate signed URL: {str(e)}")


def send_report_email(user, report_type, signed_url, expires_hours=24):
    """
    Send an email to the user with the signed URL to access their report.

    Args:
        user: Django user object
        report_type: e.g. 'Financial', 'Compensatory', 'Activity'
        signed_url: The temporary download URL
        expires_hours: How many hours the link is valid
    """
    subject = f"Your {report_type} Report is Ready"
    message = f"""
Hello {user.first_name or user.email},

Your {report_type} Report has been generated successfully.

You can download it using the secure link below:

{signed_url}

⚠️  This link expires in {expires_hours} hours for security reasons.
If the link expires, you can generate a new report from your dashboard.

If you did not request this report, please contact support immediately.

Regards,
{settings.COMPANY_NAME if hasattr(settings, 'COMPANY_NAME') else 'The Team'}
    """.strip()

    send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        fail_silently=False
    )
    logger.info(f"Report email sent to {user.email}")


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
        serializer.save(user=self.request.user, generated_by=request.user)

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
            logger.info(f"Generating financial report for user {request.user.uuid}")

            account = FinancialAccount.objects.filter(user=request.user).first()
            deposits = Deposit.objects.filter(user=request.user, status='completed')
            if date_from:
                deposits = deposits.filter(created_at__gte=date_from)
            if date_to:
                deposits = deposits.filter(created_at__lte=date_to)

            total_deposits = deposits.aggregate(total=Sum('amount'))['total'] or 0
            deposit_count = deposits.aggregate(count=Count('uuid'))['count'] or 0

            # Monthly breakdown
            monthly_deposits = []
            if deposits.exists():
                monthly_data = deposits.annotate(
                    month=TruncMonth('created_at')
                ).values('month').annotate(
                    total=Sum('amount'),
                    count=Count('uuid')
                ).order_by('month')

                for item in monthly_data:
                    monthly_deposits.append({
                        'month': item['month'].strftime('%B %Y'),
                        'total_amount': float(item['total']),
                        'transaction_count': item['count']
                    })

            # Recent deposits
            recent_deposits = deposits.order_by('-created_at')[:10].values(
                'uuid', 'amount', 'payment_method', 'created_at', 'status'
            )
            recent_deposits_list = [
                {
                    'id': str(d['uuid']),
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
                    'account_balance': float(account.total_contributions + account.interest_earned) if account else 0,
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

            logger.info("Generating PDF...")
            pdf_buffer = generate_financial_pdf_report(
                user=request.user,
                report=report,
                financial_data=financial_data,
                deposits=deposits,
                account=account
            )

            logger.info("Uploading to Supabase...")
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"financial_report_user{request.user.uuid}_{timestamp}"

            file_path = upload_report_to_supabase(pdf_buffer, 'financial', filename)
            signed_url = generate_signed_url(file_path)

            # Send email with signed URL
            send_report_email(request.user, 'Financial', signed_url)

            # Store file path (not signed URL — it expires)
            report.file_url = file_path
            report.status = 'RESOLVED'
            report.description = 'Financial report generated and emailed successfully'
            report.save()

            return Response({
                'success': True,
                'message': 'Report generated and sent to your email',
                'report': ReportSerializer(report, context={'request': request}).data,
                'financial_data': financial_data
            })

        except Exception as e:
            logger.error(f"Report generation error: {traceback.format_exc()}")
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
                    'id': str(ben.uuid),
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

            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"compensatory_report_user{request.user.uuid}_{timestamp}"

            file_path = upload_report_to_supabase(pdf_buffer, 'compensatory', filename)
            signed_url = generate_signed_url(file_path)

            send_report_email(request.user, 'Compensatory', signed_url)

            report.file_url = file_path
            report.status = 'RESOLVED'
            report.description = 'Compensatory report generated and emailed successfully'
            report.save()

            return Response({
                'success': True,
                'message': 'Report generated and sent to your email',
                'report': ReportSerializer(report, context={'request': request}).data,
                'compensatory_data': compensatory_data
            })

        except Exception as e:
            logger.error(f"Report generation error: {traceback.format_exc()}")
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

            daily_activities = (
                activities
                .annotate(date=TruncDate('created_at'))
                .values('date')
                .annotate(count=Count('id'))
                .order_by('date')
            )
            daily_chart = [
                {'date': item['date'].strftime('%Y-%m-%d'), 'activities': item['count']}
                for item in daily_activities
            ]

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

            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"activity_report_user{request.user.uuid}_{timestamp}"

            file_path = upload_report_to_supabase(pdf_buffer, 'activity', filename)
            signed_url = generate_signed_url(file_path)

            send_report_email(request.user, 'Activity', signed_url)

            report.file_url = file_path
            report.status = 'RESOLVED'
            report.description = 'Activity report generated and emailed successfully'
            report.save()

            return Response({
                'success': True,
                'message': 'Report generated and sent to your email',
                'report': ReportSerializer(report, context={'request': request}).data,
                'activity_data': activity_data
            })

        except Exception as e:
            logger.error(f"Report generation error: {traceback.format_exc()}")
            report.status = 'REJECTED'
            report.description = f"Error: {str(e)}"
            report.save()
            return Response({
                'success': False,
                'error': str(e),
                'message': 'Failed to generate report'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # ---------------------- RESEND REPORT EMAIL ----------------------
    @action(detail=True, methods=['post'])
    def resend_report_email(self, request, pk=None):
        """
        Regenerate a fresh signed URL for an existing report and resend email.
        Useful when the previous link has expired.
        """
        report = self.get_object()

        if report.user != request.user and request.user.role != 'admin':
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)

        if not report.file_url:
            return Response({'error': 'No file found for this report'}, status=status.HTTP_404_NOT_FOUND)

        try:
            signed_url = generate_signed_url(report.file_url)
            send_report_email(report.user, report.report_type.capitalize(), signed_url)

            return Response({
                'success': True,
                'message': f'Report link resent to {report.user.email}'
            })

        except Exception as e:
            logger.error(f"Resend error: {traceback.format_exc()}")
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # ---------------------- DASHBOARD SUMMARY (user-level) ----------------------
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
            'total_deposits': deposits.aggregate(count=Count('uuid'))['count'] or 0
        })

    # ---------------------- ADMIN SUMMARY ----------------------
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Admin-only aggregated platform statistics."""
        if request.user.role != 'admin':
            return Response({'error': 'Admin access required'}, status=status.HTTP_403_FORBIDDEN)

        from apps.accounts.models import User
        from apps.applications.models import Application
        from apps.documents.models import Document

        today = date.today()
        start = date(today.year, today.month, 1)

        total_users = User.objects.filter(is_active=True).count()
        total_deposits = Deposit.objects.filter(status='completed').aggregate(
            count=Count('uuid'), total=Sum('amount')
        )
        monthly_deposits = Deposit.objects.filter(
            status='completed', created_at__date__gte=start
        ).aggregate(
            count=Count('uuid'), total=Sum('amount')
        )
        accounts = FinancialAccount.objects.aggregate(
            total_savings=Sum('total_contributions'),
            total_interest=Sum('interest_earned'),
        )

        return Response({
            'users': {'total_active': total_users},
            'deposits': {
                'all_time_count': total_deposits['count'] or 0,
                'all_time_total': float(total_deposits['total'] or 0),
                'this_month_count': monthly_deposits['count'] or 0,
                'this_month_total': float(monthly_deposits['total'] or 0),
            },
            'applications': {
                'pending': Application.objects.filter(status='pending').count()
            },
            'beneficiaries': {
                'total': Beneficiary.objects.count()
            },
            'documents': {
                'pending_review': Document.objects.filter(status='pending').count()
            },
            'accounts': {
                'total_savings': float(accounts['total_savings'] or 0),
                'total_interest_earned': float(accounts['total_interest'] or 0),
            },
        })

    # ---------------------- DEPOSIT TRENDS ----------------------
    @action(detail=False, methods=['get'])
    def deposit_trends(self, request):
        """Admin-only monthly deposit totals for the last 12 months."""
        if request.user.role != 'admin':
            return Response({'error': 'Admin access required'}, status=status.HTTP_403_FORBIDDEN)

        trends = (
            Deposit.objects
            .filter(status='completed')
            .annotate(month=TruncMonth('created_at'))
            .values('month')
            .annotate(total=Sum('amount'), count=Count('uuid'))
            .order_by('-month')[:12]
        )

        return Response(list(trends))


# ---------------------- ACTIVITY LOG ----------------------
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