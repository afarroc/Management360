"""
URLs para el sistema de gestión de leads y bots
"""

from django.urls import path
from . import views

app_name = 'bots'

urlpatterns = [
    # Campañas de leads
    path('campaigns/', views.lead_campaign_list, name='campaign_list'),
    path('campaigns/create/', views.lead_campaign_create, name='campaign_create'),
    path('campaigns/<int:pk>/', views.lead_campaign_detail, name='campaign_detail'),
    path('campaigns/<int:campaign_pk>/upload/', views.lead_upload, name='lead_upload'),
    path('campaigns/<int:campaign_pk>/rules/', views.lead_distribution_rules, name='distribution_rules'),
    path('campaigns/<int:campaign_pk>/distribute/', views.trigger_distribution, name='trigger_distribution'),

    # Leads
    path('leads/', views.lead_list, name='lead_list'),
    path('leads/<int:pk>/', views.lead_detail, name='lead_detail'),
    path('leads/export/', views.lead_export, name='lead_export'),

    # API endpoints
    path('api/campaigns/<int:campaign_pk>/stats/', views.api_campaign_stats, name='api_campaign_stats'),
    path('api/campaigns/<int:campaign_pk>/distribute/', views.api_trigger_distribution, name='api_trigger_distribution'),
]