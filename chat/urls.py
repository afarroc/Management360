# chat/urls.py
from django.urls import path

from . import views, views_redis

app_name = 'chat'  # Namespace definition

urlpatterns = [
    path('', views.index, name='index'),
    path('assistant/', views.chat_view, name='assistant'),
    path('room/<str:room_name>/', views.chatroom, name='room'),
    path('clear/', views.clear_chat, name='clear'),
    path('check-redis/', views_redis.check_redis, name='check_redis'),
]