from django.urls import path
from . import views
from events.setup_views import SetupView

urlpatterns = [
    # URLs principales
    path('', views.home_view, name='home'),
    path('', views.home_view, name='index'),
    path('about/', views.about_view, name='about'),
    path('contact/', views.contact_view, name='contact'),
    path('faq/', views.faq_view, name='faq'),
    path('blank/', views.blank_view, name='blank'),

    # URLs dinámicas
    path('<int:days>/', views.home_view, name='home_by_days'),
    path('<int:days>/<int:days_ago>/', views.home_view, name='home_by_days_range'),

    # Vista basada en clase
    path('setup/', SetupView.as_view(), name='setup'),

    # Vista de búsqueda
    path('search/', views.search_view, name='search_view'),

    # Mapa de URLs del proyecto
    path('url-map/', views.url_map_html_view, name='url_map'),
    path('url-map/api/', views.url_map_view, name='url_map_api'),

    # Endpoints AJAX para lazy loading
    path('api/activities/more/', views.load_more_activities, name='load_more_activities'),
    path('api/items/<str:item_type>/more/', views.load_more_recent_items, name='load_more_recent_items'),
    path('api/categories/<str:category_type>/more/', views.load_more_categories, name='load_more_categories'),
    path('api/dashboard/refresh/', views.refresh_dashboard_data, name='refresh_dashboard_data'),

    # Endpoints de métricas y monitoreo
    path('api/metrics/performance/', views.get_performance_metrics, name='performance_metrics'),
    path('api/metrics/dashboard/', views.get_dashboard_stats, name='dashboard_stats'),

]