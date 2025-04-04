from django.urls import path
from . import views

urlpatterns = [
    path('generate/', views.generate_password, name='generate_password'),
    path('help/', views.password_help, name='password_help'),
    ]
