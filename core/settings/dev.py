# core/settings/dev.py

from .base import *
import os

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config('DEBUG', default=True, cast=bool)

ALLOWED_HOSTS = ['*']

# Database configuration for Docker
if os.getenv('DB_HOST'):
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': config('DB_NAME', default='dynamicformdb'),
            'USER': config('DB_USER', default='postgres'),
            'PASSWORD': config('DB_PASSWORD', default='postgres'),
            'HOST': config('DB_HOST', default='localhost'),
            'PORT': config('DB_PORT', default='5432'),
        }
    }

# Redis configuration for Docker
if os.getenv('REDIS_URL'):
    redis_url = config('REDIS_URL', default='redis://localhost:6379/1')
    CELERY_BROKER_URL = config('CELERY_BROKER_URL', default=f"{redis_url.split('/')[0]}/1" if '/' in redis_url else redis_url)
    CELERY_RESULT_BACKEND = config('CELERY_RESULT_BACKEND', default=f"{redis_url.split('/')[0]}/2" if '/' in redis_url else redis_url)
    
    # Channel layers for WebSocket - update hosts list
    if 'CHANNEL_LAYERS' in locals() and 'default' in CHANNEL_LAYERS:
        CHANNEL_LAYERS['default']['CONFIG']['hosts'] = [redis_url]
