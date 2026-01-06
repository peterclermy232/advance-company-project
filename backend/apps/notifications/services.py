from .models import Notification
from apps.accounts.models import User

class NotificationService:
    """Service for creating and managing notifications"""
    
    @staticmethod
    def create_notification(user, notification_type, title, message, **kwargs):
        """Create a notification for a user"""
        return Notification.objects.create(
            user=user,
            notification_type=notification_type,
            title=title,
            message=message,
            related_deposit_id=kwargs.get('related_deposit_id'),
            related_application_id=kwargs.get('related_application_id'),
            related_user_name=kwargs.get('related_user_name')
        )
    
    @staticmethod
    def notify_deposit_created(deposit):
        """Notify user when they create a deposit"""
        NotificationService.create_notification(
            user=deposit.user,
            notification_type='deposit_created',
            title='Deposit Initiated',
            message=f'Your deposit of KES {deposit.amount:,.2f} via {deposit.get_payment_method_display()} has been submitted for approval.',
            related_deposit_id=deposit.id
        )
        
        # Notify all admins about new deposit
        admins = User.objects.filter(role='admin', is_active=True)
        for admin in admins:
            NotificationService.create_notification(
                user=admin,
                notification_type='deposit_created',
                title='New Deposit Pending',
                message=f'{deposit.user.full_name} submitted a deposit of KES {deposit.amount:,.2f} for approval.',
                related_deposit_id=deposit.id,
                related_user_name=deposit.user.full_name
            )
    
    @staticmethod
    def notify_deposit_approved(deposit, approved_by):
        """Notify user when their deposit is approved"""
        NotificationService.create_notification(
            user=deposit.user,
            notification_type='deposit_approved',
            title='Deposit Approved',
            message=f'Your deposit of KES {deposit.amount:,.2f} has been approved. Your account has been credited.',
            related_deposit_id=deposit.id
        )
    
    @staticmethod
    def notify_deposit_rejected(deposit, rejected_by, reason):
        """Notify user when their deposit is rejected"""
        NotificationService.create_notification(
            user=deposit.user,
            notification_type='deposit_rejected',
            title='Deposit Rejected',
            message=f'Your deposit of KES {deposit.amount:,.2f} was rejected. Reason: {reason}',
            related_deposit_id=deposit.id
        )
    
    @staticmethod
    def notify_application_submitted(application):
        """Notify admins when a new application is submitted"""
        admins = User.objects.filter(role='admin', is_active=True)
        for admin in admins:
            NotificationService.create_notification(
                user=admin,
                notification_type='application_submitted',
                title='New Application Submitted',
                message=f'{application.user.full_name} submitted a new {application.get_application_type_display()} application.',
                related_application_id=application.id,
                related_user_name=application.user.full_name
            )
    
    @staticmethod
    def notify_application_approved(application):
        """Notify user when their application is approved"""
        NotificationService.create_notification(
            user=application.user,
            notification_type='application_approved',
            title='Application Approved',
            message=f'Your {application.get_application_type_display()} application has been approved.',
            related_application_id=application.id
        )
    
    @staticmethod
    def notify_application_rejected(application, reason):
        """Notify user when their application is rejected"""
        NotificationService.create_notification(
            user=application.user,
            notification_type='application_rejected',
            title='Application Rejected',
            message=f'Your {application.get_application_type_display()} application was rejected. {reason}',
            related_application_id=application.id
        )
    
    @staticmethod
    def notify_document_verified(document):
        """Notify user when their document is verified"""
        NotificationService.create_notification(
            user=document.user,
            notification_type='document_verified',
            title='Document Verified',
            message=f'Your document "{document.title}" has been verified.',
        )
    
    @staticmethod
    def notify_beneficiary_verified(beneficiary):
        """Notify user when their beneficiary is verified"""
        NotificationService.create_notification(
            user=beneficiary.user,
            notification_type='beneficiary_verified',
            title='Beneficiary Verified',
            message=f'Beneficiary "{beneficiary.name}" has been verified.',
        )