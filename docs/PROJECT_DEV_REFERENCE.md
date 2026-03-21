# Referencia de Desarrollo — Proyecto Management360

> **Audiencia:** Desarrolladores del proyecto y asistentes de IA (Claude, Copilot, etc.)
> **Actualizado:** 2026-03-20 (Sesión Analista Doc — lote 4: help, api, panel — documentación 20/20 ✅) | **Apps:** 20 | **Archivos Python+HTML:** ~710

---

## Índice rápido

| Sección | Contenido |
|---------|-----------|
| 1. Estructura del proyecto | Árbol, apps, convenciones |
| 2. Patrones comunes en todas las apps | Models, views, URLs, templates |
| 3. Excepciones de propietario por app | Tabla completa auditada |
| 4. Manejo de fechas (CRÍTICO) | Estándar por app |
| 5. Sistema de caché | Redis keys, TTLs, patrones |
| 6. Seguridad | CSRF, permisos, namespaces, violaciones conocidas |
| 7. Modelo User (accounts) | Campos custom, imports correctos |
| 8. Integración analyst ↔ sim | ETL, dashboards, reportes |
| 9. App simcity — arquitectura híbrida | Engine proot, proxy, arranque |
| 10. Sistemas de tiempo real | Channels (chat) vs Centrifugo (rooms) |
| 11. App chat — subsistemas | Salas vs Asistente IA (Ollama) |
| 12. App rooms — mundo virtual | Navegación, puertas, portales, 3D |
| 13. App courses — dependencias | cv, tutor, ContentBlock |
| 14. App core — infraestructura global | Layouts, dashboard, caché |
| 15. APIs internas | Estructura de respuestas, autenticación |
| 16. Frontend unificado | HTMX, Bootstrap, Chart.js |
| 17. Testing | Por app, cobertura |
| 18. Despliegue | build.sh, variables de entorno |
| 19. Migraciones | Orden, dependencias entre apps |
| 20. Documentación | Estándar por app |
| 21. Bugs conocidos globales | Issues que afectan múltiples apps |

---

## 1. Estructura del Proyecto

### Resumen de apps

| App | Namespace | Endpoints | Notas |
|-----|-----------|-----------|-------|
| `accounts` | `accounts` | 11 | Autenticación, Perfiles — `app_name` en include externo |
| `analyst` | `analyst` | 99 | Plataforma de datos (5 fases, SIM-4 integrado) |
| `api` | `—` ⚠️ | 4 | Enrutamiento puro — lógica real en `panel/views.py`. Sin `app_name` (bug #111) |
| `bitacora` | `bitacora` | 9 | Bitácora personal GTD |
| `board` | `board` ✅ | 8 | Kanban board — HTMX + WebSocket (sin activar) |
| `bots` | `bots` ✅ | 13 | Automatizaciones, bots, leads |
| `campaigns` | `campaigns` ✅ | 6 | Campañas outbound, contactos, discador |
| `chat` | `chat` ✅ | 40 | Chat en tiempo real + Asistente IA (Ollama) |
| `core` | `—` ⚠️ | 16 | Dashboard, URL-map, layouts globales |
| `courses` | `courses` ✅ | 59 | Cursos, lecciones, CMS, lecciones independientes |
| `cv` | `cv` ✅ | 14 | Curriculum Vitae dinámico |
| `events` | `—` ⚠️ | 145 | Eventos, Proyectos, Tareas (app principal) |
| `help` | `help` ✅ | 10 | CMS de ayuda — artículos, FAQs, videos, guías. Integración con `courses` |
| `kpis` | `kpis` ✅ | 5 | KPIs, AHT Dashboard, CallRecord |
| `memento` | `—` ⚠️ | 6 | Visualización de mortalidad (Memento Mori) |
| `panel` | `—` | 8 | Paquete de configuración del proyecto (settings, urls raíz, storage, middleware) |
| `passgen` | `—` ⚠️ | 2 | Generador de contraseñas — namespace no declarado |
| `rooms` | `rooms` ✅ | 53 | Salas virtuales, mundo virtual 3D, Centrifugo |
| `sim` | `sim` | 48 | Simulador WFM — SIM-1→SIM-7a completo |
| `simcity` | `simcity` | 14 | Simulador urbano — proxy proot:8001 |

> ⚠️ `core`, `events` y `memento` no declaran `app_name` en su `urls.py` — el namespace viene del `include()` en el urls raíz. Frágil si se cambia el include.
> ⚠️ `passgen` y `api` no declaran `app_name` — sin namespace. Bugs #95 y #111.

### Convenciones de nomenclatura

| Elemento | Convención | Ejemplo |
|----------|------------|---------|
| Apps | snake_case, singular | `analyst`, `events`, `sim` |
| Modelos | CamelCase | `CallRecord`, `SimAccount`, `Project` |
| Vistas | snake_case | `dashboard_view`, `project_list` |
| URLs | kebab-case | `/kpis/dashboard/`, `/events/projects/` |
| Namespaces | snake_case | `app_name = 'kpis'` |
| Templates | snake_case | `upload_data_csv.html` |
| Archivos de doc | MAYÚSCULAS + _ | `PROJECT_DESIGN.md` |

---

## 2. Patrones Comunes en Todas las Apps

### Models

```python
# PK pública — estándar del proyecto
id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

created_by = models.ForeignKey(
    settings.AUTH_USER_MODEL,
    on_delete=models.CASCADE,
    related_name='%(class)s_created',
)
created_at = models.DateTimeField(auto_now_add=True)
updated_at = models.DateTimeField(auto_now=True)
is_active = models.BooleanField(default=True)
```

### Import correcto de User

```python
# CORRECTO — en models.py
from django.conf import settings
created_by = models.ForeignKey(settings.AUTH_USER_MODEL, ...)

# CORRECTO — en views.py, forms.py, otros
from django.contrib.auth import get_user_model
User = get_user_model()

# INCORRECTO — nunca usar esto
from django.contrib.auth.models import User

# INCORRECTO — get_user_model() a nivel de módulo en models.py (board)
User = get_user_model()
owner = models.ForeignKey(User, ...)  # debe ser settings.AUTH_USER_MODEL
```

### Views

```python
@login_required
@require_POST
def api_action(request):
    try:
        data = json.loads(request.body)
        return JsonResponse({'success': True, 'data': result})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)
```

### CSRF Token en JavaScript

```javascript
function csrf() {
    return document.cookie.match(/csrftoken=([^;]+)/)?.[1] || '';
}
fetch(url, { method: 'POST', headers: { 'X-CSRFToken': csrf() }, body: ... })
```

### Respuestas JSON unificadas

```json
{"success": true, "data": {...}}
{"success": false, "error": "..."}
```

### TextChoices — módulo-level vs clase interna

`bitacora` y `courses` definen sus TextChoices a nivel de módulo, no como clases internas:

```python
# CORRECTO
from bitacora.models import CategoriaChoices, MoodChoices
from courses.models import CourseLevelChoices, LessonTypeChoices
from kpis.models import SERVICIO_CHOICES, CANAL_CHOICES

# INCORRECTO
BitacoraEntry.CategoriaChoices   # AttributeError
CallRecord.SERVICIO_CHOICES      # AttributeError — son module-level
```

---

## 3. Excepciones de Propietario por App

La convención general es `created_by`. Estas apps rompen la convención — **son intencionales, no cambiar:**

| App | Modelo(s) | Campo propietario | Motivo |
|-----|-----------|-------------------|--------|
| `events` | `Project`, `Task`, `Event` | `host` | Semántica de dominio — el anfitrión |
| `events` | `InboxItem` | `created_by` ✅ | Excepción dentro de la excepción |
| `rooms` | `Room` | `owner` + `creator` | `owner` = propietario real; `creator` = histórico |
| `courses` | `Course` | `tutor` | Semántica de dominio — el instructor |
| `courses` | `Lesson` (standalone) | `author` | Autor de la lección |
| `courses` | `ContentBlock` | `author` | Autor del bloque CMS |
| `courses` | `Enrollment` | `student` | Semántica de dominio |
| `chat` | `Conversation`, `CommandLog`, `AssistantConfiguration` | `user` | Sin convención |
| `memento` | `MementoConfig` | `user` | Sin convención |
| `bitacora` | `BitacoraEntry` | `created_by` ✅ | Sí cumple la convención |
| `board` | `Board` | `owner` | Propietario del tablero — NO `created_by` |
| `board` | `Activity` | `user` | Log de actividad — NO `created_by` |
| `cv` | `Curriculum` | `user` (OneToOne) | Propietario implícito — NO `created_by` |
| `campaigns` | Todos | — | Sin propietario — datos globales de contact center |
| `kpis` | `CallRecord` | `created_by` (null=True, SET_NULL) | ✅ Convención pero `null=True` intencional |
| `help` | `HelpArticle`, `VideoTutorial` | `author` | NO `created_by` |
| `help` | `HelpFeedback`, `HelpSearchLog` | `user` | NO `created_by` — feedback/telemetría |
| `help` | `HelpCategory`, `FAQ`, `QuickStartGuide` | — | Sin propietario explícito |

### Resumen de acceso seguro por app

```python
# events
get_object_or_404(Project, pk=pk, host=request.user)
get_object_or_404(Task, pk=pk, host=request.user)
get_object_or_404(InboxItem, pk=pk, created_by=request.user)  # excepción

# rooms
get_object_or_404(Room, pk=pk)  # luego verificar room.can_user_manage(request.user)

# courses
get_object_or_404(Course, slug=slug, tutor=request.user)
get_object_or_404(Lesson, slug=slug, author=request.user, module__isnull=True)
block = get_object_or_404(ContentBlock, slug=slug)
# luego: if block.author != request.user and not block.is_public: deny

# memento
get_object_or_404(MementoConfig, pk=pk, user=request.user)

# board
get_object_or_404(Board, pk=pk, owner=request.user)
get_object_or_404(Card, pk=pk, board__owner=request.user)

# cv
get_object_or_404(Curriculum, user=request.user)
get_object_or_404(Document, id=pk, cv__user=request.user)

# todo lo demás (estándar)
get_object_or_404(MyModel, pk=pk, created_by=request.user)
```

---

## 4. Manejo de Fechas — CRÍTICO ⚠️

| App | Modelo | Campo(s) de fecha | Ordenamiento |
|-----|--------|-------------------|--------------|
| **sim** | `Interaction` | `fecha` (DateField) + `hora_inicio` (DateTimeField) | `order_by('fecha', 'hora_inicio')` |
| **kpis** | `CallRecord` | `fecha` (DateField) + `semana` (IntegerField calculado) | `order_by('fecha', 'agente')` |
| **events** | `InboxItem` | `created_at` (DateTimeField) + `due_date` (DateField, null=True) + `processed_at` (DateTimeField, null=True) | `order_by('-created_at')` |
| **events** | `Task` | `created_at` (DateTimeField) + `reminder` (DateTimeField, null=True) — **NO tiene `due_date`** | `order_by('-created_at')` |
| **events** | `Project` | `created_at` / `updated_at` (DateTimeField) — **NO tiene `start_date`** | `order_by('-created_at')` |
| **events** | `Event` | `created_at` / `updated_at` (DateTimeField) — **NO tiene `start_date` ni `start_time`** | `order_by('-created_at')` |
| **chat** | `rooms.Message` | `created_at` (DateTimeField) | `order_by('created_at')` |
| **bitacora** | `BitacoraEntry` | `fecha_creacion` (DateTimeField) | `order_by('-fecha_creacion')` |
| **courses** | `Lesson` | `created_at` (DateTimeField) | `order_by('order', 'created_at')` |
| **simcity** | `Game` | `created_at` / `updated_at` (DateTimeField) | `order_by('-created_at')` |
| **memento** | `MementoConfig` | `updated_at` (DateTimeField) | `order_by('-updated_at')` |
| **rooms** | `Room` | `bumped_at` (DateTimeField) | `order_by('-bumped_at')` — actualiza al recibir msg |
| **campaigns** | `ProviderRawData` | `upload_date` (default=timezone.now) | `order_by('-upload_date')` |

### ⚠️ `timedelta` NO es parte de `django.utils.timezone`

```python
from datetime import timedelta   # CORRECTO
# timezone.timedelta             # INCORRECTO — AttributeError
```

### ⚠️ Campos que NO existen

```python
# kpis.CallRecord    — NO usar start_time   → usar fecha
# sim.Interaction    — NO usar started_at   → usar fecha + hora_inicio
# rooms.EntranceExit — NO tiene created_at  → no ordenar por ese campo
# rooms.Portal       — NO tiene created_at  → ídem
# rooms.RoomConnection — NO tiene created_at → ídem
# events.Task        — NO tiene due_date    → usar reminder (null=True) o created_at
# events.Project     — NO tiene start_date  → usar created_at
# events.Event       — NO tiene start_date ni start_time → usar created_at
```

---

## 5. Sistema de Caché (Redis)

| Prefix | App | TTL | Ejemplo |
|--------|-----|-----|---------|
| `df_preview_` | analyst | 2h | `df_preview_{uuid}` |
| `stored_dataset_` | analyst | ∞ | `stored_dataset_{uuid}` |
| `clip_` | analyst | 24h | `clip_{session_key}_{key}` |
| `gtr:session:` | sim | 4h | `gtr:session:{sid}` |
| `kpis:dashboard:` | kpis | 5min | `kpis:dashboard:{user_id}:{desde}:{hasta}` |
| `home_stats_` | core | 5min | `home_stats_{days}_{days_ago}` |
| `home_status_counts` | core | 10min | fijo |
| `home_event_categories` | core | 15min | fijo |
| `home_project_categories` | core | 30min | fijo |
| `chat_rate_` | chat | 60s | `chat_rate_{user_id}` — rate limit asistente IA |
| `chat_history_` | chat | 1h | `chat_history_{user_id}` — compatibilidad |
| `room_visits_` | rooms | sin TTL | `room_visits_{room_name}` — contador de visitas |

`simcity` no usa Redis — estado del mapa persiste en MariaDB (JSONField).

---

## 6. Seguridad

### Patrón estándar

```python
obj = get_object_or_404(MyModel, pk=pk, created_by=request.user)
```

### `@csrf_exempt` — PROHIBIDO

Está explícitamente prohibido en vistas con datos de usuario. Violaciones **activas** conocidas:

| App | Vista | Estado |
|-----|-------|--------|
| `chat` | 20+ endpoints POST (`chat_view`, `mark_messages_read_api`, etc.) | ⬜ activo |
| `core` | `refresh_dashboard_data` | ⬜ activo |
| `bitacora` | `upload_image` | ✅ resuelto (bug #12) |
| `simcity` | `mobMoneyBtn` endpoint | ✅ resuelto (SC-2) |

### Vulnerabilidades de seguridad activas

| ID | App | Tipo | Descripción |
|----|-----|------|-------------|
| ACC-SEC-1 | `accounts` | Credencial hardcodeada | `"DefaultPassword123"` en `reset_to_default_password` |
| ACC-SEC-2 | `accounts` | Open redirect | `next` param sin validar en `login_view` |
| MEM-SEC-1 | `memento` | IDOR | `MementoConfigUpdateView` sin `get_queryset(user=request.user)` |
| CORE-SEC-1 | `core` | Exposición de arquitectura | `url_map_view` sin `@login_required` |
| CORE-SEC-2 | `core` | Exposición de datos | `search_view` sin `@login_required` |
| ROOMS-SEC-1 | `rooms` | Múltiples vistas sin auth | `room_detail`, `room_list`, `room_3d_view`, `room_comments` |
| BOARD-SEC-1 | `board` | IDOR | `BoardDetailView` sin verificación de propietario — Bug #84 |
| CV-SEC-1 | `cv` | Reverse sin namespace | `reverse('project_detail')` en `CorporateDataMixin` → posible `NoReverseMatch` — Bug #76 |
| PANEL-SEC-1 | `panel` | Sin autenticación | `RedisTestView` sin `@login_required` — accesible públicamente — Bug #117 |
| HELP-SEC-1 | `help` | Sin autenticación | `article_feedback_stats` sin `@login_required` — solo verifica `is_staff` manualmente — Bug #102 |
| PANEL-SEC-2 | `panel` | Endpoint roto | `get_connection_token` no retorna respuesta — Bug #114 |

---

## 7. Modelo User (`accounts`)

```python
class User(AbstractUser):
    phone      = models.CharField(max_length=20, blank=True, null=True)
    avatar     = models.ImageField(upload_to='avatars/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

```python
# panel/settings.py
AUTH_USER_MODEL = 'accounts.User'
```

**`accounts` migra siempre primero** — ver §18 Migraciones.

**`accounts` NO tiene `app_name` declarado** en su `urls.py` — el namespace `accounts:` proviene del `include()` en el urls raíz.

---

## 8. Integración analyst ↔ sim

Ver `ANALYST_DEV_REFERENCE.md` y `SIM_DEV_REFERENCE.md`.
`sim` incluye SIM-7a (ACD multi-agente) — migraciones 0005+0006 aplicadas.

---

## 9. App `simcity` — Arquitectura Híbrida

`simcity` es la única app de M360 que depende de un proceso externo.
`micropolisengine` (C/SWIG) solo existe en proot Ubuntu — **nunca importar en Termux**.

### Arranque

```bash
alias engine='ubuntu run "source /root/micropolis/venv/bin/activate && cd /root/micropolis/simcity_web && python manage.py runserver 0.0.0.0:8001"'
alias m360='cd ~/projects/Management360 && source venv/bin/activate && python manage.py runserver'
bash scripts/start_simcity.sh  # alternativa
```

### Patrón de vista — manejo de engine offline (SC-3)

```python
from .services import EngineUnavailableError

@login_required
@require_POST
def tick(request, game_id):
    game = get_object_or_404(Game, pk=game_id, created_by=request.user)
    try:
        data = engine.engine_tick(game.engine_game_id, body.get('n', 1))
        game.save()
        return JsonResponse(data)
    except EngineUnavailableError as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=503)
```

---

## 10. Sistemas de Tiempo Real

### ⚠️ Dos sistemas coexistentes — NO son intercambiables

| Sistema | App | Protocolo | Uso |
|---------|-----|-----------|-----|
| **Django Channels** | `chat` | WebSocket (ASGI) | Chat en tiempo real, notificaciones push |
| **Centrifugo** | `rooms` | HTTP broadcast | Mensajes de sala, eventos join/leave |
| **Django Channels** | `board` | WebSocket (ASGI) | Movimiento de cards — ⚠️ no activado aún |

### Centrifugo (rooms)

Requiere en `settings.py`:

```python
CENTRIFUGO_HTTP_API_ENDPOINT = 'http://...'
CENTRIFUGO_HTTP_API_KEY      = '...'
CENTRIFUGO_BROADCAST_MODE    = 'api'  # 'api' | 'outbox' | 'cdc' | 'api_cdc'
CENTRIFUGU_OUTBOX_PARTITIONS = 16    # ⚠️ typo con doble U — verificar en settings real
```

### Django Channels (chat)

WebSocket consumer en `chat/consumers.py`. Routing en `chat/routing.py`:
```python
ws/chat/<str:room_name>/    → ChatConsumer
ws/notifications/           → NotificationConsumer
```
Requiere Daphne corriendo como servidor ASGI + Redis como channel layer.

### Django Channels (board) — pendiente activar

`board/consumers.py` tiene `BoardConsumer` implementado pero sin URL WebSocket. Para activar:
```python
# project/routing.py
re_path(r'ws/board/(?P<board_id>\d+)/$', BoardConsumer.as_asgi()),
```

Requiere `BOARD_CONFIG = {'CARDS_PER_PAGE': 20}` en settings (ver Bug #85).

### Ollama — Asistente IA (chat)

`chat/ollama_api.py` llama a `http://localhost:11434` (hardcodeado). Sin Ollama activo, `chat_view` retorna error en el stream SSE. Pendiente mover a `settings.OLLAMA_API_URL`.

**Streaming de respuesta:** `text/event-stream`, chunks `data: {"content": "..."}\n\n`, fin con `data: [DONE]\n\n`.

**Rate limit del asistente:** 5 requests / 60s por usuario — clave `chat_rate_{user_id}` en Redis.

---

## 11. App `chat` — Subsistemas

`chat` tiene dos subsistemas completamente distintos en el mismo `views.py` (2017 líneas):

**Subsistema 1 — Salas de chat**
Vistas y APIs sobre modelos de `rooms` (Room, Message, MessageRead, RoomMember).

**Subsistema 2 — Asistente IA**
Conversaciones persistentes en `chat.Conversation` (JSONField), comandos `/funcion params`, configuraciones de modelo (`AssistantConfiguration`), streaming SSE.

### Sistema de notificaciones

`chat.HardcodedNotificationManager` — **stub en producción**. Siempre retorna 2 notificaciones hardcodeadas. `mark_as_read` no persiste nada. **El modelo real es `rooms.Notification`** — tiene persistencia, índices, tipos y `mark_as_read()` correcto. Pendiente conectar.

### Funciones duplicadas en `views.py`

Python usa la **última** definición de cada función:

| Función | Línea primera def | Línea segunda def (activa) |
|---------|------------------|---------------------------|
| `room_admin` | L1434 | L1866 |
| `reset_unread_count_api` | L64 | L1462 |
| `room_notifications_api` | L1402 | L1812 |
| `mark_notifications_read_api` | L118 | L1504 |
| `last_room_api` | `views/api_last_room.py` | `views.py` L203 |

---

## 12. App `rooms` — Mundo Virtual

`rooms` tiene tres capas funcionales: chat (modelos para `chat`), mundo virtual gamificado (PlayerProfile, puertas, portales) y entorno 3D (Three.js).

### PlayerProfile — acceso seguro

```python
# SIEMPRE verificar antes de acceder:
if hasattr(request.user, 'player_profile'):
    player = request.user.player_profile
else:
    # crear o retornar error
```

### Propietario de Room

```python
room.can_user_manage(request.user)  # owner OR role admin/moderator en RoomMember
```

### Bugs activos de runtime

```python
# ROTO — room_comments:
room.comments.create(text=comment, ...)   # campo 'text' no existe → TypeError
# CORRECTO:
Comment.objects.create(room=room, user=request.user, comment=comment)

# ROTO — navigate_room:
entrance.face.opposite()   # str no tiene .opposite() → AttributeError
# CORRECTO:
OPPOSITES = {'NORTH':'SOUTH','SOUTH':'NORTH','EAST':'WEST','WEST':'EAST'}
opposite = OPPOSITES.get(entrance.face)

# ROTO — calculate_new_position solo implementa NORTH/SOUTH
# EAST/WEST retornan None → posición (None, None) en BD
```

---

## 13. App `courses` — Dependencias Críticas

### `courses` importa `cv` a nivel de módulo

```python
# courses/models.py línea 9:
from cv.models import Curriculum  # Si cv falla, courses no carga
```

### Verificación de tutor antes de cualquier operación

```python
if not hasattr(request.user, 'cv'):
    messages.error(request, 'Necesitas un perfil de tutor')
    return redirect('cv:detail')
```

`Course.save()` lanza `ValueError` (no `ValidationError`) si el tutor no tiene CV. Los forms Django no capturan `ValueError` automáticamente.

### Lesson dual — de curso vs independiente

```python
lesson.is_standalone  # == lesson.module is None

# Lección de curso: usa tutor del curso
# Lección independiente: usa lesson.author (requerido)

# mark_lesson_complete SOLO para lecciones de curso:
lesson.module.course  # AttributeError si module=None
```

### URL duplicada activa

```python
# courses/urls.py — dos paths idénticos:
path('content/', views.content_manager, name='content_manager'),   # wins
path('content/', views.standalone_lessons_list, name='standalone_lessons_list'),  # unreachable
```

---

## 14. App `core` — Infraestructura Global

### Dependencias de importación

```python
# core/utils.py y core/views.py importan directamente de events:
from events.models import Event, Project, Task, Status, ProjectStatus, TaskStatus
# Si events falla, core no carga.
```

### `'index'` y `'home'` — mismo endpoint

```python
path('', views.home_view, name='home'),   # redundante
path('', views.home_view, name='index'),  # el canónico usado en todo el proyecto
```

Nunca eliminar `'index'` — es el nombre usado en `redirect('index')` y `{% url 'index' %}` en decenas de lugares.

### Status names hardcodeados en `get_cached_status_counts()`

```python
# Si alguien renombra estos estados en BD, los conteos caen a 0 silenciosamente:
Status.objects.filter(status_name__in=['Completed', 'In Progress', 'Created'])
ProjectStatus.objects.filter(status_name__in=['Completed', 'In Progress'])
TaskStatus.objects.filter(status_name__in=['Completed', 'In Progress', 'To Do'])
```

### Bug semántico en `upcoming_events` (bug #41 — core)

```python
# INCORRECTO — filtra eventos creados en el futuro (siempre vacío):
Event.objects.filter(created_at__gte=timezone.now())

# CORRECTO — events.Event NO tiene start_date ni start_time (campos inexistentes).
# El modelo no tiene campo de fecha de inicio confirmado. Verificar con:
# [f.name for f in Event._meta.get_fields() if hasattr(f,'get_internal_type')
#  and 'date' in f.get_internal_type().lower()]
```

---

## 15. APIs Internas

```python
@login_required
def api_items(request):
    items = Item.objects.filter(created_by=request.user)
    return JsonResponse({'success': True, 'data': list(items.values('id', 'name'))})
```

### DRF en `rooms`

`rooms` usa Django REST Framework para sus ViewSets CRUD. Los ViewSets tienen `permission_classes = [IsAuthenticated]`. Las vistas funcionales de rooms usan `@api_view` de DRF — **no mezclar `@api_view` con `render()`** (causa problemas de content negotiation).

---

## 16. Frontend Unificado

Bootstrap 5 + HTMX en todas las apps.

**Excepciones:**
- `simcity` — JS vanilla + Canvas 2D + CSS custom. No agregar Bootstrap al template del juego.
- `rooms` (entorno 3D) — Three.js en `room_3d_interactive.html`. No mezclar con el layout global de Bootstrap.
- `board` — CSS propio (`board.css`). HTMX para CRUD de cards sin recarga.

---

## 17. Testing

| App | Tests | Cobertura | Tipo |
|-----|-------|-----------|------|
| sim | 157 | 100% | Unitarios |
| analyst | 34/50 | 68% | ⚠️ **Stub (3 líneas) — los tests no existen (INC-004)** |
| accounts | 212 líneas | — | Unitarios (tests.py) |
| core | 249 líneas | — | Performance (test_performance.py) |
| memento | 68 líneas | — | Unitarios (tests.py) |
| courses | — | — | Management commands |
| rooms | — | — | Management commands |
| simcity | 0 | 0% | Pendiente SC-8 |

---

## 18. Despliegue

### build.sh

```bash
python manage.py migrate auth
python manage.py migrate contenttypes
python manage.py migrate accounts   # ← CRÍTICO: antes que el resto
python manage.py migrate --no-input
python manage.py collectstatic --no-input
```

### Variables de entorno (.env)

```
SECRET_KEY=...
DEBUG=False
DATABASE_URL=mysql://user:pass@localhost:3306/projects
REDIS_URL=redis://:password@localhost:6379/0
SIMCITY_ENGINE_URL=http://localhost:8001
CENTRIFUGO_HTTP_API_ENDPOINT=http://...
CENTRIFUGO_HTTP_API_KEY=...
CENTRIFUGO_BROADCAST_MODE=api
OLLAMA_API_URL=http://localhost:11434  # pendiente mover desde hardcode en ollama_api.py
BOARD_CONFIG={"CARDS_PER_PAGE": 20}   # requerido por board/htmx_views.py — Bug #85
```

⚠️ **Nunca pegar output de `.env` en chats** — INC-003.

---

## 19. Migraciones

### Estado actual (2026-03-20)

| App | Última migración | Notas |
|-----|-----------------|-------|
| accounts | 0001_initial | User custom con phone, avatar, timestamps |
| bitacora | 0004_uuid_primary_keys | UUID pk en entry + attachment |
| sim | 0006_rename_... | SIM-7a ACD multi-agente completo |
| simcity | 0001_initial | Game con created_by + engine_game_id |
| events | 0004_fix_fk_auth_user_to_accounts_user | FKs → accounts_user (Sprint 8) |
| kpis | 0002_refactor_callrecord | UUID + fecha DateField + 5 índices (IF NOT EXISTS) |
| bots | 0002_alter_botlog_category_alter_lead_status | choices corregidos Sprint 8 |
| chat | 0001_initial | — |
| rooms | 0001_initial | — |
| courses | 0001_initial | — |
| memento | 0007_alter_mementoconfig_death_date | death_date alterado 6 veces |
| cv | 0001_initial | — |
| board | 0001_initial | — |
| campaigns | 0001_initial | — |

### Orden de dependencias

1. `contenttypes`, `auth`
2. **`accounts`** — PRIMERO (siempre)
3. `cv` — antes que `courses` (import directo en courses/models.py)
4. `events`, `analyst`, `sim`, `courses`, `simcity`
5. `chat`, `rooms`, `bitacora`, `bots`, `memento`
6. `board`, `campaigns`, `kpis`, `passgen`, `help`, `api`, `panel` — independientes

### ⚠️ REGLA: Nunca ignorar migrations/ en .gitignore

---

## 20. Documentación

| Tipo | Propósito |
|------|-----------|
| `APP_CONTEXT.md` | Mapa estructural (auto) — `bash scripts/m360_map.sh app ./nombre_app` |
| `APP_DEV_REFERENCE.md` | Manual técnico para devs y Claude |
| `APP_DESIGN.md` | Diseño, fases, roadmap |

**Apps con documentación completa (20/20) ✅:** `analyst`, `sim`, `bitacora`, `simcity`, `events`, `accounts`, `core`, `memento`, `chat`, `rooms`, `courses`, `bots`, `kpis`, `cv`, `board`, `campaigns`, `passgen`, `help`, `api`, `panel`.

**Sprint 7.5 documentación: COMPLETO** — 120 bugs registrados (#1–#120).

---

## 21. Bugs Conocidos Globales

| # | Estado | App | Descripción |
|---|--------|-----|-------------|
| 1 | ✅ | analyst | `clean_file()` duplicado en forms.py |
| 2 | ✅ | analyst/sim | `started_at` inexistente en sim.Interaction |
| 3 | ✅ | analyst | UUID Python en JS → `_safe_json_str()` |
| 4 | ✅ | sim | `@keyframes` dentro de `<script>` |
| 5 | ⬜ | chat | Notificaciones no marcan como leídas — **causa raíz: `HardcodedNotificationManager`; fix: conectar con `rooms.Notification`** |
| 6 | ⬜ | events | Consultas N+1 en dashboard de proyectos |
| 7 | ✅ | kpis | Índices compuestos + fecha DateField + UUID |
| 8 | ⬜ | courses | Editor de contenido lento con muchos bloques — `available_content_blocks` sin límite |
| 9 | ✅ | sim | `expected_vol` gauss negativo |
| 10 | ✅ | accounts | `accounts_user` tabla inexistente — INC-001 |
| 11 | ✅ | bitacora | `timezone.timedelta` → `from datetime import timedelta` |
| 12 | ✅ | bitacora | `@csrf_exempt` en `upload_image` |
| 13 | ✅ | bitacora | N+1 en `total_attachments` |
| 14 | ✅ | bitacora | HTML render en modelos → templatetags |
| 15 | ✅ | bitacora | Imports lazy → movidos al tope |
| 16 | ✅ | bitacora | `content_block` no renderizaba en bitacora_tags |
| 17 | ✅ | bitacora | `urls.py` usaba `<int:pk>` → `<uuid:pk>` (BIT-6) |
| 18 | ✅ | events | Bloque `try` sin `except` en `assign_to_available_user()` |
| 19 | ✅ | events | `STATUS_CHOICES` incorrecto en `TaskFilterForm` |
| 20 | ✅ | events | Campos incorrectos en `TaskScheduleForm` |
| 21 | ✅ | events | Campos incorrectos en `InboxItemForm` |
| 22 | ✅ | events | Falta `get_user_model()` en `AssignAttendeesForm` |
| 23 | ✅ | events | Falta import de `Group` en `setup_views.py` |
| 24 | ✅ | cv | Admin con campos inexistentes |
| 25 | ✅ | kpis | Migración con dependencia incorrecta |
| 26 | ✅ | kpis | `ForeignKey(User)` → `settings.AUTH_USER_MODEL` |
| 27 | ✅ | kpis | `Duplicate column name created_at` en 0002 — IF NOT EXISTS |
| 28 | ✅ | scripts | `m360_map.sh`/`app_map.sh` convertidos en stubs — restaurados |
| 29 | ✅ | bitacora | `entry.autor` en template → `entry.created_by` |
| 30 | ✅ | bitacora | `entry.mood` raw en templates → `entry.get_mood_display` |
| 31 | ✅ | bitacora | `entry.CATEGORIA_CHOICES` en templates → `categoria_choices` del contexto |
| 32 | ✅ | bitacora | `entry.get_categoria_choices` en dashboard → `categoria_choices` |
| 33 | ✅ | bitacora | `BitacoraEntry.CategoriaChoices` en views → `CategoriaChoices` (módulo-level) |
| 34 | ⬜ | bitacora | Nav prev/next no filtra por `created_by`+`is_active` (BIT-17) |
| 35 | ⬜ | bitacora | TinyMCE CDN usa `no-api-key` — registrar en tiny.cloud (BIT-18) |
| SC-1 | ✅ `bf037497` | simcity | `generate_zr_block` no estaba en urls.py de M360 |
| SC-2 | ✅ `bf037497` | simcity | `mobMoneyBtn` solo logueaba warning — ahora llama API |
| SC-3 | ✅ `bf037497` | simcity | Engine offline daba 500 — ahora 503 EngineUnavailableError |
| 36 | ⬜ | accounts | Contraseña `"DefaultPassword123"` hardcodeada en `reset_to_default_password` |
| 37 | ⬜ | accounts | Open redirect en `login_view` — param `next` sin validar |
| 38 | ⬜ | accounts | `app_name` no declarado en `urls.py` — namespace frágil |
| 39 | ⬜ | accounts | `email` sin `unique=True` en modelo — validación solo en form |
| 40 | ⬜ | accounts | Import muerto `file_tree_view` de analyst en views.py |
| 41 | ⬜ | core | `upcoming_events` filtra por `created_at` en lugar de `start_date` |
| 42 | ⬜ | core | `refresh_dashboard_data` con `@csrf_exempt` en POST autenticado |
| 43 | ⬜ | core | `search_view` y `url_map_view` sin `@login_required` |
| 44 | ⬜ | core | `Article.get_absolute_url()` hace reverse de URL inexistente → `NoReverseMatch` |
| 45 | ⬜ | core | `'home'` e `'index'` apuntan al mismo path — redundante |
| 46 | ⬜ | memento | IDOR en `MementoConfigUpdateView` — sin filtro de propietario |
| 47 | ⬜ | memento | `MinValueValidator(timezone.now().date())` congelado en tiempo de carga del módulo |
| 48 | ⬜ | memento | `build_memento_context()` sin rama `else` para frecuencia inválida |
| 49 | ⬜ | memento | `LogoutView` propio en `/memento/logout/` — duplica `accounts:logout` |
| 50 | ⬜ | chat | `HardcodedNotificationManager` en producción — datos falsos (causa de bug #5) |
| 51 | ⬜ | chat | 5 funciones duplicadas en views.py (Python usa la segunda definición) |
| 52 | ⬜ | chat | Template `edit_assistant_configuration.html` inexistente → 500 en esa vista |
| 53 | ⬜ | chat | 20+ endpoints POST con `@csrf_exempt` |
| 54 | ⬜ | chat | `moderate_message()` con `['badword1', 'badword2']` hardcodeado — placeholder |
| 55 | ⬜ | chat | URL Ollama hardcodeada en `ollama_api.py` — no configurable |
| 56 | ⬜ | rooms | `room_comments` falla con `TypeError` — campo `text` inexistente en Comment |
| 57 | ⬜ | rooms | `navigate_room` falla con `AttributeError` — `str.opposite()` no existe |
| 58 | ⬜ | rooms | `calculate_new_position` retorna `None` para EAST/WEST |
| 59 | ⬜ | rooms | 3 ViewSets CRUD ordenan por `-created_at` en modelos sin ese campo |
| 60 | ⬜ | rooms | `room_detail`, `room_list`, `room_comments` sin `@login_required` |
| 61 | ⬜ | rooms | 2 funciones duplicadas: `portal_list`, `portal_detail` |
| 62 | ⬜ | rooms | `CENTRIFUGU_OUTBOX_PARTITIONS` — typo doble U en settings key |
| 63 | ⬜ | courses | `standalone_lessons_list` inaccesible — URL duplicada con `content_manager` |
| 64 | ⬜ | courses | `mark_lesson_complete` falla con `AttributeError` en lecciones independientes |
| 65 | ⬜ | courses | `LessonAttachment.get_file_size_display()` retorna string literal `.1f` |
| 66 | ⬜ | courses | `Review.save()` y signal `update_course_rating` duplican recálculo |
| 67 | ⬜ | courses | Switch de 20 tipos duplicado entre `create_content_block` y `edit_content_block` |
| 68 | ⬜ | kpis | `UploadCSVForm` importada en views.py pero sin vista de upload — import muerto |
| 69 | ⬜ | kpis | `SERVICE_CHOICES` en forms.py difiere de `SERVICIO_CHOICES` en models.py — datos generados inconsistentes |
| 70 | ⬜ | kpis | forms.py con doble bloque de imports — legacy no limpiado |
| 71 | ⬜ | kpis | `aht_por_semana` ordena por semana ISO sin año — ambigüedad cross-year |
| 72 | ⬜ | kpis | `cache.delete_pattern()` silencioso si backend no lo soporta |
| 73 | ⬜ | cv | `from django.contrib.auth.models import User` importado sin uso en models.py |
| 74 | ⬜ | cv | Sin UUID PK en ningún modelo |
| 75 | ⬜ | cv | `EventManager/ProjectManager/TaskManager` importados a nivel de módulo — si `events.management` falla, cv no carga |
| 76 | ⬜ | cv | `reverse('project_detail', ...)` sin namespace en `CorporateDataMixin` — probable `NoReverseMatch` |
| 77 | ⬜ | cv | `pk_url_kwarg = 'user_id'` en `PublicCurriculumView` superfluo |
| 78 | ⬜ | cv | `get_upload_path()` enruta archivos CSV/xlsx al path `images/` — semánticamente incorrecto |
| 79 | ⬜ | cv | `ImageForm` acepta `.gif` pero `Image` model valida solo jpg/jpeg/png/bmp |
| 80 | ⬜ | cv | Wizard de edición sin pasos para Language ni Certification |
| 81 | ⬜ | board | Sin UUID PK en los 3 modelos |
| 82 | ⬜ | board | `Board.owner` en vez de `created_by` — violación de convención |
| 83 | ⬜ | board | `Activity.user` en vez de `created_by` — violación de convención |
| 84 | ⬜ | board | `BoardDetailView` sin verificación de propietario — IDOR activo |
| 85 | ⬜ | board | `settings.BOARD_CONFIG['CARDS_PER_PAGE']` — KeyError si no está definido en settings |
| 86 | ⬜ | board | `BoardConsumer` sin URL WebSocket registrada — tiempo real no activado |
| 87 | ⬜ | board | Sin vistas de edición ni eliminación de `Board` — CRUD incompleto |
| 88 | ⬜ | board | `Activity.target_id` es IntegerField — incompatible con modelos UUID |
| 89 | ⬜ | board | `get_user_model()` a nivel de módulo en models.py — usar `settings.AUTH_USER_MODEL` |
| 90 | ⬜ | campaigns | Sin `created_by` en ningún modelo — diseño global intencional |
| 91 | ⬜ | campaigns | `ContactRecord` y `DiscadorLoad` sin UUID PK |
| 92 | ⬜ | campaigns | `upload_date`/`load_date` con `default=timezone.now` en vez de `auto_now_add` |
| 93 | ⬜ | campaigns | `hasattr(campaign, 'discador_load')` patrón frágil para OneToOne reverse |
| 94 | ⬜ | campaigns | `contacts[:50]` hardcodeado en `campaign_detail` — sin paginación |
| 95 | ⬜ | passgen | Sin `app_name` en `urls.py` — namespace no declarado |
| 96 | ⬜ | passgen | `password_help` da `AttributeError: CATEGORIES` — vista siempre da 500 |
| 97 | ⬜ | passgen | `PasswordForm.length` y `exclude_ambiguous` definidos pero nunca leídos |
| 98 | ⬜ | passgen | `MIN_ENTROPY=60` bloquea 5 de 7 patrones predefinidos — solo `strong` y `secure` funcionan |
| 99 | ⬜ | passgen | `generate_password` y `password_help` sin `@login_required` — acceso público |
| **100** | ⬜ | help | `get_user_model()` a nivel de módulo en `models.py` — usar `settings.AUTH_USER_MODEL` en FKs |
| **101** | ⬜ | help | `from courses.models import Course, Lesson, ContentBlock, CourseCategory` a nivel de módulo — `CourseCategory` sin uso; si `courses` falla, `help` no carga |
| **102** | ⬜ | help | `article_feedback_stats` sin `@login_required` — verifica `is_staff` manualmente pero accesible por anónimos |
| **103** | ⬜ | help | `search_help` evalúa `count()` dos veces sobre los mismos querysets — doble hit a BD |
| **104** | ⬜ | help | `submit_feedback` llama `article.save()` sin `update_fields` — sobreescribe todos los campos del artículo |
| **105** | ⬜ | help | `QuickStartGuide.mark_completed(user)` — parámetro `user` ignorado, `UserGuideProgress` no implementado |
| **106** | ⬜ | help | `HelpArticle.get_related_articles()` filtra solo por categoría — docstring dice "por categoría y tags" pero ignora tags |
| **107** | ⬜ | help | 3 templates faltantes: `faq_list.html`, `video_tutorials.html`, `quick_start.html` — **TemplateDoesNotExist en runtime** |
| **108** | ⬜ | help | Sin UUID PK en ningún modelo — todos AutoField int |
| **109** | ⬜ | help | `author`/`user` en vez de `created_by` — excepción al estándar del proyecto |
| **110** | ⬜ | help | `search_help` — busca log por texto de query para actualizar stats — race condition con búsquedas simultáneas del mismo término |
| **111** | ⬜ | api | Sin `app_name` en `urls.py` — sin namespace |
| **112** | ⬜ | api | 4 endpoints registrados dos veces — en `panel/urls.py` directamente Y via `include('api.urls')` |
| **113** | ⬜ | api | `api/token/connection/` y `api/token/subscription/` no incluidos en `api/urls.py` — inconsistencia |
| **114** | 🔴 | panel | `get_connection_token` no tiene `return` — devuelve `None`, endpoint de Centrifugo inaccesible |
| **115** | ⬜ | panel | `DatabaseSelectorMiddleware` referencia `postgres_online` y `sqlite` no definidos en `DATABASES` — KeyError por request |
| **116** | ⬜ | panel | `storages.py` tiene ~30 `print()` ejecutándose en producción — spam en logs |
| **117** | ⬜ | panel | `RedisTestView` sin `@login_required` — accesible públicamente en `/redis-test/` |
| **118** | ⬜ | panel | `from django.utils import timezone` a nivel global en `settings.py` — solo usado en `TINYMCE_DEFAULT_CONFIG` |
| **119** | ⬜ | panel | `AUTH_USER_MODEL = 'accounts.User'` definido dos veces al final de `settings.py` |
| **120** | ⬜ | panel | `INSTALLED_APPS += ['django_htmx']` al final del archivo — frágil, debería estar en el bloque principal |
