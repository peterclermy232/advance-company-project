import re
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _

class StrongPasswordValidator:
    """
    Validate password strength:
    - Minimum 12 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one digit
    - At least one special character
    - No common passwords
    """
    
    def validate(self, password, user=None):
        if len(password) < 12:
            raise ValidationError(
                _("Password must be at least 12 characters long."),
                code='password_too_short',
            )
        
        if not re.search(r'[A-Z]', password):
            raise ValidationError(
                _("Password must contain at least one uppercase letter."),
                code='password_no_upper',
            )
        
        if not re.search(r'[a-z]', password):
            raise ValidationError(
                _("Password must contain at least one lowercase letter."),
                code='password_no_lower',
            )
        
        if not re.search(r'\d', password):
            raise ValidationError(
                _("Password must contain at least one digit."),
                code='password_no_digit',
            )
        
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            raise ValidationError(
                _("Password must contain at least one special character (!@#$%^&*(),.?\":{}|<>)."),
                code='password_no_special',
            )
        
        # Check for common patterns
        common_patterns = ['123456', 'password', 'qwerty', 'abc123']
        if any(pattern in password.lower() for pattern in common_patterns):
            raise ValidationError(
                _("Password contains common patterns and is not secure."),
                code='password_too_common',
            )
    
    def get_help_text(self):
        return _(
            "Your password must contain at least 12 characters, "
            "including uppercase and lowercase letters, digits, and special characters."
        )


class NoPersonalInfoValidator:
    """Ensure password doesn't contain user's personal information"""
    
    def validate(self, password, user=None):
        if not user:
            return
        
        # Check against email
        if user.email and user.email.split('@')[0].lower() in password.lower():
            raise ValidationError(
                _("Password cannot contain your email address."),
                code='password_contains_email',
            )
        
        # Check against name
        if user.full_name:
            name_parts = user.full_name.lower().split()
            for part in name_parts:
                if len(part) > 3 and part in password.lower():
                    raise ValidationError(
                        _("Password cannot contain your name."),
                        code='password_contains_name',
                    )
    
    def get_help_text(self):
        return _("Your password cannot contain your email or name.")
