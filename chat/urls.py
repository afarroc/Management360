# chat/urls.py
from django.urls import path

from . import views

app_name = 'chat'  # Namespace definition

urlpatterns = [
    path('', views.room_list, name='room_list'),
    path('room/', views.redirect_to_last_room, name='redirect_to_last_room'),
    path('room/<str:room_name>/', views.room, name='room'),
    # Endpoint para procesamiento de mensajes del chat (API)
    path('assistant/', views.chat_view, name='chat_api'),
    # Endpoint para la UI del chat (solo interfaz)
    path('ui/', views.assistant_view, name='assistant_ui'),
    path('clear/', views.clear_history, name='clear_history'),
    path('clear_history/<str:room_name>/', views.clear_history_room, name='clear_history_room'),
    # API para obtener la última sala accedida por el usuario
    path('api/chat/last-room/', views.last_room_api, name='api_last_room'),
    # API para obtener la lista de salas
    path('api/chat/room-list/', views.room_list_api, name='api_room_list'),
    # API para obtener el historial de una sala
    path('api/chat/room-history/<int:room_id>/', views.room_history_api, name='api_room_history'),
    # API para marcar mensajes como leídos
    path('api/chat/mark-read/', views.mark_messages_read_api, name='api_mark_read'),
    # API para obtener el contador de mensajes no leídos
    path('api/chat/unread-count/', views.unread_count_api, name='api_unread_count'),
    # API para resetear el contador de mensajes no leídos
    path('api/chat/reset-unread/', views.reset_unread_count_api, name='api_reset_unread'),
    # API para obtener notificaciones no leídas
    path('api/notifications/unread/', views.unread_notifications_api, name='api_unread_notifications'),
    # API para marcar notificaciones como leídas
    path('api/notifications/mark-read/', views.mark_notifications_read_api, name='api_mark_notifications_read'),
    # API para crear notificación de prueba
    path('api/notifications/test-create/', views.test_create_notification, name='api_test_create_notification'),
    # API para buscar en el historial de mensajes
    path('api/chat/search/', views.search_history, name='api_search_history'),
    # API para buscar mensajes con filtros avanzados
    path('api/chat/search-messages/', views.search_messages, name='api_search_messages'),
    # API para añadir reacciones a mensajes
    path('api/chat/reaction/<int:message_id>/', views.add_reaction, name='api_add_reaction'),
    # API para actualizar presencia del usuario
    path('api/chat/presence/', views.update_presence, name='api_update_presence'),
    # API para obtener presencia de usuarios en una sala
    path('api/chat/presence/status/', views.get_presence, name='api_get_presence'),
    # API para gestionar miembros de sala
    path('api/room/<int:room_id>/members/', views.room_members_api, name='api_room_members'),
    # API para notificaciones de sala
    path('api/room/<int:room_id>/notifications/', views.room_notifications_api, name='api_room_notifications'),
    # Panel flotante para incluir en cualquier página
    path('panel/', views.chat_panel, name='chat_panel'),
    # Panel de administración de sala
    path('room/<int:room_id>/admin/', views.room_admin, name='room_admin'),
]