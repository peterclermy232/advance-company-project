from django.conf import settings
from rest_framework.throttling import AnonRateThrottle


class LoginRateThrottle(AnonRateThrottle):
    scope = 'login'
    rate = '10/minute'


class RegisterRateThrottle(AnonRateThrottle):
    scope = 'register'
    rate = '5/minute'


class TwoFactorRateThrottle(AnonRateThrottle):
    scope = 'two_factor'
    rate = '5/5minute'


class BiometricRateThrottle(AnonRateThrottle):
    scope = 'biometric'
    rate = '10/minute'


class PasswordResetRateThrottle(AnonRateThrottle):
    scope = 'password_reset'
    rate = '3/hour' if not settings.DEBUG else '100/hour'


class EmailVerificationRateThrottle(AnonRateThrottle):
    scope = 'email_verification'
    rate = '5/minute'