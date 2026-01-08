"""
Create this file: apps/notifications/management/commands/test_email.py
Run with: python manage.py test_email your-email@example.com
"""
from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.conf import settings


class Command(BaseCommand):
    help = 'Test email configuration'

    def add_arguments(self, parser):
        parser.add_argument('email', type=str, help='Email address to send test to')

    def handle(self, *args, **options):
        email = options['email']
        
        try:
            self.stdout.write('Attempting to send test email...')
            self.stdout.write(f'EMAIL_HOST: {settings.EMAIL_HOST}')
            self.stdout.write(f'EMAIL_HOST_USER: {settings.EMAIL_HOST_USER}')
            
            send_mail(
                subject='Test Email from Advance Company',
                message='This is a test email. If you receive this, your email configuration is working!',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                fail_silently=False,
            )
            
            self.stdout.write(self.style.SUCCESS(f'✓ Email sent successfully to {email}'))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ Error sending email: {str(e)}'))
            self.stdout.write(self.style.WARNING('Check your email settings in settings.py'))