"""
apps/notifications/signals.py
Comprehensive signal handlers for all notification events
"""
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from apps.financial.models import Deposit
from apps.applications.models import Application
from apps.documents.models import Document
from apps.beneficiary.models import Beneficiary
from .models import Notification


# ============================================================
# DEPOSIT NOTIFICATIONS
# ============================================================

@receiver(post_save, sender=Deposit)
def notify_deposit_created(sender, instance, created, **kwargs):
    """
    Notify user when they create a deposit
    Notify admin when a deposit needs approval
    """
    if created:
        # Import here to avoid circular imports
        from .utils import send_multi_channel_notification
        
        # Notify the user who created the deposit
        send_multi_channel_notification(
            user=instance.user,
            notification_type='deposit_created',
            title='Deposit Created',
            message=f'Your deposit of KES {instance.amount:,.2f} has been submitted and is pending approval.',
            related_deposit_id=instance.id,
            deposit=instance  # Pass deposit object for email/SMS templates
        )
        
        # Notify all admins about new deposit
        from apps.accounts.models import User
        admins = User.objects.filter(role='admin')
        
        for admin in admins:
            # Create in-app notification only for admins (no email/SMS spam)
            Notification.objects.create(
                user=admin,
                notification_type='deposit_created',
                title='New Deposit Pending',
                message=f'{instance.user.full_name} submitted a deposit of KES {instance.amount:,.2f} for approval.',
                related_deposit_id=instance.id,
                related_user_name=instance.user.full_name
            )


@receiver(pre_save, sender=Deposit)
def notify_deposit_status_change(sender, instance, **kwargs):
    """
    Notify user when deposit is approved or rejected
    Runs before save to compare old and new status
    """
    if instance.pk:  # Only for updates, not new deposits
        try:
            old_instance = Deposit.objects.get(pk=instance.pk)
            
            # Import here to avoid circular imports
            from .utils import send_multi_channel_notification
            
            # Deposit approved
            if old_instance.status != 'completed' and instance.status == 'completed':
                send_multi_channel_notification(
                    user=instance.user,
                    notification_type='deposit_approved',
                    title='Deposit Approved',
                    message=f'Your deposit of KES {instance.amount:,.2f} has been approved and credited to your account.',
                    related_deposit_id=instance.id,
                    deposit=instance  # Pass deposit object for email/SMS templates
                )
            
            # Deposit rejected
            elif old_instance.status != 'failed' and instance.status == 'failed':
                send_multi_channel_notification(
                    user=instance.user,
                    notification_type='deposit_rejected',
                    title='Deposit Rejected',
                    message=f'Your deposit of KES {instance.amount:,.2f} was rejected. Please contact support for details.',
                    related_deposit_id=instance.id,
                    deposit=instance  # Pass deposit object for email/SMS templates
                )
        except Deposit.DoesNotExist:
            pass


# ============================================================
# APPLICATION NOTIFICATIONS
# ============================================================

@receiver(post_save, sender=Application)
def notify_application_submitted(sender, instance, created, **kwargs):
    """
    Notify user when they submit an application
    Notify admins about new application
    """
    if created:
        from .utils import send_multi_channel_notification
        
        # Notify the user
        send_multi_channel_notification(
            user=instance.user,
            notification_type='application_submitted',
            title='Application Submitted',
            message=f'Your {instance.get_application_type_display()} application has been submitted for review.',
            related_application_id=instance.id,
            application=instance
        )
        
        # Notify all admins
        from apps.accounts.models import User
        admins = User.objects.filter(role='admin')
        
        for admin in admins:
            Notification.objects.create(
                user=admin,
                notification_type='application_submitted',
                title='New Application',
                message=f'{instance.user.full_name} submitted a {instance.get_application_type_display()} application.',
                related_application_id=instance.id,
                related_user_name=instance.user.full_name
            )


@receiver(pre_save, sender=Application)
def notify_application_status_change(sender, instance, **kwargs):
    """
    Notify user when application is approved or rejected
    """
    if instance.pk:
        try:
            old_instance = Application.objects.get(pk=instance.pk)
            from .utils import send_multi_channel_notification
            
            # Application approved
            if old_instance.status != 'approved' and instance.status == 'approved':
                send_multi_channel_notification(
                    user=instance.user,
                    notification_type='application_approved',
                    title='Application Approved',
                    message=f'Your {instance.get_application_type_display()} application has been approved.',
                    related_application_id=instance.id,
                    application=instance
                )
            
            # Application rejected
            elif old_instance.status != 'rejected' and instance.status == 'rejected':
                send_multi_channel_notification(
                    user=instance.user,
                    notification_type='application_rejected',
                    title='Application Rejected',
                    message=f'Your {instance.get_application_type_display()} application was rejected. {instance.admin_comments or ""}',
                    related_application_id=instance.id,
                    application=instance
                )
        except Application.DoesNotExist:
            pass


# ============================================================
# DOCUMENT NOTIFICATIONS
# ============================================================

@receiver(post_save, sender=Document)
def notify_document_uploaded(sender, instance, created, **kwargs):
    """
    Notify user when they upload a document
    Notify admins about new document for verification
    """
    if created:
        from .utils import send_multi_channel_notification
        
        # Notify the user
        send_multi_channel_notification(
            user=instance.user,
            notification_type='document_uploaded',
            title='Document Uploaded',
            message=f'Your {instance.get_category_display()} - {instance.title} has been uploaded and is pending verification.',
        )
        
        # Notify admins for verification
        from apps.accounts.models import User
        admins = User.objects.filter(role='admin')
        
        for admin in admins:
            Notification.objects.create(
                user=admin,
                notification_type='document_uploaded',
                title='New Document for Review',
                message=f'{instance.user.full_name} uploaded a {instance.get_category_display()} document: {instance.title}',
                related_user_name=instance.user.full_name
            )


@receiver(pre_save, sender=Document)
def notify_document_status_change(sender, instance, **kwargs):
    """
    Notify user when document is verified or rejected
    """
    if instance.pk:
        try:
            old_instance = Document.objects.get(pk=instance.pk)
            from .utils import send_multi_channel_notification
            
            # Document verified
            if old_instance.status != 'verified' and instance.status == 'verified':
                send_multi_channel_notification(
                    user=instance.user,
                    notification_type='document_verified',
                    title='Document Verified',
                    message=f'Your {instance.get_category_display()} - {instance.title} has been verified.',
                )
            
            # Document rejected
            elif old_instance.status != 'rejected' and instance.status == 'rejected':
                reason = instance.rejection_reason or 'Please reupload'
                send_multi_channel_notification(
                    user=instance.user,
                    notification_type='document_rejected',
                    title='Document Rejected',
                    message=f'Your {instance.get_category_display()} - {instance.title} was rejected. Reason: {reason}',
                )
        except Document.DoesNotExist:
            pass


# ============================================================
# BENEFICIARY NOTIFICATIONS
# ============================================================

@receiver(post_save, sender=Beneficiary)
def notify_beneficiary_added(sender, instance, created, **kwargs):
    """
    Notify user when they add a beneficiary
    Notify admins about new beneficiary for verification
    """
    if created:
        from .utils import send_multi_channel_notification
        
        # Notify the user
        send_multi_channel_notification(
            user=instance.user,
            notification_type='beneficiary_added',
            title='Beneficiary Added',
            message=f'Beneficiary {instance.name} has been added and is pending verification.',
        )
        
        # Notify admins
        from apps.accounts.models import User
        admins = User.objects.filter(role='admin')
        
        for admin in admins:
            Notification.objects.create(
                user=admin,
                notification_type='beneficiary_added',
                title='New Beneficiary for Review',
                message=f'{instance.user.full_name} added beneficiary: {instance.name} ({instance.get_relation_display()})',
                related_user_name=instance.user.full_name
            )


@receiver(pre_save, sender=Beneficiary)
def notify_beneficiary_status_change(sender, instance, **kwargs):
    """
    Notify user when beneficiary is verified or status changes
    """
    if instance.pk:
        try:
            old_instance = Beneficiary.objects.get(pk=instance.pk)
            from .utils import send_multi_channel_notification
            
            # Beneficiary verified
            if old_instance.verification_status != 'verified' and instance.verification_status == 'verified':
                send_multi_channel_notification(
                    user=instance.user,
                    notification_type='beneficiary_verified',
                    title='Beneficiary Verified',
                    message=f'Beneficiary {instance.name} has been verified and is now active.',
                )
            
            # Beneficiary marked as deceased
            if old_instance.status != 'deceased' and instance.status == 'deceased':
                send_multi_channel_notification(
                    user=instance.user,
                    notification_type='beneficiary_deceased',
                    title='Beneficiary Status Updated',
                    message=f'Beneficiary {instance.name} has been marked as deceased.',
                )
        except Beneficiary.DoesNotExist:
            pass


# ============================================================
# SYSTEM NOTIFICATIONS (Manual)
# ============================================================

def send_system_notification(user, title, message):
    """
    Helper function to send system notifications manually
    Usage: send_system_notification(user, "Maintenance", "System will be down...")
    """
    Notification.objects.create(
        user=user,
        notification_type='system',
        title=title,
        message=message
    )


def send_bulk_notification(users, title, message):
    """
    Helper function to send notifications to multiple users
    Usage: send_bulk_notification(User.objects.filter(role='user'), "Update", "New feature...")
    """
    notifications = [
        Notification(
            user=user,
            notification_type='system',
            title=title,
            message=message
        )
        for user in users
    ]
    Notification.objects.bulk_create(notifications)