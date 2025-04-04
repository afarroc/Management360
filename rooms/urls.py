# urls.py
from django.urls import path
from . import views






from django.urls import path

from .views import RoomListViewSet, RoomDetailViewSet, RoomSearchViewSet, \
    MessageListCreateAPIView, JoinRoomView, LeaveRoomView


urlpatterns = [
    path('rooms/', RoomListViewSet.as_view({'get': 'list'}), name='room-list'),
    path('rooms/<int:pk>/', RoomDetailViewSet.as_view({'get': 'retrieve'}), name='room-detail'),
    path('search/', RoomSearchViewSet.as_view({'get': 'list'}), name='room-search'),
    path('rooms/<int:room_id>/messages/', MessageListCreateAPIView.as_view(), name='room-messages'),
    path('rooms/<int:room_id>/join/', JoinRoomView.as_view(), name='join-room'),
    path('rooms/<int:room_id>/leave/', LeaveRoomView.as_view(), name='leave-room'),

    # Lobby
    path('', views.lobby, name='lobby'),

    # Salas
    path('', views.room_list, name='room_list'),
    path('create/', views.create_room, name='room_create'),
    path('<int:pk>/comments/', views.room_comments, name='room_comments'),
    path('<int:pk>/evaluations/', views.room_evaluations, name='room_evaluations'),
    path('<int:pk>/', views.room_detail, name='room_detail'),

    # Entradas/Salidas
    path('entrance-exits/', views.entrance_exit_list, name='entrance_exit_list'),
    path('entrance-exits/create/', views.create_entrance_exit, name='entrance_exit_create'),
    path('entrance-exits/<int:pk>/', views.entrance_exit_detail, name='entrance_exit_detail'),

    # Portales
    path('portals/', views.portal_list, name='portal_list'),
    path('portals/create/', views.create_portal, name='portal_create'),
    path('portals/<int:pk>/', views.portal_detail, name='portal_detail'),

    # Search
    path('search/', views.room_search, name='room_search'),

    # API Room Detail
    path('rooms/api/<int:pk>/', views.room_detail_view, name='room_detail_api'),
]