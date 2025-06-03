# chat/urls.py
from django.urls import path

from . import views

app_name = 'chat'  # Namespace definition

urlpatterns = [
    path('', views.room_list, name='room_list'),
    path('room/<str:room_name>/', views.room, name='room'),
    path('assistant/', views.assistant_view, name='assistant'),
    path('clear/', views.clear_history, name='clear_history'),
]