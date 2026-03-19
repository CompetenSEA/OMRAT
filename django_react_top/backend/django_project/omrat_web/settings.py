"""Minimal Django settings for exposing OMRAT workbench endpoints."""

from __future__ import annotations

import os
from pathlib import Path
from urllib.parse import urlparse

BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = os.getenv('OMRAT_DJANGO_SECRET_KEY', 'unsafe-dev-key-change-me')
DEBUG = os.getenv('OMRAT_DJANGO_DEBUG', '0') == '1'
ALLOWED_HOSTS = [host for host in os.getenv('OMRAT_DJANGO_ALLOWED_HOSTS', '*').split(',') if host]

INSTALLED_APPS = [
    'omrat_web.apps.OmratWebConfig',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
]

ROOT_URLCONF = 'omrat_web.urls'
TEMPLATES = []
WSGI_APPLICATION = 'omrat_web.wsgi.application'
ASGI_APPLICATION = 'omrat_web.asgi.application'

def _database_config():
    db_url = os.getenv('OMRAT_DATABASE_URL', '').strip()
    if db_url.startswith('postgres://') or db_url.startswith('postgresql://'):
        parsed = urlparse(db_url)
        return {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': parsed.path.lstrip('/'),
            'USER': parsed.username or '',
            'PASSWORD': parsed.password or '',
            'HOST': parsed.hostname or '',
            'PORT': str(parsed.port or '5432'),
        }
    return {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }


DATABASES = {'default': _database_config()}

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True
STATIC_URL = 'static/'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
