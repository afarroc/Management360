from django.urls import path
from .import views

urlpatterns = [
    path('', views.index, name="index"),
    path('about/', views.about, name="about"),
    path('admin/', views.create_project, name="admin"),

    path('events/', views.events, name="events"),
    path('events/<int:id>', views.event_detail, name="event_detail"),
    path('create_event/', views.create_event, name="create_event"),

    path('projects/', views.projects, name="projects"),
    path('projects/<int:id>', views.project_detail, name="project_detail"),
    path('create_project/', views.create_project, name="create_project"),

    path('task/', views.task, name="tasks"),
    path('create_task/', views.create_task, name="create_task"),

    path('change_event_status/<int:event_id>/', views.change_event_status, name='change_event_status'),
    path('delete_event/<int:event_id>/', views.delete_event, name='delete_event'),
    path('panel/', views.panel, name='panel'),
    path('signup/', views.signup, name='signup'),
    path('logout/', views.signout, name='logout'),
    path('signin/', views.signin, name='signin'),
    
    path('panel/event_edit/<int:event_id>/', views.event_edit, name='event_edit'),
    
    path('profile/', views.ViewProfileView.as_view(), name='profile'),
    path('create_profile/', views.ProfileView.as_view(), name='create_profile'),
    path('edit_profile/<int:user_id>', views.ProfileView.as_view(), name='edit_profile'),

    
]               