from .models import Notification
from apps.accounts.models import User
import logging

logger = logging.getLogger(__name__)


class NotificationService:
    """Service for creating in-app notifications only."""

    @staticmethod
    def create_notification(user, notification_type, title, message, **kwargs):
        """Create a single in-app notification for a user."""
        return Notification.objects.create(
            user=user,
            notification_type=notification_type,
            title=title,
            message=message,
            related_deposit_id=kwargs.get('related_deposit_id'),
            related_application_id=kwargs.get('related_application_id'),
            related_user_name=kwargs.get('related_user_name'),
        )

    # ------------------------------------------------------------------
    # Deposit helpers (called from admin bulk-approve / bulk-reject only)
    # ------------------------------------------------------------------

    @staticmethod
    def notify_deposit_approved(deposit, approved_by):
        """In-app notify user when their deposit is approved (admin action)."""
        NotificationService.create_notification(
            user=deposit.user,
            notification_type='deposit_approved',
            title='Deposit Approved',
            message=(
                f'Your deposit of KES {deposit.amount:,.2f} has been approved '
                f'and credited to your account.'
            ),
            related_deposit_id=deposit.uuid,
        )

    @staticmethod
    def notify_deposit_rejected(deposit, rejected_by, reason):
        """In-app notify user when their deposit is rejected (admin action)."""
        NotificationService.create_notification(
            user=deposit.user,
            notification_type='deposit_rejected',
            title='Deposit Rejected',
            message=(
                f'Your deposit of KES {deposit.amount:,.2f} was rejected. '
                f'Reason: {reason}'
            ),
            related_deposit_id=deposit.uuid,
        )


    @staticmethod
    def notify_application_submitted(application):
        """
        Notify admins about a new application.
        Called ONLY from places where the post_save signal will NOT fire
        (e.g. management commands, bulk imports).
        For normal API flow the signal in signals.py handles this.
        """
        admins = User.objects.filter(role='admin', is_active=True)
        for admin in admins:
            try:
                NotificationService.create_notification(
                    user=admin,
                    notification_type='application_submitted',
                    title='New Application Submitted',
                    message=(
                        f'{application.user.full_name} submitted a new '
                        f'{application.get_application_type_display()} application.'
                    ),
                    related_application_id=application.uuid,
                    related_user_name=application.user.full_name,
                )
            except Exception as e:
                logger.error(f'Error notifying admin {admin.uuid}: {e}')

    @staticmethod
    def notify_application_approved(application):
        """In-app notify user when their application is approved."""
        NotificationService.create_notification(
            user=application.user,
            notification_type='application_approved',
            title='Application Approved',
            message=(
                f'Your {application.get_application_type_display()} '
                f'application has been approved.'
            ),
            related_application_id=application.uuid,
        )

    @staticmethod
    def notify_application_rejected(application, reason):
        """In-app notify user when their application is rejected."""
        NotificationService.create_notification(
            user=application.user,
            notification_type='application_rejected',
            title='Application Rejected',
            message=(
                f'Your {application.get_application_type_display()} '
                f'application was rejected. {reason}'
            ),
            related_application_id=application.uuid,
        )

    # ------------------------------------------------------------------
    # Beneficiary helpers
    # ------------------------------------------------------------------

    @staticmethod
    def notify_beneficiary_verified(beneficiary):
        """In-app notify user when their beneficiary is verified."""
        NotificationService.create_notification(
            user=beneficiary.user,
            notification_type='beneficiary_verified',
            title='Beneficiary Verified',
            message=(
                f'Your beneficiary "{beneficiary.name}" has been '
                f'verified and approved.'
            ),
        )

    @staticmethod
    def notify_beneficiary_rejected(beneficiary, reason):
        """In-app notify user when their beneficiary is rejected."""
        NotificationService.create_notification(
            user=beneficiary.user,
            notification_type='beneficiary_rejected',
            title='Beneficiary Rejected',
            message=(
                f'Your beneficiary "{beneficiary.name}" was rejected. '
                f'Reason: {reason}'
            ),
        )

    @staticmethod
    def notify_beneficiary_deceased(beneficiary):
        """In-app notify user when beneficiary is marked deceased."""
        NotificationService.create_notification(
            user=beneficiary.user,
            notification_type='beneficiary_deceased',
            title='Beneficiary Status Updated',
            message=f'Beneficiary "{beneficiary.name}" has been marked as deceased.',
        )