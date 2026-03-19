# analyst/constants.py
"""
Constantes para la aplicación analyst
"""

# Modelos prohibidos
FORBIDDEN_MODELS = {
    'auth.Permission': 'auth.Permission',
    'auth.User': 'auth.User',
    'auth.Group': 'auth.Group',
    'admin.LogEntry': 'django.contrib.admin.LogEntry',
    'contenttypes.ContentType': 'contenttypes.ContentType',
    'sessions.Session': 'sessions.Session'
}

# Formatos permitidos para nombres de modelo
ALLOWED_MODEL_FORMATS = [
    r'^[a-z][a-z0-9_]*\.[a-z][a-z0-9_]*$',  # app.model
    r'^[a-z][a-z0-9_]*(\.[a-z][a-z0-9_]*)+$'  # app.subapp.model
]

# Límites de seguridad
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
MAX_RECORDS_FOR_DELETION = 1000
MAX_RECORDS_FOR_IMPORT = 10000
MAX_SESSION_DATA_SIZE = 4 * 1024 * 1024  # 4MB
DEFAULT_CHUNK_SIZE = 1000

# Configuraciones de procesamiento
DATE_FORMATS = [
    ('%Y-%m-%d', 'YYYY-MM-DD (2024-01-31)'),
    ('%d/%m/%Y', 'DD/MM/YYYY (31/01/2024)'),
    ('%m/%d/%Y', 'MM/DD/YYYY (01/31/2024)'),
    ('%Y%m%d', 'YYYYMMDD (20240131)'),
    ('%d-%m-%Y', 'DD-MM-YYYY (31-01-2024)'),
    ('infer', 'Inferir automáticamente'),
]

# Mensajes de error
ERROR_MESSAGES = {
    'session_expired': 'La sesión ha expirado. Por favor, suba el archivo nuevamente.',
    'no_data': 'No hay datos para procesar.',
    'invalid_file': 'El archivo no es válido o está vacío.',
    'model_not_found': 'El modelo seleccionado no existe.',
    'permission_denied': 'No tiene permisos para realizar esta operación.',
}