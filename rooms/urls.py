# rooms/urls.py
from django.urls import path

from . import views

urlpatterns = [
    path("", views.lobby, name="lobby"),
    path('create/', views.create_room, name='create_room'),
    path('<pk>/', views.room_detail, name='room_detail'),
    path('<pk>/comments/', views.room_comments, name='room_comments'),
    path('<pk>/evaluations/', views.room_evaluations, name='room_evaluations'),
]