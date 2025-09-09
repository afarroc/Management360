import logging
from django.db import connections
from django.db.utils import OperationalError

logger = logging.getLogger(__name__)

class DatabaseSelectorMiddleware:
    """
    Middleware to ensure database connection is available.
    Sets `request.database_to_use` to 'default'.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        """
        Ensures the default database connection is available.
        Sets `request.database_to_use` to 'default'.
        """
        try:
            connections['default'].ensure_connection()
            request.database_to_use = 'default'
            logger.info("Connected to database: default")
        except OperationalError as e:
            logger.error(f"Database connection failed (default): {str(e)}")
        return self.get_response(request)