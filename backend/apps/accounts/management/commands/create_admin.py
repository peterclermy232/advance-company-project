from django.core.management.base import BaseCommand
from apps.accounts.models import User

class Command(BaseCommand):
    help = 'Create a superuser admin account'

    def handle(self, *args, **options):
        if not User.objects.filter(email='admin@advancecompany.com').exists():
            User.objects.create_superuser(
                email='admin@advancecompany.com',
                phone_number='+254700000000',
                full_name='System Administrator',
                password='admin123'
            )
            self.stdout.write(self.style.SUCCESS('Admin user created successfully'))
        else:
            self.stdout.write(self.style.WARNING('Admin user already exists'))
