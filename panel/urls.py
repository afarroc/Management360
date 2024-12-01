from django.contrib import admin
from django.urls import path, include
from . import views
from accounts import views as accounts_views
# from boards import views as boards_views

urlpatterns = [
    path('admin/', admin.site.urls),

    path('', include('events.urls')),
    path('accounts/', include('accounts.urls')),
    path('chat/', include('chat.urls')),
    path('tools/', include('tools.urls')),
    path('rooms/', include('rooms.urls')),

    path('api/csrf/', views.get_csrf, name='api-csrf'),
    path('api/token/connection/', views.get_connection_token, name='api-connection-token'),
    path('api/token/subscription/', views.get_subscription_token, name='api-subscription-token'),
    path('api/login/', views.login_view, name='api-login'),
    path('api/logout/', views.logout_view, name='api-logout'),
    path('api/signup/', views.signup_view, name='api-signup'),

    
]