# urls.py
from django.urls import path
from . import views

urlpatterns = [

    # Lobby
    path('', views.lobby, name='lobby'),

    # Salas
    path('rooms/', views.room_list, name='room_list'),
    path('rooms/create/', views.create_room, name='room_create'),
    path('rooms/<int:pk>/', views.room_detail, name='room_detail'),
    path('rooms/<int:pk>/comments/', views.room_comments, name='room_comments'),
    path('rooms/<int:pk>/evaluations/', views.room_evaluations, name='room_evaluations'),

    # Entradas/Salidas
    path('entrance-exits/', views.entrance_exit_list, name='entrance_exit_list'),
    path('entrance-exits/create/', views.create_entrance_exit, name='entrance_exit_create'),
    path('entrance-exits/<int:pk>/', views.entrance_exit_detail, name='entrance_exit_detail'),

    # Portales
    path('portals/', views.portal_list, name='portal_list'),
    path('portals/create/', views.create_portal, name='portal_create'),
    path('portals/<int:pk>/', views.portal_detail, name='portal_detail'),
]