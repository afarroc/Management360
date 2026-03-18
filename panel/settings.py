# panel/settings.py
import os
from pathlib import Path
from decouple import config  # Importa config desde python-decouple
import dj_database_url

# settings.py - Añade esta importación
from django.utils import timezone

# Base Configuration
BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = config('SECRET_KEY')
if not SECRET_KEY:
    raise ValueError("SECRET_KEY no está definido en las variables de entorno.")
DEBUG = config('DEBUG', default=False, cast=bool)
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost,127.0.0.1,192.168.18.46,192.168.18.47,testserver').split(',')

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
    'rooms',
    'bots',
    'help.apps.HelpConfig',
    'memento.apps.MementoConfig',
    'cv.apps.CvConfig',
    'kpis.apps.KpisConfig',
    'passgen',
    'courses.apps.CoursesConfig',
    'campaigns.apps.CampaignsConfig',
    'bitacora',
    'board.apps.BoardConfig',
    'analyst.apps.AnalystConfig',
    'sim',
    'simcity',
    
    'tinymce',

    # CKEditor apps (AGREGAR ESTAS)
    'django_ckeditor_5',
    'django.contrib.humanize',
]
# Tiempo de expiración para clips del portapapeles (en segundos)
CLIPBOARD_TIMEOUT = 3600  # 1 hora
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

# ── Cache – Redis with LocMemCache fallback ───────────────────────────────────
# Tries to connect to Redis at startup. If unavailable, falls back to
# LocMemCache so the server keeps running (clipboard/preview won't persist
# across workers but the site stays up).
# Requires: pip install django-redis
def _build_caches():
    import importlib
    _url = (
        f"rediss://:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}"
        if not DEBUG else
        f"redis://:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}"
    )
    try:
        importlib.import_module('django_redis')
        import redis as _redis
        _client = _redis.from_url(_url, socket_connect_timeout=2)
        _client.ping()
        print(f"✓ Redis cache: {_url}")
        return {
            'default': {
                'BACKEND': 'django_redis.cache.RedisCache',
                'LOCATION': _url,
                'OPTIONS': {
                    'CLIENT_CLASS': 'django_redis.client.DefaultClient',
                    'IGNORE_EXCEPTIONS': True,
                    'CONNECTION_POOL_KWARGS': {'max_connections': 20},
                    **({"SSL_CERT_REQS": None} if not DEBUG else {}),
                },
                'KEY_PREFIX': 'panel',
                'TIMEOUT': 1800,
            }
        }
    except Exception as e:
        print(f"⚠ Redis no disponible ({e}). Usando FileBasedCache como fallback.")
        print("  Preview/clipboard persisten en disco entre reinicios de Django.")
        import os as _os
        _cache_dir = _os.path.join(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))), '.django_cache')
        _os.makedirs(_cache_dir, exist_ok=True)
        return {
            'default': {
                'BACKEND': 'django.core.cache.backends.filebased.FileBasedCache',
                'LOCATION': _cache_dir,
                'TIMEOUT': None,   # datasets never expire; previews expire via explicit delete
                'OPTIONS': {
                    'MAX_ENTRIES': 2000,
                },
            }
        }

CACHES = _build_caches()

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
MEDIA_URL = 'http://192.168.18.51:8000/'
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

# Logging Configuration - VERSIÓN MEJORADA PARA DEPURACIÓN
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {asctime} {message}',
            'style': '{',
        },
        'detailed': {
            'format': '{levelname} {asctime} {name} {lineno} {funcName} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'detailed',
            'level': 'DEBUG',
        },
        'file': {
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'django.log',
            'formatter': 'verbose',
            'level': 'INFO',
        },
        'tools_file': {
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'tools_debug.log',
            'formatter': 'detailed',
            'level': 'DEBUG',
        },
        'error_file': {
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'error.log',
            'formatter': 'verbose',
            'level': 'ERROR',
        },
    },
    'root': {
        'handlers': ['console', 'file', 'error_file'],
        'level': 'INFO',
    },
    'loggers': {
        # Logger principal para tools
        'tools': {
            'handlers': ['console', 'tools_file', 'error_file'],
            'level': 'DEBUG',
            'propagate': False,
        },
        # Logger específico para data_upload
        'tools.data_upload': {
            'handlers': ['console', 'tools_file', 'error_file'],
            'level': 'DEBUG',
            'propagate': False,
        },
        # Logger para pandas
        'pandas': {
            'handlers': ['console', 'tools_file'],
            'level': 'INFO',
            'propagate': False,
        },
        # Logger para eventos (ya existente)
        'events': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': False,
        },
        # Logger para django
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'django.request': {
            'handlers': ['console', 'error_file'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'django.db.backends': {
            'handlers': ['console', 'file'],
            'level': 'INFO',  # Cambiar a DEBUG para ver queries SQL
            'propagate': False,
        },
    },
}

# Crear directorio de logs si no existe
import os
LOGS_DIR = BASE_DIR / 'logs'
if not os.path.exists(LOGS_DIR):
    try:
        os.makedirs(LOGS_DIR)
        print(f"✓ Directorio de logs creado en: {LOGS_DIR}")
    except Exception as e:
        print(f"✗ Error creando directorio de logs: {e}")

# Configuración específica para desarrollo
if DEBUG:
    # En desarrollo, mostrar más información
    LOGGING['loggers']['tools']['level'] = 'DEBUG'
    LOGGING['loggers']['tools.data_upload']['level'] = 'DEBUG'
    LOGGING['loggers']['pandas']['level'] = 'DEBUG'
    
    # Asegurar que los handlers tengan nivel DEBUG
    for handler in LOGGING['handlers'].values():
        if handler['class'] == 'logging.StreamHandler':
            handler['level'] = 'DEBUG'
    
    print("\n" + "="*60)
    print("🔧 MODO DEBUG ACTIVADO - LOGGING DETALLADO")
    print(f"📁 Archivos de log en: {LOGS_DIR}")
    print("="*60 + "\n")
else:
    # En producción, reducir nivel de logging
    LOGGING['loggers']['tools']['level'] = 'INFO'
    LOGGING['loggers']['tools.data_upload']['level'] = 'INFO'
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

# TinyMCE Configuration - VERSIÓN CORREGIDA
TINYMCE_DEFAULT_CONFIG = {
    'selector': 'textarea.tinymce-editor, textarea[name="contenido"]',
    'height': 600,
    'width': '100%',
    'menubar': 'file edit view insert format tools table help',
    'plugins': [
        'advlist', 'autolink', 'lists', 'link', 'image', 'charmap', 'preview', 'anchor', 'searchreplace',
        'visualblocks', 'code', 'fullscreen', 'insertdatetime', 'media', 'table', 'paste', 'codesample',
        'help', 'wordcount', 'emoticons', 'hr', 'pagebreak', 'nonbreaking', 'toc', 'template'
    ],
    'toolbar': 'undo redo | formatselect | bold italic underline strikethrough | '
               'forecolor backcolor | alignleft aligncenter alignright alignjustify | '
               'bullist numlist checklist | outdent indent | removeformat | '
               'link image media | emoticons charmap | code codesample | '
               'fullscreen preview | insertdatetime | table | hr pagebreak | '
               'template',
    'content_css': '/static/assets/css/style.css',
    'skin': 'oxide',
    'content_style': '''
        body { 
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif; 
            font-size: 14px; 
            line-height: 1.6;
        }
        .mce-content-body {
            padding: 20px;
        }
    ''',
    'branding': False,
    'resize': True,
    'image_advtab': True,
    'image_title': True,
    'automatic_uploads': True,
    'file_picker_types': 'image media',
    'paste_data_images': True,
    'images_upload_url': '/bitacora/upload-image/',
    'images_upload_credentials': True,
    'relative_urls': False,
    'remove_script_host': True,
    'convert_urls': True,
    'media_live_embeds': True,
    'templates': [
        {
            'title': 'Plantilla Personal',
            'description': 'Plantilla para reflexión personal',
            'content': '<h2>Reflexión Personal</h2><p><strong>Fecha:</strong> {{ fecha }}</p><p><strong>Estado de ánimo:</strong> </p><hr><p><strong>¿Qué aprendí hoy?</strong></p><p></p><p><strong>¿Qué puedo mejorar?</strong></p><p></p><p><strong>¿Qué agradezco?</strong></p><p></p>'
        },
        {
            'title': 'Plantilla Trabajo',
            'description': 'Plantilla para notas de trabajo',
            'content': '<h2>Nota de Trabajo</h2><p><strong>Proyecto:</strong> </p><p><strong>Tareas completadas:</strong></p><ul><li></li></ul><p><strong>Próximos pasos:</strong></p><ul><li></li></ul>'
        },
        {
            'title': 'Plantilla Meta',
            'description': 'Plantilla para establecimiento de metas',
            'content': '<h2>Meta Personal</h2><p><strong>Objetivo:</strong> </p><p><strong>Fecha límite:</strong> </p><p><strong>Pasos a seguir:</strong></p><ol><li></li><li></li><li></li></ol><p><strong>Recursos necesarios:</strong></p><ul><li></li></ul>'
        }
    ],
    'template_replace_values': {
        'fecha': timezone.now().strftime('%d/%m/%Y')
    }
}

# Configuración específica para bitácora
BITACORA_CONFIG = {
    'IMAGE_UPLOAD_PATH': 'bitacora/images/',
    'IMAGE_MAX_SIZE': 5 * 1024 * 1024,  # 5MB
    'ALLOWED_IMAGE_TYPES': ['image/jpeg', 'image/png', 'image/gif', 'image/webp'],
    'CONTENT_BLOCKS_ENABLED': True,
    'TEMPLATES_ENABLED': True,
    'STRUCTURED_CONTENT_ENABLED': True,
}

# Al final del archivo, antes de las configuraciones de TinyMCE

# HTMX Configuration
INSTALLED_APPS += ['django_htmx']  # Agrega esta línea

# ── Analyst ETL — Seguridad ───────────────────────────────────────────────────
# Apps cuyos modelos son accesibles via ETL.
# Lista vacía [] = todas las apps no excluidas por el sistema (auth, admin, etc.)
# Lista con apps = solo esas apps son visibles en el selector de modelos.
# Ejemplo restrictivo: ANALYST_ETL_ALLOWED_APPS = ['crm', 'events', 'analyst']
ANALYST_ETL_ALLOWED_APPS = []  # [] = todas las no-excluidas

# Máximo de filas que puede extraer un usuario no-superuser (0 = sin límite solo para superusers)
ANALYST_ETL_MAX_ROWS = 100_000

# Board App Configuration
BOARD_CONFIG = {
    'CARDS_PER_PAGE': 12,
    'ALLOWED_IMAGE_TYPES': ['image/jpeg', 'image/png', 'image/gif', 'image/webp'],
    'MAX_IMAGE_SIZE': 10 * 1024 * 1024,  # 10MB
    'ENABLE_WEBSOCKETS': True,
}

# Custom user model
AUTH_USER_MODEL = 'accounts.User'

# Custom user model
AUTH_USER_MODEL = 'accounts.User'
