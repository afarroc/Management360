# Referencia de Desarrollo — App `chat`

> **Actualizado:** 2026-03-19  
> **Audiencia:** Desarrolladores y asistentes IA  
> **Archivos:** 27 | **Vistas:** 2017 líneas (monolito) | **Templates:** 12 | **Endpoints:** 40  
> **Namespace:** `chat` ✅ declarado en `urls.py`  
> **Migración activa:** `0001_initial`

---

## Índice

| Sección | Contenido |
|---------|-----------|
| 1. Resumen | Dos subsistemas principales |
| 2. Modelos | 5 modelos + 1 clase utilitaria |
| 3. Archivos adicionales | consumers, routing, ollama, functions |
| 4. Vistas | Organizadas por subsistema |
| 5. URLs | Mapa completo de 40 endpoints |
| 6. Convenciones críticas | Gotchas, patrones, dependencias |
| 7. Bugs conocidos | Issues activos — lista extensa |
| 8. Deuda técnica | Clasificada por prioridad |

---

## 1. Resumen

`chat` tiene **dos subsistemas completamente distintos** que comparten el mismo archivo `views.py`:

**Subsistema 1 — Chat en tiempo real (salas)**
Gestión de salas de chat con mensajes en tiempo real via Django Channels (WebSockets). Los modelos de sala y mensaje viven en `rooms` — `chat` solo provee las vistas, APIs de lectura/escritura y el consumer WebSocket.

**Subsistema 2 — Asistente IA (Ollama)**
Interfaz conversacional con un modelo de lenguaje local via Ollama. Gestiona conversaciones persistentes (`Conversation`), historial en JSONField, comandos ejecutables (`/funcion params`), configuraciones del asistente (`AssistantConfiguration`) y streaming de respuestas via SSE.

**Módulos adicionales clave:**
- `consumers.py` (427 líneas) — WebSocket consumer para chat en tiempo real
- `notifications_consumer.py` (60 líneas) — WebSocket consumer para notificaciones
- `ollama_api.py` (167 líneas) — cliente async para la API de Ollama
- `functions.py` (409 líneas) — registro de funciones ejecutables por el asistente
- `routing.py` — configuración de rutas WebSocket

---

## 2. Modelos

### `Conversation` — Historial IA

```python
class Conversation(models.Model):
    user            # FK → User (CASCADE)
    conversation_id # CharField(100, unique=True) — ID de formato "conv_{user_id}_{timestamp}"
    title           # CharField(200, blank) — autogenerado del primer mensaje
    messages        # JSONField(default=list) — lista completa de mensajes
    created_at      # DateTimeField(auto_now_add)
    updated_at      # DateTimeField(auto_now)
    is_active       # BooleanField(default=True)

    class Meta:
        ordering = ['-updated_at']
```

**Estructura de cada mensaje en `messages` (JSONField):**
```python
{
    'sender':      'user' | 'ai',
    'content':     str,
    'timestamp':   ISO 8601,
    'sender_name': str | None,
    'type':        'text' | 'command' | 'command_response' | 'error'
}
```

**Métodos clave:**

| Método | Descripción |
|--------|-------------|
| `add_message(sender, content, sender_name, message_type)` | Append + `save(update_fields=['messages','updated_at'])` |
| `get_messages_for_ai()` | Lista `{role, content}` para Ollama — excluye type='error' |
| `generate_title()` | Toma primeros 50 chars del primer mensaje de usuario |
| `get_or_create_active_conversation(user)` | ClassMethod — busca `is_active=True` más reciente o crea nueva |
| `get_recent_messages(limit=50)` | Slice `self.messages[-limit:]` |

⚠️ **Semántica de `is_active`:** NO es soft delete — indica la conversación "en curso" del usuario. Un usuario puede tener múltiples `is_active=True` simultáneamente (no hay constraint). El sistema desactiva las demás al cambiar de conversación, pero no es atómico.

⚠️ **Propietario `user`**, no `created_by` — violación de convención del proyecto.

---

### `CommandLog` — Registro de comandos IA

```python
class CommandLog(models.Model):
    user           # FK → User (CASCADE)
    command        # TextField — input original del usuario
    function_name  # CharField(100)
    params         # JSONField(default=dict)
    result         # JSONField(null=True, blank=True)
    success        # BooleanField(default=False)
    execution_time # FloatField(default=0.0) — segundos
    executed_at    # DateTimeField(auto_now_add)
    error_message  # TextField(blank=True)

    class Meta:
        ordering = ['-executed_at']
```

⚠️ Propietario `user`, no `created_by`. Sin `updated_at`. Sin `is_active`.

---

### `AssistantConfiguration` — Config del modelo IA

```python
class AssistantConfiguration(models.Model):
    user              # FK → User (CASCADE)
    name              # CharField(100)
    is_active         # BooleanField(default=False) — solo una activa por usuario

    # Parámetros del modelo
    model_name        # CharField(100, default='llama2')
    temperature       # FloatField(default=0.7)  — rango 0.0–2.0
    max_tokens        # IntegerField(default=2048)
    top_p             # FloatField(default=0.9)
    top_k             # IntegerField(default=40)

    # Prompts
    system_prompt     # TextField — comportamiento del asistente
    initial_context   # TextField(blank=True)

    # Datos extra
    additional_data   # JSONField(default=dict) — texto, archivos subidos
    enabled_functions # JSONField(default=list) — funciones habilitadas

    created_at        # DateTimeField(auto_now_add)
    updated_at        # DateTimeField(auto_now)
```

**`save()` override:** al activar una config (`is_active=True`), desactiva todas las otras del mismo usuario via `update()`. Patrón correcto — similar a `GTDProcessingSettings` en `events`.

**Métodos de clase:**

| Método | Descripción |
|--------|-------------|
| `get_active_config(user)` | `.filter(is_active=True).first()` — puede retornar None |
| `get_or_create_default(user)` | Obtiene activa o crea una con defaults |

⚠️ Propietario `user`, no `created_by`.

---

### `HardcodedNotificationManager` — Placeholder de notificaciones

**No es un modelo Django.** Es una clase Python pura que retorna notificaciones hardcodeadas (2 dicts estáticos). Toda la funcionalidad de notificaciones está simulada — no persiste en BD.

```python
class HardcodedNotificationManager:
    # Retorna siempre las mismas 2 notificaciones fijas
    # "Bienvenido al sistema" + "Actualización disponible"
    # is_read siempre False — no hay persistencia de lectura
```

**⚠️ Deuda crítica** — es un stub de testing que llegó a producción. Todos los endpoints de notificaciones (`/api/notifications/*`) retornan datos falsos. Ver B1.

---

### `UserPresence` — Presencia en tiempo real

```python
class UserPresence(models.Model):
    user         # OneToOneField → User (CASCADE)
    status       # CharField(10) — 'online'|'away'|'offline', default='offline'
    last_seen    # DateTimeField(default=timezone.now)
    current_room # FK → rooms.Room (SET_NULL, nullable)
```

**Métodos:**
- `is_online()` → `status == 'online'` AND `last_seen` hace < 300 segundos
- `update_presence(status, room=None)` → actualiza y guarda

⚠️ FK directa a `rooms.Room` — acoplamiento cross-app en el modelo.

---

### `MessageReaction` — Reacciones emoji

```python
class MessageReaction(models.Model):
    user       # FK → User (CASCADE)
    message    # FK → rooms.Message (CASCADE, related_name='reactions')
    emoji      # CharField(10)
    created_at # DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ('message', 'user', 'emoji')
```

⚠️ FK directa a `rooms.Message` — modelo de `chat` que depende de `rooms`.

---

## 3. Archivos Adicionales

### `consumers.py` (427 líneas) — WebSocket Chat

Consumer de Django Channels para el chat en tiempo real. Gestiona conexión/desconexión, broadcast de mensajes al grupo de sala, comandos en tiempo real y notificaciones push.

```python
# routing.py
websocket_urlpatterns = [
    path('ws/chat/<str:room_name>/', consumers.ChatConsumer.as_asgi()),
    path('ws/notifications/', notifications_consumer.NotificationConsumer.as_asgi()),
]
```

### `ollama_api.py` (167 líneas) — Cliente Ollama

Función async `generate_response(messages)` que llama a la API local de Ollama (`http://localhost:11434`). Retorna un async generator de chunks para streaming.

⚠️ URL de Ollama hardcodeada — no usa variable de entorno ni `settings`.

### `functions.py` (409 líneas) — Registro de funciones IA

Sistema de funciones ejecutables por el asistente via comandos (`/nombre_funcion param1=val param2=val`). Incluye `function_registry`, `parse_command()` y `logged_functions` (wrappers que persisten en `CommandLog`).

### `views_redis.py` (38 líneas) — Status de Redis

Vista de diagnóstico que muestra el estado de la conexión Redis. Separada del `views.py` principal.

### `views/api_last_room.py` (12 líneas)

Una sola función `last_room_api` — duplicada también en `views.py`. Ver B2.

---

## 4. Vistas

### Vistas de UI — Subsistema Salas

| Vista | URL | Template | Descripción |
|-------|-----|----------|-------------|
| `index` | `/chat/` | `chat/index.html` | Panel de entrada al chat |
| `room_list` | `/chat/rooms/` | `chat/room_list.html` | Lista de salas con stats y no-leídos |
| `room` | `/chat/room/<str:room_name>/` | `chat/room.html` | Sala individual (room_name es el ID int) |
| `redirect_to_last_room` | `/chat/room/` | — | Redirige a la última sala activa del usuario |
| `chat_panel` | `/chat/panel/` | `chat/panel.html` | Panel flotante embebible en otras páginas |
| `room_admin` | `/chat/room/<int:room_id>/admin/` | `chat/room_admin.html` | Admin de sala — **duplicada** (ver B3) |

⚠️ `room()` recibe `room_name` como `str` pero lo usa como `Room.objects.get(id=room_name)` — el "nombre" es realmente el ID int de la sala. Inconsistencia histórica.

### Vistas de UI — Subsistema IA

| Vista | URL | Template | Descripción |
|-------|-----|----------|-------------|
| `assistant_view` | `/chat/ui/` | `chat/assistant.html` | Interfaz del asistente IA |
| `functions_panel` | `/chat/functions/` | `chat/functions_panel.html` | Lista de funciones disponibles con stats |
| `command_history` | `/chat/commands/` | `chat/command_history.html` | Historial de comandos ejecutados |
| `conversation_history` | `/chat/conversations/` | `chat/conversation_history.html` | Lista de conversaciones IA |
| `conversation_detail` | `/chat/conversation/<str:conversation_id>/` | `chat/conversation_detail.html` | Detalle de una conversación |
| `assistant_configurations` | `/chat/configurations/` | `chat/assistant_configurations.html` | Lista de configs del asistente |

### `chat_view` — Motor del asistente IA (POST `/chat/assistant/`)

Vista central del subsistema IA. Acepta GET (status check) y POST (mensaje). Flujo POST:

```
1. Rate limit check (5 req/60s por usuario, cache Redis)
2. Obtener/crear Conversation activa
3. ¿Mensaje es comando (/función params)?
   ├── Sí → parse_command() → logged_func() → JsonResponse
   └── No → continuar
4. moderate_message() — lista de palabras prohibidas hardcodeadas
5. Cargar historial (POST chat_history o desde Conversation activa)
6. Guardar mensaje en Conversation
7. generate_response() → StreamingHttpResponse (SSE)
   └── finally: guardar respuesta IA en Conversation
```

**Respuesta streaming:** `text/event-stream`, formato `data: {"content": "..."}\n\n`, finaliza con `data: [DONE]\n\n`.

⚠️ Tiene `@csrf_exempt` — violación de convención.

### APIs de mensajes y salas

| Vista | URL | Método | Descripción |
|-------|-----|--------|-------------|
| `mark_messages_read_api` | `/api/chat/mark-read/` | POST | Marca IDs específicos como leídos |
| `unread_count_api` | `/api/chat/unread-count/` | GET | Cuenta no leídos por sala o global |
| `reset_unread_count_api` | `/api/chat/reset-unread/` | POST | Marca todos como leídos — **duplicada** (ver B4) |
| `room_history_api` | `/api/chat/room-history/<int:room_id>/` | GET | Historial últimos 50 mensajes |
| `room_list_api` | `/api/chat/room-list/` | GET | Lista de salas |
| `search_history` | `/api/chat/search/` | GET | Búsqueda en mensajes |
| `search_messages` | `/api/chat/search-messages/` | GET | Búsqueda con filtros avanzados |
| `add_reaction` | `/api/chat/reaction/<int:message_id>/` | POST | Toggle de reacción emoji |
| `update_presence` | `/api/chat/presence/` | POST | Actualiza presencia del usuario |
| `get_presence` | `/api/chat/presence/status/` | GET | Obtiene presencia de usuarios en sala |
| `last_room_api` | `/api/chat/last-room/` | GET | Última sala del usuario |
| `room_members_api` | `/api/room/<int:room_id>/members/` | GET | Miembros de una sala |
| `room_notifications_api` | `/api/room/<int:room_id>/notifications/` | GET/POST | Notifs de sala — **duplicada** (ver B5) |

### APIs de notificaciones

Todas retornan datos de `HardcodedNotificationManager` — **notificaciones falsas** en producción.

| Vista | URL | Nota |
|-------|-----|------|
| `unread_notifications_api` | `/api/notifications/unread/` | Siempre retorna 2 notifs hardcodeadas |
| `mark_notifications_read_api` | `/api/notifications/mark-read/` | Simula marcar como leído, no persiste — **duplicada** (ver B6) |
| `test_create_notification` | `/api/notifications/test-create/` | Endpoint de prueba en producción |

### APIs de conversaciones IA

| Vista | URL | Método | Descripción |
|-------|-----|--------|-------------|
| `conversations_api` | `/api/conversations/` | GET | Lista últimas 20 conversaciones |
| `switch_conversation_api` | `/api/conversation/<str:id>/switch/` | POST | Cambia conversación activa |
| `conversation_messages_api` | `/api/conversation/<str:id>/messages/` | GET | Mensajes de una conversación |
| `new_conversation_api` | `/api/conversation/new/` | POST | Crea nueva conversación |

### Vistas de configuración IA

| Vista | URL | Método | Descripción |
|-------|-----|--------|-------------|
| `create_assistant_configuration` | `/configurations/create/` | GET/POST | Crear config — sin form Django, lee `request.POST` directo |
| `edit_assistant_configuration` | `/configurations/<int:config_id>/edit/` | GET/POST | Editar config + upload archivos |
| `delete_assistant_configuration` | `/configurations/<int:config_id>/delete/` | POST | Eliminar config |
| `set_active_configuration` | `/configurations/<int:config_id>/set-active/` | POST | Activar config |

---

## 5. URLs

> ✅ `app_name = 'chat'` declarado correctamente en `urls.py`.

| URL | Name | Auth | Método |
|-----|------|------|--------|
| `/chat/` | `chat:index` | ✅ | GET |
| `/chat/rooms/` | `chat:room_list` | ✅ | GET |
| `/chat/room/` | `chat:redirect_to_last_room` | ✅ | GET |
| `/chat/room/<str:room_name>/` | `chat:room` | ✅ | GET |
| `/chat/assistant/` | `chat:chat_api` | ✅⚠️csrf | GET/POST |
| `/chat/ui/` | `chat:assistant_ui` | ✅ | GET |
| `/chat/functions/` | `chat:functions_panel` | ✅ | GET |
| `/chat/commands/` | `chat:command_history` | ✅ | GET |
| `/chat/conversations/` | `chat:conversation_history` | ✅ | GET |
| `/chat/conversation/<str:conversation_id>/` | `chat:conversation_detail` | ✅ | GET |
| `/chat/clear/` | `chat:clear_history` | ✅ | GET/POST |
| `/chat/clear_history/<str:room_name>/` | `chat:clear_history_room` | ✅ | POST |
| `/chat/api/chat/last-room/` | `chat:api_last_room` | ✅ | GET |
| `/chat/api/chat/room-list/` | `chat:api_room_list` | ✅⚠️csrf | GET |
| `/chat/api/chat/room-history/<int:room_id>/` | `chat:api_room_history` | ✅⚠️csrf | GET |
| `/chat/api/chat/mark-read/` | `chat:api_mark_read` | ✅⚠️csrf | POST |
| `/chat/api/chat/unread-count/` | `chat:api_unread_count` | ✅⚠️csrf | GET |
| `/chat/api/chat/reset-unread/` | `chat:api_reset_unread` | ✅⚠️csrf | POST |
| `/chat/api/notifications/unread/` | `chat:api_unread_notifications` | ✅ | GET |
| `/chat/api/notifications/mark-read/` | `chat:api_mark_notifications_read` | ✅⚠️csrf | POST |
| `/chat/api/notifications/test-create/` | `chat:api_test_create_notification` | ✅ | POST |
| `/chat/api/chat/search/` | `chat:api_search_history` | ✅⚠️csrf | GET |
| `/chat/api/chat/search-messages/` | `chat:api_search_messages` | ✅⚠️csrf | GET |
| `/chat/api/chat/reaction/<int:message_id>/` | `chat:api_add_reaction` | ✅⚠️csrf | POST |
| `/chat/api/chat/presence/` | `chat:api_update_presence` | ✅⚠️csrf | POST |
| `/chat/api/chat/presence/status/` | `chat:api_get_presence` | ✅ | GET |
| `/chat/api/room/<int:room_id>/members/` | `chat:api_room_members` | ✅ | GET |
| `/chat/api/room/<int:room_id>/notifications/` | `chat:api_room_notifications` | ✅⚠️csrf | GET/POST |
| `/chat/panel/` | `chat:chat_panel` | ✅⚠️csrf | GET |
| `/chat/stats/` | `chat:chat_stats` | ✅ | GET |
| `/chat/room/<int:room_id>/admin/` | `chat:room_admin` | ✅ | GET/POST |
| `/chat/api/conversations/` | `chat:api_conversations` | ✅⚠️csrf | GET |
| `/chat/api/conversation/<str:id>/switch/` | `chat:api_switch_conversation` | ✅⚠️csrf | POST |
| `/chat/api/conversation/<str:id>/messages/` | `chat:api_conversation_messages` | ✅⚠️csrf | GET |
| `/chat/api/conversation/new/` | `chat:api_new_conversation` | ✅⚠️csrf | POST |
| `/chat/configurations/` | `chat:assistant_configurations` | ✅ | GET |
| `/chat/configurations/create/` | `chat:create_assistant_configuration` | ✅ | GET/POST |
| `/chat/configurations/<int:config_id>/edit/` | `chat:edit_assistant_configuration` | ✅ | GET/POST |
| `/chat/configurations/<int:config_id>/delete/` | `chat:delete_assistant_configuration` | ✅ | POST |
| `/chat/configurations/<int:config_id>/set-active/` | `chat:set_active_configuration` | ✅⚠️csrf | POST |

---

## 6. Convenciones Críticas

### Propietario: `user`, no `created_by` — en todos los modelos de chat

```python
# CORRECTO en chat
conv = get_object_or_404(Conversation, conversation_id=cid, user=request.user)
config = get_object_or_404(AssistantConfiguration, id=config_id, user=request.user)

# INCORRECTO — no existe created_by en estos modelos
```

### `room_name` en URL es el ID int de la sala, no un nombre

```python
# chat/urls.py
path('room/<str:room_name>/', views.room, name='room')

# En views.py:
room_obj = Room.objects.get(id=room_name)  # id numérico pasado como str
```

Al construir URLs hacia salas: `{% url 'chat:room' room_name=room.id %}`.

### Streaming SSE en `chat_view`

```python
# Cliente JS debe leer el stream así:
const eventSource = new EventSource('/chat/assistant/');
eventSource.onmessage = (e) => {
    if (e.data === '[DONE]') return;
    const chunk = JSON.parse(e.data);
    // chunk.content tiene el texto parcial
    // chunk.error tiene el error si ocurrió
};
```

### Rate limit del asistente

Implementado con Redis: `chat_rate_{user_id}`, máx 5 requests/60s. Si se excede, retorna 429.

### `conversation_id` — formato y búsqueda

El campo `conversation_id` tiene formato `conv_{user_id}_{unix_timestamp}`. La vista `conversation_detail` intenta resolverlo de tres formas distintas (por `conversation_id`, por `id` numérico, por fallback) — señal de que el campo fue inconsistente en algún momento.

### Caché del historial

```python
cache_key = f'chat_history_{request.user.id}'
cache.set(cache_key, chat_history, timeout=3600)  # 1 hora
```
Caché de compatibilidad — el sistema real de historial usa la `Conversation` en BD.

### Dependencia en tiempo real: Django Channels + Redis

El consumer WebSocket requiere:
1. `CHANNEL_LAYERS` configurado en `settings.py` con Redis
2. Daphne corriendo como servidor ASGI
3. Sin Daphne, las rutas WebSocket (`ws/chat/`, `ws/notifications/`) no funcionan

### Ollama debe estar corriendo localmente

`ollama_api.py` apunta a `http://localhost:11434`. Sin Ollama activo, `chat_view` retorna error en la respuesta de streaming.

---

## 7. Bugs Conocidos

| # | Estado | Descripción |
|---|--------|-------------|
| B1 | 🔴 crítico | `HardcodedNotificationManager` en producción — todas las notificaciones son datos falsos hardcodeados; `mark_notifications_read` no persiste nada |
| B2 | ⬜ activo | `last_room_api` definida dos veces: en `views.py` (L203) y en `views/api_last_room.py` — Django usará la del `views.py` importado en `urls.py` |
| B3 | ⬜ activo | `room_admin` definida dos veces en `views.py` (L1434 y L1866) con lógica diferente — Django usará la segunda definición (L1866) |
| B4 | ⬜ activo | `reset_unread_count_api` definida dos veces en `views.py` (L64 y L1462) con implementaciones distintas — Django usará la segunda |
| B5 | ⬜ activo | `room_notifications_api` definida dos veces en `views.py` (L1402 y L1812) con lógica diferente — Django usará la segunda |
| B6 | ⬜ activo | `mark_notifications_read_api` definida dos veces en `views.py` (L118 y L1504) — segunda implementación tiene `return` duplicado en L1529 (código muerto) |
| B7 | ⬜ activo | `@csrf_exempt` en 20+ endpoints POST autenticados — violación masiva de la convención del proyecto |
| B8 | ⬜ activo | `unread_count_api` (L44) sin `@require_GET` ni `@require_POST` — acepta cualquier método |
| B9 | ⬜ activo | `room_list` (L692) tiene N+1: por cada sala hace 3 queries (is_member, total_messages, read_messages) — para 20 salas son 60+ queries |
| B10 | ⬜ activo | `edit_assistant_configuration` usa `render` con template `'chat/edit_assistant_configuration.html'` — este template NO existe en el CONTEXT (12 templates listados, ninguno con ese nombre) |
| B11 | ⬜ activo | `chatroom()` (L540) no está en `urls.py` — función definida pero sin URL registrada (código muerto) |
| B12 | ⬜ activo | `clear_chat()` (L473) y `export_chat_history()` (L494) no están en `urls.py` — código muerto |
| B13 | ⬜ activo | `moderate_message()` tiene palabras prohibidas hardcodeadas: `['badword1', 'badword2']` — placeholder nunca actualizado |
| B14 | ⬜ activo | `ollama_api.py` URL hardcodeada `localhost:11434` — no configurable via settings |
| B15 | ✅ resuelto | Bug global #5 — notificaciones no siempre marcan como leídas (abierto, causa: `HardcodedNotificationManager`) |
| B16 | ⬜ activo | Todos los modelos usan `user` en lugar de `created_by` — fuera de convención del proyecto |
| B17 | ⬜ activo | `test_create_notification` endpoint en producción — endpoint de debug sin restricción de `is_staff` |
| B18 | ⬜ activo | `views.py` con 2017 líneas — monolito extremo, imposible de mantener sin refactor |

---

## 8. Deuda Técnica

**Alta prioridad (funcionalidad rota o seguridad):**
- **Implementar sistema de notificaciones real** — reemplazar `HardcodedNotificationManager` con modelo Django real. Es la deuda más crítica de la app
- **Resolver las 5 funciones duplicadas** — `room_admin`, `reset_unread_count_api`, `room_notifications_api`, `mark_notifications_read_api`, `last_room_api` tienen dos definiciones; Python usa la última, pero la primera definición (potencialmente diferente) queda inaccesible
- **Eliminar `@csrf_exempt`** de todos los endpoints POST autenticados — usar CSRF correctamente en el cliente JS
- **Crear template faltante** `edit_assistant_configuration.html` o cambiar el render a template existente

**Media prioridad:**
- **Refactorizar `views.py`** (2017 líneas) en módulos: `views/rooms.py`, `views/assistant.py`, `views/api.py`, `views/notifications.py`
- **Fix N+1 en `room_list`** — `select_related` + `prefetch_related` + query anotada
- **Eliminar código muerto** — `chatroom()`, `clear_chat()`, `export_chat_history()` sin URLs
- **Mover URL Ollama a settings** — `OLLAMA_API_URL = 'http://localhost:11434'`
- **Actualizar `moderate_message()`** — reemplazar placeholder con lista real o integrar con servicio externo
- **Restringir `test_create_notification`** a `@user_passes_test(lambda u: u.is_staff)`

**Baja prioridad:**
- Migrar `user` → `created_by` en todos los modelos (requiere migración)
- Agregar `is_active` a `CommandLog` y `AssistantConfiguration`
- Documentar `consumers.py` y `functions.py` — no se revisaron en esta sesión
- Unificar los dos sistemas de historial (caché Redis vs `Conversation` en BD)
