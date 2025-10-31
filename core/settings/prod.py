# core/settings/prod.py

from .base import *
import os

# ============================================
# SECURITY SETTINGS
# ============================================

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config('DEBUG', default=False, cast=bool)

# Allowed hosts - must be explicitly set in production
ALLOWED_HOSTS = config(
    'ALLOWED_HOSTS',
    default='',
    cast=lambda v: [s.strip() for s in v.split(',') if s.strip()]
)

# Security settings for HTTPS
SECURE_SSL_REDIRECT = config('SECURE_SSL_REDIRECT', default=True, cast=bool)
SESSION_COOKIE_SECURE = config('SESSION_COOKIE_SECURE', default=True, cast=bool)
CSRF_COOKIE_SECURE = config('CSRF_COOKIE_SECURE', default=True, cast=bool)
SECURE_HSTS_SECONDS = config('SECURE_HSTS_SECONDS', default=31536000, cast=int)  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = config('SECURE_HSTS_INCLUDE_SUBDOMAINS', default=True, cast=bool)
SECURE_HSTS_PRELOAD = config('SECURE_HSTS_PRELOAD', default=True, cast=bool)
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Content Security Policy
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = 'DENY'

# ============================================
# DATABASE CONFIGURATION
# ============================================

# Production database with connection pooling
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('DB_NAME'),
        'USER': config('DB_USER'),
        'PASSWORD': config('DB_PASSWORD'),
        'HOST': config('DB_HOST', default='localhost'),
        'PORT': config('DB_PORT', default='5432'),
        'CONN_MAX_AGE': config('CONN_MAX_AGE', default=600, cast=int),  # Connection pooling
        'OPTIONS': {
            'connect_timeout': 10,
            'options': '-c statement_timeout=30000'  # 30 seconds query timeout
        }
    }
}

# ============================================
# CACHE CONFIGURATION (Redis)
# ============================================

# Production cache - use Redis
redis_url = config('REDIS_URL', default='redis://localhost:6379/0')
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': redis_url,
        # Note: For advanced options like compression, install django-redis:
        # 'BACKEND': 'django_redis.cache.RedisCache',
        # 'OPTIONS': {
        #     'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        #     'COMPRESSOR': 'django_redis.compressors.zlib.ZlibCompressor',
        #     'IGNORE_EXCEPTIONS': True,
        # },
        'KEY_PREFIX': 'dynamicform',
        'TIMEOUT': 300,  # 5 minutes default timeout
    }
}

# ============================================
# REDIS & CELERY CONFIGURATION
# ============================================

# Channel layers for WebSocket (Redis)
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            'hosts': [redis_url],
            'capacity': 1500,  # Max messages in queue
            'expiry': 10,  # Message expiry in seconds
        },
    },
}

# Celery configuration with Redis
CELERY_BROKER_URL = config('CELERY_BROKER_URL', default=f"{redis_url.split('/')[0]}/1")
CELERY_RESULT_BACKEND = config('CELERY_RESULT_BACKEND', default=f"{redis_url.split('/')[0]}/2")
CELERY_ACCEPT_CONTENT = ['application/json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'UTC'

# Celery task settings for production
CELERY_TASK_ACKS_LATE = True
CELERY_WORKER_PREFETCH_MULTIPLIER = 1
CELERY_TASK_REJECT_ON_WORKER_LOST = True
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 30 * 60  # 30 minutes
CELERY_TASK_SOFT_TIME_LIMIT = 25 * 60  # 25 minutes

CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'

# ============================================
# STATIC FILES & MEDIA
# ============================================

STATIC_URL = config('STATIC_URL', default='/static/')
STATIC_ROOT = config('STATIC_ROOT', default=BASE_DIR / 'staticfiles')

MEDIA_URL = config('MEDIA_URL', default='/media/')
MEDIA_ROOT = config('MEDIA_ROOT', default=BASE_DIR / 'media')

# Storage backends (use S3 or similar in production)
# Uncomment and configure if using cloud storage:
# DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
# STATICFILES_STORAGE = 'storages.backends.s3boto3.S3StaticStorage'
# AWS_ACCESS_KEY_ID = config('AWS_ACCESS_KEY_ID')
# AWS_SECRET_ACCESS_KEY = config('AWS_SECRET_ACCESS_KEY')
# AWS_STORAGE_BUCKET_NAME = config('AWS_STORAGE_BUCKET_NAME')
# AWS_S3_REGION_NAME = config('AWS_S3_REGION_NAME', default='us-east-1')

# ============================================
# EMAIL CONFIGURATION
# ============================================

# Production email - use SMTP backend
EMAIL_BACKEND = config('EMAIL_BACKEND', default='django.core.mail.backends.smtp.EmailBackend')
EMAIL_HOST = config('EMAIL_HOST', default='smtp.gmail.com')
EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=True, cast=bool)
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='noreply@dynamicforms.com')
SERVER_EMAIL = config('SERVER_EMAIL', default=DEFAULT_FROM_EMAIL)

# Frontend URL for email links
FRONTEND_URL = config('FRONTEND_URL', default='https://app.dynamicforms.com')

# ============================================
# LOGGING CONFIGURATION
# ============================================

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
        'json': {
            'format': '{"level": "{levelname}", "time": "{asctime}", "module": "{module}", "message": "{message}"}',
            'style': '{',
        },
    },
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': config('LOG_FILE', default=BASE_DIR / 'logs' / 'django.log'),
            'maxBytes': 1024 * 1024 * 10,  # 10 MB
            'backupCount': 10,
            'formatter': 'verbose',
        },
        'mail_admins': {
            'level': 'ERROR',
            'class': 'django.utils.log.AdminEmailHandler',
            'filters': ['require_debug_false'],
            'email_backend': EMAIL_BACKEND,
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': config('LOG_LEVEL', default='INFO'),
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': config('DJANGO_LOG_LEVEL', default='INFO'),
            'propagate': False,
        },
        'django.security': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': False,
        },
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': False,
        },
        'celery': {
            'handlers': ['console', 'file'],
            'level': config('CELERY_LOG_LEVEL', default='INFO'),
            'propagate': False,
        },
    },
}

# Create logs directory if it doesn't exist
os.makedirs(BASE_DIR / 'logs', exist_ok=True)

# ============================================
# API CONFIGURATION
# ============================================

API_VERSION = config('API_VERSION', default='1.0.0')
CHANGELOG_URL = config('CHANGELOG_URL', default=None)
ENVIRONMENT = config('ENVIRONMENT', default='production')

# ============================================
# PERFORMANCE & OPTIMIZATION
# ============================================

# Database connection pooling is already configured in DATABASES above

# Session configuration
SESSION_ENGINE = 'django.contrib.sessions.backends.cached_db'
SESSION_CACHE_ALIAS = 'default'
SESSION_COOKIE_AGE = 86400  # 24 hours
SESSION_COOKIE_HTTPONLY = True

# ============================================
# MONITORING & HEALTH CHECKS
# ============================================

# Enable Django's check framework
# Run: python manage.py check --deploy

# ============================================
# CORS SETTINGS (if needed for frontend)
# ============================================

# Uncomment and configure if using django-cors-headers:
# CORS_ALLOWED_ORIGINS = config(
#     'CORS_ALLOWED_ORIGINS',
#     default='',
#     cast=lambda v: [s.strip() for s in v.split(',') if s.strip()]
# )
# CORS_ALLOW_CREDENTIALS = True
# CORS_ALLOW_METHODS = ['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'OPTIONS']
# CORS_ALLOW_HEADERS = ['content-type', 'authorization', 'x-csrftoken']

# ============================================
# RATE LIMITING (if needed)
# ============================================

# Uncomment if using django-ratelimit or similar:
# RATELIMIT_ENABLE = True
# RATELIMIT_USE_CACHE = 'default'

# ============================================
# SENTRY ERROR TRACKING (optional)
# ============================================

# Uncomment and configure if using Sentry:
# import sentry_sdk
# from sentry_sdk.integrations.django import DjangoIntegration
# from sentry_sdk.integrations.celery import CeleryIntegration
# 
# sentry_sdk.init(
#     dsn=config('SENTRY_DSN', default=''),
#     integrations=[
#         DjangoIntegration(),
#         CeleryIntegration(),
#     ],
#     traces_sample_rate=config('SENTRY_TRACES_SAMPLE_RATE', default=0.1, cast=float),
#     send_default_pii=False,
#     environment=ENVIRONMENT,
# )

