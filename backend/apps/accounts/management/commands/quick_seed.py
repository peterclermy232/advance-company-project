from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal

from apps.accounts.models import User
from apps.financial.models import FinancialAccount, Deposit
from apps.beneficiary.models import Beneficiary


class Command(BaseCommand):
    help = 'Quick seed with minimal test data'

    def handle(self, *args, **options):
        self.stdout.write('Creating quick test data...')
        
        # Create admin
        admin, created = User.objects.get_or_create(
            email='admin@advancecompany.com',
            defaults={
                'phone_number': '+254700000000',
                'full_name': 'System Administrator',
                'role': 'admin',
                'is_staff': True,
                'is_superuser': True
            }
        )
        if created:
            admin.set_password('admin123')
            admin.save()
        
        # Create test user
        user, created = User.objects.get_or_create(
            email='test@user.com',
            defaults={
                'phone_number': '+254712345678',
                'full_name': 'Test User',
                'role': 'user',
                'age': 30,
                'gender': 'M',
                'marital_status': 'married',
                'number_of_kids': 2,
                'profession': 'Software Developer',
                'activity_status': 'Active'
            }
        )
        if created:
            user.set_password('password123')
            user.save()
        
        # Create financial account
        account, _ = FinancialAccount.objects.get_or_create(
            user=user,
            defaults={
                'total_contributions': Decimal('50000.00'),
                'interest_earned': Decimal('2500.00'),
                'interest_rate': Decimal('5.00')
            }
        )
        
        # Create 5 deposits
        for i in range(5):
            Deposit.objects.get_or_create(
                user=user,
                transaction_reference=f'TXN00000{i+1}',
                defaults={
                    'amount': Decimal('5000.00'),
                    'payment_method': 'mpesa',
                    'status': 'completed',
                    'created_at': timezone.now() - timedelta(days=30*(i+1))
                }
            )
        
        # Create beneficiary
        Beneficiary.objects.get_or_create(
            user=user,
            name='Jane Doe',
            defaults={
                'relation': 'spouse',
                'age': 28,
                'gender': 'F',
                'phone_number': '+254712345679',
                'status': 'active',
                'verification_status': 'verified'
            }
        )
        
        self.stdout.write(self.style.SUCCESS('✅ Quick seed completed!'))
        self.stdout.write(self.style.SUCCESS('Login with:'))
        self.stdout.write(self.style.SUCCESS('  test@user.com / password123'))
        self.stdout.write(self.style.SUCCESS('  admin@advancecompany.com / admin123'))