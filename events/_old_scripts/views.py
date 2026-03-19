# events/views.py - ARCHIVO PRINCIPAL REFACTORIZADO (VERSIÓN FINAL)
# ============================================================================
# Este archivo ahora actúa únicamente como punto de entrada unificado
# que importa y re-exporta todas las vistas desde sus módulos especializados.
# ============================================================================

import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.utils import timezone

# ============================================================================
# IMPORTACIONES DE UTILIDADES COMPARTIDAS
# ============================================================================

from .my_utils import statuses_get
from .utils.chart_utils import get_optimized_chart_data
from .utils.status_utils import update_status
from .utils.schedule_utils import log_schedule_changes
from .management.utils import add_credits_to_user

# ============================================================================
# IMPORTACIÓN DE MODELOS (para mantener disponibilidad en el namespace)
# ============================================================================

from .models import (
    Event, Project, Task, Status,
    ProjectStatus, TaskStatus, EventState, TaskState,
    EventAttendee, TaskDependency,
    Classification, TagCategory, Tag,
    ProjectTemplate, TemplateTask,
    InboxItem, InboxItemClassification, InboxItemAuthorization, InboxItemHistory,
    TaskSchedule, TaskProgram,
    Reminder,
    GTDProcessingSettings
)

# ============================================================================
# IMPORTACIÓN DE FORMULARIOS (para mantener disponibilidad en el namespace)
# ============================================================================

from .forms import (
    CreateNewEvent, CreateNewProject, CreateNewTask,
    EventStatusForm, TaskStatusForm, ProjectStatusForm,
    EditClassificationForm,
    ProjectTemplateForm, TemplateTaskForm, TemplateTaskFormSet,
    ReminderForm, TaskScheduleForm
)

# ============================================================================
# IMPORTACIÓN DE MANAGERS (para mantener disponibilidad en el namespace)
# ============================================================================

from .management.event_manager import EventManager
from .management.project_manager import ProjectManager
from .management.task_manager import TaskManager

# ============================================================================
# IMPORTACIÓN DE VISTAS ESPECIALIZADAS - MÓDULOS PRINCIPALES
# ============================================================================

# Vistas de eventos
from .events_views import *

# Vistas de proyectos
from .projects_views import *

# Vistas de tareas
from .tasks_views import *

# Vistas GTD (Getting Things Done)
from .gtd_views import *

# ============================================================================
# IMPORTACIÓN DE VISTAS ESPECIALIZADAS - NUEVOS MÓDULOS
# ============================================================================

# Gestión de estados
from .status_views import *

# Gestión de clasificaciones
from .classification_views import *

# Tableros Kanban
from .kanban_views import *

# Matriz de Eisenhower
from .eisenhower_views import *

# Plantillas de proyectos
from .templates_views import *

# Dependencias entre tareas
from .dependencies_views import *

# Programaciones y horarios
from .schedules_views import *

# Recordatorios
from .reminders_views import *

# Gestión de créditos
from .credits_views import *

# Dashboards unificados
from .dashboard_views import *

# Bots y automatizaciones
from .bot_views import *

# Vistas de prueba
from .test_views import *

# ============================================================================
# VISTAS BASE (MANTENIDAS EN EL ARCHIVO PRINCIPAL)
# ============================================================================

logger = logging.getLogger(__name__)


def index(request):
    """
    Vista principal del dashboard.
    """
    # Redirigir al dashboard unificado si el usuario está autenticado
    if request.user.is_authenticated:
        return redirect('unified_dashboard')
    return redirect('login')


def dashboard(request):
    """
    Dashboard principal.
    Redirige al dashboard unificado para mantener compatibilidad.
    """
    if request.user.is_authenticated:
        return redirect('unified_dashboard')
    return redirect('login')


# ============================================================================
# NOTA: 
# Todas las demás vistas han sido movidas a sus módulos especializados:
# - events_views.py       → Vistas de eventos
# - projects_views.py     → Vistas de proyectos
# - tasks_views.py        → Vistas de tareas
# - gtd_views.py          → Vistas GTD (inbox, procesamiento)
# - status_views.py       → Gestión de estados
# - classification_views.py → Gestión de clasificaciones
# - kanban_views.py       → Tableros Kanban
# - eisenhower_views.py   → Matriz de Eisenhower
# - templates_views.py    → Plantillas de proyectos
# - dependencies_views.py → Dependencias entre tareas
# - schedules_views.py    → Programaciones y horarios
# - reminders_views.py    → Recordatorios
# - credits_views.py      → Gestión de créditos
# - dashboard_views.py    → Dashboards unificados
# - bot_views.py          → Bots y automatizaciones
# - test_views.py         → Vistas de prueba
# ============================================================================

# ============================================================================
# EXPORTACIONES PARA FACILITAR EL ACCESO DESDE URLS.PY
# ============================================================================

# Esta sección lista explícitamente las vistas más comunes para facilitar
# las importaciones en urls.py, aunque todas están disponibles a través de
# los import * anteriores.

__all__ = [
    # Vistas base
    'index', 'dashboard',
    
    # Vistas de eventos
    'events', 'event_detail', 'event_panel', 'event_create', 'event_edit',
    'event_assign', 'event_status_change', 'assign_attendee_to_event',
    'event_delete', 'event_bulk_action', 'event_export', 'event_history',
    'update_event', 'panel',
    
    # Vistas de proyectos
    'projects', 'project_panel', 'project_detail', 'project_create',
    'project_edit', 'project_delete', 'change_project_status',
    'project_activate', 'project_bulk_action', 'project_export',
    'get_project_alerts_ajax', 'project_tasks_status_check',
    
    # Vistas de tareas
    'tasks', 'task_panel', 'task_create', 'task_edit', 'task_delete',
    'change_task_status', 'task_export', 'task_bulk_action',
    'task_change_status_ajax', 'task_activate',
    
    # Vistas GTD
    'inbox_view', 'event_inbox_panel', 'inbox_stats_api',
    'process_inbox_item', 'get_inbox_creation_options',
    'create_from_inbox_api', 'inbox_admin_dashboard',
    'inbox_item_detail_admin', 'classify_inbox_item_admin',
    'authorize_inbox_item', 'inbox_admin_bulk_action',
    'get_available_tasks', 'get_available_projects',
    'inbox_management_panel', 'update_processing_settings',
    'get_queue_data', 'get_email_queue_items', 'get_call_queue_items',
    'get_chat_queue_items', 'process_queue', 'assign_interaction_to_agent',
    'mark_interaction_resolved', 'assign_inbox_item_api',
    'create_inbox_item_api', 'inbox_link_checker',
    
    # Vistas de estados
    'status', 'status_edit', 'status_create', 'status_delete',
    
    # Vistas de clasificaciones
    'create_Classification', 'edit_Classification', 'delete_Classification',
    'Classification_list',
    
    # Vistas Kanban
    'kanban_board_unified', 'kanban_project',
    
    # Vistas Eisenhower
    'eisenhower_matrix', 'move_task_eisenhower',
    
    # Vistas de plantillas
    'project_templates', 'create_project_template', 'project_template_detail',
    'edit_project_template', 'delete_project_template', 'use_project_template',
    
    # Vistas de dependencias
    'task_dependencies', 'create_task_dependency', 'delete_task_dependency',
    'task_dependency_graph',
    
    # Vistas de programaciones
    'planning_task', 'task_programs_calendar', 'task_schedules',
    'create_task_schedule', 'task_schedule_detail', 'edit_task_schedule',
    'task_schedule_preview', 'delete_task_schedule',
    'generate_schedule_occurrences', 'user_schedules_panel',
    'schedule_admin_dashboard', 'schedule_admin_bulk_action',
    'TaskScheduleEditView',
    
    # Vistas de recordatorios
    'reminders_dashboard', 'create_reminder', 'edit_reminder',
    'delete_reminder', 'mark_reminder_sent', 'bulk_reminder_action',
    
    # Vistas de créditos
    'add_credits',
    
    # Vistas de dashboards
    'unified_dashboard', 'root', 'root_bulk_actions', 'management_index',
    
    # Vistas de bots
    'check_new_emails_api', 'activate_bot', 'process_cx_emails_api',
    
    # Vistas de prueba
    'test_board',
]

# ============================================================================
# FIN DEL ARCHIVO - TODAS LAS VISTAS ESTÁN AHORA EN MÓDULOS ESPECIALIZADOS
# ============================================================================