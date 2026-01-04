import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'advance_company.settings')

app = Celery('advance_company')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

# Periodic tasks
app.conf.beat_schedule = {
    'generate-monthly-reports': {
        'task': 'apps.reports.tasks.generate_monthly_reports',
        'schedule': crontab(day_of_month='1', hour='0', minute='0'),
    },
}