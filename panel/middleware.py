import logging
from django.db import connections
from django.db.utils import OperationalError

logger = logging.getLogger(__name__)

class DatabaseSelectorMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.db_order = ['default', 'postgres_online', 'sqlite']  # Configurable priority

    def __call__(self, request):
        for db in self.db_order:
            try:
                connections[db].ensure_connection()
                request.database_to_use = db
                logger.info(f"Connected to database: {db}")
                break
            except OperationalError as e:
                logger.warning(f"Database connection failed ({db}): {str(e)}")
                continue

        return self.get_response(request)