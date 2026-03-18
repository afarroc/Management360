"""
Dashboard Utils Package
Utilidades y funciones helper centralizadas para toda la aplicación
"""

# ============================================================================
# IMPORTACIONES DE SUBSISTEMAS
# ============================================================================

# Gestión de perfiles y usuarios
from .profile_utils import (
    create_user_profile,
    get_user_role,
    is_superuser_role,
    has_dashboard_access
)

# Gestión de créditos y finanzas
from .credit_utils import (
    add_credits_to_user,
    ensure_credit_account,
    get_credit_balance,
    deduct_credits,
    format_currency
)

# Gestión de tiempo y fechas (Memento Mori)
from .time_utils import (
    memento_mori,
    get_date_range,
    format_date,
    get_relative_time,
    get_week_range,
    get_month_range
)

# Estadísticas y gráficos del dashboard
from .chart_utils import (
    get_bar_chart_data,
    get_line_chart_data,
    get_duration_chart_data,
    get_combined_chart_data,
    get_task_states_with_duration,
    filter_data_last_month,
    count_created_per_day,
    fill_data_for_dates
)

# Tarjetas de métricas y KPIs
from .metric_utils import (
    get_card_data,
    calculate_percentage_increase,
    get_metric_trend,
    format_percentage,
    format_metric_value
)

# Utilidades de dashboard root
from .dashboard_utils import (
    check_root_access,
    get_responsive_grid_classes,
    handle_dashboard_error,
    log_dashboard_access,
    validate_dashboard_params,
    get_dashboard_cache_key,
    invalidate_dashboard_cache
)

# Utilidades GTD (Getting Things Done)
from .gtd_utils import (
    verify_inbox_links,
    fix_broken_links,
    get_inbox_statistics,
    classify_inbox_item,
    create_from_inbox
)

# Utilidades de estados
from .status_utils import (
    statuses_get,
    get_default_status,
    get_active_status,
    ensure_default_statuses,
    update_status,
)

# Creación consistente de proyectos
from .project_utils import (
    create_consistent_project,
    get_project_alerts
)

# Utilidades de permisos y validación
from .permission_utils import (
    has_event_permission,
    can_edit_event,
    get_editable_events,
    is_superuser,
    has_role,
    check_edit_permissions
)

# Importar utilidades de managers
from .managers import (
    get_managers_for_user,
    get_manager_by_type
)
# ============================================================================
# EXPORTACIONES PÚBLICAS
# ============================================================================

__all__ = [
    # Perfiles
    'create_user_profile',
    'get_user_role',
    'is_superuser_role',
    'has_dashboard_access',
    
    # Créditos
    'add_credits_to_user',
    'ensure_credit_account',
    'get_credit_balance',
    'deduct_credits',
    'format_currency',
    
    # Tiempo
    'memento_mori',
    'get_date_range',
    'format_date',
    'get_relative_time',
    'get_week_range',
    'get_month_range',
    
    # Gráficos
    'get_bar_chart_data',
    'get_line_chart_data',
    'get_duration_chart_data',
    'get_combined_chart_data',
    'get_task_states_with_duration',
    'filter_data_last_month',
    'count_created_per_day',
    'fill_data_for_dates',
    
    # Métricas
    'get_card_data',
    'calculate_percentage_increase',
    'get_metric_trend',
    'format_percentage',
    'format_metric_value',
    
    # Dashboard Root
    'check_root_access',
    'get_responsive_grid_classes',
    'handle_dashboard_error',
    'log_dashboard_access',
    'validate_dashboard_params',
    'get_dashboard_cache_key',
    'invalidate_dashboard_cache',
    
    # GTD
    'verify_inbox_links',
    'fix_broken_links',
    'get_inbox_statistics',
    'classify_inbox_item',
    'create_from_inbox',
    
    # Estados
    'statuses_get',
    'get_default_status',
    'get_active_status',
    'ensure_default_statuses',
    'update_status',
    
    # Proyectos
    'create_consistent_project',
    'get_project_alerts',
    # Permisos
    'has_event_permission',
    'can_edit_event',
    'get_editable_events',
    'is_superuser',
    'has_role',
    'check_edit_permissions',
    
    # Managers
    'get_managers_for_user',
    'get_manager_by_type',
]