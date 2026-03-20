# Mapa de Contexto — App `rooms`

> Generado por `m360_map.sh`  |  2026-03-19 18:42:27
> Ruta: `/data/data/com.termux/files/home/projects/Management360/rooms`  |  Total archivos: **46**

---

## Índice

| # | Categoría | Archivos |
|---|-----------|----------|
| 1 | 👁 `views` | 1 |
| 2 | 🎨 `templates` | 30 |
| 3 | 🗃 `models` | 1 |
| 4 | 📝 `forms` | 1 |
| 5 | 🔗 `urls` | 1 |
| 6 | 🛡 `admin` | 1 |
| 7 | 📄 `management` | 2 |
| 8 | 🧪 `tests` | 2 |
| 9 | 📄 `other` | 7 |

---

## Archivos por Categoría


### VIEWS (1 archivos)

| Archivo | Líneas | Ruta relativa |
|---------|--------|---------------|
| `views.py` | 2858 | `views.py` |

### TEMPLATES (30 archivos)

| Archivo | Líneas | Ruta relativa |
|---------|--------|---------------|
| `breadcrumb.html` | 11 | `templates/partials/breadcrumb.html` |
| `basic_3d_environment.html` | 615 | `templates/rooms/basic_3d_environment.html` |
| `create_room.html` | 164 | `templates/rooms/create_room.html` |
| `doors_portals_connections_crud.html` | 1 | `templates/rooms/doors_portals_connections_crud.html` |
| `entrance_exit_confirm_delete.html` | 136 | `templates/rooms/entrance_exit_confirm_delete.html` |
| `entrance_exit_detail.html` | 17 | `templates/rooms/entrance_exit_detail.html` |
| `entrance_exit_form.html` | 145 | `templates/rooms/entrance_exit_form.html` |
| `entrance_exit_list.html` | 45 | `templates/rooms/entrance_exit_list.html` |
| `card1.html` | 11 | `templates/rooms/includes/card1.html` |
| `card2.html` | 33 | `templates/rooms/includes/card2.html` |
| `entrance_exit_modal.html` | 37 | `templates/rooms/includes/entrance_exit_modal.html` |
| `portal_modal.html` | 37 | `templates/rooms/includes/portal_modal.html` |
| `lobby.html` | 197 | `templates/rooms/lobby.html` |
| `breadcrumb.html` | 11 | `templates/rooms/partials/breadcrumb.html` |
| `portal_create.html` | 19 | `templates/rooms/portal_create.html` |
| `portal_detail.html` | 26 | `templates/rooms/portal_detail.html` |
| `portal_list.html` | 45 | `templates/rooms/portal_list.html` |
| `room_3d.html` | 144 | `templates/rooms/room_3d.html` |
| `room_3d_interactive.html` | 902 | `templates/rooms/room_3d_interactive.html` |
| `room_comments.html` | 71 | `templates/rooms/room_comments.html` |
| `room_confirm_delete.html` | 195 | `templates/rooms/room_confirm_delete.html` |
| `room_connection_confirm_delete.html` | 103 | `templates/rooms/room_connection_confirm_delete.html` |
| `room_connection_form.html` | 138 | `templates/rooms/room_connection_form.html` |
| `room_crud.html` | 672 | `templates/rooms/room_crud.html` |
| `room_detail.html` | 588 | `templates/rooms/room_detail.html` |
| `room_evaluations.html` | 12 | `templates/rooms/room_evaluations.html` |
| `room_form.html` | 323 | `templates/rooms/room_form.html` |
| `room_form_complete.html` | 808 | `templates/rooms/room_form_complete.html` |
| `room_list.html` | 84 | `templates/rooms/room_list.html` |
| `room_view.html` | 322 | `templates/rooms/room_view.html` |

### MODELS (1 archivos)

| Archivo | Líneas | Ruta relativa |
|---------|--------|---------------|
| `models.py` | 843 | `models.py` |

### FORMS (1 archivos)

| Archivo | Líneas | Ruta relativa |
|---------|--------|---------------|
| `forms.py` | 399 | `forms.py` |

### URLS (1 archivos)

| Archivo | Líneas | Ruta relativa |
|---------|--------|---------------|
| `urls.py` | 131 | `urls.py` |

### ADMIN (1 archivos)

| Archivo | Líneas | Ruta relativa |
|---------|--------|---------------|
| `admin.py` | 141 | `admin.py` |

### MANAGEMENT (2 archivos)

| Archivo | Líneas | Ruta relativa |
|---------|--------|---------------|
| `check_setup.py` | 19 | `management/commands/check_setup.py` |
| `seed_rooms.py` | 0 | `management/commands/seed_rooms.py` |

### TESTS (2 archivos)

| Archivo | Líneas | Ruta relativa |
|---------|--------|---------------|
| `create_test_room.py` | 18 | `management/commands/create_test_room.py` |
| `test_navigation_zone.py` | 78 | `management/commands/test_navigation_zone.py` |

### OTHER (7 archivos)

| Archivo | Líneas | Ruta relativa |
|---------|--------|---------------|
| `__init__.py` | 0 | `__init__.py` |
| `apps.py` | 5 | `apps.py` |
| `exceptions.py` | 5 | `exceptions.py` |
| `serializers.py` | 348 | `serializers.py` |
| `signals.py` | 14 | `signals.py` |
| `transition_manager.py` | 336 | `transition_manager.py` |
| `utils.py` | 251 | `utils.py` |

---

## Árbol de Directorios

```
rooms/
├── management
│   └── commands
│       ├── check_setup.py
│       ├── create_test_room.py
│       ├── seed_rooms.py
│       └── test_navigation_zone.py
├── templates
│   ├── partials
│   │   └── breadcrumb.html
│   └── rooms
│       ├── includes
│       │   ├── card1.html
│       │   ├── card2.html
│       │   ├── entrance_exit_modal.html
│       │   └── portal_modal.html
│       ├── partials
│       │   └── breadcrumb.html
│       ├── basic_3d_environment.html
│       ├── create_room.html
│       ├── doors_portals_connections_crud.html
│       ├── entrance_exit_confirm_delete.html
│       ├── entrance_exit_detail.html
│       ├── entrance_exit_form.html
│       ├── entrance_exit_list.html
│       ├── lobby.html
│       ├── portal_create.html
│       ├── portal_detail.html
│       ├── portal_list.html
│       ├── room_3d.html
│       ├── room_3d_interactive.html
│       ├── room_comments.html
│       ├── room_confirm_delete.html
│       ├── room_connection_confirm_delete.html
│       ├── room_connection_form.html
│       ├── room_crud.html
│       ├── room_detail.html
│       ├── room_evaluations.html
│       ├── room_form.html
│       ├── room_form_complete.html
│       ├── room_list.html
│       └── room_view.html
├── __init__.py
├── admin.py
├── apps.py
├── exceptions.py
├── forms.py
├── models.py
├── serializers.py
├── signals.py
├── transition_manager.py
├── urls.py
├── utils.py
└── views.py
```

---

## Endpoints registrados

Fuente: `urls.py`  |  namespace: `rooms`

```python
  path('', views.lobby, name='lobby'),
  path('register-presence/', views.register_presence, name='register_presence'),
  path('search/', views.room_search, name='room_search'),
  path('rooms/', views.room_list, name='room_list'),
  path('rooms/crud/', views.room_crud_view, name='room_crud'),
  path('rooms/create/', views.create_room, name='room_create'),
  path('rooms/create-complete/', views.create_room_complete, name='room_create_complete'),
  path('rooms/<int:pk>/', views.room_detail, name='room_detail'),
  path('rooms/<int:pk>/delete/', views.room_delete, name='room_delete'),
  path('rooms/<int:pk>/3d/', views.room_3d_view, name='room_3d'),
  path('rooms/<int:pk>/3d-interactive/', views.room_3d_interactive_view, name='room_3d_interactive'),
  path('rooms/<int:pk>/comments/', views.room_comments, name='room_comments'),
  path('rooms/<int:pk>/evaluations/', views.room_evaluations, name='room_evaluations'),
  path('portals/', views.portal_list, name='portal_list'),
  path('portals/create/', views.create_portal, name='portal_create'),
  path('portals/<int:pk>/', views.portal_detail, name='portal_detail'),
  path('entrance-exits/', views.entrance_exit_list, name='entrance_exit_list'),
  path('entrance-exits/create/', views.create_entrance_exit, name='entrance_exit_create'),
  path('entrance-exits/<int:pk>/', views.entrance_exit_detail, name='entrance_exit_detail'),
  path('entrance-exits/<int:pk>/edit/', views.edit_entrance_exit, name='edit_entrance_exit'),
  path('entrance-exits/<int:pk>/delete/', views.delete_entrance_exit, name='delete_entrance_exit'),
  path('rooms/<int:room_id>/connections/create/', create_room_connection, name='create_room_connection'),
  path('rooms/<int:room_id>/connections/<int:connection_id>/edit/', edit_room_connection, name='edit_room_connection'),
  path('rooms/<int:room_id>/connections/<int:connection_id>/delete/', delete_room_connection, name='delete_room_connection'),
  path('api/rooms/', RoomListViewSet.as_view({'get': 'list'}), name='room-list-api'),
  path('api/rooms/<int:pk>/', RoomDetailViewSet.as_view({'get': 'retrieve'}), name='room-detail-api'),
  path('api/rooms/search/', RoomSearchViewSet.as_view({'get': 'list'}), name='room-search-api'),
  path('api/crud/rooms/', RoomCRUDViewSet.as_view({
  path('api/crud/rooms/<int:pk>/', RoomCRUDViewSet.as_view({
  path('api/crud/doors/', EntranceExitCRUDViewSet.as_view({
  path('api/crud/doors/<int:pk>/', EntranceExitCRUDViewSet.as_view({
  path('api/crud/portals/', PortalCRUDViewSet.as_view({
  path('api/crud/portals/<int:pk>/', PortalCRUDViewSet.as_view({
  path('api/crud/connections/', RoomConnectionCRUDViewSet.as_view({
  path('api/crud/connections/<int:pk>/', RoomConnectionCRUDViewSet.as_view({
  path('api/rooms/<int:room_id>/messages/', MessageListCreateAPIView.as_view(), name='room-messages-api'),
  path('api/rooms/<int:room_id>/join/', JoinRoomView.as_view(), name='join-room-api'),
  path('api/rooms/<int:room_id>/leave/', LeaveRoomView.as_view(), name='leave-room-api'),
  path('api/transitions/available/', views.get_available_transitions, name='available-transitions-api'),
  path('api/entrance/<int:entrance_id>/use/', views.use_entrance_exit, name='use-entrance-api'),
  path('api/entrance/<int:entrance_id>/info/', views.get_entrance_info, name='entrance-info-api'),
  path('api/teleport/<int:room_id>/', views.teleport_to_room, name='teleport-to-room-api'),
  path('api/navigation/history/', views.get_navigation_history, name='navigation-history-api'),
  path('api/user/current-room/', views.get_user_current_room, name='user-current-room-api'),
  path('api/3d/rooms/<int:room_id>/data/', views.get_room_3d_data, name='room-3d-data-api'),
  path('api/3d/transition/', views.room_transition, name='room-transition-api'),
  path('api/3d/player/position/', views.update_player_position, name='update-player-position-api'),
  path('api/3d/player/status/', views.get_player_status, name='player-status-api'),
  path('3d-basic/', views.basic_3d_environment, name='basic_3d_environment'),
  path('navigation-test-zone/', views.create_navigation_test_zone, name='create_navigation_test_zone'),
  path('room/', room_view, name='current_room'),
  path('room/<int:room_id>/', room_view, name='room_view'),
  path('navigate/<str:direction>/', navigate_room, name='navigate_room'),
```

---

## Modelos detectados

**`models.py`**

- línea 8: `class PlayerProfile(models.Model):`
- línea 215: `class RoomManager(models.Manager):`
- línea 218: `class Room(models.Model):`
- línea 388: `class RoomConnection(models.Model):`
- línea 401: `class RoomObject(models.Model):`
- línea 430: `class EntranceExit(models.Model):`
- línea 668: `class Portal(models.Model):`
- línea 684: `class Comment(models.Model):`
- línea 691: `class Evaluation(models.Model):`
- línea 699: `class RoomMember(models.Model):`
- línea 727: `class Message(models.Model):`
- línea 758: `class MessageRead(models.Model):`
- línea 766: `class Notification(models.Model):`
- línea 804: `class RoomNotification(models.Model):`
- línea 832: `class Outbox(models.Model):`
- línea 839: `class CDC(models.Model):`


---

## Migraciones

| Archivo | Estado |
|---------|--------|
| `0001_initial` | aplicada |

---

## Funciones clave (views/ y services/)


---

## Compartir con Claude

```bash
cat /data/data/com.termux/files/home/projects/Management360/rooms/views/mi_vista.py | termux-clipboard-set
```
