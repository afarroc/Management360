"""
Dashboard Utils Package

Utilidades y funciones helper para el dashboard root y otras funcionalidades.
"""

# Importar funciones del módulo original utils.py (directorio padre)
try:
    from ..utils import create_user_profile
except ImportError:
    # Fallback si no se puede importar
    create_user_profile = None

# Importar funciones del módulo dashboard_utils.py
from .dashboard_utils import (
    check_root_access,
    get_responsive_grid_classes,
    handle_dashboard_error,
    log_dashboard_access,
    validate_dashboard_params,
    get_dashboard_cache_key,
    invalidate_dashboard_cache
)

__all__ = [
    # Funciones originales
    'create_user_profile',
    # Funciones del dashboard
    'check_root_access',
    'get_responsive_grid_classes',
    'handle_dashboard_error',
    'log_dashboard_access',
    'validate_dashboard_params',
    'get_dashboard_cache_key',
    'invalidate_dashboard_cache'
]