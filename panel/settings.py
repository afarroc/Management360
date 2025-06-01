# panel/settings.py
import os
from pathlib import Path
from decouple import config  # Importa config desde python-decouple
import dj_database_url

# Base Configuration
BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = config('SECRET_KEY')
if not SECRET_KEY:
    raise ValueError("SECRET_KEY no está definido en las variables de entorno.")
DEBUG = config('DEBUG', default=True, cast=bool)  # Mejor default=True para desarrollo
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost,127.0.0.1').split(',')

if RENDER_EXTERNAL_HOSTNAME := os.environ.get('RENDER_EXTERNAL_HOSTNAME'):
    ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)

# Application Definition
INSTALLED_APPS = [
    # Third-party Apps
    'daphne',
    'channels',
    'rest_framework',    
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
    
    # core
    'core.apps.CoreConfig',
    'api.apps.ApiConfig',
    
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

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            BASE_DIR / 'core/templates/layout', 
        ],
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

# ASGI/Channels Configuration
ASGI_APPLICATION = 'panel.asgi.application'

REDIS_HOST = config('REDIS_HOST', default='192.168.18.49')
REDIS_PORT = config('REDIS_PORT', default='6379')
REDIS_DB = config('REDIS_DB', default='1')
REDIS_PASSWORD = config('REDIS_PASSWORD', default='123456')

REDIS_URL = f"redis://:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}"
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [REDIS_URL],
            "symmetric_encryption_keys": [SECRET_KEY],
        },
    }
}

DATABASES = {
    'default': dj_database_url.config(
        default='postgresql://postgres:postgres@localhost:5432/mysite',
        conn_max_age=600
    )
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
USE_TZ = True

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
if DEBUG:
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'  # Display emails in the console
else:
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

EMAIL_HOST = config('EMAIL_HOST', default='smtp.gmail.com')
EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=True, cast=bool)
EMAIL_HOST_USER = config('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD')

# Miscellaneous Settings
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
CRISPY_TEMPLATE_PACK = 'bootstrap5'
LOGIN_REDIRECT_URL = 'home'

if not DEBUG:
    # Configuraciones de seguridad
    SECURE_HSTS_SECONDS = 31536000  # 1 año
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')  # Si usas proxy
    SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'