import os
from pathlib import Path
from datetime import timedelta

from decouple import config
import dj_database_url
import dotenv

dotenv.load_dotenv()

# ==========================================================
# BASE
# ==========================================================

BASE_DIR = Path(__file__).resolve().parent.parent

# ==========================================================
# SECURITY CORE
# ==========================================================

SECRET_KEY = config('SECRET_KEY')
if not SECRET_KEY or 'change-this' in SECRET_KEY.lower():
    raise ValueError("❌ SECRET_KEY must be set securely")

DEBUG = config('DEBUG', default=False, cast=bool)
if DEBUG:
    print("⚠️  WARNING: DEBUG=True")

# ==========================================================
# HELPERS
# ==========================================================

def parse_csv(value: str):
    if not value:
        return []
    return [v.strip().strip('"').strip("'") for v in value.split(',') if v.strip()]

# ==========================================================
# HOSTS & CORS
# ==========================================================

ALLOWED_HOSTS = config(
    'ALLOWED_HOSTS',
    default='',
    cast=parse_csv
)

if not ALLOWED_HOSTS or '*' in ALLOWED_HOSTS:
    raise ValueError("❌ ALLOWED_HOSTS must be explicitly set")

CORS_ALLOWED_ORIGINS = config(
    'CORS_ALLOWED_ORIGINS',
    default='',
    cast=parse_csv
)

if not CORS_ALLOWED_ORIGINS:
    raise ValueError("❌ CORS_ALLOWED_ORIGINS must be set")

CSRF_TRUSTED_ORIGINS = config(
    'CSRF_TRUSTED_ORIGINS',
    default='',
    cast=parse_csv
)

CORS_ALLOW_CREDENTIALS = True
FRONTEND_URL = config('FRONTEND_URL')

# ==========================================================
# APPLICATIONS
# ==========================================================

INSTALLED_APPS = [
    # Django
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third-party
    'rest_framework',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
    'corsheaders',
    'django_filters',
    'django_ratelimit',

    # Local
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

# ==========================================================
# MIDDLEWARE
# ==========================================================

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',

    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# ==========================================================
# URLS / WSGI
# ==========================================================

ROOT_URLCONF = 'advance_company.urls'
WSGI_APPLICATION = 'advance_company.wsgi.application'

# ==========================================================
# DATABASE
# ==========================================================

DATABASES = {
    'default': dj_database_url.parse(
        config('DATABASE_URL'),
        conn_max_age=600,
        conn_health_checks=True
    )
}

# ==========================================================
# CACHE / RATE LIMIT
# ==========================================================

CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': config('REDIS_URL', default='redis://127.0.0.1:6379/0'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'PASSWORD': config('REDIS_PASSWORD', default=''),
        },
        'KEY_PREFIX': 'advance_company',
    }
}

RATELIMIT_ENABLE = True
RATELIMIT_USE_CACHE = 'default'

# ==========================================================
# AUTH / SECURITY
# ==========================================================

AUTH_USER_MODEL = 'accounts.User'

PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.Argon2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',
]

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', 'OPTIONS': {'min_length': 12}},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
    {'NAME': 'apps.accounts.validators.StrongPasswordValidator'},
    {'NAME': 'apps.accounts.validators.NoPersonalInfoValidator'},
]

# ==========================================================
# SESSIONS & CSRF
# ==========================================================

SESSION_COOKIE_AGE = 3600
SESSION_SAVE_EVERY_REQUEST = True
SESSION_COOKIE_SECURE = not DEBUG
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Strict'

CSRF_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = 'Strict'
CSRF_USE_SESSIONS = True

# ==========================================================
# REST FRAMEWORK
# ==========================================================

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/hour',
        'user': '1000/hour',
    },
}

# ==========================================================
# JWT
# ==========================================================

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=30),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,
    'SIGNING_KEY': SECRET_KEY,
    'AUTH_HEADER_TYPES': ('Bearer',),
}

# ==========================================================
# STATIC & MEDIA
# ==========================================================

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# ==========================================================
# EMAIL
# ==========================================================

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = config('EMAIL_HOST')
EMAIL_PORT = config('EMAIL_PORT', cast=int)
EMAIL_USE_TLS = True
EMAIL_HOST_USER = config('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL')

# ==========================================================
# LOGGING
# ==========================================================

os.makedirs(BASE_DIR / 'logs', exist_ok=True)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR / 'logs/django.log',
            'maxBytes': 10 * 1024 * 1024,
            'backupCount': 5,
            'level': 'WARNING',
        },
        'security': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR / 'logs/security.log',
            'maxBytes': 10 * 1024 * 1024,
            'backupCount': 5,
            'level': 'WARNING',
        },
    },
    'loggers': {
        'django': {'handlers': ['file'], 'level': 'WARNING'},
        'django.security': {'handlers': ['security'], 'level': 'WARNING'},
    },
}

# ==========================================================
# PRODUCTION HARDENING
# ==========================================================

if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'

# ==========================================================
# I18N
# ==========================================================

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Africa/Nairobi'
USE_I18N = True
USE_TZ = True

# ==========================================================
# M-PESA CONFIGURATION
# ==========================================================

MPESA_ENVIRONMENT = config('MPESA_ENVIRONMENT', default='sandbox')
MPESA_CONSUMER_KEY = config('MPESA_CONSUMER_KEY', default='')
MPESA_CONSUMER_SECRET = config('MPESA_CONSUMER_SECRET', default='')
MPESA_SHORTCODE = config('MPESA_SHORTCODE', default='174379')
MPESA_PASSKEY = config(
    'MPESA_PASSKEY',
    default='bfb279f9aa9bdbcf158e97dd71a467cd2e0c893059b10f78e6b72ada1ed2c919'
)
MPESA_CALLBACK_URL = config('MPESA_CALLBACK_URL', default='')


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
# ==========================================================
# DEFAULT AUTO FIELD (Fix the warnings)
# ==========================================================

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
# ==========================================================
# FINAL CHECK
# ==========================================================

print("✅ Settings loaded | DEBUG =", DEBUG)
