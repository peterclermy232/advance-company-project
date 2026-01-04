from celery import shared_task
from django.core.mail import send_mail
from .models import Report
from .utils import generate_financial_pdf_report
from apps.financial.models import Deposit, FinancialAccount

@shared_task
def generate_monthly_reports():
    """Generate monthly reports for all users"""
    from apps.accounts.models import User
    
    users = User.objects.filter(is_active=True, role='user')
    
    for user in users:
        try:
            account = FinancialAccount.objects.get(user=user)
            deposits = Deposit.objects.filter(user=user, status='completed')
            
            # Generate PDF
            pdf_buffer = generate_financial_pdf_report(user, deposits, account)
            
            # Create report record
            report = Report.objects.create(
                user=user,
                report_type='financial',
                title=f'Monthly Report {datetime.now().strftime("%B %Y")}',
                status='ready'
            )
            
            report.file.save(
                f'monthly_report_{user.id}_{datetime.now().strftime("%Y%m")}.pdf',
                pdf_buffer
            )
            
            # Send email notification
            send_mail(
                'Monthly Financial Report Ready',
                f'Your monthly report for {datetime.now().strftime("%B %Y")} is ready.',
                'noreply@advancecompany.com',
                [user.email],
                fail_silently=True,
            )
            
        except Exception as e:
            print(f"Error generating report for user {user.id}: {str(e)}")
    
    return f"Generated reports for {users.count()} users"
