import logging

from django.db import connections
from django.db.utils import OperationalError

logger = logging.getLogger(__name__)


class DatabaseSelectorMiddleware:
    """
    Intenta conectar a las BD en orden de prioridad y setea
    `request.database_to_use` con el primer alias disponible.

    Nota: solo se incluyen aliases definidos en settings.DATABASES.
    Aliases inexistentes generan KeyError antes de OperationalError.
    """

    def __init__(self, get_response):
        self.get_response = get_response
        self.db_order = ['default']  # Ampliar solo si se agregan aliases en DATABASES

    def __call__(self, request):
        for db in self.db_order:
            try:
                connections[db].ensure_connection()
                request.database_to_use = db
                break
            except (OperationalError, KeyError) as e:
                logger.warning(f"Database connection failed ({db}): {e}")
                continue
        else:
            logger.error("No database connection could be established.")

        return self.get_response(request)
