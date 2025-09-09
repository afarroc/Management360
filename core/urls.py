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

]