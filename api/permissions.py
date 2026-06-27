from __future__ import annotations

from django.conf import settings
from rest_framework import permissions


class IsWriteAuthenticated(permissions.BasePermission):
    """
    - Lecturas (GET/HEAD/OPTIONS): requieren sesión Django activa.
    - Escritura (POST/PATCH/PUT/DELETE): acepta sesión Django o Bearer token.
    """

    def has_permission(self, request, view):
        if request.user and request.user.is_authenticated:
            return True

        if request.method in permissions.SAFE_METHODS:
            return False

        auth = request.META.get("HTTP_AUTHORIZATION", "")
        if auth.startswith("Bearer "):
            token = auth.split(" ", 1)[1].strip()
            expected = getattr(settings, "M360_API_KEY", "")
            return bool(expected and token == expected)

        return False
