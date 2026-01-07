from django.apps import AppConfig

class NotificationsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.notifications'   
"""
apps/notifications/apps.py
App configuration with signal registration
"""
from django.apps import AppConfig


class NotificationsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.notifications'
    
    def ready(self):
        """
        Import signals when the app is ready
        This ensures all signal handlers are registered
        """
        
        import apps.notifications.signals  # noqa