from django.urls import path
from panel import views

app_name = 'api'

urlpatterns = [
    # Autenticación JSON
    path('csrf/',    views.get_csrf,      name='csrf'),
    path('login/',   views.login_view,    name='login'),
    path('logout/',  views.logout_view,   name='logout'),
    path('signup/',  views.signup_view,   name='signup'),

    # Tokens Centrifugo
    path('token/connection/',    views.get_connection_token,   name='connection-token'),
    path('token/subscription/',  views.get_subscription_token, name='subscription-token'),
]
