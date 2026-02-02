from django.apps import AppConfig

class ReportsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.reports'

    def ready(self):
        # Import signals here so Django loads them
        import apps.reports.signals
