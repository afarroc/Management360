# urls.py
from django.urls import path
from . import views
from .views import RoomListViewSet, RoomDetailViewSet, RoomSearchViewSet, \
    MessageListCreateAPIView, JoinRoomView, LeaveRoomView, \
    room_view, navigate_room


urlpatterns = [
    # Main views
    path('', views.lobby, name='lobby'),
    path('search/', views.room_search, name='room_search'),

    # Rooms
    path('rooms/', views.room_list, name='room_list'),
    path('rooms/create/', views.create_room, name='room_create'),
    path('rooms/<int:pk>/', views.room_detail, name='room_detail'),
    path('rooms/<int:pk>/comments/', views.room_comments, name='room_comments'),
    path('rooms/<int:pk>/evaluations/', views.room_evaluations, name='room_evaluations'),

    # Portals
    path('portals/', views.portal_list, name='portal_list'),
    path('portals/create/', views.create_portal, name='portal_create'),
    path('portals/<int:pk>/', views.portal_detail, name='portal_detail'),

    # Entrance/Exits
    path('entrance-exits/', views.entrance_exit_list, name='entrance_exit_list'),
    path('entrance-exits/create/', views.create_entrance_exit, name='entrance_exit_create'),
    path('entrance-exits/<int:pk>/', views.entrance_exit_detail, name='entrance_exit_detail'),

    # API Routes
    path('api/rooms/', RoomListViewSet.as_view({'get': 'list'}), name='room-list-api'),
    path('api/rooms/<int:pk>/', RoomDetailViewSet.as_view({'get': 'retrieve'}), name='room-detail-api'),
    path('api/rooms/search/', RoomSearchViewSet.as_view({'get': 'list'}), name='room-search-api'),
    path('api/rooms/<int:room_id>/messages/', MessageListCreateAPIView.as_view(), name='room-messages-api'),
    path('api/rooms/<int:room_id>/join/', JoinRoomView.as_view(), name='join-room-api'),
    path('api/rooms/<int:room_id>/leave/', LeaveRoomView.as_view(), name='leave-room-api'),

   # ... otras URLs existentes ...
    path('room/', room_view, name='current_room'),
    path('room/<int:room_id>/', room_view, name='room_view'),
    path('navigate/<str:direction>/', navigate_room, name='navigate_room'),
]

