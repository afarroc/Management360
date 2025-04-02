# chat/urls.py
from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="chat"),
    path("room/<str:room_name>/", views.room, name="room"),
    path('assistant/', views.chat_view, name='assistant'),
    path('chat/clear/', views.clear_chat, name='clear'),
]