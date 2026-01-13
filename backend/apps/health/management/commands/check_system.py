from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from apps.financial.models import Deposit
from django.utils import timezone
from datetime import timedelta

class Command(BaseCommand):
    help = 'Check system health and send alerts'

    def handle(self, *args, **options):
        issues = []
        
        # Check for stuck deposits
        stuck_deposits = Deposit.objects.filter(
            status='pending',
            created_at__lt=timezone.now() - timedelta(hours=24)
        )
        
        if stuck_deposits.count() > 0:
            issues.append(f'{stuck_deposits.count()} deposits stuck for >24h')
        
        # Check for failed payments (>10% failure rate)
        recent_deposits = Deposit.objects.filter(
            created_at__gte=timezone.now() - timedelta(hours=24)
        )
        if recent_deposits.count() > 10:
            failed = recent_deposits.filter(status='failed').count()
            failure_rate = (failed / recent_deposits.count()) * 100
            
            if failure_rate > 10:
                issues.append(f'High failure rate: {failure_rate:.1f}%')
        
        # Send alerts if issues found
        if issues:
            send_mail(
                subject='🚨 System Alert - Advance Company',
                message='\n'.join(issues),
                from_email='alerts@yourdomain.com',
                recipient_list=['admin@yourdomain.com'],
            )
            
            self.stdout.write(self.style.WARNING('Alerts sent'))
        else:
            self.stdout.write(self.style.SUCCESS('All checks passed'))