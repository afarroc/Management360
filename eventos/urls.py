from django.urls import path
from .import views

urlpatterns = [
    # Páginas principales
    path('', views.index, name="index"),
    path('about/', views.about, name="about"),
    path('admin/', views.create_project, name="admin"),

    # Eventos
    path('events/', views.events, name="events"),
    path('events/<int:id>', views.event_detail, name="event_detail"),
    path('events/create', views.create_event, name="create_event"),
    path('events/edit/', views.edit_event, name="edit_event"),
    path('events/edit/<int:event_id>', views.edit_event, name="edit_event"),
    
    # Proyectos
    path('projects/', views.projects, name="projects"),
    path('projects/<int:id>', views.project_detail, name="project_detail"),
    path('create_project/', views.create_project, name="create_project"),

    # Tareas
    path('task/', views.task, name="tasks"),
    path('create_task/', views.create_task, name="create_task"),

    # Cambio de estado y eliminación de eventos
    path('change_event_status/<int:event_id>/', views.change_event_status, name='change_event_status'),
    path('delete_event/<int:event_id>/', views.delete_event, name='delete_event'),

    # Panel
    path('panel/', views.panel, name='panel'),
    path('panel/event_edit/<int:event_id>/', views.edit_event, name='event_edit'),

    # Sesión
    path('statics/session/signup/', views.signup, name='signup'),
    path('logout/', views.signout, name='logout'),
    path('statics/session/signin/', views.signin, name='signin'),

    # Perfil
    path('profile/<int:user_id>', views.ViewProfileView.as_view(), name='profile'),
    path('edit_profile/<int:user_id>', views.ProfileView.as_view(), name='edit_profile'),
    path('create_profile/<int:user_id>/', views.ProfileView.as_view(), name='create_profile'),
    
    # Configuración
    path('configuration/status_list/', views.status_list, name='status_list'),
    path('configuration/edit_status/<int:status_id>/', views.edit_status, name='edit_status'),
    path('configuration/delete_status/<int:status_id>/', views.delete_status, name='delete_status'),
    path('configuration/create_status/', views.create_status, name='create_status'),
]
