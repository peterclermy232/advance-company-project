from django.contrib import admin
from .models import User

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ['email', 'full_name', 'role', 'is_active', 'created_at']
    list_filter = ['role', 'is_active', 'marital_status']
    search_fields = ['email', 'full_name', 'phone_number']
    readonly_fields = ['created_at', 'updated_at']
