from django.urls import path
from . import views

urlpatterns = [
    path('calculate_agents/', views.calculate_agents, name='calculate_agents'),
]