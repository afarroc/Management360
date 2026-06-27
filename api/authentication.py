from __future__ import annotations

from django.conf import settings
from rest_framework.authentication import BaseAuthentication
from rest_framework import exceptions


class BearerAuthentication(BaseAuthentication):
    keyword = "Bearer"

    def authenticate(self, request):
        auth = request.META.get("HTTP_AUTHORIZATION", "")
        parts = auth.split(" ", 1)
        if len(parts) != 2 or parts[0].lower() != self.keyword.lower():
            return None

        token = parts[1].strip()
        expected = getattr(settings, "M360_API_KEY", "")
        if not expected or token != expected:
            return None

        # No asociamos usuario Django; la validación queda en el permiso.
        return (None, token)


class BearerAPIAccess(exceptions.APIException):
    status_code = 403
    default_detail = "Bearer token inválido o ausente."
    default_code = "invalid_bearer"
