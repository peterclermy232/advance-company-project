from rest_framework.throttling import AnonRateThrottle


class LoginRateThrottle(AnonRateThrottle):
    """Rate limiting for login attempts - 10 per minute."""
    scope = 'login'
    rate = '10/minute'


class RegisterRateThrottle(AnonRateThrottle):
    """Rate limiting for registration - 5 per minute."""
    scope = 'register'
    rate = '5/minute'


class TwoFactorRateThrottle(AnonRateThrottle):
    """Rate limiting for 2FA verification - 5 per 5 minutes."""
    scope = 'two_factor'
    rate = '5/5minute'


class BiometricRateThrottle(AnonRateThrottle):
    """Rate limiting for biometric auth - 10 per minute."""
    scope = 'biometric'
    rate = '10/minute'


class PasswordResetRateThrottle(AnonRateThrottle):
    """Rate limiting for password reset - 3 per hour."""
    scope = 'password_reset'
    rate = '3/hour'


class EmailVerificationRateThrottle(AnonRateThrottle):
    """Rate limiting for email verification - 5 per minute."""
    scope = 'email_verification'
    rate = '5/minute'