"""
Dashboard Utilities Module

Utilidades y funciones helper para el dashboard root.
"""

import logging
from typing import Dict, Any
from django.utils import timezone

logger = logging.getLogger(__name__)


def check_root_access(user) -> bool:
    """
    Verifica si el usuario tiene acceso al panel root basado en múltiples criterios
    """
    # Superusuario siempre tiene acceso
    if user.is_superuser:
        return True

    # Verificar rol en perfil si existe
    if hasattr(user, 'profile') and user.cv:
        role = getattr(user.cv, 'role', None)
        # Roles con acceso al panel root - más permisivo
        allowed_roles = ['SU', 'ADMIN', 'GTD_ANALYST', 'SYS_ADMIN', 'USER', 'STAFF']
        if role and role in allowed_roles:
            return True

    # Verificar permisos específicos de Django
    if user.has_perm('events.view_inboxitem') or user.has_perm('events.change_inboxitem'):
        return True

    # Verificar si es staff con permisos específicos
    if user.is_staff:
        return True

    # Usuarios autenticados con perfil pueden acceder (más permisivo)
    if hasattr(user, 'profile') and user.is_authenticated:
        return True

    # Usuarios autenticados activos pueden acceder como fallback
    if user.is_authenticated and user.is_active:
        return True

    return False


def get_responsive_grid_classes() -> Dict[str, str]:
    """
    Genera clases CSS responsivas optimizadas para el layout de 12 contenedores
    """
    return {
        # Layout principal de 12 contenedores en grid
        'main_grid': 'grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4 p-4',

        # Contenedores individuales con tamaños responsivos
        'container_small': 'col-span-1 bg-white rounded-lg shadow-md p-4 hover:shadow-lg transition-shadow duration-200',
        'container_medium': 'col-span-1 md:col-span-2 bg-white rounded-lg shadow-md p-4 hover:shadow-lg transition-shadow duration-200',
        'container_large': 'col-span-1 md:col-span-2 lg:col-span-3 bg-white rounded-lg shadow-md p-4 hover:shadow-lg transition-shadow duration-200',
        'container_full': 'col-span-1 md:col-span-2 lg:col-span-3 xl:col-span-4 bg-white rounded-lg shadow-md p-4 hover:shadow-lg transition-shadow duration-200',

        # Contenedores específicos para diferentes tipos de contenido
        'user_info_container': 'col-span-1 md:col-span-2 lg:col-span-3 bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg shadow-md p-4 border-l-4 border-blue-500',
        'stats_container': 'col-span-1 bg-white rounded-lg shadow-md p-4 hover:shadow-lg transition-shadow duration-200',
        'inbox_container': 'col-span-1 md:col-span-2 lg:col-span-3 xl:col-span-4 bg-white rounded-lg shadow-md p-4',
        'email_backend_container': 'col-span-1 md:col-span-2 bg-gray-50 rounded-lg shadow-md p-4 border-l-4 border-green-500',

        # Clases para elementos internos responsivos
        'responsive_text': 'text-sm md:text-base',
        'responsive_table': 'w-full text-xs md:text-sm overflow-x-auto',
        'responsive_button': 'px-2 py-1 md:px-4 md:py-2 text-xs md:text-sm',
        'responsive_input': 'w-full px-2 py-1 md:px-3 md:py-2 text-xs md:text-sm border rounded',

        # Utilidades para ocultar/mostrar en diferentes breakpoints
        'hidden_mobile': 'hidden md:block',
        'hidden_tablet': 'hidden lg:block',
        'hidden_desktop': 'block xl:hidden',

        # Espaciado responsivo
        'spacing_mobile': 'space-y-2 md:space-y-4',
        'spacing_desktop': 'space-y-4 lg:space-y-6',
    }


def handle_dashboard_error(view_func):
    """
    Decorator para manejo consistente de errores en vistas del dashboard
    """
    def wrapper(request, *args, **kwargs):
        try:
            return view_func(request, *args, **kwargs)
        except Exception as e:
            logger.error(f"Error in {view_func.__name__}: {str(e)}", exc_info=True)
            from django.contrib import messages
            from django.shortcuts import redirect
            messages.error(request, f'Error inesperado en {view_func.__name__}. Contacte al administrador.')
            return redirect('dashboard')
    return wrapper


def log_dashboard_access(user, action: str, details: Dict[str, Any] = None):
    """
    Registrar acceso al dashboard para auditoría
    """
    details_str = f" - {details}" if details else ""
    logger.info(f"Dashboard access: User {user.username} performed {action}{details_str}")


def validate_dashboard_params(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validar parámetros del dashboard con sanitización
    """
    validated = {}

    # Validar y sanitizar búsqueda
    search = params.get('search', '').strip()
    if len(search) > 100:  # Limitar longitud
        search = search[:100]
    validated['search'] = search

    # Validar fechas
    for date_field in ['date_from', 'date_to']:
        date_str = params.get(date_field, '').strip()
        if date_str:
            try:
                # Intentar parsear la fecha
                from datetime import datetime
                datetime.strptime(date_str, '%Y-%m-%d')
                validated[date_field] = date_str
            except ValueError:
                logger.warning(f"Invalid date format for {date_field}: {date_str}")
                validated[date_field] = ''
        else:
            validated[date_field] = ''

    # Validar números enteros con límites
    for int_field in ['page', 'per_page']:
        try:
            value = int(params.get(int_field, 1))
            if int_field == 'page':
                validated[int_field] = max(1, value)
            elif int_field == 'per_page':
                validated[int_field] = max(1, min(value, 100))
        except (ValueError, TypeError):
            validated[int_field] = 1 if int_field == 'page' else 20

    # Validar opciones de selección
    valid_choices = {
        'status': ['all', 'processed', 'unprocessed'],
        'content_type': ['all', 'email', 'call', 'chat'],
        'priority': ['all', 'alta', 'media', 'baja'],
        'sort': ['created_at', 'updated_at', 'title', 'priority'],
        'order': ['asc', 'desc']
    }

    for field, choices in valid_choices.items():
        value = params.get(field, choices[0])
        validated[field] = value if value in choices else choices[0]

    return validated


def get_dashboard_cache_key(user, filters: Dict[str, Any], prefix: str = 'dashboard') -> str:
    """
    Generar clave de caché consistente para el dashboard
    """
    # Crear hash determinístico de los filtros
    import hashlib
    filter_str = str(sorted(filters.items()))
    filter_hash = hashlib.md5(filter_str.encode()).hexdigest()[:8]

    return f"{prefix}_{user.id}_{filter_hash}"


def invalidate_dashboard_cache(user, pattern: str = None):
    """
    Invalidar caché del dashboard para un usuario
    """
    from django.core.cache import cache

    if pattern:
        # Invalidar patrón específico
        cache.delete_pattern(f"{pattern}_{user.id}_*")
    else:
        # Invalidar todo el caché del usuario
        cache.delete_pattern(f"*_{user.id}_*")