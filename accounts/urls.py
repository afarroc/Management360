from django.urls import path
from .views import home, register, login, token_send, success, verify, error_page

urlpatterns = [
    path('', home, name='home'),
    path('register/', register, name='register'),
    path('login/', login, name='login'),
    path('token/', token_send, name='token'),
    path('success/', success, name ='success'),
    path('verify/<auth_token>/', verify, name = "verify"),
    path('error/', error_page, name = "error"),
    path('logout/', home, name = "logout"),
]