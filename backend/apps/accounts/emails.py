from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings

def send_verification_email(user):
    """Send email verification"""
    token = user.generate_verification_token()
    
    # Construct verification URL
    verification_url = f"{settings.FRONTEND_URL}/auth/verify-email?token={token}&email={user.email}"
    
    context = {
        'user': user,
        'verification_url': verification_url,
        'expiry_hours': 24
    }
    
    subject = 'Verify Your Email - Advance Company'
    
    text_content = f"""
    Hello {user.full_name},
    
    Welcome to Advance Company! Please verify your email address by clicking the link below:
    
    {verification_url}
    
    This link will expire in 24 hours.
    
    If you didn't create this account, please ignore this email.
    
    Best regards,
    Advance Company Team
    """
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background: linear-gradient(135deg, #2563eb, #4f46e5); color: white; padding: 30px; text-align: center; border-radius: 8px 8px 0 0; }}
            .content {{ background: #f9fafb; padding: 30px; border-radius: 0 0 8px 8px; }}
            .button {{ display: inline-block; background: #2563eb; color: white; padding: 12px 30px; text-decoration: none; border-radius: 6px; margin: 20px 0; }}
            .footer {{ text-align: center; color: #6b7280; font-size: 12px; margin-top: 20px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Welcome to Advance Company!</h1>
            </div>
            <div class="content">
                <p>Hello <strong>{user.full_name}</strong>,</p>
                <p>Thank you for registering with Advance Company. To complete your registration and start using your account, please verify your email address.</p>
                <div style="text-align: center;">
                    <a href="{verification_url}" class="button">Verify Email Address</a>
                </div>
                <p>Or copy and paste this link into your browser:</p>
                <p style="word-break: break-all; color: #2563eb;">{verification_url}</p>
                <p><strong>This link will expire in 24 hours.</strong></p>
                <p>If you didn't create this account, please ignore this email.</p>
            </div>
            <div class="footer">
                <p>&copy; 2024 Advance Company. All rights reserved.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    msg = EmailMultiAlternatives(subject, text_content, settings.DEFAULT_FROM_EMAIL, [user.email])
    msg.attach_alternative(html_content, "text/html")
    msg.send()