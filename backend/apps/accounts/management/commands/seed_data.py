from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal
import random

from apps.accounts.models import User
from apps.financial.models import FinancialAccount, Deposit, InterestCalculation
from apps.beneficiary.models import Beneficiary
from apps.documents.models import Document
from apps.applications.models import Application, ApplicationActivity
from apps.reports.models import Report, ActivityLog


class Command(BaseCommand):
    help = 'Seed database with test data'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting database seeding...'))
        
        # Clear existing data (optional - comment out if you want to keep existing data)
        self.stdout.write('Cleaning existing data...')
        ActivityLog.objects.all().delete()
        Report.objects.all().delete()
        ApplicationActivity.objects.all().delete()
        Application.objects.all().delete()
        Document.objects.all().delete()
        InterestCalculation.objects.all().delete()
        Deposit.objects.all().delete()
        Beneficiary.objects.all().delete()
        FinancialAccount.objects.all().delete()
        User.objects.filter(email__contains='test').delete()  # Only delete test users
        
        # Create users
        self.stdout.write('Creating users...')
        users = self.create_users()
        
        # Create financial data
        self.stdout.write('Creating financial accounts and deposits...')
        self.create_financial_data(users)
        
        # Create beneficiaries
        self.stdout.write('Creating beneficiaries...')
        self.create_beneficiaries(users)
        
        # Create documents
        self.stdout.write('Creating documents...')
        self.create_documents(users)
        
        # Create applications
        self.stdout.write('Creating applications...')
        self.create_applications(users)
        
        # Create reports
        self.stdout.write('Creating reports...')
        self.create_reports(users)
        
        # Create activity logs
        self.stdout.write('Creating activity logs...')
        self.create_activity_logs(users)
        
        self.stdout.write(self.style.SUCCESS('✅ Database seeding completed successfully!'))
        self.stdout.write(self.style.SUCCESS('\n=== TEST CREDENTIALS ==='))
        self.stdout.write(self.style.SUCCESS('Admin: admin@advancecompany.com / admin123'))
        self.stdout.write(self.style.SUCCESS('User 1: john.doe@test.com / password123'))
        self.stdout.write(self.style.SUCCESS('User 2: jane.smith@test.com / password123'))
        self.stdout.write(self.style.SUCCESS('User 3: mike.johnson@test.com / password123'))
        self.stdout.write(self.style.SUCCESS('User 4: sarah.williams@test.com / password123'))

    def create_users(self):
        """Create test users"""
        # Ensure admin exists
        admin, created = User.objects.get_or_create(
            email='admin@advancecompany.com',
            defaults={
                'phone_number': '+254700000000',
                'full_name': 'System Administrator',
                'role': 'admin',
                'is_staff': True,
                'is_superuser': True,
                'age': 35,
                'gender': 'M',
                'marital_status': 'married',
                'profession': 'Administrator',
                'activity_status': 'Active'
            }
        )
        if created:
            admin.set_password('admin123')
            admin.save()
        
        users_data = [
            {
                'email': 'john.doe@test.com',
                'phone_number': '+254712345001',
                'full_name': 'John Doe',
                'age': 35,
                'gender': 'M',
                'marital_status': 'married',
                'number_of_kids': 2,
                'profession': 'Software Engineer',
                'salary_range': '100,000 - 150,000',
                'spouse_name': 'Jane Doe',
                'spouse_age': 33,
                'spouse_profession': 'Teacher'
            },
            {
                'email': 'jane.smith@test.com',
                'phone_number': '+254712345002',
                'full_name': 'Jane Smith',
                'age': 28,
                'gender': 'F',
                'marital_status': 'single',
                'number_of_kids': 0,
                'profession': 'Marketing Manager',
                'salary_range': '80,000 - 100,000'
            },
            {
                'email': 'mike.johnson@test.com',
                'phone_number': '+254712345003',
                'full_name': 'Mike Johnson',
                'age': 42,
                'gender': 'M',
                'marital_status': 'married',
                'number_of_kids': 3,
                'profession': 'Business Analyst',
                'salary_range': '120,000 - 150,000',
                'spouse_name': 'Lisa Johnson',
                'spouse_age': 40,
                'spouse_profession': 'Nurse'
            },
            {
                'email': 'sarah.williams@test.com',
                'phone_number': '+254712345004',
                'full_name': 'Sarah Williams',
                'age': 31,
                'gender': 'F',
                'marital_status': 'divorced',
                'number_of_kids': 1,
                'profession': 'Accountant',
                'salary_range': '90,000 - 120,000'
            },
            {
                'email': 'david.brown@test.com',
                'phone_number': '+254712345005',
                'full_name': 'David Brown',
                'age': 45,
                'gender': 'M',
                'marital_status': 'married',
                'number_of_kids': 2,
                'profession': 'Civil Engineer',
                'salary_range': '150,000 - 200,000',
                'spouse_name': 'Mary Brown',
                'spouse_age': 43,
                'spouse_profession': 'Architect'
            }
        ]
        
        users = [admin]
        for user_data in users_data:
            user, created = User.objects.get_or_create(
                email=user_data['email'],
                defaults={
                    **user_data,
                    'role': 'user',
                    'activity_status': 'Active'
                }
            )
            if created:
                user.set_password('password123')
                user.save()
            users.append(user)
        
        return users

    def create_financial_data(self, users):
        """Create financial accounts and deposits"""
        payment_methods = ['mpesa', 'bank', 'mansa_x']
        statuses = ['completed', 'pending', 'failed']
        
        for user in users:
            if user.role == 'admin':
                continue
                
            # Create financial account
            account, _ = FinancialAccount.objects.get_or_create(
                user=user,
                defaults={
                    'total_contributions': Decimal('0.00'),
                    'interest_earned': Decimal('0.00'),
                    'interest_rate': Decimal('5.00')
                }
            )
            
            # Create deposits for the last 12 months
            total_contributions = Decimal('0.00')
            for month in range(12, 0, -1):
                deposit_date = timezone.now() - timedelta(days=30 * month)
                amount = Decimal(random.choice([3000, 4000, 5000, 5500, 6000]))
                status = random.choice(['completed'] * 8 + ['pending', 'failed'])  # 80% completed
                
                deposit = Deposit.objects.create(
                    user=user,
                    amount=amount,
                    payment_method=random.choice(payment_methods),
                    status=status,
                    transaction_reference=f'TXN{random.randint(100000, 999999)}',
                    mpesa_phone=user.phone_number if random.choice([True, False]) else None,
                    notes=random.choice(['Monthly contribution', 'Regular deposit', '']),
                    created_at=deposit_date
                )
                
                if status == 'completed':
                    total_contributions += amount
            
            # Update account
            account.total_contributions = total_contributions
            account.interest_earned = total_contributions * Decimal('0.05')  # 5% interest
            account.save()
            
            # Create interest calculations
            for quarter in range(4):
                calc_date = timezone.now() - timedelta(days=90 * quarter)
                InterestCalculation.objects.create(
                    user=user,
                    principal_amount=total_contributions / 4,
                    interest_rate=Decimal('5.00'),
                    interest_amount=(total_contributions / 4) * Decimal('0.0125'),  # Quarterly
                    calculation_date=calc_date.date(),
                    period_start=(calc_date - timedelta(days=90)).date(),
                    period_end=calc_date.date()
                )

    def create_beneficiaries(self, users):
        """Create beneficiaries for users"""
        relations = ['spouse', 'child', 'parent', 'sibling']
        statuses = ['active', 'deceased']
        verification_statuses = ['verified', 'pending', 'rejected']
        
        child_names = [
            'Emily', 'Michael', 'Sophia', 'Daniel', 'Olivia', 'James',
            'Emma', 'William', 'Ava', 'Alexander', 'Isabella', 'Benjamin'
        ]
        
        for user in users:
            if user.role == 'admin':
                continue
            
            # Add spouse if married
            if user.marital_status == 'married' and user.spouse_name:
                Beneficiary.objects.create(
                    user=user,
                    name=user.spouse_name,
                    relation='spouse',
                    age=user.spouse_age or 35,
                    gender='F' if user.gender == 'M' else 'M',
                    phone_number=f'+2547{random.randint(10000000, 99999999)}',
                    profession=user.spouse_profession or 'Professional',
                    salary_range='50,000 - 100,000',
                    status='active',
                    verification_status='verified'
                )
            
            # Add children
            for i in range(user.number_of_kids):
                child_age = random.randint(1, 18)
                Beneficiary.objects.create(
                    user=user,
                    name=f'{random.choice(child_names)} {user.full_name.split()[1]}',
                    relation='child',
                    age=child_age,
                    gender=random.choice(['M', 'F']),
                    phone_number=f'+2547{random.randint(10000000, 99999999)}' if child_age > 15 else None,
                    profession='Student' if child_age > 5 else 'Minor',
                    status='active',
                    verification_status=random.choice(['verified', 'pending'])
                )
            
            # Add parent or sibling
            if random.choice([True, False]):
                relation = random.choice(['parent', 'sibling'])
                Beneficiary.objects.create(
                    user=user,
                    name=f'{random.choice(["Robert", "Mary", "Thomas", "Patricia"])} {user.full_name.split()[1]}',
                    relation=relation,
                    age=random.randint(55, 75) if relation == 'parent' else random.randint(25, 45),
                    gender=random.choice(['M', 'F']),
                    phone_number=f'+2547{random.randint(10000000, 99999999)}',
                    profession=random.choice(['Retired', 'Teacher', 'Farmer', 'Business Owner']),
                    status=random.choice(['active', 'active', 'active', 'deceased']),
                    verification_status='verified'
                )

    def create_documents(self, users):
        """Create documents for users"""
        categories = ['identity', 'beneficiary', 'birth_certificate', 'death_certificate', 'additional']
        statuses = ['verified', 'pending', 'rejected']
        
        document_titles = {
            'identity': ['National ID', 'Passport', 'Driver License'],
            'beneficiary': ['Beneficiary ID Card', 'Beneficiary Passport'],
            'birth_certificate': ['Birth Certificate - Child 1', 'Birth Certificate - Child 2'],
            'death_certificate': ['Death Certificate - Parent'],
            'additional': ['Marriage Certificate', 'Property Documents', 'Bank Statement']
        }
        
        for user in users:
            if user.role == 'admin':
                continue
            
            # Create 2-4 documents per category
            for category in categories:
                num_docs = random.randint(1, 3)
                for i in range(num_docs):
                    if category in document_titles:
                        title = random.choice(document_titles[category])
                    else:
                        title = f'{category.replace("_", " ").title()} Document {i+1}'
                    
                    Document.objects.create(
                        user=user,
                        category=category,
                        title=title,
                        file=f'documents/sample_{category}_{i+1}.pdf',  # Placeholder
                        status=random.choice(['verified', 'verified', 'pending']),  # 66% verified
                        uploaded_at=timezone.now() - timedelta(days=random.randint(1, 180))
                    )

    def create_applications(self, users):
        """Create applications"""
        application_types = ['entry', 'exit']
        statuses = ['pending', 'under_review', 'approved', 'rejected']
        
        reasons = {
            'entry': [
                'I would like to join the Advance Company scheme to secure my family\'s future and benefit from the group savings plan.',
                'Interested in participating in the company\'s financial program for better retirement planning.',
                'Looking to be part of the mutual benefit society for long-term financial security.'
            ],
            'exit': [
                'I am relocating to another country for employment opportunities and need to exit the scheme.',
                'Due to financial constraints, I need to withdraw from the program at this time.',
                'I have achieved my savings goals and would like to exit the scheme.'
            ]
        }
        
        for user in users[1:4]:  # Create applications for first 3 test users
            app_type = random.choice(application_types)
            status = random.choice(statuses)
            
            application = Application.objects.create(
                user=user,
                application_type=app_type,
                reason=random.choice(reasons[app_type]),
                status=status,
                submitted_at=timezone.now() - timedelta(days=random.randint(1, 30))
            )
            
            if status in ['approved', 'rejected']:
                application.reviewed_by = users[0]  # Admin
                application.reviewed_at = timezone.now() - timedelta(days=random.randint(1, 5))
                application.admin_comments = f'Application has been {status}. All requirements met.' if status == 'approved' else 'Additional documentation required.'
                if status == 'approved':
                    application.approved_at = application.reviewed_at
                application.save()
            
            # Create activity log
            ApplicationActivity.objects.create(
                application=application,
                user=user,
                action='submitted',
                notes='Application submitted for review'
            )
            
            if status != 'pending':
                ApplicationActivity.objects.create(
                    application=application,
                    user=users[0],
                    action='under_review',
                    notes='Application under review by admin',
                    created_at=timezone.now() - timedelta(days=random.randint(1, 10))
                )
            
            if status in ['approved', 'rejected']:
                ApplicationActivity.objects.create(
                    application=application,
                    user=users[0],
                    action=status,
                    notes=application.admin_comments,
                    created_at=application.reviewed_at
                )

    def create_reports(self, users):
        """Create reports"""
        report_types = ['financial', 'compensatory', 'activity']
        statuses = ['ready', 'generating', 'failed']
        
        for user in users:
            if user.role == 'admin':
                # Admin gets all types of reports
                for report_type in report_types:
                    for month in range(3):  # Last 3 months
                        report_date = timezone.now() - timedelta(days=30 * month)
                        Report.objects.create(
                            user=user,
                            report_type=report_type,
                            title=f'{report_type.title()} Report - {report_date.strftime("%B %Y")}',
                            file=f'reports/{report_type}_{user.id}_{report_date.strftime("%Y%m")}.pdf',
                            status=random.choice(['ready', 'ready', 'generating']),
                            date_from=(report_date - timedelta(days=30)).date(),
                            date_to=report_date.date(),
                            generated_by=user,
                            created_at=report_date
                        )
            else:
                # Regular users get monthly financial reports
                for month in range(6):  # Last 6 months
                    report_date = timezone.now() - timedelta(days=30 * month)
                    Report.objects.create(
                        user=user,
                        report_type='financial',
                        title=f'Monthly Financial Report - {report_date.strftime("%B %Y")}',
                        file=f'reports/financial_{user.id}_{report_date.strftime("%Y%m")}.pdf',
                        status='ready',
                        date_from=(report_date - timedelta(days=30)).date(),
                        date_to=report_date.date(),
                        generated_by=user,
                        created_at=report_date
                    )

    def create_activity_logs(self, users):
        """Create activity logs"""
        actions = [
            'user_login',
            'user_logout',
            'deposit_created',
            'document_uploaded',
            'beneficiary_added',
            'profile_updated',
            'report_generated',
            'application_submitted'
        ]
        
        descriptions = {
            'user_login': 'User logged into the system',
            'user_logout': 'User logged out from the system',
            'deposit_created': 'New deposit transaction initiated',
            'document_uploaded': 'Document uploaded to the system',
            'beneficiary_added': 'New beneficiary added to account',
            'profile_updated': 'User profile information updated',
            'report_generated': 'Financial report generated',
            'application_submitted': 'Entry/Exit application submitted'
        }
        
        for user in users:
            # Create 20-30 activity logs per user
            for _ in range(random.randint(20, 30)):
                action = random.choice(actions)
                ActivityLog.objects.create(
                    user=user,
                    action=action,
                    description=descriptions[action],
                    ip_address=f'192.168.1.{random.randint(1, 255)}',
                    user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)',
                    created_at=timezone.now() - timedelta(days=random.randint(1, 90))
                )

