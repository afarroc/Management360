# chat/urls.py
from django.urls import path

from . import views

app_name = 'chat'  # Namespace definition

urlpatterns = [
    path('', views.room_list, name='room_list'),
    path('room/<str:room_name>/', views.room, name='room'),
    # Endpoint para procesamiento de mensajes del chat (API)
    path('assistant/', views.chat_view, name='chat_api'),
    # Endpoint para la UI del chat (solo interfaz)
    path('ui/', views.assistant_view, name='assistant_ui'),
    path('clear/', views.clear_history, name='clear_history'),
]