from django.contrib import admin
from .models import Application, ApplicationActivity

@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ['user', 'application_type', 'status', 'submitted_at']
    list_filter = ['application_type', 'status', 'submitted_at']
    search_fields = ['user__full_name', 'reason']

@admin.register(ApplicationActivity)
class ApplicationActivityAdmin(admin.ModelAdmin):
    list_display = ['application', 'user', 'action', 'created_at']
    list_filter = ['action', 'created_at']