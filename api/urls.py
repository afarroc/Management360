from django.urls import path
from panel import views
from . import views as api_views

app_name = 'api'

urlpatterns = [
    path('csrf/', views.get_csrf, name='csrf'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('signup/', views.signup_view, name='signup'),
    path('token/connection/', views.get_connection_token, name='connection-token'),
    path('token/subscription/', views.get_subscription_token, name='subscription-token'),
    path('content/publish/', api_views.publish_content, name='publish-content'),
]
