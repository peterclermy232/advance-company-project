from django.core.management.base import BaseCommand
from apps.accounts.models import User
import secrets
import string

class Command(BaseCommand):
    help = 'Create a superuser admin account with secure password'

    def handle(self, *args, **options):
        email = 'admin@advancecompany.com'
        
        if User.objects.filter(email=email).exists():
            self.stdout.write(self.style.WARNING('Admin user already exists'))
            return
        
        # Generate secure random password
        alphabet = string.ascii_letters + string.digits + string.punctuation
        password = ''.join(secrets.choice(alphabet) for i in range(16))
        
        User.objects.create_superuser(
            email=email,
            phone_number='+254700000000',
            full_name='System Administrator',
            password=password
        )
        
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write(self.style.SUCCESS('Admin user created successfully'))
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write(self.style.SUCCESS(f'Email: {email}'))
        self.stdout.write(self.style.SUCCESS(f'Password: {password}'))
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write(self.style.WARNING('IMPORTANT: Save this password securely!'))
        self.stdout.write(self.style.WARNING('This password will not be shown again.'))