from django.contrib import admin
from django.utils.html import format_html
from .models import Beneficiary

@admin.register(Beneficiary)
class BeneficiaryAdmin(admin.ModelAdmin):
    list_display = [
        'name', 
        'user', 
        'relation', 
        'age',
        'status', 
        'verification_status_badge',
        'created_at'
    ]
    list_filter = [
        'status', 
        'verification_status', 
        'relation', 
        'gender',
        'created_at'
    ]
    search_fields = [
        'name', 
        'user__full_name', 
        'user__email',
        'phone_number'
    ]
    readonly_fields = [
        'created_at', 
        'updated_at',
        'user_name',
        'document_previews'
    ]
    
    fieldsets = (
        ('Beneficiary Information', {
            'fields': (
                'user',
                'user_name',
                'name',
                'relation',
                'age',
                'gender',
                'phone_number',
                'profession',
                'salary_range',
            )
        }),
        ('Documents', {
            'fields': (
                'identity_document',
                'birth_certificate',
                'death_certificate',
                'death_certificate_number',
                'additional_documents',
                'document_previews',
            )
        }),
        ('Status & Verification', {
            'fields': (
                'status',
                'verification_status',
            ),
            'classes': ('wide',)
        }),
        ('Timestamps', {
            'fields': (
                'created_at',
                'updated_at',
            ),
            'classes': ('collapse',)
        }),
    )
    
    actions = [
        'approve_beneficiaries',
        'reject_beneficiaries',
        'mark_as_pending',
        'mark_as_active',
        'mark_as_deceased'
    ]
    
    def user_name(self, obj):
        """Display user's full name"""
        return obj.user.full_name
    user_name.short_description = 'User Full Name'
    
    def verification_status_badge(self, obj):
        """Display verification status with colored badge"""
        colors = {
            'verified': 'green',
            'pending': 'orange',
            'rejected': 'red'
        }
        color = colors.get(obj.verification_status, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px; font-weight: bold;">{}</span>',
            color,
            obj.get_verification_status_display()
        )
    verification_status_badge.short_description = 'Verification Status'
    
    def document_previews(self, obj):
        """Display links to view documents"""
        html = '<div style="line-height: 2;">'
        
        if obj.identity_document:
            html += format_html(
                '<p><strong>Identity Document:</strong> <a href="{}" target="_blank">View Document</a></p>',
                obj.identity_document.url
            )
        
        if obj.birth_certificate:
            html += format_html(
                '<p><strong>Birth Certificate:</strong> <a href="{}" target="_blank">View Document</a></p>',
                obj.birth_certificate.url
            )
        
        if obj.death_certificate:
            html += format_html(
                '<p><strong>Death Certificate:</strong> <a href="{}" target="_blank">View Document</a> ({})</p>',
                obj.death_certificate.url,
                obj.death_certificate_number or 'No number'
            )
        
        if obj.additional_documents:
            html += format_html(
                '<p><strong>Additional Documents:</strong> <a href="{}" target="_blank">View Document</a></p>',
                obj.additional_documents.url
            )
        
        html += '</div>'
        return format_html(html)
    document_previews.short_description = 'Document Links'
    
    # Admin Actions
    def approve_beneficiaries(self, request, queryset):
        """Approve selected beneficiaries"""
        updated = queryset.update(verification_status='verified')
        self.message_user(
            request,
            f'{updated} beneficiary(ies) successfully approved.'
        )
    approve_beneficiaries.short_description = '✓ Approve selected beneficiaries'
    
    def reject_beneficiaries(self, request, queryset):
        """Reject selected beneficiaries"""
        updated = queryset.update(verification_status='rejected')
        self.message_user(
            request,
            f'{updated} beneficiary(ies) rejected.'
        )
    reject_beneficiaries.short_description = '✗ Reject selected beneficiaries'
    
    def mark_as_pending(self, request, queryset):
        """Mark selected beneficiaries as pending"""
        updated = queryset.update(verification_status='pending')
        self.message_user(
            request,
            f'{updated} beneficiary(ies) marked as pending.'
        )
    mark_as_pending.short_description = '⏳ Mark as pending review'
    
    def mark_as_active(self, request, queryset):
        """Mark selected beneficiaries as active"""
        updated = queryset.update(status='active')
        self.message_user(
            request,
            f'{updated} beneficiary(ies) marked as active.'
        )
    mark_as_active.short_description = '🟢 Mark as active'
    
    def mark_as_deceased(self, request, queryset):
        """Mark selected beneficiaries as deceased"""
        updated = queryset.update(status='deceased')
        self.message_user(
            request,
            f'{updated} beneficiary(ies) marked as deceased.'
        )
    mark_as_deceased.short_description = '⚫ Mark as deceased'
    
    def get_queryset(self, request):
        """Optimize queryset with select_related"""
        queryset = super().get_queryset(request)
        return queryset.select_related('user')