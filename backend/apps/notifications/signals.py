"""
backend/apps/notifications/signals.py
Fixed version with email/SMS integration
"""
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from apps.financial.models import Deposit
from apps.applications.models import Application
from apps.documents.models import Document
from apps.beneficiary.models import Beneficiary
from .models import Notification
from .utils import (
    send_multi_channel_notification,
    send_deposit_created_email,
    send_deposit_approved_email,
    send_deposit_created_sms,
    send_deposit_approved_sms
)
import logging

logger = logging.getLogger(__name__)


# ============================================================
# DEPOSIT NOTIFICATIONS
# ============================================================

@receiver(post_save, sender=Deposit)
def notify_deposit_created(sender, instance, created, **kwargs):
    """
    Notify user when they create a deposit
    Notify admin when a deposit needs approval
    Sends in-app, email, and SMS notifications
    """
    if created:
        try:
            # Use multi-channel notification for the user
            send_multi_channel_notification(
                user=instance.user,
                notification_type='deposit_created',
                title='Deposit Created',
                message=f'Your deposit of KES {instance.amount:,.2f} has been submitted and is pending approval.',
                related_deposit_id=instance.id,
                deposit=instance  # Pass deposit for email/SMS templates
            )
            
            # Notify all admins about new deposit
            from apps.accounts.models import User
            admins = User.objects.filter(role='admin', is_active=True)
            
            for admin in admins:
                try:
                    # Create in-app notification for admins
                    Notification.objects.create(
                        user=admin,
                        notification_type='deposit_created',
                        title='New Deposit Pending',
                        message=f'{instance.user.full_name} submitted a deposit of KES {instance.amount:,.2f} for approval.',
                        related_deposit_id=instance.id,
                        related_user_name=instance.user.full_name
                    )
                except Exception as e:
                    logger.error(f"Error notifying admin {admin.id}: {str(e)}")
            
            logger.info(f"Notifications sent for new deposit {instance.id}")
            
        except Exception as e:
            logger.error(f"Error sending deposit created notifications for deposit {instance.id}: {str(e)}", exc_info=True)


@receiver(pre_save, sender=Deposit)
def notify_deposit_status_change(sender, instance, **kwargs):
    """
    Notify user when deposit is approved or rejected
    Sends in-app, email, and SMS notifications
    """
    if instance.pk:  # Only for updates, not new deposits
        try:
            old_instance = Deposit.objects.get(pk=instance.pk)
            
            # Deposit approved
            if old_instance.status != 'completed' and instance.status == 'completed':
                try:
                    # Use multi-channel notification
                    send_multi_channel_notification(
                        user=instance.user,
                        notification_type='deposit_approved',
                        title='Deposit Approved',
                        message=f'Your deposit of KES {instance.amount:,.2f} has been approved and credited to your account.',
                        related_deposit_id=instance.id,
                        deposit=instance  # Pass deposit for email/SMS templates
                    )
                    logger.info(f"Approval notification sent for deposit {instance.id}")
                except Exception as e:
                    logger.error(f"Error sending approval notification for deposit {instance.id}: {str(e)}", exc_info=True)
            
            # Deposit rejected
            elif old_instance.status != 'failed' and instance.status == 'failed':
                try:
                    reason = instance.rejection_reason or 'No reason provided'
                    
                    # Use multi-channel notification
                    send_multi_channel_notification(
                        user=instance.user,
                        notification_type='deposit_rejected',
                        title='Deposit Rejected',
                        message=f'Your deposit of KES {instance.amount:,.2f} was rejected. Reason: {reason}',
                        related_deposit_id=instance.id
                    )
                    logger.info(f"Rejection notification sent for deposit {instance.id}")
                except Exception as e:
                    logger.error(f"Error sending rejection notification for deposit {instance.id}: {str(e)}", exc_info=True)
                    
        except Deposit.DoesNotExist:
            pass
        except Exception as e:
            logger.error(f"Error in deposit status change handler: {str(e)}", exc_info=True)


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
        try:
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
            admins = User.objects.filter(role='admin', is_active=True)
            
            for admin in admins:
                try:
                    Notification.objects.create(
                        user=admin,
                        notification_type='application_submitted',
                        title='New Application',
                        message=f'{instance.user.full_name} submitted a {instance.get_application_type_display()} application.',
                        related_application_id=instance.id,
                        related_user_name=instance.user.full_name
                    )
                except Exception as e:
                    logger.error(f"Error notifying admin {admin.id}: {str(e)}")
            
            logger.info(f"Notifications sent for new application {instance.id}")
            
        except Exception as e:
            logger.error(f"Error sending application submitted notifications: {str(e)}", exc_info=True)


@receiver(pre_save, sender=Application)
def notify_application_status_change(sender, instance, **kwargs):
    """
    Notify user when application is approved or rejected
    """
    if instance.pk:
        try:
            old_instance = Application.objects.get(pk=instance.pk)
            
            # Application approved
            if old_instance.status != 'approved' and instance.status == 'approved':
                try:
                    send_multi_channel_notification(
                        user=instance.user,
                        notification_type='application_approved',
                        title='Application Approved',
                        message=f'Your {instance.get_application_type_display()} application has been approved.',
                        related_application_id=instance.id,
                        application=instance
                    )
                    logger.info(f"Approval notification sent for application {instance.id}")
                except Exception as e:
                    logger.error(f"Error sending application approval notification: {str(e)}", exc_info=True)
            
            # Application rejected
            elif old_instance.status != 'rejected' and instance.status == 'rejected':
                try:
                    comments = instance.admin_comments or 'No comments provided'
                    send_multi_channel_notification(
                        user=instance.user,
                        notification_type='application_rejected',
                        title='Application Rejected',
                        message=f'Your {instance.get_application_type_display()} application was rejected. {comments}',
                        related_application_id=instance.id
                    )
                    logger.info(f"Rejection notification sent for application {instance.id}")
                except Exception as e:
                    logger.error(f"Error sending application rejection notification: {str(e)}", exc_info=True)
                    
        except Application.DoesNotExist:
            pass
        except Exception as e:
            logger.error(f"Error in application status change handler: {str(e)}", exc_info=True)


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
        try:
            # Notify the user
            send_multi_channel_notification(
                user=instance.user,
                notification_type='document_uploaded',
                title='Document Uploaded',
                message=f'Your {instance.get_category_display()} - {instance.title} has been uploaded and is pending verification.'
            )
            
            # Notify admins for verification
            from apps.accounts.models import User
            admins = User.objects.filter(role='admin', is_active=True)
            
            for admin in admins:
                try:
                    Notification.objects.create(
                        user=admin,
                        notification_type='document_uploaded',
                        title='New Document for Review',
                        message=f'{instance.user.full_name} uploaded a {instance.get_category_display()} document: {instance.title}',
                        related_user_name=instance.user.full_name
                    )
                except Exception as e:
                    logger.error(f"Error notifying admin {admin.id}: {str(e)}")
            
            logger.info(f"Notifications sent for new document {instance.id}")
            
        except Exception as e:
            logger.error(f"Error sending document upload notifications: {str(e)}", exc_info=True)


@receiver(pre_save, sender=Document)
def notify_document_status_change(sender, instance, **kwargs):
    """
    Notify user when document is verified or rejected
    """
    if instance.pk:
        try:
            old_instance = Document.objects.get(pk=instance.pk)
            
            # Document verified
            if old_instance.status != 'verified' and instance.status == 'verified':
                try:
                    send_multi_channel_notification(
                        user=instance.user,
                        notification_type='document_verified',
                        title='Document Verified',
                        message=f'Your {instance.get_category_display()} - {instance.title} has been verified.'
                    )
                    logger.info(f"Verification notification sent for document {instance.id}")
                except Exception as e:
                    logger.error(f"Error sending document verification notification: {str(e)}", exc_info=True)
            
            # Document rejected
            elif old_instance.status != 'rejected' and instance.status == 'rejected':
                try:
                    reason = instance.rejection_reason or 'Please reupload'
                    send_multi_channel_notification(
                        user=instance.user,
                        notification_type='document_rejected',
                        title='Document Rejected',
                        message=f'Your {instance.get_category_display()} - {instance.title} was rejected. Reason: {reason}'
                    )
                    logger.info(f"Rejection notification sent for document {instance.id}")
                except Exception as e:
                    logger.error(f"Error sending document rejection notification: {str(e)}", exc_info=True)
                    
        except Document.DoesNotExist:
            pass
        except Exception as e:
            logger.error(f"Error in document status change handler: {str(e)}", exc_info=True)


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
        try:
            # Notify the user
            send_multi_channel_notification(
                user=instance.user,
                notification_type='beneficiary_added',
                title='Beneficiary Added',
                message=f'Beneficiary {instance.name} has been added and is pending verification.'
            )
            
            # Notify admins
            from apps.accounts.models import User
            admins = User.objects.filter(role='admin', is_active=True)
            
            for admin in admins:
                try:
                    Notification.objects.create(
                        user=admin,
                        notification_type='beneficiary_added',
                        title='New Beneficiary for Review',
                        message=f'{instance.user.full_name} added beneficiary: {instance.name} ({instance.get_relation_display()})',
                        related_user_name=instance.user.full_name
                    )
                except Exception as e:
                    logger.error(f"Error notifying admin {admin.id}: {str(e)}")
            
            logger.info(f"Notifications sent for new beneficiary {instance.id}")
            
        except Exception as e:
            logger.error(f"Error sending beneficiary added notifications: {str(e)}", exc_info=True)


@receiver(pre_save, sender=Beneficiary)
def notify_beneficiary_status_change(sender, instance, **kwargs):
    """
    Notify user when beneficiary is verified or status changes
    """
    if instance.pk:
        try:
            old_instance = Beneficiary.objects.get(pk=instance.pk)
            
            # Beneficiary verified
            if old_instance.verification_status != 'verified' and instance.verification_status == 'verified':
                try:
                    send_multi_channel_notification(
                        user=instance.user,
                        notification_type='beneficiary_verified',
                        title='Beneficiary Verified',
                        message=f'Beneficiary {instance.name} has been verified and is now active.'
                    )
                    logger.info(f"Verification notification sent for beneficiary {instance.id}")
                except Exception as e:
                    logger.error(f"Error sending beneficiary verification notification: {str(e)}", exc_info=True)
            
            # Beneficiary marked as deceased
            if old_instance.status != 'deceased' and instance.status == 'deceased':
                try:
                    send_multi_channel_notification(
                        user=instance.user,
                        notification_type='beneficiary_deceased',
                        title='Beneficiary Status Updated',
                        message=f'Beneficiary {instance.name} has been marked as deceased.'
                    )
                    logger.info(f"Deceased notification sent for beneficiary {instance.id}")
                except Exception as e:
                    logger.error(f"Error sending beneficiary deceased notification: {str(e)}", exc_info=True)
                    
        except Beneficiary.DoesNotExist:
            pass
        except Exception as e:
            logger.error(f"Error in beneficiary status change handler: {str(e)}", exc_info=True)