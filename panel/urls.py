#panel.urls.py
# Django Imports

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from . import views
from .views import RedisTestView

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),

    # Core (Vistas principales)
    path('', include('core.urls')),  # Home, About, Contact
    
    # Apps
    path('accounts/', include('accounts.urls')),
    path('campaigns/', include('campaigns.urls')),
    path('chat/', include('chat.urls', namespace='chat')),
    path('courses/', include('courses.urls')),
    path('cv/', include('cv.urls')),
    path('events/', include('events.urls')),
    path('kpis/', include('kpis.urls')),
    path('memento/', include('memento.urls')),
    path('passgen/', include('passgen.urls')),
    path('rooms/', include('rooms.urls')),
    path('tools/', include('tools.urls')),
    
    # API Endpoints (alphabetical order)
    path('api/csrf/', views.get_csrf, name='api-csrf'),
    path('api/login/', views.login_view, name='api-login'),
    path('api/logout/', views.logout_view, name='api-logout'),
    path('api/signup/', views.signup_view, name='api-signup'),
    path('api/token/connection/', views.get_connection_token, name='api-connection-token'),
    path('api/token/subscription/', views.get_subscription_token, name='api-subscription-token'),
    
    # API (Recomendado mover a una app dedicada)
    path('api/', include('api.urls')),  # Crear app "api" para estos endpoints

    # Redis Test
    path('redis-test/', RedisTestView.as_view(), name='redis_test'),
]

# Serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)