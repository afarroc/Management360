from django.urls import path
from . import views

app_name = 'campaigns'

urlpatterns = [
    # Dashboard principal
    path('', views.dashboard, name='dashboard'),

    # Gestión de campañas
    path('campaigns/', views.campaign_list, name='campaign_list'),
    path('campaigns/<uuid:pk>/', views.campaign_detail, name='campaign_detail'),

    # Gestión de contactos
    path('campaigns/<uuid:campaign_id>/contacts/', views.contact_list, name='contact_list'),

    # Gestión del discador
    path('discador/', views.discador_loads, name='discador_loads'),
    path('discador/<int:pk>/', views.discador_load_detail, name='discador_load_detail'),
]