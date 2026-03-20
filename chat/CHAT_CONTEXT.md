# Mapa de Contexto — App `chat`

> Generado por `m360_map.sh`  |  2026-03-19 18:31:47
> Ruta: `/data/data/com.termux/files/home/projects/Management360/chat`  |  Total archivos: **27**

---

## Índice

| # | Categoría | Archivos |
|---|-----------|----------|
| 1 | 👁 `views` | 3 |
| 2 | 🎨 `templates` | 12 |
| 3 | 🗃 `models` | 1 |
| 4 | 🔗 `urls` | 1 |
| 5 | 🛡 `admin` | 1 |
| 6 | 🧪 `tests` | 1 |
| 7 | 📄 `other` | 8 |

---

## Archivos por Categoría


### VIEWS (3 archivos)

| Archivo | Líneas | Ruta relativa |
|---------|--------|---------------|
| `views.py` | 2017 | `views.py` |
| `api_last_room.py` | 12 | `views/api_last_room.py` |
| `views_redis.py` | 38 | `views_redis.py` |

### TEMPLATES (12 archivos)

| Archivo | Líneas | Ruta relativa |
|---------|--------|---------------|
| `assistant.html` | 1227 | `templates/chat/assistant.html` |
| `assistant_configurations.html` | 142 | `templates/chat/assistant_configurations.html` |
| `command_history.html` | 202 | `templates/chat/command_history.html` |
| `conversation_detail.html` | 198 | `templates/chat/conversation_detail.html` |
| `conversation_history.html` | 161 | `templates/chat/conversation_history.html` |
| `functions_panel.html` | 310 | `templates/chat/functions_panel.html` |
| `index.html` | 681 | `templates/chat/index.html` |
| `panel.html` | 750 | `templates/chat/panel.html` |
| `redis_status.html` | 49 | `templates/chat/redis_status.html` |
| `room.html` | 1635 | `templates/chat/room.html` |
| `room_admin.html` | 201 | `templates/chat/room_admin.html` |
| `room_list.html` | 317 | `templates/chat/room_list.html` |

### MODELS (1 archivos)

| Archivo | Líneas | Ruta relativa |
|---------|--------|---------------|
| `models.py` | 344 | `models.py` |

### URLS (1 archivos)

| Archivo | Líneas | Ruta relativa |
|---------|--------|---------------|
| `urls.py` | 76 | `urls.py` |

### ADMIN (1 archivos)

| Archivo | Líneas | Ruta relativa |
|---------|--------|---------------|
| `admin.py` | 3 | `admin.py` |

### TESTS (1 archivos)

| Archivo | Líneas | Ruta relativa |
|---------|--------|---------------|
| `test.py` | 105 | `templates/chat/test.py` |

### OTHER (8 archivos)

| Archivo | Líneas | Ruta relativa |
|---------|--------|---------------|
| `__init__.py` | 0 | `__init__.py` |
| `apps.py` | 6 | `apps.py` |
| `assistant.py` | 40 | `assistant.py` |
| `consumers.py` | 427 | `consumers.py` |
| `functions.py` | 409 | `functions.py` |
| `notifications_consumer.py` | 60 | `notifications_consumer.py` |
| `ollama_api.py` | 167 | `ollama_api.py` |
| `routing.py` | 8 | `routing.py` |

---

## Árbol de Directorios

```
chat/
├── templates
│   └── chat
│       ├── assistant.html
│       ├── assistant_configurations.html
│       ├── command_history.html
│       ├── conversation_detail.html
│       ├── conversation_history.html
│       ├── functions_panel.html
│       ├── index.html
│       ├── panel.html
│       ├── redis_status.html
│       ├── room.html
│       ├── room_admin.html
│       ├── room_list.html
│       └── test.py
├── views
│   └── api_last_room.py
├── __init__.py
├── admin.py
├── apps.py
├── assistant.py
├── consumers.py
├── functions.py
├── models.py
├── notifications_consumer.py
├── ollama_api.py
├── routing.py
├── urls.py
├── views.py
└── views_redis.py
```

---

## Endpoints registrados

Fuente: `urls.py`  |  namespace: `chat`

```python
  path('', views.index, name='index'),
  path('rooms/', views.room_list, name='room_list'),
  path('room/', views.redirect_to_last_room, name='redirect_to_last_room'),
  path('room/<str:room_name>/', views.room, name='room'),
  path('assistant/', views.chat_view, name='chat_api'),
  path('ui/', views.assistant_view, name='assistant_ui'),
  path('functions/', views.functions_panel, name='functions_panel'),
  path('commands/', views.command_history, name='command_history'),
  path('conversations/', views.conversation_history, name='conversation_history'),
  path('conversation/<str:conversation_id>/', views.conversation_detail, name='conversation_detail'),
  path('clear/', views.clear_history, name='clear_history'),
  path('clear_history/<str:room_name>/', views.clear_history_room, name='clear_history_room'),
  path('api/chat/last-room/', views.last_room_api, name='api_last_room'),
  path('api/chat/room-list/', views.room_list_api, name='api_room_list'),
  path('api/chat/room-history/<int:room_id>/', views.room_history_api, name='api_room_history'),
  path('api/chat/mark-read/', views.mark_messages_read_api, name='api_mark_read'),
  path('api/chat/unread-count/', views.unread_count_api, name='api_unread_count'),
  path('api/chat/reset-unread/', views.reset_unread_count_api, name='api_reset_unread'),
  path('api/notifications/unread/', views.unread_notifications_api, name='api_unread_notifications'),
  path('api/notifications/mark-read/', views.mark_notifications_read_api, name='api_mark_notifications_read'),
  path('api/notifications/test-create/', views.test_create_notification, name='api_test_create_notification'),
  path('api/chat/search/', views.search_history, name='api_search_history'),
  path('api/chat/search-messages/', views.search_messages, name='api_search_messages'),
  path('api/chat/reaction/<int:message_id>/', views.add_reaction, name='api_add_reaction'),
  path('api/chat/presence/', views.update_presence, name='api_update_presence'),
  path('api/chat/presence/status/', views.get_presence, name='api_get_presence'),
  path('api/room/<int:room_id>/members/', views.room_members_api, name='api_room_members'),
  path('api/room/<int:room_id>/notifications/', views.room_notifications_api, name='api_room_notifications'),
  path('panel/', views.chat_panel, name='chat_panel'),
  path('stats/', views.chat_stats_api, name='chat_stats'),
  path('room/<int:room_id>/admin/', views.room_admin, name='room_admin'),
  path('api/conversations/', views.conversations_api, name='api_conversations'),
  path('api/conversation/<str:conversation_id>/switch/', views.switch_conversation_api, name='api_switch_conversation'),
  path('api/conversation/<str:conversation_id>/messages/', views.conversation_messages_api, name='api_conversation_messages'),
  path('api/conversation/new/', views.new_conversation_api, name='api_new_conversation'),
  path('configurations/', views.assistant_configurations, name='assistant_configurations'),
  path('configurations/create/', views.create_assistant_configuration, name='create_assistant_configuration'),
  path('configurations/<int:config_id>/edit/', views.edit_assistant_configuration, name='edit_assistant_configuration'),
  path('configurations/<int:config_id>/delete/', views.delete_assistant_configuration, name='delete_assistant_configuration'),
  path('configurations/<int:config_id>/set-active/', views.set_active_configuration, name='set_active_configuration'),
```

---

## Modelos detectados

**`models.py`**

- línea 12: `class Conversation(models.Model):`
- línea 92: `class CommandLog(models.Model):`
- línea 113: `class AssistantConfiguration(models.Model):`
- línea 186: `class HardcodedNotificationManager:`
- línea 299: `class UserPresence(models.Model):`
- línea 331: `class MessageReaction(models.Model):`


---

## Migraciones

| Archivo | Estado |
|---------|--------|
| `0001_initial` | aplicada |

---

## Funciones clave (views/ y services/)

**`views/api_last_room.py`**

```
6:def last_room_api(request):
```


---

## Compartir con Claude

```bash
cat /data/data/com.termux/files/home/projects/Management360/chat/views/mi_vista.py | termux-clipboard-set
```
