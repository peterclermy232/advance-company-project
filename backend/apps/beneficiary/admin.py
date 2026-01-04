from django.contrib import admin
from .models import Beneficiary

@admin.register(Beneficiary)
class BeneficiaryAdmin(admin.ModelAdmin):
    list_display = ['name', 'user', 'relation', 'status', 'verification_status']
    list_filter = ['status', 'verification_status', 'relation']
    search_fields = ['name', 'user__full_name']
