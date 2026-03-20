# Diseño y Roadmap — App `chat`

> **Actualizado:** 2026-03-19  
> **Estado:** Funcional con deuda técnica severa — documentación generada esta sesión  
> **Sprint actual:** 7 completado | Próximo: Sprint 8

---

## Visión General

`chat` es la app de **comunicación y asistencia IA** de Management360. Tiene dos subsistemas completamente distintos que comparten código pero sirven propósitos diferentes.

```
┌─────────────────────────────────────────────────────────────┐
│                        APP CHAT                             │
│                                                             │
│  ┌──────────────────────────┐  ┌───────────────────────┐   │
│  │  SALAS EN TIEMPO REAL    │  │   ASISTENTE IA        │   │
│  │                          │  │                       │   │
│  │  Room (de rooms)         │  │  Conversation         │   │
│  │  Message (de rooms)      │  │  AssistantConfig      │   │
│  │  WebSocket (Channels)    │  │  CommandLog           │   │
│  │  consumers.py            │  │  functions.py         │   │
│  │                          │  │  ollama_api.py        │   │
│  │  → chat en tiempo real   │  │  → SSE streaming      │   │
│  │  → historial persistente │  │  → comandos /funcion  │   │
│  └──────────────────────────┘  └───────────────────────┘   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  NOTIFICACIONES                                     │   │
│  │  HardcodedNotificationManager ← 🔴 STUB / FAKE     │   │
│  │  notifications_consumer.py (WebSocket)              │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
         │                            │
         ▼                            ▼
   rooms.{Room,              accounts.User
   Message,RoomMember,       (Conversation.user,
   MessageRead}               CommandLog.user,
                              AssistantConfig.user)
```

---

## Estado de Implementación

| Módulo | Estado | Observaciones |
|--------|--------|---------------|
| Chat en tiempo real (salas) | ✅ Funcional | Depende de `rooms` para modelos |
| WebSocket consumer (`consumers.py`) | ✅ Funcional | Requiere Daphne + Channels + Redis |
| Asistente IA (`chat_view` + streaming) | ✅ Funcional | Requiere Ollama local en :11434 |
| Historial de conversaciones IA | ✅ Funcional | JSONField en `Conversation` |
| Comandos del asistente (`functions.py`) | ✅ Funcional | No revisado en detalle esta sesión |
| Configuraciones del asistente | ✅ Funcional | CRUD completo |
| Sistema de notificaciones | 🔴 Stub/Fake | `HardcodedNotificationManager` — datos falsos |
| Presencia de usuarios (`UserPresence`) | ⚠️ Parcial | Modelo y endpoints OK; UI muestra `is_online: True` hardcodeado |
| Reacciones a mensajes | ✅ Funcional | Toggle get_or_create/delete |
| Búsqueda en mensajes | ✅ Funcional | Dos endpoints con distinto nivel de filtros |
| Panel flotante (`chat_panel`) | ✅ Funcional | Embebible en otras páginas |
| Admin de sala | ⚠️ Duplicado | Dos definiciones de `room_admin` con lógica distinta |
| `views.py` | 🔴 Monolito | 2017 líneas — 5 funciones duplicadas |
| Tests | ⚠️ Desconocido | `test.py` dentro de templates/ — ubicación incorrecta |
| Documentación | ✅ Esta sesión | Primera documentación formal |

---

## Arquitectura de Datos

### Dependencias cross-app

```
chat → rooms  (MessageReaction.message FK, UserPresence.current_room FK,
               views importan Room, Message, RoomMember, MessageRead)
chat → accounts.User (todos los modelos)
chat ← core   (chat_panel embebible en cualquier página del proyecto)
chat ← events (notificaciones de tareas — pendiente formalizar, según PROJECT_DESIGN)
```

`chat` es la app con **mayor acoplamiento del proyecto** — sus modelos tienen FKs directas a `rooms`, y sus vistas importan desde `rooms` en 15+ lugares.

### Infraestructura requerida

```
Servidor principal (Termux/Daphne)
  └── Django + ASGI (chat HTTP + WebSocket)
        ├── Redis (channel layers + caché historial + rate limit)
        └── MariaDB (Conversation, CommandLog, AssistantConfiguration, UserPresence)

Proceso externo (Termux, terminal separada)
  └── Ollama → localhost:11434
        └── Modelo LLM descargado (ej: llama2, mistral)
```

### Modelo `Conversation` vs caché de historial

El sistema tiene **dos mecanismos de historial simultáneos**:

```
1. Conversation (BD) — historial persistente real
   └── messages: JSONField con todos los mensajes

2. cache_key = 'chat_history_{user_id}' (Redis, 1h)
   └── historial de compatibilidad — usado si no hay chat_history en POST
```

Deben permanecer sincronizados. Si Redis expira, el historial se recarga desde `Conversation`.

---

## Roadmap

### Deuda inmediata (pre-Sprint 8)

| ID | Tarea | Prioridad |
|----|-------|-----------|
| CHAT-1 | Implementar sistema de notificaciones real — modelo `Notification` o integrar con `rooms.Notification` | 🔴 |
| CHAT-2 | Resolver las 5 funciones duplicadas en `views.py` — determinar cuál versión es la correcta y eliminar la otra | 🔴 |
| CHAT-3 | Crear template faltante `edit_assistant_configuration.html` | 🔴 |
| CHAT-4 | Eliminar `@csrf_exempt` de endpoints POST — máxima prioridad por política del proyecto | 🔴 |
| CHAT-5 | Mover `test.py` fuera de `templates/` — no es un template | 🟠 |

### Sprint 8 — Refactor estructural

| ID | Tarea | Prioridad |
|----|-------|-----------|
| CHAT-6 | Dividir `views.py` (2017 líneas) en módulos: `views/rooms.py`, `views/assistant.py`, `views/api_messages.py`, `views/notifications.py` | 🔴 |
| CHAT-7 | Fix N+1 en `room_list` — `annotate` + `prefetch_related` | 🟠 |
| CHAT-8 | Eliminar código muerto: `chatroom()`, `clear_chat()`, `export_chat_history()` | 🟠 |
| CHAT-9 | Mover URL Ollama a `settings.OLLAMA_API_URL` | 🟠 |
| CHAT-10 | Actualizar `moderate_message()` con lista real o eliminar | 🟠 |
| CHAT-11 | Restringir `test_create_notification` a `is_staff` | 🟠 |
| CHAT-12 | Documentar `consumers.py` y `functions.py` | 🟡 |

### Sprint 9 — Optimización

| ID | Tarea | Prioridad |
|----|-------|-----------|
| CHAT-13 | Migrar `user` → `created_by` en todos los modelos | 🟡 |
| CHAT-14 | Implementar presencia real (`is_online`) — ahora hardcodeado como `True` en `room_members_api` | 🟠 |
| CHAT-15 | Unificar los dos sistemas de historial (BD + caché Redis) | 🟡 |
| CHAT-16 | Agregar tests para los dos subsistemas principales | 🟡 |

---

## Notas para Claude

- **Namespace `chat:` declarado** ✅ — usar `{% url 'chat:room' room_name=room.id %}` etc.
- **`room_name` en URL es el ID int** de la sala, no un nombre de texto — no confundir
- **Propietario `user`** en todos los modelos, no `created_by`
- **5 funciones duplicadas** en `views.py` — Python ejecuta la **última** definición del archivo: `room_admin` (L1866), `reset_unread_count_api` (L1462), `room_notifications_api` (L1812), `mark_notifications_read_api` (L1504), `last_room_api` (en `views.py`, no en `views/api_last_room.py`)
- **Notificaciones son falsas** — `HardcodedNotificationManager` siempre retorna las mismas 2 notificaciones; `mark_as_read` no persiste nada
- **`edit_assistant_configuration.html` no existe** — la vista llama a un template que no está en el árbol de archivos
- **Ollama debe estar corriendo** en `:11434` para que el asistente funcione — sin él, streaming retorna error
- **Streaming SSE** en `chat_view`: responde con `text/event-stream`, chunks `data: {"content": "..."}\n\n`, fin con `data: [DONE]\n\n`
- **Bug global #5** (notificaciones no marcan como leídas) tiene como causa raíz a `HardcodedNotificationManager` — el bug real es que no hay modelo real, no un problema de lógica
- **`test.py` está dentro de `templates/chat/`** — fue detectado por `m360_map.sh` como template; es un archivo Python mal ubicado
- **Rate limit del asistente:** 5 requests/60s por usuario, clave Redis `chat_rate_{user_id}` — no confundir con la caché de historial `chat_history_{user_id}`
