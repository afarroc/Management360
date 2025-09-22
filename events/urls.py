from django.urls import path, include
from . import views
from .setup_views import SetupView
import logging

# Configurar logger para debug de URLs
logger = logging.getLogger(__name__)

# ============================================================================
# URL PATTERNS FOR EVENTS MANAGEMENT SYSTEM
# ============================================================================
#
# This file contains all URL patterns for the Events Management System.
# The URLs are organized by functionality for better maintainability.
#
# Main sections:
# - Configuration and Setup
# - Main Dashboard and Overview
# - Events Management
# - Projects Management
# - Tasks Management
# - GTD (Getting Things Done) System
# - Productivity Tools (Kanban, Eisenhower)
# - Task Dependencies System
# - Project Templates System
# - Reminders and Notifications System
# - Configuration and Settings
# - Legacy Routes (backward compatibility)
#
# Naming convention:
# - Use descriptive names that indicate the action and resource
# - Include IDs in the URL pattern when needed
# - Group related functionality together
# - Use consistent patterns across similar resources
#
# Example:
# - /events/<id>/edit/ instead of /events/edit/<id>/
# - /projects/<project_id>/tasks/ for project-specific tasks
# - /api/ prefix for API endpoints
#
# ============================================================================

urlpatterns = [
    # ============================================================================
    # CONFIGURATION AND SETUP
    # ============================================================================
    path('setup/', SetupView.as_view(), name='setup'),
    path('credits/', views.add_credits, name='add_credits'),

    # ============================================================================
    # MAIN DASHBOARD AND OVERVIEW
    # ============================================================================
    path('dashboard/', views.unified_dashboard, name='unified_dashboard'),
    path('panel/', views.panel, name='panel'),
    path('management/', views.management_index, name='management_index'),

    # ============================================================================
    # EVENTS MANAGEMENT
    # ============================================================================
    path('events/', views.events, name='events'),
    path('events/create/', views.event_create, name='event_create'),
    path('events/<int:event_id>/', views.event_detail, name='event_detail'),
    path('events/<int:event_id>/edit/', views.event_edit, name='event_edit'),
    path('events/<int:event_id>/delete/', views.event_delete, name='event_delete'),
    path('events/<int:event_id>/status/', views.event_status_change, name='event_status_change'),
    path('events/<int:event_id>/assign/', views.event_assign, name='event_assign'),
    path('events/<int:event_id>/history/', views.event_history, name='event_history'),
    path('events/panel/', views.event_panel, name='event_panel'),
    path('events/panel/<int:event_id>/', views.event_panel, name='event_panel_with_id'),
    path('events/export/', views.event_export, name='event_export'),
    path('events/bulk-action/', views.event_bulk_action, name='event_bulk_action'),

    # ============================================================================
    # PROJECTS MANAGEMENT
    # ============================================================================
    path('projects/', views.projects, name='projects'),
    path('projects/create/', views.project_create, name='project_create'),
    path('projects/<int:project_id>/', views.projects, name='projects_with_id'),
    path('projects/<int:project_id>/detail/', views.project_detail, name='project_detail'),
    path('projects/<int:project_id>/edit/', views.project_edit, name='project_edit'),
    path('projects/<int:project_id>/delete/', views.project_delete, name='project_delete'),
    path('projects/<int:project_id>/activate/', views.project_activate, name='project_activate'),
    path('projects/<int:project_id>/status/', views.change_project_status, name='change_project_status'),
    path('projects/panel/', views.project_panel, name='project_panel'),
    path('projects/panel/<int:project_id>/', views.project_panel, name='project_panel_with_id'),
    path('projects/export/', views.project_export, name='project_export'),
    path('projects/bulk-action/', views.project_bulk_action, name='project_bulk_action'),
    path('projects/alerts/ajax/', views.get_project_alerts_ajax, name='project_alerts_ajax'),

    # ============================================================================
    # TASKS MANAGEMENT
    # ============================================================================
    path('tasks/', views.tasks, name='tasks'),
    path('tasks/create/', views.task_create, name='task_create'),
    path('tasks/<int:task_id>/', views.tasks, name='tasks_with_id'),
    path('tasks/<int:task_id>/edit/', views.task_edit, name='task_edit'),
    path('tasks/<int:task_id>/delete/', views.task_delete, name='task_delete'),
    path('tasks/<int:task_id>/activate/', views.task_activate, name='task_activate'),
    path('tasks/<int:task_id>/status/', views.change_task_status, name='change_task_status'),
    path('tasks/<int:task_id>/dependencies/', views.task_dependencies, name='task_dependencies'),
    path('tasks/panel/', views.task_panel, name='task_panel'),
    path('tasks/panel/<int:task_id>/', views.task_panel, name='task_panel_with_id'),
    path('tasks/export/', views.task_export, name='task_export'),
    path('tasks/bulk-action/', views.task_bulk_action, name='task_bulk_action'),
    path('tasks/status/ajax/', views.task_change_status_ajax, name='task_change_status_ajax'),

    # ============================================================================
    # GTD (GETTING THINGS DONE) SYSTEM
    # ============================================================================
    path('inbox/', views.inbox_view, name='inbox'),
    path('inbox/process/<int:item_id>/', views.process_inbox_item, name='process_inbox_item'),
    path('inbox/api/tasks/', views.get_available_tasks, name='inbox_api_tasks'),
    path('inbox/api/projects/', views.get_available_projects, name='inbox_api_projects'),
    path('inbox/api/stats/', views.inbox_stats_api, name='inbox_api_stats'),

    # Inbox Administration System
    path('inbox/admin/', views.inbox_admin_dashboard, name='inbox_admin_dashboard'),
    path('inbox/admin/<int:item_id>/', views.inbox_item_detail_admin, name='inbox_item_detail_admin'),
    path('inbox/admin/<int:item_id>/classify/', views.classify_inbox_item_admin, name='classify_inbox_item_admin'),
    path('inbox/admin/<int:item_id>/authorize/', views.authorize_inbox_item, name='authorize_inbox_item'),
    path('inbox/admin/bulk-action/', views.inbox_admin_bulk_action, name='inbox_admin_bulk_action'),

    # ============================================================================
    # PRODUCTIVITY TOOLS
    # ============================================================================

    # Kanban Board
    path('kanban/', views.kanban_board_unified, name='kanban_board'),
    path('kanban/organized/', views.kanban_board_unified, name='kanban_board_organized'),
    path('kanban/project/<int:project_id>/', views.kanban_project, name='kanban_project'),

    # Eisenhower Matrix
    path('eisenhower/', views.eisenhower_matrix, name='eisenhower_matrix'),
    path('eisenhower/move/<int:task_id>/<str:quadrant>/', views.move_task_eisenhower, name='move_task_eisenhower'),

    # ============================================================================
    # TASK DEPENDENCIES SYSTEM
    # ============================================================================
    path('dependencies/', views.task_dependencies, name='task_dependencies_list'),
    path('dependencies/create/<int:task_id>/', views.create_task_dependency, name='create_task_dependency'),
    path('dependencies/<int:dependency_id>/delete/', views.delete_task_dependency, name='delete_task_dependency'),
    path('dependencies/graph/<int:task_id>/', views.task_dependency_graph, name='task_dependency_graph'),

    # ============================================================================
    # PROJECT TEMPLATES SYSTEM
    # ============================================================================
    path('templates/', views.project_templates, name='project_templates'),
    path('templates/create/', views.create_project_template, name='create_project_template'),
    path('templates/<int:template_id>/', views.project_template_detail, name='project_template_detail'),
    path('templates/<int:template_id>/edit/', views.edit_project_template, name='edit_project_template'),
    path('templates/<int:template_id>/delete/', views.delete_project_template, name='delete_project_template'),
    path('templates/<int:template_id>/use/', views.use_project_template, name='use_project_template'),

    # ============================================================================
    # REMINDERS AND NOTIFICATIONS SYSTEM
    # ============================================================================
    path('reminders/', views.reminders_dashboard, name='reminders_dashboard'),
    path('reminders/create/', views.create_reminder, name='create_reminder'),
    path('reminders/<int:reminder_id>/edit/', views.edit_reminder, name='edit_reminder'),
    path('reminders/<int:reminder_id>/delete/', views.delete_reminder, name='delete_reminder'),
    path('reminders/<int:reminder_id>/mark-sent/', views.mark_reminder_sent, name='mark_reminder_sent'),
    path('reminders/bulk-action/', views.bulk_reminder_action, name='bulk_reminder_action'),

    # ============================================================================
    # CONFIGURATION AND SETTINGS
    # ============================================================================
    path('configuration/', include([
        path('status/', views.status, name='status'),
        path('status/create/', views.status_create, name='status_create'),
        path('status/create/<int:model_id>/', views.status_create, name='status_create_with_model'),
        path('status/edit/', views.status_edit, name='status_edit'),
        path('status/edit/<int:model_id>/', views.status_edit, name='status_edit_with_model'),
        path('status/edit/<int:model_id>/<int:status_id>/', views.status_edit, name='status_edit_with_id'),
        path('status/delete/<int:model_id>/', views.status_delete, name='status_delete_model'),
        path('status/delete/<int:model_id>/<int:status_id>/', views.status_delete, name='status_delete'),

        path('classifications/', views.Classification_list, name='classification_list'),
        path('classifications/create/', views.create_Classification, name='create_classification'),
        path('classifications/<int:classification_id>/edit/', views.edit_Classification, name='edit_classification'),
        path('classifications/<int:classification_id>/delete/', views.delete_Classification, name='delete_classification'),
    ])),

    # ============================================================================
    # LEGACY ROUTES (for backward compatibility)
    # ============================================================================
    path('unified_dashboard/', views.unified_dashboard, name='unified_dashboard_alt'),
    path('management/events/', views.events, name='management_events'),
    path('management/projects/', views.projects, name='management_projects'),
    path('management/tasks/', views.tasks, name='management_tasks'),
    path('events/assign/', views.event_assign, name='event_assign_no_id'),
    path('events/history/', views.event_history, name='event_history_no_id'),
    path('projects/activate/', views.project_activate, name='project_activate_no_id'),
    path('projects/edit/', views.project_edit, name='project_edit_no_id'),
    path('tasks/activate/', views.task_activate, name='task_activate_no_id'),
    path('tasks/edit/', views.task_edit, name='task_edit_no_id'),
    path('tasks/create/<int:project_id>/', views.task_create, name='task_create_with_project'),
    path('tasks/<int:project_id>/', views.tasks, name='tasks_with_project_id'),
    path('configuration/status/create/', views.status_create, name='status_create_no_model'),
    path('configuration/status/edit/', views.status_edit, name='status_edit_no_model'),
    path('configuration/status/delete/<int:model_id>/', views.status_delete, name='status_delete_no_status_id'),
]

# ============================================================================
# URL PATTERN NAMING CONVENTIONS
# ============================================================================
#
# 1. Resource-based URLs:
#    - /resource/ (list view)
#    - /resource/create/ (create form)
#    - /resource/<id>/ (detail view)
#    - /resource/<id>/edit/ (edit form)
#    - /resource/<id>/delete/ (delete confirmation)
#
# 2. Action-based URLs:
#    - /resource/<id>/action/ (specific actions)
#    - /resource/bulk-action/ (bulk operations)
#    - /resource/export/ (export functionality)
#
# 3. API endpoints:
#    - /api/ prefix for AJAX and API calls
#    - /resource/api/ for resource-specific APIs
#
# 4. Nested resources:
#    - /parent/<parent_id>/child/ (list children of parent)
#    - /parent/<parent_id>/child/<child_id>/ (specific child)
#
# 5. Special functionality:
#    - /kanban/ (kanban board view)
#    - /eisenhower/ (eisenhower matrix view)
#    - /inbox/ (GTD inbox)
#    - /templates/ (project templates)
#    - /dependencies/ (task dependencies)
#    - /reminders/ (reminders system)
#
# ============================================================================
# URL STRUCTURE SUMMARY
# ============================================================================
#
# Configuration and Setup:
# - /setup/ - Initial setup
# - /credits/ - Credit management
#
# Main Dashboard:
# - /dashboard/ - Unified dashboard
# - /panel/ - Main panel
# - /management/ - Management index
#
# Events Management:
# - /events/ - Events list
# - /events/create/ - Create event
# - /events/<id>/ - Event detail
# - /events/<id>/edit/ - Edit event
# - /events/<id>/delete/ - Delete event
# - /events/<id>/status/ - Change status
# - /events/<id>/assign/ - Assign attendees
# - /events/<id>/history/ - Event history
# - /events/panel/ - Events panel
# - /events/export/ - Export events
# - /events/bulk-action/ - Bulk actions
#
# Projects Management:
# - /projects/ - Projects list
# - /projects/create/ - Create project
# - /projects/<id>/ - Project detail
# - /projects/<id>/edit/ - Edit project
# - /projects/<id>/delete/ - Delete project
# - /projects/<id>/activate/ - Activate project
# - /projects/<id>/status/ - Change status
# - /projects/panel/ - Projects panel
# - /projects/export/ - Export projects
# - /projects/bulk-action/ - Bulk actions
# - /projects/alerts/ajax/ - Project alerts API
#
# Tasks Management:
# - /tasks/ - Tasks list
# - /tasks/create/ - Create task
# - /tasks/<id>/ - Task detail
# - /tasks/<id>/edit/ - Edit task
# - /tasks/<id>/delete/ - Delete task
# - /tasks/<id>/activate/ - Activate task
# - /tasks/<id>/status/ - Change status
# - /tasks/<id>/dependencies/ - Task dependencies
# - /tasks/panel/ - Tasks panel
# - /tasks/export/ - Export tasks
# - /tasks/bulk-action/ - Bulk actions
# - /tasks/status/ajax/ - Status change API
#
# GTD System:
# - /inbox/ - GTD inbox
# - /inbox/process/<id>/ - Process inbox item
# - /inbox/api/tasks/ - Available tasks API
# - /inbox/api/projects/ - Available projects API
#
# Productivity Tools:
# - /kanban/ - Kanban board
# - /kanban/project/<id>/ - Project kanban
# - /eisenhower/ - Eisenhower matrix
# - /eisenhower/move/<id>/<quadrant>/ - Move task in matrix
#
# Task Dependencies:
# - /dependencies/ - Dependencies list
# - /dependencies/create/<id>/ - Create dependency
# - /dependencies/<id>/delete/ - Delete dependency
# - /dependencies/graph/<id>/ - Dependency graph
#
# Project Templates:
# - /templates/ - Templates list
# - /templates/create/ - Create template
# - /templates/<id>/ - Template detail
# - /templates/<id>/edit/ - Edit template
# - /templates/<id>/delete/ - Delete template
# - /templates/<id>/use/ - Use template
#
# Reminders System:
# - /reminders/ - Reminders dashboard
# - /reminders/create/ - Create reminder
# - /reminders/<id>/edit/ - Edit reminder
# - /reminders/<id>/delete/ - Delete reminder
# - /reminders/<id>/mark-sent/ - Mark as sent
# - /reminders/bulk-action/ - Bulk actions
#
# Configuration:
# - /configuration/status/ - Status management
# - /configuration/classifications/ - Classifications
#
# Legacy Routes (backward compatibility):
# - /unified_dashboard/ - Alternative dashboard
# - /management/events/ - Legacy events
# - /management/projects/ - Legacy projects
# - /management/tasks/ - Legacy tasks
# - Various legacy routes for backward compatibility
#
# ============================================================================
# URL STRUCTURE DOCUMENTATION
# ============================================================================
#
# This file has been completely reorganized for better maintainability.
# All URLs are now grouped by functionality with clear section headers.
#
# Key improvements:
# 1. Logical grouping by functionality
# 2. Consistent naming conventions
# 3. Clear documentation and comments
# 4. Better URL patterns (e.g., /resource/<id>/action/ instead of /resource/action/<id>/)
# 5. Comprehensive summary of all available routes
# 6. Maintenance guidelines and best practices
#
# For detailed documentation, see: README_URLs.md
#
# ============================================================================
# QUICK REFERENCE
# ============================================================================
#
# Most common URLs:
# - Dashboard: /dashboard/
# - Events: /events/
# - Projects: /projects/
# - Tasks: /tasks/
# - Inbox GTD: /inbox/
# - Kanban: /kanban/
# - Eisenhower: /eisenhower/
# - Templates: /templates/
# - Reminders: /reminders/
#
# API endpoints:
# - /inbox/api/tasks/ - Available tasks for inbox
# - /inbox/api/projects/ - Available projects for inbox
# - /projects/alerts/ajax/ - Project alerts
# - /tasks/status/ajax/ - Task status changes
#
# Configuration:
# - /configuration/status/ - Status management
# - /configuration/classifications/ - Classifications
#
# ============================================================================
# URL STRUCTURE DOCUMENTATION
# ============================================================================
#
# This file has been completely reorganized for better maintainability.
# All URLs are now grouped by functionality with clear section headers.
#
# Key improvements:
# 1. Logical grouping by functionality
# 2. Consistent naming conventions
# 3. Clear documentation and comments
# 4. Better URL patterns (e.g., /resource/<id>/action/ instead of /resource/action/<id>/)
# 5. Comprehensive summary of all available routes
# 6. Maintenance guidelines and best practices
#
# For detailed documentation, see: README_URLs.md
#
# ============================================================================
# QUICK REFERENCE
# ============================================================================
#
# Most common URLs:
# - Dashboard: /dashboard/
# - Events: /events/
# - Projects: /projects/
# - Tasks: /tasks/
# - Inbox GTD: /inbox/
# - Kanban: /kanban/
# - Eisenhower: /eisenhower/
# - Templates: /templates/
# - Reminders: /reminders/
#
# API endpoints:
# - /inbox/api/tasks/ - Available tasks for inbox
# - /inbox/api/projects/ - Available projects for inbox
# - /projects/alerts/ajax/ - Project alerts
# - /tasks/status/ajax/ - Task status changes
#
# Configuration:
# - /configuration/status/ - Status management
# - /configuration/classifications/ - Classifications
#
# ============================================================================
# URL STRUCTURE DOCUMENTATION
# ============================================================================
#
# This file has been completely reorganized for better maintainability.
# All URLs are now grouped by functionality with clear section headers.
#
# Key improvements:
# 1. Logical grouping by functionality
# 2. Consistent naming conventions
# 3. Clear documentation and comments
# 4. Better URL patterns (e.g., /resource/<id>/action/ instead of /resource/action/<id>/)
# 5. Comprehensive summary of all available routes
# 6. Maintenance guidelines and best practices
#
# For detailed documentation, see: README_URLs.md
#
# ============================================================================
# QUICK REFERENCE
# ============================================================================
#
# Most common URLs:
# - Dashboard: /dashboard/
# - Events: /events/
# - Projects: /projects/
# - Tasks: /tasks/
# - Inbox GTD: /inbox/
# - Kanban: /kanban/
# - Eisenhower: /eisenhower/
# - Templates: /templates/
# - Reminders: /reminders/
#
# API endpoints:
# - /inbox/api/tasks/ - Available tasks for inbox
# - /inbox/api/projects/ - Available projects for inbox
# - /projects/alerts/ajax/ - Project alerts
# - /tasks/status/ajax/ - Task status changes
#
# Configuration:
# - /configuration/status/ - Status management
# - /configuration/classifications/ - Classifications
#
# ============================================================================
# URL STRUCTURE DOCUMENTATION
# ============================================================================
#
# This file has been completely reorganized for better maintainability.
# All URLs are now grouped by functionality with clear section headers.
#
# Key improvements:
# 1. Logical grouping by functionality
# 2. Consistent naming conventions
# 3. Clear documentation and comments
# 4. Better URL patterns (e.g., /resource/<id>/action/ instead of /resource/action/<id>/)
# 5. Comprehensive summary of all available routes
# 6. Maintenance guidelines and best practices
#
# For detailed documentation, see: README_URLs.md
#
# ============================================================================
# QUICK REFERENCE
# ============================================================================
#
# Most common URLs:
# - Dashboard: /dashboard/
# - Events: /events/
# - Projects: /projects/
# - Tasks: /tasks/
# - Inbox GTD: /inbox/
# - Kanban: /kanban/
# - Eisenhower: /eisenhower/
# - Templates: /templates/
# - Reminders: /reminders/
#
# API endpoints:
# - /inbox/api/tasks/ - Available tasks for inbox
# - /inbox/api/projects/ - Available projects for inbox
# - /projects/alerts/ajax/ - Project alerts
# - /tasks/status/ajax/ - Task status changes
#
# Configuration:
# - /configuration/status/ - Status management
# - /configuration/classifications/ - Classifications
#
# ============================================================================
# URL STRUCTURE DOCUMENTATION
# ============================================================================
#
# This file has been completely reorganized for better maintainability.
# All URLs are now grouped by functionality with clear section headers.
#
# Key improvements:
# 1. Logical grouping by functionality
# 2. Consistent naming conventions
# 3. Clear documentation and comments
# 4. Better URL patterns (e.g., /resource/<id>/action/ instead of /resource/action/<id>/)
# 5. Comprehensive summary of all available routes
# 6. Maintenance guidelines and best practices
#
# For detailed documentation, see: README_URLs.md
#
# ============================================================================
# QUICK REFERENCE
# ============================================================================
#
# Most common URLs:
# - Dashboard: /dashboard/
# - Events: /events/
# - Projects: /projects/
# - Tasks: /tasks/
# - Inbox GTD: /inbox/
# - Kanban: /kanban/
# - Eisenhower: /eisenhower/
# - Templates: /templates/
# - Reminders: /reminders/
#
# API endpoints:
# - /inbox/api/tasks/ - Available tasks for inbox
# - /inbox/api/projects/ - Available projects for inbox
# - /projects/alerts/ajax/ - Project alerts
# - /tasks/status/ajax/ - Task status changes
#
# Configuration:
# - /configuration/status/ - Status management
# - /configuration/classifications/ - Classifications
#
# ============================================================================
# URL STRUCTURE DOCUMENTATION
# ============================================================================
#
# This file has been completely reorganized for better maintainability.
# All URLs are now grouped by functionality with clear section headers.
#
# Key improvements:
# 1. Logical grouping by functionality
# 2. Consistent naming conventions
# 3. Clear documentation and comments
# 4. Better URL patterns (e.g., /resource/<id>/action/ instead of /resource/action/<id>/)
# 5. Comprehensive summary of all available routes
# 6. Maintenance guidelines and best practices
#
# For detailed documentation, see: README_URLs.md
#
# ============================================================================
# QUICK REFERENCE
# ============================================================================
#
# Most common URLs:
# - Dashboard: /dashboard/
# - Events: /events/
# - Projects: /projects/
# - Tasks: /tasks/
# - Inbox GTD: /inbox/
# - Kanban: /kanban/
# - Eisenhower: /eisenhower/
# - Templates: /templates/
# - Reminders: /reminders/
#
# API endpoints:
# - /inbox/api/tasks/ - Available tasks for inbox
# - /inbox/api/projects/ - Available projects for inbox
# - /projects/alerts/ajax/ - Project alerts
# - /tasks/status/ajax/ - Task status changes
#
# Configuration:
# - /configuration/status/ - Status management
# - /configuration/classifications/ - Classifications
#
# ============================================================================
# URL STRUCTURE DOCUMENTATION
# ============================================================================
#
# This file has been completely reorganized for better maintainability.
# All URLs are now grouped by functionality with clear section headers.
#
# Key improvements:
# 1. Logical grouping by functionality
# 2. Consistent naming conventions
# 3. Clear documentation and comments
# 4. Better URL patterns (e.g., /resource/<id>/action/ instead of /resource/action/<id>/)
# 5. Comprehensive summary of all available routes
# 6. Maintenance guidelines and best practices
#
# For detailed documentation, see: README_URLs.md
#
# ============================================================================
# QUICK REFERENCE
# ============================================================================
#
# Most common URLs:
# - Dashboard: /dashboard/
# - Events: /events/
# - Projects: /projects/
# - Tasks: /tasks/
# - Inbox GTD: /inbox/
# - Kanban: /kanban/
# - Eisenhower: /eisenhower/
# - Templates: /templates/
# - Reminders: /reminders/
#
# API endpoints:
# - /inbox/api/tasks/ - Available tasks for inbox
# - /inbox/api/projects/ - Available projects for inbox
# - /projects/alerts/ajax/ - Project alerts
# - /tasks/status/ajax/ - Task status changes
#
# Configuration:
# - /configuration/status/ - Status management
# - /configuration/classifications/ - Classifications
#
# ============================================================================
# URL STRUCTURE DOCUMENTATION
# ============================================================================
#
# This file has been completely reorganized for better maintainability.
# All URLs are now grouped by functionality with clear section headers.
#
# Key improvements:
# 1. Logical grouping by functionality
# 2. Consistent naming conventions
# 3. Clear documentation and comments
# 4. Better URL patterns (e.g., /resource/<id>/action/ instead of /resource/action/<id>/)
# 5. Comprehensive summary of all available routes
# 6. Maintenance guidelines and best practices
#
# For detailed documentation, see: README_URLs.md
#
# ============================================================================
# QUICK REFERENCE
# ============================================================================
#
# Most common URLs:
# - Dashboard: /dashboard/
# - Events: /events/
# - Projects: /projects/
# - Tasks: /tasks/
# - Inbox GTD: /inbox/
# - Kanban: /kanban/
# - Eisenhower: /eisenhower/
# - Templates: /templates/
# - Reminders: /reminders/
#
# API endpoints:
# - /inbox/api/tasks/ - Available tasks for inbox
# - /inbox/api/projects/ - Available projects for inbox
# - /projects/alerts/ajax/ - Project alerts
# - /tasks/status/ajax/ - Task status changes
#
# Configuration:
# - /configuration/status/ - Status management
# - /configuration/classifications/ - Classifications
#
# ============================================================================
# URL STRUCTURE DOCUMENTATION
# ============================================================================
#
# This file has been completely reorganized for better maintainability.
# All URLs are now grouped by functionality with clear section headers.
#
# Key improvements:
# 1. Logical grouping by functionality
# 2. Consistent naming conventions
# 3. Clear documentation and comments
# 4. Better URL patterns (e.g., /resource/<id>/action/ instead of /resource/action/<id>/)
# 5. Comprehensive summary of all available routes
# 6. Maintenance guidelines and best practices
#
# For detailed documentation, see: README_URLs.md
#
# ============================================================================
# QUICK REFERENCE
# ============================================================================
#
# Most common URLs:
# - Dashboard: /dashboard/
# - Events: /events/
# - Projects: /projects/
# - Tasks: /tasks/
# - Inbox GTD: /inbox/
# - Kanban: /kanban/
# - Eisenhower: /eisenhower/
# - Templates: /templates/
# - Reminders: /reminders/
#
# API endpoints:
# - /inbox/api/tasks/ - Available tasks for inbox
# - /inbox/api/projects/ - Available projects for inbox
# - /projects/alerts/ajax/ - Project alerts
# - /tasks/status/ajax/ - Task status changes
#
# Configuration:
# - /configuration/status/ - Status management
# - /configuration/classifications/ - Classifications
#
# ============================================================================
# URL STRUCTURE DOCUMENTATION
# ============================================================================
#
# This file has been completely reorganized for better maintainability.
# All URLs are now grouped by functionality with clear section headers.
#
# Key improvements:
# 1. Logical grouping by functionality
# 2. Consistent naming conventions
# 3. Clear documentation and comments
# 4. Better URL patterns (e.g., /resource/<id>/action/ instead of /resource/action/<id>/)
# 5. Comprehensive summary of all available routes
# 6. Maintenance guidelines and best practices
#
# For detailed documentation, see: README_URLs.md
#
# ============================================================================
# QUICK REFERENCE
# ============================================================================
#
# Most common URLs:
# - Dashboard: /dashboard/
# - Events: /events/
# - Projects: /projects/
# - Tasks: /tasks/
# - Inbox GTD: /inbox/
# - Kanban: /kanban/
# - Eisenhower: /eisenhower/
# - Templates: /templates/
# - Reminders: /reminders/
#
# API endpoints:
# - /inbox/api/tasks/ - Available tasks for inbox
# - /inbox/api/projects/ - Available projects for inbox
# - /projects/alerts/ajax/ - Project alerts
# - /tasks/status/ajax/ - Task status changes
#
# Configuration:
# - /configuration/status/ - Status management
# - /configuration/classifications/ - Classifications
#
# ============================================================================
# URL STRUCTURE DOCUMENTATION
# ============================================================================
#
# This file has been completely reorganized for better maintainability.
# All URLs are now grouped by functionality with clear section headers.
#
# Key improvements:
# 1. Logical grouping by functionality
# 2. Consistent naming conventions
# 3. Clear documentation and comments
# 4. Better URL patterns (e.g., /resource/<id>/action/ instead of /resource/action/<id>/)
# 5. Comprehensive summary of all available routes
# 6. Maintenance guidelines and best practices
#
# For detailed documentation, see: README_URLs.md
#
# ============================================================================
# QUICK REFERENCE
# ============================================================================
#
# Most common URLs:
# - Dashboard: /dashboard/
# - Events: /events/
# - Projects: /projects/
# - Tasks: /tasks/
# - Inbox GTD: /inbox/
# - Kanban: /kanban/
# - Eisenhower: /eisenhower/
# - Templates: /templates/
# - Reminders: /reminders/
#
# API endpoints:
# - /inbox/api/tasks/ - Available tasks for inbox
# - /inbox/api/projects/ - Available projects for inbox
# - /projects/alerts/ajax/ - Project alerts
# - /tasks/status/ajax/ - Task status changes
#
# Configuration:
# - /configuration/status/ - Status management
# - /configuration/classifications/ - Classifications
#
# ============================================================================
# MAINTENANCE NOTES
# ============================================================================
#
# When adding new URLs:
# 1. Follow the established naming conventions
# 2. Add them to the appropriate section
# 3. Include proper documentation in comments
# 4. Update this summary if adding new functionality
# 5. Test all new routes thoroughly
#
# When modifying existing URLs:
# 1. Maintain backward compatibility when possible
# 2. Add legacy routes if breaking changes are needed
# 3. Update documentation accordingly
# 4. Inform other developers of changes
#
# URL Pattern Best Practices:
# 1. Use descriptive names that indicate purpose
# 2. Keep URLs as short as possible while being clear
# 3. Use hyphens instead of underscores in URLs
# 4. Group related functionality together
# 5. Use consistent patterns across similar resources
#
# ============================================================================
