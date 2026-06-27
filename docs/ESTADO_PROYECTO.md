# Estado del proyecto Management360

**Fecha:** 2026-06-27T06:05-05:00  
**Rama:** `main`  
**Último commit:** `767a10de` fix(api/v1): corregir serializers Event/Reminder y filtros por proyecto

---

## API v1 — Estado actual

**Base URL:** `/api/v1/`

| Endpoint | Método | Estado | Descripción |
|----------|--------|--------|-------------|
| `/api/v1/health/` | GET | Implementado | Health check del API |
| `/api/v1/projects/` | GET | Implementado | Lista de proyectos con paginación |
| `/api/v1/projects/{id}/` | GET | Implementado | Detalle de proyecto con stats |
| `/api/v1/tasks/` | GET | Implementado | Tareas (filtro: `project_id`, `status`, `assigned_to`) |
| `/api/v1/tasks/{id}/` | GET | Implementado | Detalle de tarea |
| `/api/v1/tasks/{id}/status/` | POST | Implementado | Actualizar estado de tarea |
| `/api/v1/events/` | GET | Implementado | Eventos (filtro: `project_id`, `category`, `status`) |
| `/api/v1/reminders/` | GET | Implementado | Recordatorios (filtro: `project_id`, `is_sent`) |
| `/api/v1/inbox/` | GET | Implementado | Inbox GTD (filtro: `gtd_category`, `created_by`) |
| `/api/v1/inbox/{id}/` | POST | Implementado | Actualizar item de inbox (PATCH) |

**Filtros soportados (todos los endpoints de lista):**
- `?q=` — búsqueda por texto
- `?limit=` — tamaño de página (default 20, max 100)
- `?offset=` — desplazamiento
- `?from=` / `?to=` — rango de fechas ISO (creación)

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
- **Servidor:** `python manage.py runserver` (puerto 8000)
- **Panel:** http://127.0.0.1:8000/
- **API Health:** http://127.0.0.1:8000/api/v1/health/
- **Proyecto M360 ID:** 60 (MementoBloom)

## Verificación API v1 (2026-06-27)

| Endpoint | Estado |
|----------|--------|
| `GET /api/v1/health/` | OK |
| `GET /api/v1/projects/` | OK (51 proyectos) |
| `GET /api/v1/projects/60/` | OK |
| `GET /api/v1/tasks/?project_id=60` | OK (18 tareas) |
| `GET /api/v1/events/?project_id=60` | OK (1 evento) |
| `GET /api/v1/reminders/?project_id=60` | OK (5 recordatorios) |
| `GET /api/v1/inbox/` | OK (181 items) |
- **Commits recientes M360:** `767a10de`, `36dea8be`, `9c7826f2`, `6bea7cd6`, `72c87156`
