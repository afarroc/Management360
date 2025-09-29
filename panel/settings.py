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
DEBUG = config('DEBUG', default=False, cast=bool)
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost,127.0.0.1,192.168.18.46,192.168.18.47').split(',')

if RENDER_EXTERNAL_HOSTNAME := os.environ.get('RENDER_EXTERNAL_HOSTNAME'):
    ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)
    # Ensure WebSockets allowed from external host
    CSRF_TRUSTED_ORIGINS = [f"https://{RENDER_EXTERNAL_HOSTNAME}"]

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
    'bots',
    'help.apps.HelpConfig',
    'memento.apps.MementoConfig',
    'cv.apps.CvConfig',
    'kpis.apps.KpisConfig',
    'passgen',
    'courses.apps.CoursesConfig',
    'campaigns.apps.CampaignsConfig',
    
    'django.contrib.humanize',
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
            BASE_DIR / 'core/templates',
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

# Redis Configuration (for both Django and Channels)
REDIS_HOST = config('REDIS_HOST', default='localhost')
REDIS_PORT = config('REDIS_PORT', default=6379, cast=int)
REDIS_PASSWORD = config('REDIS_PASSWORD', default='')
REDIS_DB = config('REDIS_DB', default=0, cast=int)

# For standard Redis connections
REDIS_URL = f"redis://:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}"

# WebSocket configuration
ASGI_APPLICATION = 'panel.asgi.application'

# Channel Layers Configuration
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [os.environ.get('REDIS_URL', REDIS_URL)],
        },
    }
}

# Production settings for secure WebSocket connections
if not DEBUG:
    CHANNEL_LAYERS['default']['CONFIG']['hosts'] = [
        {
            'address': f"rediss://:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}",
            'ssl_cert_reqs': None
        }
    ]
    # Ensure secure cookies and trusted origins for WebSockets
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    CSRF_TRUSTED_ORIGINS = [f"https://{RENDER_EXTERNAL_HOSTNAME}"] if RENDER_EXTERNAL_HOSTNAME else []

# Configuración de la base de datos
if DEBUG:
    # Configuración para desarrollo (MySQL en servidor remoto)
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.mysql',
            'NAME': config('DATABASE_NAME', default='management360'),
            'USER': config('DATABASE_USER', default='root'),
            'PASSWORD': config('DATABASE_PASSWORD', default=''),
            'HOST': config('DATABASE_HOST', default='192.168.18.46'),
            'PORT': config('DATABASE_PORT', default='3306'),
            'OPTIONS': {'charset': 'utf8mb4'},
        }
    }
else:
    # Configuración para producción (PostgreSQL en Render)
    DATABASES = {
        'default': dj_database_url.config(
            default=config('DATABASE_URL'),  # Lee de variable de entorno
            conn_max_age=600,
            ssl_require=True
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

# WhiteNoise configuration
if DEBUG:
    # En desarrollo: usar WhiteNoise pero permitir autorefresh
    STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
    WHITENOISE_USE_FINDERS = True
    WHITENOISE_AUTOREFRESH = True
else:
    # En producción: optimizar con WhiteNoise
    STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
    WHITENOISE_USE_FINDERS = True
    WHITENOISE_AUTOREFRESH = False

# Media Files - Ahora servidos desde servidor remoto en Termux
MEDIA_URL = 'http://192.168.18.46:8000/'
# MEDIA_ROOT = BASE_DIR / 'media'  # No needed with custom storage

# Custom storage for uploading directly to remote server
DEFAULT_FILE_STORAGE = 'panel.storages.RemoteMediaStorage'

# Force RemoteMediaStorage initialization
from django.core.files.storage import default_storage
from panel.storages import RemoteMediaStorage

# Replace the default storage with our custom one
if not isinstance(default_storage, RemoteMediaStorage):
    print("=== FORCING REMOTE MEDIA STORAGE ===")
    default_storage._wrapped = RemoteMediaStorage()
    print("RemoteMediaStorage forced successfully")

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

# Email Reception Configuration (for CX processing)
EMAIL_RECEPTION_ENABLED = config('EMAIL_RECEPTION_ENABLED', default=False, cast=bool)
EMAIL_IMAP_HOST = config('EMAIL_IMAP_HOST', default='imap.gmail.com')
EMAIL_IMAP_PORT = config('EMAIL_IMAP_PORT', default=993, cast=int)
EMAIL_IMAP_USER = config('EMAIL_IMAP_USER', default=EMAIL_HOST_USER)
EMAIL_IMAP_PASSWORD = config('EMAIL_IMAP_PASSWORD', default=EMAIL_HOST_PASSWORD)
EMAIL_CX_FOLDER = config('EMAIL_CX_FOLDER', default='INBOX/CX')  # Carpeta específica para CX
EMAIL_CHECK_INTERVAL = config('EMAIL_CHECK_INTERVAL', default=300, cast=int)  # 5 minutos por defecto

# CX Email Processing
CX_EMAIL_DOMAINS = config('CX_EMAIL_DOMAINS', default='@cliente.com,@support.com').split(',')
CX_KEYWORDS = config('CX_KEYWORDS', default='cambio de plan,modificar plan,actualizar plan,solicitud,queja,reclamo').split(',')

# Logging Configuration
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
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
        'file': {
            'class': 'logging.FileHandler',
            'filename': 'django.log',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': 'INFO',
    },
    'loggers': {
        'events': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

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