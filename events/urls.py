from django.urls import path
from .import views

from django.conf import settings
from django.conf.urls.static import static

from django.contrib import admin
from django.urls import path, include
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

from . import views
from .setup_views import SetupView

urlpatterns = [

    path('setup/', SetupView.as_view(), name='setup'),
    path('credits/', views.add_credits, name='add_credits'),

    # Eventos
    path('events/', views.events, name="events"),
    path('events/detail/<int:event_id>/', views.event_detail, name="event_detail"),
    path('events/create/', views.event_create, name="event_create"),
    path('events/delete/<int:event_id>/', views.event_delete, name='event_delete'),
    path('events/edit/', views.event_edit, name="event_edit"),
    path('events/edit/<int:event_id>/', views.event_edit, name="event_edit"),
    path('events/panel/', views.event_panel, name="event_panel"),
    path('events/panel/<int:event_id>', views.event_panel, name="event_panel"),
    path('events/status_change/<int:event_id>/', views.event_status_change, name='event_status_change'),
    path('events/assign/', views.event_assign, name="event_assign"),
    path('events/assign/<int:event_id>', views.event_assign, name="event_assign"),
    path('events/history/', views.event_history, name="event_history"),
    path('events/history/<int:event_id>', views.event_history, name="event_history"),
    path('events/export/', views.event_export, name='event_export'),
    path('events/bulk-action/', views.event_bulk_action, name='event_bulk_action'),

    # Proyectos
    path('projects/', views.projects, name="projects"),
    path('projects/<int:project_id>', views.projects, name="projects"),
    path('projects/panel/', views.project_panel, name="project_panel"),
    path('projects/panel/<int:project_id>', views.project_panel, name="project_panel"),
    path('projects/detail/<int:id>', views.project_detail, name="project_detail"),
    path('projects/create/', views.project_create, name="project_create"),
    path('projects/delete/<int:project_id>', views.project_delete, name="project_delete"),
    path('projects/edit/', views.project_edit, name="project_edit"),
    path('projects/edit/<int:project_id>', views.project_edit, name="project_edit"),
    path('projects/activate/',views.project_activate, name='project_activate'),
    path('projects/activate/<int:project_id>',views.project_activate, name='project_activate'),
    path('projects/export/', views.project_export, name='project_export'),
    path('projects/bulk-action/', views.project_bulk_action, name='project_bulk_action'),
    path('projects/alerts/ajax/', views.get_project_alerts_ajax, name='project_alerts_ajax'),

    # Tareas
    path('tasks/', views.tasks, name="tasks"),
    path('tasks/<int:task_id>', views.tasks, name="tasks"),
    path('tasks/<int:project_id>', views.tasks, name="tasks"),
    path('tasks/create/', views.task_create, name="task_create"),
    path('tasks/create/<int:project_id>', views.task_create, name="task_create"),
    path('tasks/edit/', views.task_edit, name="task_edit"),
    path('tasks/edit/<int:task_id>', views.task_edit, name="task_edit"),
    path('tasks/delete/<int:task_id>', views.task_delete, name="task_delete"),
    path('tasks/panel/', views.task_panel, name="task_panel"),
    path('tasks/panel/<int:task_id>', views.task_panel, name="task_panel"),
    path('tasks/activate/',views.task_activate, name='task_activate'),
    path('tasks/activate/<int:task_id>',views.task_activate, name='task_activate'),
    path('tasks/export/', views.task_export, name='task_export'),
    path('tasks/bulk-action/', views.task_bulk_action, name='task_bulk_action'),


    # Cambio de estado y eliminación de eventos
    path('change_project_status/<int:project_id>/', views.change_project_status, name='change_project_status'),
    path('change_task_status/<int:task_id>/', views.change_task_status, name='change_task_status'),
    path('task_change_status_ajax/', views.task_change_status_ajax, name='task_change_status_ajax'),

    # Panel
    path('panel/', views.panel, name='panel'),

    # Configuración
    path('configuration/status/', views.status, name='status'),
    path('configuration/status/delete/<int:model_id>/', views.status_delete, name='status_delete_model'),
    path('configuration/status/delete/<int:model_id>/<int:status_id>/', views.status_delete, name='status_delete'),
    path('configuration/status/create/', views.status_create, name='status_create'),
    path('configuration/status/create/<int:model_id>/', views.status_create, name='status_create'),
    path('configuration/status/edit/', views.status_edit, name='status_edit'),
    path('configuration/status/edit/<int:model_id>/', views.status_edit, name='status_edit'),
    path('configuration/status/edit/<int:model_id>/<int:status_id>', views.status_edit, name='status_edit'),
    
    # management
    path('management/', views.management_index, name='management'),
    path('management/events/', views.events, name='management_events'),
    path('management/projects/', views.projects, name='management_projects'),
    path('management/tasks/', views.tasks, name='management_tasks'),

    path('configuration/create_classification/', views.create_Classification, name='create_classification'),
    path('configuration/edit_classification/<int:Classification_id>/', views.edit_Classification, name='edit_classification'),
    path('configuration/delete_classification/<int:Classification_id>/', views.delete_Classification, name='delete_classification'),
    path('configuration/classification_list/', views.Classification_list, name='classification_list'),

# Media files are now served from remote Termux server
# Commenting out local media serving
# ]+static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
]
