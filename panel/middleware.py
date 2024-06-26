# En tu archivo middleware.py
from django.db import connections
from django.db.utils import OperationalError

class DatabaseSelectorMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        for db in ['default', 'mysql2', 'sqlite']:
            try:
                connections[db].ensure_connection()
                request.database_to_use = db
                break
            except OperationalError:
                continue

        response = self.get_response(request)

        return response
