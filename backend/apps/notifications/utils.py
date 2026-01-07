"""
apps/notifications/utils.py
Email and SMS notification utilities with robust error handling
"""
from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

# Safe import of requests (optional dependency)
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    logger.warning("requests library not installed - SMS notifications disabled")


# ============================================================
# EMAIL NOTIFICATIONS
# ============================================================

def send_email_notification(user, subject, message, html_message=None):
    """
    Send email notification to user
    
    Args:
        user: User object
        subject: Email subject
        message: Plain text message
        html_message: HTML formatted message (optional)
    
    Returns:
        bool: True if sent successfully
    """
    try:
        # Check if user has email
        if not user.email:
            logger.warning(f"User {user.full_name} has no email address")
            return False
        
        # Check if user has email enabled
        if hasattr(user, 'notification_preferences'):
            if not user.notification_preferences.email_enabled:
                logger.info(f"Email disabled for user {user.email}")
                return False
        
        # Check if email is configured
        if not getattr(settings, 'EMAIL_HOST_USER', None):
            logger.warning("Email not configured in settings - skipping email")
            return False
        
        # Send email
        if html_message:
            # Send both plain text and HTML
            email = EmailMultiAlternatives(
                subject=subject,
                body=message,
                from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', settings.EMAIL_HOST_USER),
                to=[user.email]
            )
            email.attach_alternative(html_message, "text/html")
            email.send()
        else:
            # Send plain text only
            send_mail(
                subject=subject,
                message=message,
                from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', settings.EMAIL_HOST_USER),
                recipient_list=[user.email],
                fail_silently=False,
            )
        
        logger.info(f"Email sent to {user.email}")
        return True
        
    except Exception as e:
        logger.error(f"Error sending email to {user.email}: {str(e)}")
        return False


def send_deposit_created_email(user, deposit):
    """Send email when deposit is created"""
    subject = "Deposit Submitted - Advance Company"
    message = f"""
Hello {user.full_name},

Your deposit of KES {deposit.amount:,.2f} has been successfully submitted for approval.

Payment Method: {deposit.get_payment_method_display()}
Transaction Reference: {deposit.transaction_reference}
Date: {deposit.created_at.strftime('%B %d, %Y at %I:%M %p')}

You will receive a notification once your deposit has been reviewed.

Thank you for using Advance Company!

Best regards,
The Advance Company Team
    """
    
    # Create HTML version
    html_message = f"""
    <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #2563eb;">Deposit Submitted</h2>
                <p>Hello <strong>{user.full_name}</strong>,</p>
                <p>Your deposit has been successfully submitted for approval.</p>
                
                <div style="background: #f3f4f6; padding: 15px; border-radius: 8px; margin: 20px 0;">
                    <p style="margin: 5px 0;"><strong>Amount:</strong> KES {deposit.amount:,.2f}</p>
                    <p style="margin: 5px 0;"><strong>Payment Method:</strong> {deposit.get_payment_method_display()}</p>
                    <p style="margin: 5px 0;"><strong>Reference:</strong> {deposit.transaction_reference}</p>
                    <p style="margin: 5px 0;"><strong>Date:</strong> {deposit.created_at.strftime('%B %d, %Y at %I:%M %p')}</p>
                </div>
                
                <p>You will receive a notification once your deposit has been reviewed.</p>
                <p>Thank you for using Advance Company!</p>
                <br>
                <p style="color: #666; font-size: 12px;">
                    Best regards,<br>
                    The Advance Company Team
                </p>
            </div>
        </body>
    </html>
    """
    
    return send_email_notification(user, subject, message, html_message)


def send_deposit_approved_email(user, deposit):
    """Send email when deposit is approved"""
    subject = "Deposit Approved - Advance Company"
    message = f"""
Hello {user.full_name},

Great news! Your deposit of KES {deposit.amount:,.2f} has been approved and credited to your account.

Transaction Reference: {deposit.transaction_reference}
Approved: {deposit.updated_at.strftime('%B %d, %Y at %I:%M %p')}

You can view your updated balance in the Financial section of your dashboard.

Thank you for using Advance Company!

Best regards,
The Advance Company Team
    """
    
    html_message = f"""
    <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #16a34a;">✓ Deposit Approved</h2>
                <p>Hello <strong>{user.full_name}</strong>,</p>
                <p>Great news! Your deposit has been approved and credited to your account.</p>
                
                <div style="background: #dcfce7; padding: 15px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #16a34a;">
                    <p style="margin: 5px 0;"><strong>Amount:</strong> KES {deposit.amount:,.2f}</p>
                    <p style="margin: 5px 0;"><strong>Reference:</strong> {deposit.transaction_reference}</p>
                    <p style="margin: 5px 0;"><strong>Approved:</strong> {deposit.updated_at.strftime('%B %d, %Y at %I:%M %p')}</p>
                </div>
                
                <p>You can view your updated balance in the Financial section of your dashboard.</p>
                <p>Thank you for using Advance Company!</p>
                <br>
                <p style="color: #666; font-size: 12px;">
                    Best regards,<br>
                    The Advance Company Team
                </p>
            </div>
        </body>
    </html>
    """
    
    return send_email_notification(user, subject, message, html_message)


# ============================================================
# SMS NOTIFICATIONS (Africa's Talking)
# ============================================================

def send_sms_notification(user, message):
    """
    Send SMS notification to user using Africa's Talking
    
    Args:
        user: User object
        message: SMS message (max 160 characters recommended)
    
    Returns:
        bool: True if sent successfully
    """
    try:
        # Check if requests is available
        if not REQUESTS_AVAILABLE:
            logger.warning("requests library not available - cannot send SMS")
            return False
        
        # Check if user has phone number
        if not hasattr(user, 'phone_number') or not user.phone_number:
            logger.warning(f"User {user.full_name} has no phone number")
            return False
        
        # Check if user has SMS enabled
        if hasattr(user, 'notification_preferences'):
            if not user.notification_preferences.sms_enabled:
                logger.info(f"SMS disabled for user {user.phone_number}")
                return False
        
        # Africa's Talking API credentials
        api_key = getattr(settings, 'AFRICAS_TALKING_API_KEY', None)
        username = getattr(settings, 'AFRICAS_TALKING_USERNAME', None)
        
        if not api_key or not username:
            logger.warning("Africa's Talking credentials not configured - skipping SMS")
            return False
        
        url = "https://api.africastalking.com/version1/messaging"
        
        headers = {
            "apiKey": api_key,
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json"
        }
        
        data = {
            "username": username,
            "to": user.phone_number,
            "message": message,
            "from": getattr(settings, 'AFRICAS_TALKING_SENDER_ID', "ADVANCE")
        }
        
        response = requests.post(url, headers=headers, data=data, timeout=10)
        
        if response.status_code == 201:
            logger.info(f"SMS sent to {user.phone_number}")
            return True
        else:
            logger.error(f"SMS failed: {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"Error sending SMS to {getattr(user, 'phone_number', 'unknown')}: {str(e)}")
        return False


def send_deposit_created_sms(user, deposit):
    """Send SMS when deposit is created"""
    message = f"Advance Company: Your deposit of KES {deposit.amount:,.2f} has been submitted for approval. Ref: {deposit.transaction_reference}"
    return send_sms_notification(user, message)


def send_deposit_approved_sms(user, deposit):
    """Send SMS when deposit is approved"""
    message = f"Advance Company: Your deposit of KES {deposit.amount:,.2f} has been APPROVED and credited to your account. Ref: {deposit.transaction_reference}"
    return send_sms_notification(user, message)


def send_application_approved_sms(user, application):
    """Send SMS when application is approved"""
    message = f"Advance Company: Your {application.get_application_type_display()} application has been APPROVED. Check your dashboard for details."
    return send_sms_notification(user, message)


# ============================================================
# UNIFIED NOTIFICATION SENDER
# ============================================================

def send_multi_channel_notification(user, notification_type, title, message, **kwargs):
    """
    Send notification across all enabled channels (in-app, email, SMS)
    
    Args:
        user: User object
        notification_type: Type of notification
        title: Notification title
        message: Notification message
        **kwargs: Additional data (deposit, application, etc.)
    
    Returns:
        dict: Status of each channel
    """
    from .models import Notification, NotificationPreferences
    
    results = {
        'in_app': False,
        'email': False,
        'sms': False
    }
    
    # Get or create user preferences
    try:
        prefs, created = NotificationPreferences.objects.get_or_create(user=user)
        if created:
            logger.info(f"Created notification preferences for {user.full_name}")
    except Exception as e:
        logger.error(f"Error getting preferences for {user.full_name}: {str(e)}")
        prefs = None
    
    # 1. In-App Notification (always create if push enabled)
    try:
        if not prefs or (prefs.push_enabled and prefs.should_notify(notification_type, 'push')):
            # Extract only valid Notification model fields
            notification_kwargs = {}
            if 'related_deposit_id' in kwargs:
                notification_kwargs['related_deposit_id'] = kwargs['related_deposit_id']
            if 'related_application_id' in kwargs:
                notification_kwargs['related_application_id'] = kwargs['related_application_id']
            if 'related_user_name' in kwargs:
                notification_kwargs['related_user_name'] = kwargs['related_user_name']
            
            Notification.objects.create(
                user=user,
                notification_type=notification_type,
                title=title,
                message=message,
                **notification_kwargs
            )
            results['in_app'] = True
            logger.info(f"Created in-app notification for {user.full_name}")
    except Exception as e:
        logger.error(f"Error creating in-app notification: {str(e)}")
    
    # 2. Email Notification
    try:
        if not prefs or (prefs.email_enabled and prefs.should_notify(notification_type, 'email')):
            # Use specific email template if available
            if notification_type == 'deposit_created' and 'deposit' in kwargs:
                results['email'] = send_deposit_created_email(user, kwargs['deposit'])
            elif notification_type == 'deposit_approved' and 'deposit' in kwargs:
                results['email'] = send_deposit_approved_email(user, kwargs['deposit'])
            else:
                # Generic email
                results['email'] = send_email_notification(user, title, message)
    except Exception as e:
        logger.error(f"Error sending email notification: {str(e)}")
    
    # 3. SMS Notification
    try:
        if not prefs or (prefs.sms_enabled and prefs.should_notify(notification_type, 'sms')):
            # Shorten message for SMS (max 160 chars)
            sms_message = message[:150] + "..." if len(message) > 150 else message
            
            # Use specific SMS template if available
            if notification_type == 'deposit_created' and 'deposit' in kwargs:
                results['sms'] = send_deposit_created_sms(user, kwargs['deposit'])
            elif notification_type == 'deposit_approved' and 'deposit' in kwargs:
                results['sms'] = send_deposit_approved_sms(user, kwargs['deposit'])
            elif notification_type == 'application_approved' and 'application' in kwargs:
                results['sms'] = send_application_approved_sms(user, kwargs['application'])
            else:
                # Generic SMS
                results['sms'] = send_sms_notification(user, sms_message)
    except Exception as e:
        logger.error(f"Error sending SMS notification: {str(e)}")
    
    logger.info(f"Multi-channel notification to {user.email}: {results}")
    return results