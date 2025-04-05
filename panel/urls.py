from django.contrib import admin
from django.urls import path, include
from . import views
from accounts import views as accounts_views

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),

    # App Includes (alphabetical order)
    path('accounts/', include('accounts.urls')),
    path('chat/', include('chat.urls')),
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
]