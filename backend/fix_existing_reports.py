import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'advance_company.settings')
django.setup()

import cloudinary
import cloudinary.api
import cloudinary.uploader
from django.conf import settings
from apps.reports.models import Report
from apps.financial.models import FinancialAccount, Deposit
from apps.beneficiary.models import Beneficiary
from apps.reports.models import ActivityLog
from apps.reports.utils import (
    generate_financial_pdf_report,
    generate_compensatory_pdf_report,
    generate_activity_pdf_report
)
from django.db.models import Sum, Count
from datetime import datetime

print("="*70)
print("FIXING EXISTING REPORTS - Re-uploading with Public Access")
print("="*70)

# Configure Cloudinary
cloudinary.config(
    cloud_name=settings.CLOUDINARY_STORAGE['CLOUD_NAME'],
    api_key=settings.CLOUDINARY_STORAGE['API_KEY'],
    api_secret=settings.CLOUDINARY_STORAGE['API_SECRET'],
    secure=True
)

# Get all reports with status 'ready' or 'RESOLVED' that have file_url
reports = Report.objects.filter(
    file_url__isnull=False
).exclude(file_url='')

print(f"\n📊 Found {reports.count()} reports to fix\n")

fixed_count = 0
error_count = 0

for report in reports:
    print(f"\n[{report.id}] {report.title}")
    print(f"   User: {report.user.full_name}")
    print(f"   Type: {report.report_type}")
    print(f"   Old URL: {report.file_url}")
    
    try:
        # Regenerate the report PDF
        print(f"   → Regenerating PDF...")
        
        if report.report_type == 'FINANCIAL':
            # Gather data
            account = FinancialAccount.objects.filter(user=report.user).first()
            deposits = Deposit.objects.filter(user=report.user, status='completed')
            
            if report.date_from:
                deposits = deposits.filter(created_at__gte=report.date_from)
            if report.date_to:
                deposits = deposits.filter(created_at__lte=report.date_to)
            
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
                },
                'monthly_breakdown': monthly_deposits,
                'recent_transactions': recent_deposits_list
            }
            
            pdf_buffer = generate_financial_pdf_report(
                user=report.user,
                report=report,
                financial_data=financial_data,
                deposits=deposits,
                account=account
            )
            
        elif report.report_type == 'COMPENSATORY':
            beneficiaries = Beneficiary.objects.filter(user=report.user)
            deposits = Deposit.objects.filter(user=report.user, status='completed')
            
            if report.date_from:
                deposits = deposits.filter(created_at__gte=report.date_from)
            if report.date_to:
                deposits = deposits.filter(created_at__lte=report.date_to)
            
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
                },
                'beneficiaries': beneficiary_data,
            }
            
            pdf_buffer = generate_compensatory_pdf_report(
                user=report.user,
                report=report,
                compensatory_data=compensatory_data
            )
            
        elif report.report_type == 'ACTIVITY':
            activities = ActivityLog.objects.filter(user=report.user)
            
            if report.date_from:
                activities = activities.filter(created_at__gte=report.date_from)
            if report.date_to:
                activities = activities.filter(created_at__lte=report.date_to)
            
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
                    'most_common_action': action_summary.first()['action'] if action_summary else None
                },
                'action_breakdown': list(action_summary),
                'recent_activities': list(recent_activities),
                'daily_activity_chart': daily_chart
            }
            
            pdf_buffer = generate_activity_pdf_report(
                user=report.user,
                report=report,
                activity_data=activity_data
            )
        
        else:
            print(f"   ⚠️  Unknown report type: {report.report_type}")
            continue
        
        # Upload to Cloudinary with PUBLIC access
        print(f"   → Uploading to Cloudinary with public access...")
        pdf_buffer.seek(0)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_type_folder = report.report_type.lower()
        filename = f"{report_type_folder}_report_user{report.user.id}_{timestamp}"
        
        result = cloudinary.uploader.upload(
            pdf_buffer,
            resource_type='raw',
            folder=f'reports/{report_type_folder}',
            public_id=filename,
            format='pdf',
            type='upload',
            overwrite=True,
            invalidate=True,
            access_mode='public',  # ⭐ THE FIX!
            use_filename=False,
            unique_filename=False
        )
        
        # Update report with new URL
        old_url = report.file_url
        new_url = result['secure_url']
        report.file_url = new_url
        
        # Update status to match model choices
        if report.status not in ['PENDING', 'IN_PROGRESS', 'RESOLVED', 'REJECTED']:
            report.status = 'RESOLVED'
        
        report.save()
        
        print(f"   ✅ SUCCESS!")
        print(f"   New URL: {new_url}")
        
        # Verify the URL is accessible
        import requests
        try:
            response = requests.head(new_url, timeout=5)
            if response.status_code == 200:
                print(f"   ✅ URL verified - PDF is accessible!")
            else:
                print(f"   ⚠️  URL returned status {response.status_code}")
        except:
            print(f"   ⚠️  Could not verify URL accessibility")
        
        fixed_count += 1
        
    except Exception as e:
        print(f"   ❌ ERROR: {str(e)}")
        import traceback
        print(traceback.format_exc())
        error_count += 1

print("\n" + "="*70)
print("SUMMARY")
print("="*70)
print(f"Total reports: {reports.count()}")
print(f"✅ Fixed: {fixed_count}")
print(f"❌ Errors: {error_count}")
print("="*70)

if fixed_count > 0:
    print("\n🎉 Reports have been re-uploaded with public access!")
    print("All report URLs should now work correctly.")
else:
    print("\n⚠️  No reports were fixed. Check errors above.")