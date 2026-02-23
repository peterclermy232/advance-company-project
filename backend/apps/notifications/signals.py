from django.db.models.signals import post_save, pre_save, post_delete
from django.dispatch import receiver

from apps.financial.models import Deposit
from apps.applications.models import Application
from apps.documents.models import Document
from apps.beneficiary.models import Beneficiary
from .models import Notification
from .utils import send_multi_channel_notification
import logging

logger = logging.getLogger(__name__)


# ============================================================
# DEPOSIT NOTIFICATIONS
# ============================================================

@receiver(post_save, sender=Deposit)
def notify_deposit_created(sender, instance, created, **kwargs):
    """Notify user + admins when a new deposit is created."""
    if not created:
        return

    try:
        send_multi_channel_notification(
            user=instance.user,
            notification_type='deposit_created',
            title='Deposit Created',
            message=(
                f'Your deposit of KES {instance.amount:,.2f} has been submitted '
                f'and is pending approval.'
            ),
            related_deposit_id=instance.uuid,
            deposit=instance,
        )

        from apps.accounts.models import User
        for admin in User.objects.filter(role='admin', is_active=True):
            try:
                Notification.objects.create(
                    user=admin,
                    notification_type='deposit_created',
                    title='New Deposit Pending',
                    message=(
                        f'{instance.user.full_name} submitted a deposit of '
                        f'KES {instance.amount:,.2f} for approval.'
                    ),
                    related_deposit_id=instance.uuid,
                    related_user_name=instance.user.full_name,
                )
            except Exception as e:
                logger.error(f'Error notifying admin {admin.uuid}: {e}')

        logger.info(f'Notifications sent for new deposit {instance.uuid}')

    except Exception as e:
        logger.error(f'Error in notify_deposit_created: {e}', exc_info=True)


@receiver(pre_save, sender=Deposit)
def notify_deposit_status_change(sender, instance, **kwargs):
    """Notify user when deposit is approved or rejected."""
    if not instance.pk:
        return

    try:
        old = Deposit.objects.get(pk=instance.pk)
    except Deposit.DoesNotExist:
        return
    except Exception as e:
        logger.error(f'Error fetching old deposit: {e}')
        return

    try:
        if old.status != 'completed' and instance.status == 'completed':
            send_multi_channel_notification(
                user=instance.user,
                notification_type='deposit_approved',
                title='Deposit Approved',
                message=(
                    f'Your deposit of KES {instance.amount:,.2f} has been approved '
                    f'and credited to your account.'
                ),
                related_deposit_id=instance.uuid,
                deposit=instance,
            )
            logger.info(f'Approval notification sent for deposit {instance.uuid}')

        elif old.status != 'failed' and instance.status == 'failed':
            reason = instance.rejection_reason or 'No reason provided'
            send_multi_channel_notification(
                user=instance.user,
                notification_type='deposit_rejected',
                title='Deposit Rejected',
                message=(
                    f'Your deposit of KES {instance.amount:,.2f} was rejected. '
                    f'Reason: {reason}'
                ),
                related_deposit_id=instance.uuid,
            )
            logger.info(f'Rejection notification sent for deposit {instance.uuid}')

    except Exception as e:
        logger.error(f'Error in notify_deposit_status_change: {e}', exc_info=True)


# ============================================================
# APPLICATION NOTIFICATIONS
# ============================================================

@receiver(post_save, sender=Application)
def notify_application_submitted(sender, instance, created, **kwargs):
    """Notify user + admins when a new application is submitted."""
    if not created:
        return

    try:
        send_multi_channel_notification(
            user=instance.user,
            notification_type='application_submitted',
            title='Application Submitted',
            message=(
                f'Your {instance.get_application_type_display()} application '
                f'has been submitted for review.'
            ),
            related_application_id=instance.uuid,
            application=instance,
        )

        from apps.accounts.models import User
        for admin in User.objects.filter(role='admin', is_active=True):
            try:
                Notification.objects.create(
                    user=admin,
                    notification_type='application_submitted',
                    title='New Application',
                    message=(
                        f'{instance.user.full_name} submitted a '
                        f'{instance.get_application_type_display()} application.'
                    ),
                    related_application_id=instance.uuid,
                    related_user_name=instance.user.full_name,
                )
            except Exception as e:
                logger.error(f'Error notifying admin {admin.uuid}: {e}')

        logger.info(f'Notifications sent for new application {instance.uuid}')

    except Exception as e:
        logger.error(f'Error in notify_application_submitted: {e}', exc_info=True)


@receiver(pre_save, sender=Application)
def notify_application_status_change(sender, instance, **kwargs):
    """Notify user when application status changes to approved or rejected."""
    if not instance.pk:
        return

    try:
        old = Application.objects.get(pk=instance.pk)
    except Application.DoesNotExist:
        return
    except Exception as e:
        logger.error(f'Error fetching old application: {e}')
        return

    try:
        if old.status != 'approved' and instance.status == 'approved':
            send_multi_channel_notification(
                user=instance.user,
                notification_type='application_approved',
                title='Application Approved',
                message=(
                    f'Your {instance.get_application_type_display()} '
                    f'application has been approved.'
                ),
                related_application_id=instance.uuid,
                application=instance,
            )
            logger.info(f'Approval notification sent for application {instance.uuid}')

        elif old.status != 'rejected' and instance.status == 'rejected':
            comments = instance.admin_comments or 'No comments provided'
            send_multi_channel_notification(
                user=instance.user,
                notification_type='application_rejected',
                title='Application Rejected',
                message=(
                    f'Your {instance.get_application_type_display()} '
                    f'application was rejected. {comments}'
                ),
                related_application_id=instance.uuid,
            )
            logger.info(f'Rejection notification sent for application {instance.uuid}')

    except Exception as e:
        logger.error(f'Error in notify_application_status_change: {e}', exc_info=True)


# ============================================================
# DOCUMENT NOTIFICATIONS
# ============================================================

@receiver(post_save, sender=Document)
def notify_document_uploaded(sender, instance, created, **kwargs):
    """Notify user + admins when a document is uploaded."""
    if not created:
        return

    try:
        send_multi_channel_notification(
            user=instance.user,
            notification_type='document_uploaded',
            title='Document Uploaded',
            message=(
                f'Your {instance.get_category_display()} — {instance.title} '
                f'has been uploaded and is pending verification.'
            ),
        )

        from apps.accounts.models import User
        for admin in User.objects.filter(role='admin', is_active=True):
            try:
                Notification.objects.create(
                    user=admin,
                    notification_type='document_uploaded',
                    title='New Document for Review',
                    message=(
                        f'{instance.user.full_name} uploaded a '
                        f'{instance.get_category_display()} document: {instance.title}'
                    ),
                    related_user_name=instance.user.full_name,
                )
            except Exception as e:
                logger.error(f'Error notifying admin {admin.uuid}: {e}')

        logger.info(f'Notifications sent for new document {instance.uuid}')

    except Exception as e:
        logger.error(f'Error in notify_document_uploaded: {e}', exc_info=True)


@receiver(pre_save, sender=Document)
def notify_document_status_change(sender, instance, **kwargs):
    """Notify user when document is verified or rejected."""
    if not instance.pk:
        return

    try:
        old = Document.objects.get(pk=instance.pk)
    except Document.DoesNotExist:
        return
    except Exception as e:
        logger.error(f'Error fetching old document: {e}')
        return

    try:
        if old.status != 'verified' and instance.status == 'verified':
            send_multi_channel_notification(
                user=instance.user,
                notification_type='document_verified',
                title='Document Verified',
                message=(
                    f'Your {instance.get_category_display()} — '
                    f'{instance.title} has been verified.'
                ),
            )
            logger.info(f'Verification notification sent for document {instance.uuid}')

        elif old.status != 'rejected' and instance.status == 'rejected':
            reason = instance.rejection_reason or 'Please re-upload'
            send_multi_channel_notification(
                user=instance.user,
                notification_type='document_rejected',
                title='Document Rejected',
                message=(
                    f'Your {instance.get_category_display()} — '
                    f'{instance.title} was rejected. Reason: {reason}'
                ),
            )
            logger.info(f'Rejection notification sent for document {instance.uuid}')

    except Exception as e:
        logger.error(f'Error in notify_document_status_change: {e}', exc_info=True)


@receiver(post_delete, sender=Document)
def notify_document_deleted(sender, instance, **kwargs):
    """Notify user when their document is deleted."""
    try:
        if instance.user and instance.user.is_active:
            send_multi_channel_notification(
                user=instance.user,
                notification_type='document_deleted',
                title='Document Deleted',
                message=(
                    f'Your {instance.get_category_display()} — '
                    f'{instance.title} has been deleted from the system.'
                ),
            )
            logger.info(f'Delete notification sent for document {instance.uuid}')
    except Exception as e:
        logger.error(f'Error in notify_document_deleted: {e}', exc_info=True)


# ============================================================
# BENEFICIARY NOTIFICATIONS
# ============================================================

@receiver(post_save, sender=Beneficiary)
def notify_beneficiary_added(sender, instance, created, **kwargs):
    """Notify user + admins when a beneficiary is added."""
    if not created:
        return

    try:
        send_multi_channel_notification(
            user=instance.user,
            notification_type='beneficiary_added',
            title='Beneficiary Added',
            message=(
                f'Beneficiary {instance.name} has been added '
                f'and is pending verification.'
            ),
        )

        from apps.accounts.models import User
        for admin in User.objects.filter(role='admin', is_active=True):
            try:
                Notification.objects.create(
                    user=admin,
                    notification_type='beneficiary_added',
                    title='New Beneficiary for Review',
                    message=(
                        f'{instance.user.full_name} added beneficiary: '
                        f'{instance.name} ({instance.get_relation_display()})'
                    ),
                    related_user_name=instance.user.full_name,
                )
            except Exception as e:
                logger.error(f'Error notifying admin {admin.uuid}: {e}')

        logger.info(f'Notifications sent for new beneficiary {instance.uuid}')

    except Exception as e:
        logger.error(f'Error in notify_beneficiary_added: {e}', exc_info=True)


@receiver(pre_save, sender=Beneficiary)
def notify_beneficiary_status_change(sender, instance, **kwargs):
    """Notify user when beneficiary verification status or life status changes."""
    if not instance.pk:
        return

    try:
        old = Beneficiary.objects.get(pk=instance.pk)
    except Beneficiary.DoesNotExist:
        return
    except Exception as e:
        logger.error(f'Error fetching old beneficiary: {e}')
        return

    try:
        if old.verification_status != 'verified' and instance.verification_status == 'verified':
            send_multi_channel_notification(
                user=instance.user,
                notification_type='beneficiary_verified',
                title='Beneficiary Verified',
                message=f'Beneficiary {instance.name} has been verified and is now active.',
            )
            logger.info(f'Verification notification sent for beneficiary {instance.uuid}')

        elif old.verification_status != 'rejected' and instance.verification_status == 'rejected':
            send_multi_channel_notification(
                user=instance.user,
                notification_type='beneficiary_rejected',
                title='Beneficiary Rejected',
                message=(
                    f'Beneficiary {instance.name} could not be verified. '
                    f'Please review the details and resubmit.'
                ),
            )
            logger.info(f'Rejection notification sent for beneficiary {instance.uuid}')

        if old.status != 'deceased' and instance.status == 'deceased':
            send_multi_channel_notification(
                user=instance.user,
                notification_type='beneficiary_deceased',
                title='Beneficiary Status Updated',
                message=f'Beneficiary {instance.name} has been marked as deceased.',
            )
            logger.info(f'Deceased notification sent for beneficiary {instance.uuid}')

    except Exception as e:
        logger.error(f'Error in notify_beneficiary_status_change: {e}', exc_info=True)


@receiver(post_delete, sender=Beneficiary)
def notify_beneficiary_deleted(sender, instance, **kwargs):
    """Notify user when their beneficiary is deleted."""
    try:
        if instance.user and instance.user.is_active:
            send_multi_channel_notification(
                user=instance.user,
                notification_type='beneficiary_deleted',
                title='Beneficiary Removed',
                message=(
                    f'Beneficiary {instance.name} ({instance.get_relation_display()}) '
                    f'has been removed from your account.'
                ),
            )
            logger.info(f'Delete notification sent for beneficiary {instance.uuid}')
    except Exception as e:
        logger.error(f'Error in notify_beneficiary_deleted: {e}', exc_info=True)