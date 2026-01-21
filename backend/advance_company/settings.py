"""
Django settings for advance_company project.
"""

import os
from pathlib import Path
from datetime import timedelta

from decouple import config
import dj_database_url
import dotenv

dotenv.load_dotenv()

# Build paths inside the project
BASE_DIR = Path(__file__).resolve().parent.parent


# Helper to strip quotes from Railway env vars
def strip_quotes(value):
    """Strip surrounding quotes that Railway adds automatically."""
    if isinstance(value, str):
        return value.strip('"').strip("'")
    return value


def parse_list(value):
    """Parse comma-separated string into list, handling quotes."""
    if not value:
        return []
    value = strip_quotes(value)
    return [item.strip() for item in value.split(',') if item.strip()]


def parse_bool(value):
    """Parse boolean, handling quoted strings from Railway."""
    if isinstance(value, bool):
        return value
    value = strip_quotes(str(value)).lower()
    return value in ('true', '1', 'yes', 'on')


# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = strip_quotes(config('SECRET_KEY'))

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = parse_bool(config('DEBUG', default=False))

ALLOWED_HOSTS = parse_list(config('ALLOWED_HOSTS', default=''))

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Third party
    'rest_framework',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
    'corsheaders',
    'django_filters',
    'django_ratelimit',
    
    # Local apps
    'apps.accounts',
    'apps.financial',
    'apps.beneficiary',
    'apps.documents',
    'apps.applications',
    'apps.reports',
    'apps.notifications',
    'apps.analytics',
    'apps.health',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'advance_company.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'advance_company.wsgi.application'

# Database
DATABASES = {
    'default': dj_database_url.parse(
        strip_quotes(config('DATABASE_URL')),
        conn_max_age=600,
        conn_health_checks=True,
    )
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', 'OPTIONS': {'min_length': 12}},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
    {'NAME': 'apps.accounts.validators.StrongPasswordValidator'},
    {'NAME': 'apps.accounts.validators.NoPersonalInfoValidator'},
]

PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.Argon2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Africa/Nairobi'
USE_I18N = True
USE_TZ = True

# Static files
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Custom user model
AUTH_USER_MODEL = 'accounts.User'

# CORS Configuration
CORS_ALLOWED_ORIGINS = parse_list(config('CORS_ALLOWED_ORIGINS', default=''))
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
]

# CSRF Configuration - Disabled for API
CSRF_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = 'Lax'
CSRF_TRUSTED_ORIGINS = parse_list(config('CSRF_TRUSTED_ORIGINS', default=''))

CSRF_USE_SESSIONS = False
CSRF_COOKIE_NAME = None

# Session Configuration
SESSION_COOKIE_SECURE = not DEBUG
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
SESSION_COOKIE_AGE = 3600

# Security Settings for Production
if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SECURE_SSL_REDIRECT = False  # Railway handles SSL at load balancer
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'

# REST Framework
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.AllowAny',
    ],
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/hour',
        'user': '1000/hour',
        # Custom throttle rates for auth endpoints
        'login': '10/minute',
        'register': '5/minute',
        'two_factor': '5/5minute',
        'biometric': '10/minute',
        'password_reset': '3/hour',
        'email_verification': '5/minute',
    },
    'EXCEPTION_HANDLER': 'rest_framework.views.exception_handler',
    'UNAUTHENTICATED_USER': None,
    'UNAUTHENTICATED_TOKEN': None,
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',
        'rest_framework.parsers.JSONParser',
        'rest_framework.parsers.FormParser',
        'rest_framework.parsers.MultiPartParser',
    ],
}

# JWT Settings
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=30),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,
    'SIGNING_KEY': SECRET_KEY,
    'AUTH_HEADER_TYPES': ('Bearer',),
}

# Cache Configuration
REDIS_URL = config('REDIS_URL', default=None)
if REDIS_URL:
    REDIS_URL = strip_quotes(REDIS_URL)
    CACHES = {
        'default': {
            'BACKEND': 'django_redis.cache.RedisCache',
            'LOCATION': REDIS_URL,
            'OPTIONS': {
                'CLIENT_CLASS': 'django_redis.client.DefaultClient',
                'IGNORE_EXCEPTIONS': True,
            },
            'KEY_PREFIX': 'advance_company',
        }
    }
else:
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        }
    }

# Rate Limiting
RATELIMIT_ENABLE = False
RATELIMIT_USE_CACHE = 'default'

# Email Configuration
EMAIL_BACKEND = strip_quotes(config('EMAIL_BACKEND', default='django.core.mail.backends.smtp.EmailBackend'))
EMAIL_HOST = strip_quotes(config('EMAIL_HOST'))
EMAIL_PORT = int(strip_quotes(config('EMAIL_PORT', default='587')))
EMAIL_USE_TLS = parse_bool(config('EMAIL_USE_TLS', default=True))
EMAIL_HOST_USER = strip_quotes(config('EMAIL_HOST_USER'))
EMAIL_HOST_PASSWORD = strip_quotes(config('EMAIL_HOST_PASSWORD'))
DEFAULT_FROM_EMAIL = strip_quotes(config('DEFAULT_FROM_EMAIL'))

# M-PESA Configuration
MPESA_ENVIRONMENT = strip_quotes(config('MPESA_ENVIRONMENT', default='sandbox'))
MPESA_CONSUMER_KEY = strip_quotes(config('MPESA_CONSUMER_KEY', default=''))
MPESA_CONSUMER_SECRET = strip_quotes(config('MPESA_CONSUMER_SECRET', default=''))
MPESA_SHORTCODE = strip_quotes(config('MPESA_SHORTCODE', default='174379'))
MPESA_PASSKEY = strip_quotes(config('MPESA_PASSKEY', default='bfb279f9aa9bdbcf158e97dd71a467cd2e0c893059b10f78e6b72ada1ed2c919'))
MPESA_CALLBACK_URL = strip_quotes(config('MPESA_CALLBACK_URL', default=''))

# Frontend URL
FRONTEND_URL = strip_quotes(config('FRONTEND_URL'))

# Logging
os.makedirs(BASE_DIR / 'logs', exist_ok=True)
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'file': {
            'level': 'WARNING',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR / 'logs/django.log',
            'maxBytes': 10485760,
            'backupCount': 5,
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'apps.accounts': {  # Add this
        'handlers': ['console'],
        'level': 'INFO',
        'propagate': False,
    },
    },
}

# Debug output for production troubleshooting
print("="*50)
print("SETTINGS LOADED")
print("="*50)
print(f"DEBUG: {DEBUG}")
print(f"ALLOWED_HOSTS: {ALLOWED_HOSTS}")
print(f"CORS_ALLOWED_ORIGINS: {CORS_ALLOWED_ORIGINS}")
print(f"CSRF_TRUSTED_ORIGINS: {CSRF_TRUSTED_ORIGINS}")
print(f"CSRF Middleware: DISABLED (JWT API)")
print("="*50)