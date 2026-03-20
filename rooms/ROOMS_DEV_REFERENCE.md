# Referencia de Desarrollo — App `rooms`

> **Actualizado:** 2026-03-19  
> **Audiencia:** Desarrolladores y asistentes IA  
> **Archivos:** 46 | **Vistas:** 2858 líneas | **Modelos:** 843 líneas | **Templates:** 30 | **Endpoints:** 53  
> **Namespace:** `rooms` ✅ declarado en `urls.py`  
> **Migración activa:** `0001_initial`

---

## Índice

| Sección | Contenido |
|---------|-----------|
| 1. Resumen | Tres capas funcionales |
| 2. Modelos | 16 modelos documentados |
| 3. Archivos adicionales | serializers, transition_manager, signals, utils |
| 4. Vistas | UI tradicional, APIs REST y navegación 3D |
| 5. URLs | Mapa completo de 53 endpoints |
| 6. Convenciones críticas | Propietario `owner`, PKs, Centrifugo |
| 7. Bugs conocidos | Issues activos |
| 8. Deuda técnica | Clasificada por prioridad |

---

## 1. Resumen

`rooms` es la app de **espacios virtuales** de Management360. Es la app más compleja del proyecto con tres capas funcionales completamente distintas conviviendo en el mismo codebase:

**Capa 1 — Chat en tiempo real (salas de texto)**
El modelo de sala (`Room`) y mensajes (`Message`, `MessageRead`) que usa la app `chat`. `rooms` es el proveedor de datos — `chat` es el consumidor de vistas.

**Capa 2 — Mundo virtual gamificado (navegación entre habitaciones)**
Sistema completo de mundo virtual con jugador (`PlayerProfile`), puertas (`EntranceExit`), conexiones (`RoomConnection`), portales con cooldown (`Portal`) y jerarquía de habitaciones padre/hijo. El jugador navega físicamente entre salas con costo de energía.

**Capa 3 — Entorno 3D (Three.js + SVG isométrico)**
API para renderizado 3D de habitaciones con geometría, materiales, física y propiedades visuales. Incluye `room_3d_interactive.html` (902 líneas) con Three.js embebido.

**Arquitectura adicional notable:**
- `CentrifugoMixin` — integración con Centrifugo para broadcasting en tiempo real (alternativa a Django Channels)
- `RoomTransitionManager` (336 líneas) — motor de transiciones entre habitaciones
- `serializers.py` (348 líneas) — serializers DRF para API REST completa

---

## 2. Modelos

### `PlayerProfile` — Perfil del jugador en el mundo virtual

```python
class PlayerProfile(models.Model):
    user           # OneToOneField → User (CASCADE, related: 'player_profile')
    current_room   # FK → Room (SET_NULL, nullable) — habitación física actual
    position_x     # IntegerField(default=0)
    position_y     # IntegerField(default=0)
    energy         # IntegerField(default=100) — costo de moverse
    productivity   # IntegerField(default=50)
    social         # IntegerField(default=50)
    last_interaction     # DateTimeField(auto_now)
    state          # CharField choices: AVAILABLE|WORKING|RESTING|SOCIALIZING|IDLE|DISCONNECTED
    skills         # JSONField(default=list) — ej: ["programming", "design"]
    last_state_change    # DateTimeField(auto_now)
    navigation_history   # JSONField(default=list) — últimas 10 habitaciones visitadas
    last_navigation_time # DateTimeField(auto_now)
```

**Métodos clave:**

| Método | Descripción |
|--------|-------------|
| `move_to_room(direction)` | Mueve al jugador vía `EntranceExit.face` — retorna bool |
| `get_available_exits()` | Lista salidas: entradas físicas + portales + objetos + jerarquía |
| `can_use_exit(exit_type, exit_id)` | Verifica si puede usar una salida (energía, estado) |
| `use_exit(exit_type, exit_id)` | Ejecuta la transición — actualiza `current_room`, `position_x/y`, `energy` |
| `add_to_navigation_history(room_id)` | Agrega al historial, máx 10, sin duplicados consecutivos |
| `can_teleport_to(target_room)` | Verifica disponibilidad (energía mínima 20) |
| `teleport_to(target_room)` | Teletransporta — costo 20 energía |
| `calculate_new_position(direction)` | ⚠️ Solo implementa NORTH y SOUTH — otras direcciones retornan None |

⚠️ `calculate_new_position()` tiene solo dos ramas (`NORTH`/`SOUTH`). Para EAST/WEST la función cae al final sin `return` explícito — Python retorna `None`, lo que asigna `(None, None)` como posición.

---

### `Room` — Sala virtual (núcleo de la app)

```python
class Room(models.Model):
    # Identidad
    name           # CharField(100, unique=True)
    description    # TextField(blank=True)
    owner          # FK → User (CASCADE, related: 'owned_rooms') ← propietario
    creator        # FK → User (CASCADE, nullable, related: 'created_rooms')
    administrators # M2M → User (related: 'administered_rooms')
    permissions    # CharField choices: 'public'|'private'|'restricted'
    room_type      # CharField choices: OFFICE|MEETING|LOUNGE|KITCHEN|BATHROOM|SPECIAL

    # Timestamps y versioning
    created_at     # DateTimeField(auto_now_add)
    updated_at     # DateTimeField(auto_now)
    version        # PositiveBigIntegerField(default=0) — optimistic locking
    bumped_at      # DateTimeField(auto_now_add) — actualizado al recibir mensaje

    # Mensaje
    last_message   # FK → Message (SET_NULL, nullable)

    # Geometría 3D
    x, y, z        # IntegerField(default=0) — posición en el mundo
    length, width, height  # IntegerField(default=30/30/10)
    pitch, yaw, roll       # IntegerField(default=0) — rotación

    # Relaciones
    connections    # M2M → self through RoomConnection (asymmetric)
    parent_room    # FK → self (CASCADE, nullable, related: 'child_of_rooms')
    portals        # M2M → Portal (related: 'rooms')

    # Apariencia y física
    color_primary, color_secondary  # CharField(7) — hex
    material_type  # CharField choices: WOOD|METAL|GLASS|CONCRETE|PLASTIC|FABRIC|STONE|SPECIAL
    texture_url, opacity, mass, density, friction, restitution  # Propiedades físicas

    # Estado
    is_active      # BooleanField(default=True) ✅
    health, temperature, lighting_intensity, sound_ambient, special_properties

    # Media
    capacity       # IntegerField(default=0)
    address        # CharField(255, blank=True)
    image          # ImageField(upload_to='./room_images/')
    rating         # DecimalField(3,2)

    # Relaciones M2M a través de modelos intermedios
    comments       # M2M → User through Comment
    evaluations    # M2M → User through Evaluation

    objects = RoomManager()  # Manager vacío (pass)
```

⚠️ **Propietario: `owner`**, no `created_by` — convención documentada del proyecto.
⚠️ **Sin UUID** — PK es int (AutoField). Convención documentada en PROJECT_DESIGN.

**Métodos clave:**

| Método | Descripción |
|--------|-------------|
| `increment_version()` | `version += 1; save()` — usado en transacciones atómicas |
| `get_image_url()` | Retorna URL de imagen o `None` |
| `add_member(user, role, added_by)` | Crea `RoomMember` + `Notification` + `RoomNotification` |
| `remove_member(user, removed_by)` | Elimina `RoomMember` + `RoomNotification` |
| `get_active_members()` | `members.filter(is_active=True).select_related('user')` |
| `get_online_members()` | Miembros con `last_seen >= now - 5min` |
| `can_user_manage(user)` | `owner == user` OR member con role admin/moderator |

---

### `RoomConnection` — Conexión entre habitaciones

```python
class RoomConnection(models.Model):
    from_room    # FK → Room (related: 'from_connections')
    to_room      # FK → Room (related: 'to_connections')
    entrance     # FK → EntranceExit (related: 'room_connections')
    bidirectional# BooleanField(default=True)
    energy_cost  # IntegerField(default=0)

    class Meta:
        unique_together = ('from_room', 'to_room', 'entrance')
```

---

### `RoomObject` — Objeto interactivo dentro de una habitación

```python
class RoomObject(models.Model):
    name         # CharField(100)
    room         # FK → Room (related: 'room_objects')
    position_x/y # IntegerField(default=0)
    object_type  # CharField choices: WORK|SOCIAL|REST|DOOR|EQUIPMENT
    effect       # JSONField(default=dict)
    interaction_cooldown # IntegerField(default=60) segundos
```

`interact(player)` modifica el estado del jugador según `object_type` (WORK → productivity+10, SOCIAL → social+5).

---

### `EntranceExit` — Puerta / entrada entre habitaciones

El modelo más complejo de la app con **30+ campos**. Representa una puerta física con propiedades visuales, físicas, funcionales y de seguridad detalladas.

**Campos esenciales:**

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `name` | CharField(255) | Nombre de la puerta |
| `room` | FK → Room | Habitación que contiene la puerta |
| `face` | CharField choices | NORTH/SOUTH/EAST/WEST/UP/DOWN |
| `position_x/y` | IntegerField(nullable) | Posición en el grid de la habitación |
| `enabled` | BooleanField(default=True) | Si la puerta está habilitada |
| `connection` | FK → RoomConnection (nullable) | Conexión activa |
| `is_locked` | BooleanField | Si está cerrada con llave |
| `access_level` | IntegerField(0-10) | Nivel requerido (0=abierto) |
| `health` | IntegerField(default=100) | Durabilidad de la puerta |
| `usage_count` | IntegerField | Veces usada |

**Campos de apariencia:** `door_type`, `material`, `color`, `texture_url`, `opacity`, `glow_color`, `glow_intensity`, `particle_effects`, `decoration_type`

**Campos funcionales:** `auto_close`, `close_delay`, `open_speed`, `close_speed`, `interaction_type`, `animation_type`, `requires_both_hands`, `interaction_distance`, `cooldown`, `max_usage_per_hour`, `experience_reward`, `energy_cost_modifier`

**Campos de seguridad:** `security_system`, `alarm_triggered`, `allowed_users` (M2M → User)

**Campos ambientales:** `seals_air`, `seals_sound`, `temperature_resistance`, `pressure_resistance`

**`save()` override:** si `position_x` o `position_y` son None, llama `assign_default_position()` que posiciona la puerta según `face` en el centro del lado correspondiente de la habitación.

**Métodos:**
- `can_player_use(player_profile)` — delega a `RoomTransitionManager.attempt_transition()`
- `attempt_transition(player_profile)` — ídem
- `get_transition_info(player_profile)` — información detallada de la transición posible
- `get_opposite_entrance()` — encuentra la puerta correspondiente en la habitación destino
- `get_usage_statistics()` — dict con `total_usage`, `last_used`, `is_open`, `health_percentage`

---

### `Portal` — Teletransporte entre habitaciones con cooldown

```python
class Portal(models.Model):
    name        # CharField(255)
    entrance    # FK → EntranceExit (related: 'portal_entrance')
    exit        # FK → EntranceExit (related: 'portal_exit')
    energy_cost # IntegerField(default=10)
    cooldown    # IntegerField(default=300) — segundos entre usos
    last_used   # DateTimeField(nullable)
```

`is_active()` → `last_used is None OR last_used + cooldown < now()`

⚠️ `Portal` no tiene `created_at` — `get_recent_activities()` en `views.py` lo verifica con `hasattr(Portal, 'created_at')` antes de consultar.

---

### `Comment` y `Evaluation`

Modelos simples sin lógica adicional.

```python
class Comment(models.Model):
    user / room / comment(TextField) / created_at

class Evaluation(models.Model):
    user / room / rating(IntegerField) / comment(TextField, blank) / created_at
```

---

### `RoomMember` — Membresía de usuario en sala

```python
class RoomMember(models.Model):
    room         # FK → Room (related: 'members')
    user         # FK → User (related: 'room_memberships')
    joined_at    # DateTimeField(auto_now_add)
    role         # CharField choices: 'member'|'moderator'|'admin'
    is_active    # BooleanField(default=True) ✅
    last_seen    # DateTimeField(auto_now)
    notification_preferences # JSONField(default=dict)

    class Meta:
        unique_together = ('room', 'user')
```

Métodos: `can_manage_room()` → role in ['admin','moderator'] OR room.owner == user. `can_delete_messages()` → role == 'admin' OR room.owner == user.

---

### `Message` y `MessageRead`

```python
class Message(models.Model):
    room         # FK → Room (related: 'messages')
    user         # FK → User (nullable, related: 'messages')
    content      # TextField
    created_at   # DateTimeField(auto_now_add)
    edited_at    # DateTimeField(nullable)
    is_deleted   # BooleanField(default=False) — soft delete ✅
    reply_to     # FK → self (SET_NULL, nullable, related: 'replies')
    message_type # CharField choices: 'text'|'system'|'file'|'image'

    class Meta:
        indexes = [('room','created_at'), ('user','created_at')]

class MessageRead(models.Model):
    user / message / read_at(auto_now_add)
    class Meta:
        unique_together = ('user', 'message')
```

---

### `Notification` — Notificaciones de usuario

```python
class Notification(models.Model):
    user              # FK → User (related: 'notifications')
    title             # CharField(255)
    message           # TextField
    notification_type # CharField choices: chat|system|alert|info|room_invite|room_join|room_leave|admin_action
    is_read           # BooleanField(default=False)
    created_at        # DateTimeField(auto_now_add)
    read_at           # DateTimeField(nullable)
    related_room      # FK → Room (CASCADE, nullable)
    related_message   # FK → Message (CASCADE, nullable)
    action_url        # CharField(500) — URL de redirección al hacer click

    class Meta:
        indexes = [('user','is_read','created_at'), ('user','notification_type')]
```

`mark_as_read()` → `is_read=True`, `read_at=now()`, save.

⚠️ **Este es el modelo de notificaciones real** del proyecto — `chat.HardcodedNotificationManager` debería reemplazarse por este modelo. Ver CHAT_DEV_REFERENCE Bug B1.

---

### `RoomNotification` — Notificaciones específicas de sala

```python
class RoomNotification(models.Model):
    room / user / title / message
    notification_type  # choices: member_join|member_leave|room_update|admin_change|message_pinned|room_settings
    is_read / created_at
    created_by         # FK → User (SET_NULL, nullable, related: 'created_room_notifications') ← usa created_by ✅
```

---

### `Outbox` y `CDC`

Modelos para integración con Centrifugo (broadcasting en tiempo real).

```python
class Outbox(models.Model):
    method    # TextField(default="publish")
    payload   # JSONField
    partition # BigIntegerField(default=0)
    created_at

class CDC(models.Model):
    # Igual que Outbox — usado para Change Data Capture vía Debezium/Kafka
```

Estos modelos son el mecanismo de outbox pattern para garantizar entrega de mensajes a Centrifugo incluso ante fallos de red.

---

## 3. Archivos Adicionales

### `transition_manager.py` (336 líneas) — Motor de transiciones

`RoomTransitionManager` gestiona toda la lógica de transición entre habitaciones. Singleton accesible via `get_room_transition_manager()`.

Métodos principales:
- `attempt_transition(player_profile, entrance)` → `{success, message, target_room, energy_cost, ...}`
- `get_available_transitions(player_profile)` → lista de transiciones posibles desde la habitación actual
- `_validate_access(player_profile, entrance)` → verifica `is_locked`, `access_level`, `allowed_users`
- `_calculate_energy_cost(connection, entrance)` → base + `energy_cost_modifier` de la puerta

### `serializers.py` (348 líneas) — DRF Serializers

| Serializer | Modelo | Uso |
|-----------|--------|-----|
| `RoomSerializer` | Room | API de lista/detalle |
| `RoomSearchSerializer` | Room | Búsqueda con campo `is_member` anotado |
| `RoomCRUDSerializer` | Room | CRUD completo |
| `MessageSerializer` | Message | Lista/creación de mensajes |
| `RoomMemberSerializer` | RoomMember | Join/Leave events |
| `EntranceExitCRUDSerializer` | EntranceExit | CRUD de puertas |
| `PortalCRUDSerializer` | Portal | CRUD de portales |
| `RoomConnectionCRUDSerializer` | RoomConnection | CRUD de conexiones |

### `signals.py` (14 líneas)

Señales post-save/post-delete sobre `Message` o `RoomMember` para triggers automáticos. No se revisó el detalle en esta sesión.

### `utils.py` (251 líneas)

Utilidades de la app. No se revisó en detalle — probablemente contiene helpers para cálculos de geometría o validaciones.

### `transition_manager.py` importado con lazy singleton

```python
from .transition_manager import get_room_transition_manager
manager = get_room_transition_manager()
```

---

## 4. Vistas

`views.py` tiene 2858 líneas con **tres familias de vistas** y una peculiaridad estructural importante: los imports de DRF y `logger` están **en el medio del archivo** (línea 735), no al principio. Todo el código antes de esa línea no puede usar `logger` — hay referencias a `logger` en `room_detail` (L137) antes de su declaración.

### Vistas de UI tradicionales

| Vista | URL | Auth | Template |
|-------|-----|------|----------|
| `lobby` | `/rooms/` | ✅ | `rooms/lobby.html` |
| `room_list` | `/rooms/rooms/` | manual redirect | `rooms/room_list.html` |
| `room_detail` | `/rooms/rooms/<int:pk>/` | ❌ | `rooms/room_detail.html` |
| `room_delete` | `/rooms/rooms/<int:pk>/delete/` | ✅ | `rooms/room_confirm_delete.html` |
| `create_room` | `/rooms/rooms/create/` | ✅ | `rooms/room_form.html` |
| `create_room_complete` | `/rooms/rooms/create-complete/` | ✅ | `rooms/room_form_complete.html` |
| `room_3d_view` | `/rooms/rooms/<int:pk>/3d/` | ❌ | `rooms/room_3d.html` |
| `room_3d_interactive_view` | `/rooms/rooms/<int:pk>/3d-interactive/` | ✅ | `rooms/room_3d_interactive.html` |
| `room_comments` | `/rooms/rooms/<int:pk>/comments/` | ❌ | `rooms/room_comments.html` |
| `room_evaluations` | `/rooms/rooms/<int:pk>/evaluations/` | ❌ | `rooms/room_evaluations.html` |
| `room_crud_view` | `/rooms/rooms/crud/` | ✅ | `rooms/room_crud.html` |
| `basic_3d_environment` | `/rooms/3d-basic/` | ✅ | `rooms/basic_3d_environment.html` |
| `register_presence` | `/rooms/register-presence/` | ✅ | redirect |

**`room_detail`** maneja también POST de `create_entrance_exit` y `create_portal` — vista multipropósito. Sin `@login_required` explícito.

**`basic_3d_environment`** es una vista de setup: crea la habitación base + 3 habitaciones conectadas + puertas + conexiones + perfil del jugador si no existen. Es idempotente via `get_or_create`.

### Vistas de gestión de entradas/portales/conexiones

| Vista | URL | Auth |
|-------|-----|------|
| `entrance_exit_list` | `/rooms/entrance-exits/` | ❌ |
| `create_entrance_exit` | `/rooms/entrance-exits/create/` | ✅ |
| `entrance_exit_detail` | `/rooms/entrance-exits/<int:pk>/` | ❌ |
| `edit_entrance_exit` | `/rooms/entrance-exits/<int:pk>/edit/` | ✅ |
| `delete_entrance_exit` | `/rooms/entrance-exits/<int:pk>/delete/` | ✅ |
| `portal_list` | `/rooms/portals/` | ❌ — **duplicada** (ver B1) |
| `portal_detail` | `/rooms/portals/<int:pk>/` | ❌ — **duplicada** (ver B1) |
| `create_portal` | `/rooms/portals/create/` | ✅ |
| `create_room_connection` | `/rooms/rooms/<id>/connections/create/` | ✅ |
| `edit_room_connection` | `/rooms/rooms/<id>/connections/<id>/edit/` | ✅ |
| `delete_room_connection` | `/rooms/rooms/<id>/connections/<id>/delete/` | ✅ |

⚠️ `create_entrance_exit` (L452) redirige a `reverse_lazy('entrance_exit_list')` sin namespace — debería ser `rooms:entrance_exit_list`. Y el template es `'create_entrance_exit.html'` sin el prefijo `rooms/` — probablemente no existe.

### ViewSets DRF

| ViewSet | Base URL | Operaciones |
|---------|----------|-------------|
| `RoomListViewSet` | `/rooms/api/rooms/` | GET list — filtra por membresía |
| `RoomDetailViewSet` | `/rooms/api/rooms/<pk>/` | GET retrieve |
| `RoomSearchViewSet` | `/rooms/api/rooms/search/` | GET list — anota `is_member` |
| `RoomCRUDViewSet` | `/rooms/api/crud/rooms/` | Full CRUD con permisos |
| `EntranceExitCRUDViewSet` | `/rooms/api/crud/doors/` | Full CRUD |
| `PortalCRUDViewSet` | `/rooms/api/crud/portals/` | Full CRUD |
| `RoomConnectionCRUDViewSet` | `/rooms/api/crud/connections/` | Full CRUD |
| `MessageListCreateAPIView` | `/rooms/api/rooms/<id>/messages/` | GET list + POST create con Centrifugo |
| `JoinRoomView` | `/rooms/api/rooms/<id>/join/` | POST — join con broadcast |
| `LeaveRoomView` | `/rooms/api/rooms/<id>/leave/` | POST — leave con broadcast |

`MessageListCreateAPIView` y `JoinRoomView`/`LeaveRoomView` heredan de `CentrifugoMixin` y usan `@transaction.atomic` + `select_for_update()`.

### APIs de navegación (sistema de juego)

Todas usan `@api_view` de DRF:

| Vista | URL | Método | Descripción |
|-------|-----|--------|-------------|
| `use_entrance_exit` | `/rooms/api/entrance/<id>/use/` | POST | Usa una puerta — delega a TransitionManager |
| `get_entrance_info` | `/rooms/api/entrance/<id>/info/` | GET | Info detallada de puerta + transición |
| `get_available_transitions` | `/rooms/api/transitions/available/` | GET | Todas las salidas disponibles del jugador |
| `teleport_to_room` | `/rooms/api/teleport/<room_id>/` | POST | Teletransportación (costo 20 energía) |
| `get_navigation_history` | `/rooms/api/navigation/history/` | GET | Historial de habitaciones visitadas |
| `get_user_current_room` | `/rooms/api/user/current-room/` | GET | Habitación actual del jugador |
| `room_view` | `/rooms/room/<int:room_id>/` | GET | Vista JSON de la habitación actual |
| `navigate_room` | `/rooms/navigate/<str:direction>/` | GET | Navega en dirección — retorna JSON |

### APIs del entorno 3D

| Vista | URL | Descripción |
|-------|-----|-------------|
| `get_room_3d_data` | `/rooms/api/3d/rooms/<id>/data/` | Datos completos 3D: geometría, objetos, conexiones, player |
| `room_transition` | `/rooms/api/3d/transition/` | Transición desde entorno 3D |
| `update_player_position` | `/rooms/api/3d/player/position/` | Actualiza posición XY del jugador |
| `get_player_status` | `/rooms/api/3d/player/status/` | Estado completo del jugador |

### `CentrifugoMixin` — Broadcasting en tiempo real

```python
class CentrifugoMixin:
    def get_room_member_channels(self, room_id):
        # Retorna ['personal:{user_id}', ...] para todos los miembros
    
    def broadcast_room(self, room_id, broadcast_payload):
        # Modos: 'api' | 'outbox' | 'cdc' | 'api_cdc'
        # Controlado por settings.CENTRIFUGO_BROADCAST_MODE
```

Requiere en `settings.py`:
- `CENTRIFUGO_HTTP_API_ENDPOINT`
- `CENTRIFUGO_HTTP_API_KEY`
- `CENTRIFUGO_BROADCAST_MODE`
- `CENTRIFUGU_OUTBOX_PARTITIONS` (typo en el nombre — con doble U)

---

## 5. URLs

> ✅ `app_name = 'rooms'` declarado correctamente.

El mapa completo está en el CONTEXT.md. Puntos clave:

- Todas las rutas bajo prefijo `/rooms/` (según include en urls raíz)
- PKs son int — `<int:pk>` y `<int:room_id>`
- `room_view` y `navigate_room` importados directamente en `urls.py` (no vía `views.`)

---

## 6. Convenciones Críticas

### Propietario: `owner`, no `created_by`

```python
# CORRECTO en rooms
room = get_object_or_404(Room, pk=pk)
if room.owner != request.user:
    # denegar acceso

# Para verificar gestión:
room.can_user_manage(request.user)  # owner OR admin/moderator member

# INCORRECTO — rooms no tiene created_by en Room
```

### `creator` vs `owner`

`Room` tiene **ambos campos**. `owner` es el propietario real (permisos). `creator` es quien la creó originalmente (puede ser diferente si el ownership se transfiere). Siempre se asignan iguales en la creación:

```python
room.owner = request.user
room.creator = request.user
```

### PKs son int

```python
# CORRECTO
room = get_object_or_404(Room, pk=pk)  # pk es int
{% url 'rooms:room_detail' pk=room.id %}

# INCORRECTO — no usar uuid
```

### `PlayerProfile` — acceso seguro

```python
# CORRECTO — verificar antes de acceder
if hasattr(request.user, 'player_profile'):
    player_profile = request.user.player_profile
    # usar player_profile

# INCORRECTO — puede lanzar RelatedObjectDoesNotExist
player = request.user.player_profile  # sin verificar
```

### Centrifugo vs Django Channels

`rooms` usa **Centrifugo** para broadcasting (via `CentrifugoMixin`). `chat` usa **Django Channels** (WebSockets). Son dos sistemas de tiempo real distintos en el mismo proyecto. No mezclarlos.

### `RoomListViewSet` filtra por membresía — no retorna todas las salas

```python
# Este ViewSet solo retorna salas donde el usuario ES MIEMBRO
RoomListViewSet  # → Room.objects.filter(members__id=user_id)

# Para todas las salas:
Room.objects.all()  # usado en room_list (vista UI)
```

### Idempotencia de `basic_3d_environment`

Llama a múltiples `get_or_create`. Es seguro llamarla varias veces — crea la estructura solo la primera vez. Usarla como setup inicial del entorno 3D de pruebas.

---

## 7. Bugs Conocidos

| # | Estado | Descripción |
|---|--------|-------------|
| B1 | ⬜ activo | `portal_list` y `portal_detail` definidas dos veces en `views.py` (L594-596 y L603-611) — Python usa la segunda definición; primera es código muerto |
| B2 | ⬜ activo | `room_detail` (L135) usa `logger` antes de su declaración (L739) — en Python esto funciona porque `logger` se resuelve en tiempo de ejecución, pero es confuso y potencialmente problemático si se reorganiza el archivo |
| B3 | ⬜ activo | `room_detail` (L135) sin `@login_required` — cualquier anónimo puede ver detalles de sala |
| B4 | ⬜ activo | `room_list` (L708) usa `redirect('login')` manual en lugar de `@login_required` — inconsistente con el resto del proyecto |
| B5 | ⬜ activo | `room_comments` (L424) llama `room.comments.create(text=comment, user=request.user)` — el campo `Comment.comment` es `TextField`, no `text` — esto lanzará `TypeError` al ejecutarse |
| B6 | ⬜ activo | `create_entrance_exit` (L459) redirige a `reverse_lazy('entrance_exit_list')` sin namespace `rooms:` — puede romper la redirección |
| B7 | ⬜ activo | `create_entrance_exit` template hardcodeado como `'create_entrance_exit.html'` sin prefijo `rooms/` — probablemente inexistente |
| B8 | ⬜ activo | `create_portal` (L584) redirige a `reverse_lazy('portal_list')` sin namespace — mismo problema que B6 |
| B9 | ⬜ activo | `PlayerProfile.calculate_new_position()` solo implementa NORTH/SOUTH — EAST/WEST retornan `None` implícitamente, corrompiendo posición |
| B10 | ⬜ activo | `navigate_room` (L1574) llama `entrance.face.opposite()` — `str` no tiene método `.opposite()`; esto lanzará `AttributeError` |
| B11 | ⬜ activo | `EntranceExitCRUDViewSet.get_queryset()` ordena por `-created_at` — `EntranceExit` no tiene `created_at` en el modelo — lanzará `FieldError` |
| B12 | ⬜ activo | `PortalCRUDViewSet.get_queryset()` ordena por `-created_at` — `Portal` no tiene `created_at` — mismo problema que B11 |
| B13 | ⬜ activo | `RoomConnectionCRUDViewSet.get_queryset()` ordena por `-created_at` — `RoomConnection` no tiene `created_at` — mismo problema |
| B14 | ⬜ activo | `CENTRIFUGU_OUTBOX_PARTITIONS` — typo en settings key (doble U en "CENTRIFUGU") — si la key está bien escrita en settings, el acceso fallará |
| B15 | ⬜ activo | Todos los modelos usan `user` en lugar de `created_by` — fuera de convención (excepto `RoomNotification.created_by` ✅) |
| B16 | ⬜ activo | `room_search` (L729) decorado con `@api_view(['GET'])` pero retorna `render()` (template HTML) — mezcla DRF con Django views; el content negotiation de DRF puede interferir |

---

## 8. Deuda Técnica

**Alta prioridad (bugs que rompen funcionalidad):**
- **Fix `room_comments`** — campo `text` → `comment` en `create()` (B5)
- **Fix `navigate_room`** — `entrance.face.opposite()` → mapa de opuestos manual (B10)
- **Fix `calculate_new_position`** — agregar ramas EAST/WEST (B9)
- **Fix ViewSets con `order_by('-created_at')`** — `EntranceExit`, `Portal` y `RoomConnection` no tienen ese campo (B11, B12, B13)
- **Agregar `@login_required` a `room_detail`** (B3)

**Media prioridad:**
- **Resolver funciones duplicadas** `portal_list` y `portal_detail` (B1)
- **Fix namespaces** en `create_entrance_exit` y `create_portal` redirects (B6, B8)
- **Fix template path** en `create_entrance_exit` (B7)
- **Verificar typo** `CENTRIFUGU_OUTBOX_PARTITIONS` en settings (B14)
- **Corregir `room_search`** — no mezclar `@api_view` con `render()` (B16)
- **Mover imports** de DRF y `logger` al tope del archivo — eliminan el problema del `logger` usado antes de declararse
- **Documentar `signals.py` y `utils.py`** — no revisados en esta sesión

**Baja prioridad:**
- **Agregar `created_at` a `EntranceExit`, `Portal` y `RoomConnection`** para consistencia y para que los ViewSets funcionen
- **Refactorizar `views.py`** (2858 líneas) — separar en `views/ui.py`, `views/api.py`, `views/navigation.py`, `views/3d.py`
- Migrar `user` → `created_by` donde aplique
- Implementar `RoomManager` con lógica real (actualmente solo hereda de `Manager` con `pass`)
- Documentar integración con Centrifugo en settings
