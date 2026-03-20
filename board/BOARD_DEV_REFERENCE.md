# Referencia de Desarrollo — App `board`

> **Actualizado:** 2026-03-20 (Sesión Analista Doc — documentación completa)
> **Audiencia:** Desarrolladores del proyecto y asistentes de IA (Claude)
> **Stats:** 17 archivos · models.py 107 L · views.py 32 L · htmx_views.py 99 L · consumers.py 46 L
> **Namespace:** `board` ✅

---

## Índice

| # | Sección | Contenido |
|---|---------|-----------|
| 1 | Resumen | Qué hace la app |
| 2 | Modelos | Board, Card, Activity |
| 3 | Vistas | views.py + htmx_views.py |
| 4 | WebSocket | consumers.py — BoardConsumer |
| 5 | URLs | Mapa completo |
| 6 | Convenciones críticas y violaciones | Gotchas |
| 7 | Bugs conocidos | Tabla con estado |
| 8 | Deuda técnica | Clasificada por prioridad |

---

## 1. Resumen

La app `board` implementa un **Kanban / tablero visual de tarjetas** estilo Pinterest para Management360. Permite crear tableros con layouts configurables (masonry, grid, libre) y agregar cards de distintos tipos (nota, imagen, enlace, tarea, video). Las operaciones sobre cards son sin recarga de página vía **HTMX**. Incluye un consumer WebSocket (`BoardConsumer`) para sincronización en tiempo real del movimiento de cards entre usuarios — actualmente **no conectado a ninguna URL** (infraestructura preparada, no activada).

---

## 2. Modelos

### 2.1 `Board`

| Campo | Tipo | Notas |
|-------|------|-------|
| `id` | `AutoField` | ⚠️ Sin UUID — violación de convención |
| `name` | `CharField(200)` | — |
| `description` | `TextField(blank=True)` | — |
| `owner` | `FK(User, CASCADE, related_name='boards')` | ⚠️ `owner` — NO `created_by` |
| `collaborators` | `ManyToManyField(User, blank=True, related_name='shared_boards')` | Colaboradores con acceso |
| `cover_image` | `ImageField(upload_to='board/covers/', null=True)` | Sin storage personalizado |
| `layout` | `CharField(20, choices=LAYOUT_CHOICES, default='masonry')` | `masonry`/`grid`/`free` |
| `is_public` | `BooleanField(default=False)` | Tablero público/privado |
| `created_at` | `DateTimeField(auto_now_add=True)` | ✅ |
| `updated_at` | `DateTimeField(auto_now=True)` | ✅ |

**Índices:** `[owner, -updated_at]` · `[is_public]`  
**Ordering:** `['-updated_at']`  
**`get_absolute_url()`:** `reverse('board:detail', args=[self.pk])`

---

### 2.2 `Card`

| Campo | Tipo | Notas |
|-------|------|-------|
| `id` | `AutoField` | ⚠️ Sin UUID |
| `board` | `FK(Board, CASCADE, related_name='cards')` | — |
| `created_by` | `FK(User, SET_NULL, null=True)` | ✅ Convención correcta |
| `card_type` | `CharField(10, choices=CARD_TYPES, default='note')` | `note`/`image`/`link`/`task`/`video` |
| `title` | `CharField(255, blank=True)` | — |
| `content` | `TextField(blank=True)` | Contenido de la nota |
| `url` | `URLField(blank=True)` | Para tipo `link` |
| `image` | `ImageField(upload_to='board/cards/', null=True)` | Para tipo `image` |
| `position_x` | `IntegerField(default=0)` | Posición X (layout `free`) |
| `position_y` | `IntegerField(default=0)` | Posición Y (layout `free`) |
| `width` | `IntegerField(default=1)` | Ancho en unidades de grid |
| `height` | `IntegerField(default=1)` | Alto en unidades de grid |
| `color` | `CharField(20, default='white')` | Color de fondo de la card |
| `is_pinned` | `BooleanField(default=False)` | Cards fijadas aparecen primero |
| `created_at` | `DateTimeField(auto_now_add=True)` | ✅ |
| `updated_at` | `DateTimeField(auto_now=True)` | ✅ |

**Índices:** `[board, -created_at]` · `[board, card_type]`  
**Ordering:** `['-is_pinned', '-created_at']` — cards fijadas primero, luego por fecha desc.

---

### 2.3 `Activity`

Log de actividad por tablero. Registro inmutable de acciones.

| Campo | Tipo | Notas |
|-------|------|-------|
| `id` | `AutoField` | ⚠️ Sin UUID |
| `board` | `FK(Board, CASCADE, related_name='activities')` | — |
| `user` | `FK(User, CASCADE)` | ⚠️ `user` — NO `created_by` |
| `action` | `CharField(20, choices)` | `created`/`updated`/`deleted`/`moved`/`pinned` |
| `target` | `CharField(100)` | Nombre/título del objeto afectado |
| `target_id` | `IntegerField(null=True)` | ⚠️ `IntegerField` — incompatible con UUID |
| `timestamp` | `DateTimeField(auto_now_add=True)` | ⚠️ NO es `created_at` — nombre inconsistente |

**Índice:** `[board, -timestamp]`  
**Ordering:** `['-timestamp']`

---

## 3. Vistas

### views.py — Vistas CBV

| Vista | URL | Template | Notas |
|-------|-----|----------|-------|
| `BoardListView` | `GET /board/` | `board/board_list.html` | Filtra por `owner=request.user` — solo propios |
| `BoardDetailView` | `GET /board/<int:pk>/` | `board/board_detail.html` | ⚠️ **Sin verificación de propietario** — IDOR activo |
| `BoardCreateView` | `GET\|POST /board/create/` | `board/board_form.html` | Inyecta `owner=request.user` en `form_valid()`. Solo expone `name`, `description`, `layout`, `is_public` |

`BoardDetailView` añade `card_types = Card.CARD_TYPES` al contexto.

---

### htmx_views.py — Endpoints HTMX

Todas las vistas tienen `@login_required`. Las operaciones sobre cards verifican `board__owner=request.user` o `owner=request.user`.

| Función | URL | Método | Template retornado | Notas |
|---------|-----|--------|--------------------|-------|
| `board_grid` | `/board/htmx/<board_id>/grid/` | GET | `board/partials/card_grid.html` | Paginación via `settings.BOARD_CONFIG['CARDS_PER_PAGE']` ⚠️ |
| `create_card_htmx` | `/board/htmx/<board_id>/create-card/` | POST | `board/partials/card.html` | Crea card + registra Activity |
| `delete_card_htmx` | `/board/htmx/card/<card_id>/delete/` | DELETE | `HttpResponse(200)` | Emite `HX-Trigger: cardDeleted` |
| `toggle_pin_card` | `/board/htmx/card/<card_id>/toggle-pin/` | POST | `board/partials/card.html` | Toggle `is_pinned`, retorna card actualizada |
| `load_more_cards` | `/board/htmx/<board_id>/load-more/` | GET | `board/partials/card_grid_items.html` | Infinite scroll — `offset` + `limit` |

**`settings.BOARD_CONFIG`** — todas las vistas htmx que paginen dependen de esta clave. Debe estar definida en `settings.py`:
```python
BOARD_CONFIG = {
    'CARDS_PER_PAGE': 20,  # ajustar según necesidad
}
```
Si no está definida → `KeyError` en runtime.

---

## 4. WebSocket — `BoardConsumer`

`consumers.py` implementa `BoardConsumer(AsyncWebsocketConsumer)` para sincronización en tiempo real de movimientos de cards entre usuarios del mismo tablero.

**Grupo:** `board_{board_id}` en channel layer.

**Flujo:**
1. `connect()` — verifica autenticación, une al grupo `board_{id}`, acepta conexión.
2. `receive()` — procesa acción `card_moved`: broadcast a todo el grupo con `card_id` y `position`.
3. `card_update()` — envía el evento al cliente WebSocket conectado.

⚠️ **No hay URL de WebSocket registrada** — `routing.py` no existe en la app. El consumer está implementado pero no está conectado al router ASGI. Para activarlo se necesita agregar en el routing global:
```python
# project/routing.py
re_path(r'ws/board/(?P<board_id>\d+)/$', BoardConsumer.as_asgi()),
```

⚠️ **Solo soporta `card_moved`** — las acciones de crear/eliminar/pin no se broadcastean por WebSocket (solo via HTMX unidireccional).

---

## 5. URLs

| Pattern | Name | Vista | Método |
|---------|------|-------|--------|
| `/board/` | `board:list` | `BoardListView` | GET |
| `/board/create/` | `board:create` | `BoardCreateView` | GET, POST |
| `/board/<int:pk>/` | `board:detail` | `BoardDetailView` | GET |
| `/board/htmx/<int:board_id>/grid/` | `board:grid` | `board_grid` | GET |
| `/board/htmx/<int:board_id>/create-card/` | `board:create_card_htmx` | `create_card_htmx` | POST |
| `/board/htmx/card/<int:card_id>/delete/` | `board:delete_card_htmx` | `delete_card_htmx` | DELETE |
| `/board/htmx/card/<int:card_id>/toggle-pin/` | `board:toggle_pin` | `toggle_pin_card` | POST |
| `/board/htmx/<int:board_id>/load-more/` | `board:load_more` | `load_more_cards` | GET |

**Namespace:** `app_name = 'board'` ✅ declarado en `urls.py`.

**Ausentes (deuda):** No hay URL para editar ni eliminar un Board.

---

## 6. Convenciones Críticas y Violaciones

| Convención | Estándar | Estado en `board` |
|------------|----------|------------------|
| PK UUID | `UUIDField(primary_key=True)` | ❌ Todos usan AutoField int |
| `created_by` | `FK(settings.AUTH_USER_MODEL)` | ⚠️ `Board.owner` y `Activity.user` violan; `Card.created_by` ✅ |
| Timestamps | `created_at`/`updated_at` | ⚠️ `Activity` usa `timestamp` en vez de `created_at` |
| User import en models | `settings.AUTH_USER_MODEL` | ❌ Usa `get_user_model()` a nivel de módulo |
| Namespace | `app_name = 'board'` | ✅ |
| `@login_required` | en todas las vistas | ✅ htmx_views; ⚠️ `BoardDetailView` sin verificación de propietario |

**Import de User correcto en models.py:**
```python
# INCORRECTO (actual) — get_user_model() a nivel de módulo
User = get_user_model()
owner = models.ForeignKey(User, ...)

# CORRECTO
from django.conf import settings
owner = models.ForeignKey(settings.AUTH_USER_MODEL, ...)
```

---

## 7. Bugs Conocidos

| # | Estado | Descripción | Impacto |
|---|--------|-------------|---------|
| #81 | ⬜ | Sin UUID PKs en los 3 modelos | Bajo (deuda) |
| #82 | ⬜ | `Board.owner` en vez de `created_by` — violación de convención | Bajo |
| #83 | ⬜ | `Activity.user` en vez de `created_by` — violación de convención | Bajo |
| **#84** | ⬜ | `BoardDetailView` sin verificación de propietario — IDOR: cualquier usuario autenticado puede ver cualquier tablero por pk | **Alto — seguridad** |
| **#85** | ⬜ | `settings.BOARD_CONFIG['CARDS_PER_PAGE']` — KeyError si no está definido en settings | **Alto — runtime** |
| #86 | ⬜ | `BoardConsumer` sin URL WebSocket registrada — funcionalidad de tiempo real no activada | Medio |
| #87 | ⬜ | Sin vistas de edición ni eliminación de `Board` — CRUD incompleto | Medio |
| #88 | ⬜ | `Activity.target_id` es `IntegerField` — incompatible con modelos UUID del proyecto | Bajo |
| #89 | ⬜ | `get_user_model()` a nivel de módulo en `models.py` — usar `settings.AUTH_USER_MODEL` | Bajo |

---

## 8. Deuda Técnica

### Alta prioridad
- **Bug #84 — Fix IDOR** en `BoardDetailView`: agregar `get_queryset()` filtrando por `owner=self.request.user` o verificar en `get_object()`.
- **Bug #85 — `BOARD_CONFIG`** en settings: confirmar que existe o agregar con valor por defecto.

### Media prioridad
- **Bug #86 — Activar WebSocket**: registrar `BoardConsumer` en routing ASGI del proyecto.
- **Bug #87 — CRUD completo**: implementar `BoardUpdateView` y `BoardDeleteView`.
- **Colaboradores**: `Board.collaborators` (M2M) existe pero ninguna vista lo usa para filtrar acceso.

### Baja prioridad
- UUID PKs en los 3 modelos
- `settings.AUTH_USER_MODEL` en lugar de `get_user_model()` en models
- Tests — `tests.py` es stub (3 líneas)
- `admin.py` vacío — registrar modelos
