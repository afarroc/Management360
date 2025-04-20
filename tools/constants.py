# constants.py
FORBIDDEN_MODELS = {
    # Modelos prohibidos con sus formatos específicos
    'auth.Permission': 'auth.Permission',
    'auth.User': 'auth.User',
    'auth.Group': 'auth.Group',
    'admin.LogEntry': 'django.contrib.admin.LogEntry',
    'contenttypes.ContentType': 'contenttypes.ContentType',
    'sessions.Session': 'sessions.Session'
}

# Formatos permitidos (expresiones regulares)
ALLOWED_MODEL_FORMATS = [
    r'^[a-z][a-z0-9_]*\.[a-z][a-z0-9_]*$',  # app.model
    r'^[a-z][a-z0-9_]*(\.[a-z][a-z0-9_]*)+$'  # app.subapp.model (múltiples puntos)
]

MAX_RECORDS_FOR_DELETION = 1000
MAX_RECORDS_FOR_IMPORT = 10000