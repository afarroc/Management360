import logging
from django.db import connections
from django.db.utils import OperationalError

logger = logging.getLogger(__name__)

class DatabaseSelectorMiddleware:
    """
    Middleware to select an available database connection based on a priority order.
    Sets `request.database_to_use` to the first successfully connected database.
    """

    def __init__(self, get_response):
        self.get_response = get_response
        self.db_order = ['default', 'postgres_online', 'sqlite']  # Configurable priority

    def __call__(self, request):
        """
        Attempts to connect to databases in the specified order.
        Sets `request.database_to_use` to the first available database.
        Logs warnings for failed connections and an error if no connection is successful.
        """
        for db in self.db_order:
            try:
                connections[db].ensure_connection()
                request.database_to_use = db
                logger.info(f"Connected to database: {db}")
                break
            except OperationalError as e:
                logger.warning(f"Database connection failed ({db}): {str(e)}")
                continue
        else:
            logger.error("No database connection could be established.")
        return self.get_response(request)