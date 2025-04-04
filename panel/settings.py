# panel/settings.py
import os
from pathlib import Path
from .secrets import EMAIL_HOST_USER, EMAIL_HOST_PASSWORD, DATABASE_HOST, HOST_PASSWORD, DATABASE_USER

# Base Configuration
BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = os.environ.get('SECRET_KEY', default='your-secret-key-here')
DEBUG = 'RENDER' not in os.environ
ALLOWED_HOSTS = ['*']

if RENDER_EXTERNAL_HOSTNAME := os.environ.get('RENDER_EXTERNAL_HOSTNAME'):
    ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)

# Application Definition
INSTALLED_APPS = [
    # Third-party Apps
    'rest_framework',
    'daphne',
    'channels',
    'crispy_forms',
    'crispy_bootstrap5',
    'widget_tweaks',
    
    # Django Core Apps
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Local Apps
    'accounts.apps.AccountsConfig',
    'events.apps.EventsConfig',
    'chat',
    'tools',
    'rooms',
    'memento.apps.MementoConfig',
    'cv.apps.CvConfig',
    'kpis.apps.KpisConfig',
    'passgen',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'panel.middleware.DatabaseSelectorMiddleware',
]

ROOT_URLCONF = 'panel.urls'

TEMPLATES = [{
    'BACKEND': 'django.template.backends.django.DjangoTemplates',
    'DIRS': [],
    'APP_DIRS': True,
    'OPTIONS': {
        'context_processors': [
            'django.template.context_processors.debug',
            'django.template.context_processors.request',
            'django.contrib.auth.context_processors.auth',
            'django.contrib.messages.context_processors.messages',
        ],
    },
}]

# ASGI/Channels Configuration
ASGI_APPLICATION = 'panel.asgi.application'
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [("redis://:123456@192.168.18.49:6379/1")],
            "symmetric_encryption_keys": [SECRET_KEY],
        },
    }
}

# Database Configuration
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'projects',
        'USER': DATABASE_USER,
        'PASSWORD': HOST_PASSWORD,
        'HOST': DATABASE_HOST,
        'PORT': '3306',
        'OPTIONS': {'charset': 'utf8mb4'},
    },
    'sqlite': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    },
}

# Authentication
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = False

# Static Files
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']
if not DEBUG:
    STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Media Files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Email Configuration
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = "smtp.gmail.com"
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = EMAIL_HOST_USER
EMAIL_HOST_PASSWORD = EMAIL_HOST_PASSWORD

# Miscellaneous Settings
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
CRISPY_TEMPLATE_PACK = 'bootstrap5'
LOGIN_REDIRECT_URL = 'home'