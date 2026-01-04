from django.contrib import admin
from .models import Report, ActivityLog

@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ['title', 'user', 'report_type', 'status', 'created_at']
    list_filter = ['report_type', 'status', 'created_at']
    search_fields = ['title', 'user__full_name']

@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ['user', 'action', 'created_at']
    list_filter = ['action', 'created_at']
    search_fields = ['user__full_name', 'action', 'description']
