# Estado del proyecto Management360

**Fecha:** 2026-06-27T10:58-05:00  
**Rama:** `main`  
**Último commit:** (pendiente — serializer writable)

---

## Integración M360 API v1 — Estado actual

**Resultado end-to-end:** `sync_sprint.py --sprint-id S-27-06` → `ok=7 errors=0`

| Recurso | Estado | IDs creados |
|---------|--------|-------------|
| Proyecto | OK | 78 |
| Tareas | OK | 278, 279, 280 |
| Eventos | OK | kickoff, review |
| Recordatorio | OK | reminder-1 |

**Cambios aplicados en esta sesión:**
- `api/v1/serializers.py`:
  - `ProjectSerializer`: campos escribibles `project_status_id`, `host_id`, `assigned_to_id`
  - `TaskSerializer`: campos escribibles `task_status_id`, `project_id`, `assigned_to_id`, `host_id`
  - `EventSerializer`: campos escribibles `event_status_id`, `host_id`, `assigned_to_id`
- `tools/m360_bridge/client.py` (mementobloom):
  - Método `_request_json` para envío JSON con CSRF
  - Métodos `api_v1_*` (projects, tasks, events, reminders, inbox, health)
  - Defaults seguros en `create_project`, `create_task`, `create_reminder`
- `tools/m360_bridge/sync.py` (mementobloom):
  - Consume endpoints `/api/v1/` en lugar de rutas legacy

**Base URL:** `/api/v1/`

| Endpoint | Método | Estado | Descripción |
|----------|--------|--------|-------------|
| `/api/v1/health/` | GET | OK | Health check del API |
| `/api/v1/projects/` | GET/POST | OK | Lista/creación de proyectos |
| `/api/v1/projects/{id}/` | GET | OK | Detalle de proyecto con stats |
| `/api/v1/tasks/` | GET/POST | OK | Tareas (filtro: `project_id`, `status`, `assigned_to`) |
| `/api/v1/tasks/{id}/` | GET | OK | Detalle de tarea |
| `/api/v1/tasks/{id}/status/` | POST | OK | Actualizar estado de tarea |
| `/api/v1/events/` | GET/POST | OK | Eventos (filtro: `project_id`, `category`, `status`) |
| `/api/v1/reminders/` | GET/POST | OK | Recordatorios (filtro: `project_id`, `is_sent`) |
| `/api/v1/inbox/` | GET/POST | OK | Inbox GTD (filtro: `gtd_category`, `created_by`) |
| `/api/v1/inbox/{id}/` | PATCH | OK | Actualizar item de inbox |

**Filtros soportados (todos los endpoints de lista):**
- `?q=` — búsqueda por texto
- `?limit=` — tamaño de página (default 20, max 100)
- `?offset=` — desplazamiento
- `?from=` / `?to=` — rango de fechas ISO (creación)

**Servidor:** Daphne/ASGI en `0.0.0.0:8000`  
**Último health check:** OK  
**Proyecto M360 ID:** 78 (MementoBloom - S-27-06)

---

## Cambios pendientes (working tree)

| Archivo | Tipo | Estado | Notas |
|---------|------|--------|-------|
| `api/v1/serializers.py` | Modificado | **Commiteado** | Fix fields EventSerializer |
| `api/v1/views.py` | Modificado | **Commiteado** | Fix filtros project__id |
| `.env` | Modificado | Sin commit (ignorado) | ALLOWED_HOSTS agregado |
| `chat/views.py` | Modificado | Pendiente | ai_test endpoint |
| `chat/ollama_api.py` | Modificado | Pendiente | Cambios en integración Ollama |
| `courses/views.py` | Modificado | Pendiente | Plantillas público |
| `docs/HANDOFF_*.md` | Nuevos (4) | Pendiente | Documentación histórica |

## Hardcodeos eliminados

| Antes | Después |
|-------|---------|
| `ALLOWED_HOSTS` con IPs en `panel/settings.py` | `localhost,127.0.0.1,testserver` (default) |
| | IPs movidas a `.env` como `ALLOWED_HOSTS` |

## Hardcodeos restantes en .env (pendientes)

| Variable | Valor actual | Acción |
|----------|--------------|--------|
| `DATABASE_HOST` | `192.168.18.59` | Pendiente mover a variable de entorno |
| `OLLAMA_HOST` | `192.168.18.59` | Pendiente mover a variable de entorno |
| `OLLAMA_BASE_URL` | `http://192.168.18.59:11434` | Pendiente mover a variable de entorno |

## Acceso

- **Django check:** `python manage.py check` → OK (0 issues)
- **Servidor:** Daphne/ASGI en puerto 8000
- **Panel:** http://127.0.0.1:8000/
- **API Health:** http://127.0.0.1:8000/api/v1/health/
- **Proyecto M360 ID:** 78 (MementoBloom - S-27-06)

## Verificación API v1 (2026-06-27)

| Endpoint | Estado |
|----------|--------|
| `GET /api/v1/health/` | OK |
| `GET /api/v1/projects/` | OK (proyecto creado id=78) |
| `GET /api/v1/tasks/?project_id=78` | OK (3 tareas) |
| `GET /api/v1/events/?project_id=78` | OK |
| `GET /api/v1/reminders/?project_id=78` | OK (1 recordatorio) |
| `GET /api/v1/inbox/` | OK |

## Commits recientes M360

- `767a10de` fix(api/v1): corregir serializers Event/Reminder y filtros por proyecto
- `36dea8be` feat(api/v1): ViewSets, paginacion, filtrado y rutas /api/v1/
- `065d957f` feat(api/v1): serializers para Project, Task, Event, Reminder, InboxItem
- `6bea7cd6` chore: agregar API_SPEC.md
- `72c87156` fix(migrations): resolver conflicto en 0023_evento_tipo
