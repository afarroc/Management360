# En tu archivo middleware.py
from django.db import connections
from django.db.utils import OperationalError
import logging

logger = logging.getLogger(__name__)

class DatabaseSelectorMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        for db in ['default',  'postgres_online', 'sqlite']:
            try:
                logger.info(f"Intentando conectar a la base de datos '{db}'")
                connections[db].ensure_connection()
                request.database_to_use = db
                break
            except OperationalError:
                logger.warning(f"No se pudo conectar a la base de datos '{db}', intentando la siguiente")
                continue

        response = self.get_response(request)

        return response
