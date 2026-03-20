# Diseño y Roadmap — App `rooms`

> **Actualizado:** 2026-03-19  
> **Estado:** Funcional con bugs activos de runtime — documentación generada esta sesión  
> **Sprint actual:** 7 completado | Próximo: Sprint 8

---

## Visión General

`rooms` es la **app de espacios virtuales** de Management360 y la más compleja del proyecto por la cantidad de modelos, la profundidad funcional y el alcance arquitectónico que cubre tres capas completamente distintas.

```
┌────────────────────────────────────────────────────────────────┐
│                         APP ROOMS                              │
│                                                                │
│  ┌─────────────────────────┐  ┌────────────────────────────┐   │
│  │  CHAT EN TIEMPO REAL    │  │   MUNDO VIRTUAL (Juego)    │   │
│  │                         │  │                            │   │
│  │  Room + Message         │  │  PlayerProfile             │   │
│  │  MessageRead            │  │  EntranceExit (puerta)     │   │
│  │  RoomMember             │  │  RoomConnection            │   │
│  │  Notification           │  │  Portal (cooldown)         │   │
│  │  RoomNotification       │  │  RoomObject                │   │
│  │                         │  │  TransitionManager         │   │
│  │  → base de chat app     │  │  → navegación gamificada   │   │
│  └─────────────────────────┘  └────────────────────────────┘   │
│                                                                │
│  ┌────────────────────────────────────────────────────────┐    │
│  │  ENTORNO 3D (Three.js + SVG isométrico)                │    │
│  │  room_3d_interactive.html (902 líneas)                 │    │
│  │  API: get_room_3d_data, update_player_position, etc.   │    │
│  │  → visualización 3D de habitaciones                    │    │
│  └────────────────────────────────────────────────────────┘    │
│                                                                │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  BROADCASTING                                           │   │
│  │  CentrifugoMixin: api | outbox | cdc | api_cdc          │   │
│  │  Outbox + CDC models → Debezium/Kafka                   │   │
│  └─────────────────────────────────────────────────────────┘   │
└────────────────────────────────────────────────────────────────┘
         │
         ├── chat (consume Room, Message, MessageRead, RoomMember)
         └── events (pendiente formalizar)
```

---

## Estado de Implementación

| Módulo | Estado | Observaciones |
|--------|--------|---------------|
| Modelo `Room` (30+ campos) | ✅ Completo | Geometría 3D, física, apariencia |
| Chat en tiempo real (modelos) | ✅ Completo | Message, MessageRead, RoomMember |
| Sistema de notificaciones real | ✅ Completo | `Notification` + `RoomNotification` — correctos |
| CRUD de salas (UI) | ✅ Funcional | create, create-complete, delete, detail, list |
| CRUD de salas (API REST) | ✅ Completo | `RoomCRUDViewSet` con permisos |
| Sistema de navegación (juego) | ⚠️ Parcial | Bugs activos en `navigate_room` y `calculate_new_position` |
| `PlayerProfile` | ⚠️ Parcial | Métodos con bugs (EAST/WEST, `.opposite()`) |
| `EntranceExit` (puertas) | ✅ Modelo completo | 30+ campos, lógica de transición |
| `RoomTransitionManager` | ✅ Funcional | No revisado en detalle |
| Portales con cooldown | ✅ Modelo completo | `is_active()` funcional |
| Entorno 3D interactivo | ✅ Funcional | Three.js, room_3d_interactive.html |
| Vista 3D SVG isométrica | ✅ Funcional | `generate_room_3d_svg()` |
| APIs 3D | ✅ Funcional | get_room_3d_data, transitions, player |
| Centrifugo broadcasting | ✅ Implementado | 4 modos — requiere config en settings |
| `room_comments` | 🔴 Bug crítico | Llama campo incorrecto — lanza TypeError |
| CRUD ViewSets de puertas/portales | 🔴 Bug activo | `order_by('-created_at')` en modelos sin ese campo |
| Tests | ⚠️ Management commands | tests en `management/commands/` — no tests unitarios reales |
| Documentación | ✅ Esta sesión | Primera documentación formal |

---

## Arquitectura de Datos

### Jerarquía de modelos

```
Room
  ├── RoomMember (M2M users through RoomMember)
  ├── Message (related: 'messages')
  │     └── MessageRead (related: 'reads')
  ├── Notification (related_room FK)
  ├── RoomNotification (related: 'room_notifications')
  ├── EntranceExit (related: 'entrance_exits')
  │     └── RoomConnection (FK entrance)
  │           ├── from_room → Room
  │           └── to_room → Room
  ├── Room.portals (M2M → Portal)
  │     ├── entrance → EntranceExit
  │     └── exit → EntranceExit
  ├── RoomObject (related: 'room_objects')
  ├── Room.parent_room (self FK, related: 'child_of_rooms')
  └── Room.connections (M2M self through RoomConnection)

PlayerProfile (OneToOne → User)
  └── current_room → Room
```

### Dependencias cross-app

```
rooms ← chat     (chat importa Room, Message, MessageRead, RoomMember en 15+ lugares)
rooms ← events   (pendiente formalizar — según PROJECT_DESIGN)
rooms ← chat.UserPresence (FK a rooms.Room)
rooms ← chat.MessageReaction (FK a rooms.Message)
rooms → accounts.User (todos los FK de propietario)
```

`rooms` es el **proveedor de infraestructura** de `chat`. Modificar los modelos de `rooms` requiere verificar el impacto en `chat`.

### Settings requeridos para Centrifugo

```python
# panel/settings.py — requeridos para CentrifugoMixin
CENTRIFUGO_HTTP_API_ENDPOINT = 'http://localhost:8000'
CENTRIFUGO_HTTP_API_KEY = '...'
CENTRIFUGO_BROADCAST_MODE = 'api'  # 'api' | 'outbox' | 'cdc' | 'api_cdc'
CENTRIFUGU_OUTBOX_PARTITIONS = 16  # ⚠️ typo — doble U
```

Si Centrifugo no está configurado, `MessageListCreateAPIView.create()` y `JoinRoomView`/`LeaveRoomView` lanzarán errores al intentar hacer broadcast.

---

## Roadmap

### Deuda inmediata — bugs de runtime (pre-Sprint 8)

| ID | Tarea | Prioridad |
|----|-------|-----------|
| ROOM-1 | Fix `room_comments`: `room.comments.create(text=...)` → `Comment.objects.create(room=room, user=..., comment=...)` | 🔴 |
| ROOM-2 | Fix `navigate_room`: `entrance.face.opposite()` → dict de opuestos `{'NORTH':'SOUTH', ...}` | 🔴 |
| ROOM-3 | Fix `calculate_new_position`: agregar ramas EAST, WEST, UP, DOWN | 🔴 |
| ROOM-4 | Fix ViewSets con `order_by('-created_at')`: agregar el campo a `EntranceExit`, `Portal`, `RoomConnection` o cambiar el ordering | 🔴 |
| ROOM-5 | Agregar `@login_required` a `room_detail`, `room_list`, `room_comments`, `room_evaluations` | 🟠 |

### Sprint 8

| ID | Tarea | Prioridad |
|----|-------|-----------|
| ROOM-6 | Fix namespaces en redirects de `create_entrance_exit` y `create_portal` | 🟠 |
| ROOM-7 | Fix/crear template `create_entrance_exit.html` | 🟠 |
| ROOM-8 | Resolver funciones duplicadas `portal_list` y `portal_detail` | 🟠 |
| ROOM-9 | Verificar y corregir typo `CENTRIFUGU_OUTBOX_PARTITIONS` en código y settings | 🟠 |
| ROOM-10 | Fix `room_search` — no mezclar `@api_view` con `render()` | 🟠 |
| ROOM-11 | Mover todos los imports al tope del archivo — DRF imports en línea 735 | 🟡 |
| ROOM-12 | Conectar `chat.HardcodedNotificationManager` → `rooms.Notification` real | 🔴 |

### Sprint 9

| ID | Tarea | Prioridad |
|----|-------|-----------|
| ROOM-13 | Refactorizar `views.py` (2858 líneas) en módulos por capa funcional | 🟠 |
| ROOM-14 | Documentar y revisar `signals.py` y `utils.py` | 🟠 |
| ROOM-15 | Implementar `RoomManager` con lógica útil (actualmente `pass`) | 🟡 |
| ROOM-16 | Agregar tests unitarios reales (actualmente solo management commands) | 🟡 |
| ROOM-17 | Evaluar separación de la capa de juego en app propia (`world` o `game`) | 🟡 |

---

## Notas para Claude

- **Propietario `owner`**, NO `created_by` — para acceso seguro usar `get_object_or_404(Room, pk=pk)` luego `room.can_user_manage(request.user)` o `room.owner == request.user`
- **`Room` tiene `creator` Y `owner`** — ambos se asignan a `request.user` en creación; no son lo mismo conceptualmente
- **PKs son int** — `<int:pk>`, no UUID
- **`PlayerProfile` se accede como `request.user.player_profile`** — SIEMPRE verificar con `hasattr(request.user, 'player_profile')` antes, o usar `try/except PlayerProfile.DoesNotExist`
- **Tres sistemas de tiempo real coexisten:** Django Channels (chat), Centrifugo (rooms broadcasting), y polling simple para presencia
- **`room_comments` está roto** — no intentar usarlo hasta fix ROOM-1
- **`navigate_room` está roto** — no usarlo hasta fix ROOM-2
- **Los ViewSets de puertas/portales/conexiones están rotos** — lanzarán `FieldError` al listar
- **`Notification` en `rooms` es el modelo real** de notificaciones — `chat.HardcodedNotificationManager` debe migrar hacia este modelo (ROOM-12 / CHAT-1)
- **`RoomTransitionManager`** es el punto central de la lógica de navegación — siempre delegar a él en lugar de reimplementar la lógica de transición
- **`room_search` usa `@api_view`** pero retorna HTML — responderá con `406 Not Acceptable` si el cliente envía `Accept: application/json` y podría causar problemas con DRF
- **`CENTRIFUGU_OUTBOX_PARTITIONS`** tiene un typo (doble U) — buscar y verificar que el nombre sea consistente en todo el código
- **`basic_3d_environment`** es idempotente — crea estructura de ejemplo solo si no existe; seguro de llamar múltiples veces
