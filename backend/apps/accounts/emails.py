from django.core.mail import EmailMultiAlternatives
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

BRAND = 'Advance Company'
BRAND_COLOR = '#2563eb'


def _base_html(body_html: str) -> str:
    """Wrap content in a consistent branded HTML shell."""
    return f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <style>
    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0; background: #f3f4f6; }}
    .wrapper {{ max-width: 600px; margin: 40px auto; background: #fff; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.08); }}
    .header {{ background: linear-gradient(135deg, {BRAND_COLOR}, #4f46e5); color: #fff; padding: 32px 30px; text-align: center; }}
    .header h1 {{ margin: 0; font-size: 24px; }}
    .content {{ padding: 30px; background: #f9fafb; }}
    .button {{ display: inline-block; background: {BRAND_COLOR}; color: #fff !important; padding: 12px 30px; text-decoration: none; border-radius: 6px; margin: 20px 0; font-weight: bold; }}
    .url-fallback {{ word-break: break-all; color: {BRAND_COLOR}; font-size: 13px; }}
    .footer {{ text-align: center; color: #9ca3af; font-size: 12px; padding: 20px 30px; }}
    .info-box {{ background: #eff6ff; border-left: 4px solid {BRAND_COLOR}; padding: 15px; border-radius: 4px; margin: 16px 0; }}
  </style>
</head>
<body>
  <div class="wrapper">
    {body_html}
    <div class="footer">
      <p>&copy; 2024 {BRAND}. All rights reserved.</p>
      <p>If you did not request this email, please ignore it.</p>
    </div>
  </div>
</body>
</html>"""


def send_verification_email(user):
    """Send a branded email verification message."""
    frontend_url = getattr(settings, 'FRONTEND_URL', '').rstrip('/')
    if not frontend_url:
        logger.error('FRONTEND_URL is not set — cannot send verification email')
        raise ValueError('FRONTEND_URL setting is required')

    token = user.generate_verification_token()
    verification_url = (
        f'{frontend_url}/auth/verify-email'
        f'?token={token}&email={user.email}'
    )

    subject = f'Verify Your Email — {BRAND}'

    text_content = (
        f'Hello {user.full_name},\n\n'
        f'Welcome to {BRAND}! Please verify your email address by visiting:\n\n'
        f'{verification_url}\n\n'
        f'This link expires in 24 hours.\n\n'
        f'If you did not create this account, please ignore this email.\n\n'
        f'Best regards,\n{BRAND} Team'
    )

    body_html = f"""
    <div class="header"><h1>Welcome to {BRAND}!</h1></div>
    <div class="content">
      <p>Hello <strong>{user.full_name}</strong>,</p>
      <p>Thank you for registering. Please verify your email address to activate your account.</p>
      <div style="text-align:center;">
        <a href="{verification_url}" class="button">Verify Email Address</a>
      </div>
      <p>Or copy this link into your browser:</p>
      <p class="url-fallback">{verification_url}</p>
      <div class="info-box"><strong>This link expires in 24 hours.</strong></div>
    </div>"""

    _send(subject, text_content, _base_html(body_html), user.email)


def send_password_reset_email(user, reset_url: str):
    """Send a branded password reset email."""
    subject = f'Reset Your Password — {BRAND}'

    text_content = (
        f'Hello {user.full_name},\n\n'
        f'We received a request to reset your {BRAND} password.\n\n'
        f'Click the link below to choose a new password:\n\n'
        f'{reset_url}\n\n'
        f'This link expires in 1 hour. If you did not request a password reset, '
        f'please ignore this email — your account is safe.\n\n'
        f'Best regards,\n{BRAND} Team'
    )

    body_html = f"""
    <div class="header"><h1>Password Reset Request</h1></div>
    <div class="content">
      <p>Hello <strong>{user.full_name}</strong>,</p>
      <p>We received a request to reset your <strong>{BRAND}</strong> password.</p>
      <div style="text-align:center;">
        <a href="{reset_url}" class="button">Reset My Password</a>
      </div>
      <p>Or copy this link into your browser:</p>
      <p class="url-fallback">{reset_url}</p>
      <div class="info-box">
        <strong>This link expires in 1 hour.</strong><br>
        If you did not request a password reset, you can safely ignore this email.
        Your account has not been changed.
      </div>
    </div>"""

    _send(subject, text_content, _base_html(body_html), user.email)


def _send(subject: str, text: str, html: str, to_email: str):
    from django.conf import settings

    resend_api_key = getattr(settings, 'RESEND_API_KEY', None) or None

    if resend_api_key:
        try:
            import resend
            resend.api_key = resend_api_key
            from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'Advance Company <onboarding@resend.dev>')

            # Support both old and new Resend SDK versions
            try:
                # New SDK (>=1.0.0): resend.Emails.send(params={...})
                params = {
                    "from": from_email,
                    "to": [to_email] if isinstance(to_email, str) else to_email,
                    "subject": subject,
                    "html": html,
                    "text": text,
                }
                resend.Emails.send(params)
            except TypeError:
                # Old SDK: positional dict argument
                resend.Emails.send({
                    "from": from_email,
                    "to": to_email,
                    "subject": subject,
                    "html": html,
                    "text": text,
                })

            logger.info(f'Email "{subject}" sent to {to_email} via Resend')

        except Exception as e:
            logger.error(f'Resend email failed: {e}', exc_info=True)
            raise
    else:
        from django.core.mail import EmailMultiAlternatives
        from_email = getattr(settings, 'DEFAULT_FROM_EMAIL',
                             getattr(settings, 'EMAIL_HOST_USER', None))

        if not from_email:
            raise ValueError('DEFAULT_FROM_EMAIL or EMAIL_HOST_USER must be set')

        msg = EmailMultiAlternatives(subject, text, from_email, [to_email])
        msg.attach_alternative(html, 'text/html')
        msg.send()
        logger.info(f'Email "{subject}" sent to {to_email} via Gmail SMTP')
        