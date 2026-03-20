# Referencia de Desarrollo — App `events`

> **Actualizado:** 2026-03-20  
> **Audiencia:** Desarrolladores y asistentes IA  
> **Archivos:** ~235 | **Vistas:** 21 archivos | **Templates:** 152 | **Endpoints:** ~145

---

## Índice

| Sección | Contenido |
|---------|-----------|
| 1. Resumen | Qué hace esta app |
| 2. Modelos | Todos los modelos y sus relaciones |
| 3. Vistas | Organización por módulo |
| 4. URLs | Mapa completo de endpoints |
| 5. Convenciones críticas | Campos especiales, gotchas |
| 6. Sistema GTD | Inbox, clasificación, consenso |
| 7. Bugs conocidos | Issues activos y resueltos |
| 8. Deuda técnica | Lo que necesita refactor |

---

## 1. Resumen

`events` es la **app principal** de Management360. Gestiona el ciclo completo de trabajo:

- **Eventos** → contenedores de alto nivel (venue, asistentes, ticket)
- **Proyectos** → agrupación de tareas, con estados e historial
- **Tareas** → unidad mínima de trabajo, con dependencias y programación
- **GTD / Inbox** → sistema Getting Things Done con clasificación colaborativa
- **Kanban / Eisenhower** → vistas de productividad sobre las tareas
- **Recordatorios** → notificaciones ligadas a eventos/proyectos/tareas
- **Plantillas de proyectos** → reutilización de estructuras comunes
- **TaskSchedule** → programación recurrente de tareas (diaria/semanal/custom)

---

## 2. Modelos

### ⚠️ Convenciones especiales de `events`

| Concepto | Campo | Nota |
|----------|-------|------|
| Propietario de Project | `host` | NO `created_by` — NO cambiar |
| Propietario de Task | `host` | NO `created_by` — NO cambiar |
| Propietario de Event | `host` | NO `created_by` — NO cambiar |
| Responsable asignado | `assigned_to` | FK a User, presente en Event/Project/Task |
| PKs | `AutoField` (int) | Toda la app usa int, NO UUID |

### Modelos de Estado (configurables por admin)

```python
Status        # Estado de Event
ProjectStatus # Estado de Project
TaskStatus    # Estado de Task
```

Todos tienen: `status_name`, `icon`, `active`, `color`.

### Project

```python
class Project(models.Model):
    title          # CharField(200)
    description    # TextField (nullable)
    created_at     # auto_now_add
    updated_at     # auto_now
    done           # BooleanField
    event          # FK → Event (nullable)
    project_status # FK → ProjectStatus
    host           # FK → User (related: 'hosted_projects')
    assigned_to    # FK → User (related: 'managed_projets')  ← typo histórico, no cambiar
    attendees      # M2M → User through ProjectAttendee
    ticket_price   # DecimalField(6,2)
```

Métodos clave:
- `change_status(new_status_id)` — cierra estado actual, abre nuevo, persiste
- `record_edit(editor, field_name, old_value, new_value)` — dispara `change_status` si field es `project_status`

### Task

```python
class Task(models.Model):
    title       # CharField(200)
    description # TextField (nullable)
    important   # BooleanField
    created_at  # auto_now_add
    updated_at  # auto_now
    done        # BooleanField
    project     # FK → Project (nullable)
    event       # FK → Event (nullable)
    task_status # FK → TaskStatus
    assigned_to # FK → User (related: 'managed_tasks')
    host        # FK → User (related: 'hosted_tasks')
    ticket_price# DecimalField(6,2)
    tags        # M2M → Tag
```

Campos de fecha: `due_date` (DateField) — ordenar por `order_by('due_date')`.

Métodos clave:
- `change_status(new_status_id, user=None)` — igual a Project + registra en TaskHistory si hay user
- `record_edit(...)` — igual patrón que Project

### Event

```python
class Event(models.Model):
    title          # CharField(200)
    description    # TextField (nullable)
    event_status   # FK → Status
    venue          # CharField(200)
    host           # FK → User (related: 'hosted_events')
    event_category # CharField(50) — libre, no choices
    max_attendees  # IntegerField
    ticket_price   # DecimalField(6,2)
    assigned_to    # FK → User (related: 'managed_events')
    attendees      # M2M → User through EventAttendee
    tags           # M2M → Tag
    links          # M2M → self (asimétrico)
    classification # FK → Classification (nullable)
```

### Historial y Estados (patrón triple)

| Entidad | Estado temporal | Historial de edición |
|---------|----------------|----------------------|
| Event | `EventState` | `EventHistory` |
| Project | `ProjectState` | `ProjectHistory` |
| Task | `TaskState` | `TaskHistory` |

`*State`: registra transiciones con `start_time`/`end_time`.  
`*History`: registra cambios de campo con `field_name`, `old_value`, `new_value`, `editor`.

### TaskSchedule — Recurrencia

```python
class TaskSchedule(models.Model):
    task            # FK → Task
    host            # FK → User
    recurrence_type # 'weekly' | 'daily' | 'custom'
    monday..sunday  # BooleanField × 7
    start_time      # TimeField
    duration        # DurationField (default 1h)
    start_date      # DateField
    end_date        # DateField (nullable = indefinido)
    is_active       # BooleanField
```

### InboxItem — Core del GTD

```python
class InboxItem(models.Model):
    title          # CharField(200)
    description    # TextField
    created_by     # FK → User  ← usa created_by (excepción al patrón host)
    is_processed   # BooleanField
    processed_at   # DateTimeField (nullable)

    # GenericFK — puede apuntar a Task o Project
    processed_to_content_type # FK → ContentType
    processed_to_object_id    # PositiveIntegerField
    processed_to              # GenericForeignKey

    # GTD
    gtd_category    # 'accionable' | 'no_accionable' | 'pendiente'
    action_type     # 'hacer' | 'delegar' | 'posponer' | 'proyecto' | 'eliminar' | 'archivar' | 'incubar' | 'esperar'
    priority        # 'alta' | 'media' | 'baja'
    context         # CharField(50)
    estimated_time  # IntegerField (minutos, nullable)
    due_date        # DateTimeField (nullable)
    energy_required # 'baja' | 'media' | 'alta'

    # Colaboración
    is_public       # BooleanField
    assigned_to     # FK → User (nullable)
    authorized_users# M2M → User through InboxItemAuthorization
    classification_votes # M2M → User through InboxItemClassification

    # Waiting For
    waiting_for      # TextField
    waiting_for_date # DateTimeField (nullable)

    # Revisión GTD
    next_review_date # DateTimeField (nullable)
    review_notes     # TextField

    # Metadatos
    created_during  # 'morning' | 'afternoon' | 'evening' | 'night'
    user_context    # JSONField (nullable)
    view_count      # PositiveIntegerField
    last_activity   # auto_now
```

Métodos importantes:
- `get_classification_consensus()` — voto mayoritario de `gtd_category`
- `get_action_type_consensus()` — voto mayoritario de `action_type`
- `assign_to_available_user()` — asignación automática por workload + rol CX/FTE
- `increment_views()` — update_fields=['view_count', 'last_activity']

---

## 3. Vistas (resumen por módulo)

| Archivo | Responsabilidad |
|---------|----------------|
| `dashboard_views.py` | `unified_dashboard`, `root`, `management_index`, bulk actions inbox |
| `events_views.py` | CRUD eventos, assign, history, export, bulk |
| `projects_views.py` | CRUD proyectos, alerts, export, bulk, templates |
| `tasks_views.py` | CRUD tareas, ajax status, export, bulk |
| `gtd_views.py` | Inbox GTD, clasificación, consenso, colaboración |
| `schedules_views.py` | TaskSchedule, recurrencia, admin dashboard |
| `kanban_views.py` | Kanban unificado + por proyecto |
| `eisenhower_views.py` | Eisenhower matrix, move AJAX |
| `dependencies_views.py` | TaskDependency, grafo visual |
| `reminders_views.py` | Recordatorios, bulk |
| `templates_views.py` | ProjectTemplate, TemplateTask |
| `bot_views.py` | Simulación de bots (pendiente conectar con app `bots`) |
| `status_views.py` | CRUD de Status/ProjectStatus/TaskStatus |
| `classification_views.py` | CRUD de Classification |

---

## 4. URLs

**Namespace:** `events` — usar siempre `{% url 'events:nombre' %}` en templates.

**Eventos**
```
/events/                                  → events
/events/create/                           → event_create
/events/<int:event_id>/                   → event_detail
/events/<int:event_id>/edit/              → event_edit
/events/<int:event_id>/delete/            → event_delete
/events/<int:event_id>/status/            → event_status_change
/events/<int:event_id>/assign/            → event_assign
/events/<int:event_id>/history/           → event_history
/events/panel/                            → event_panel
/events/export/                           → event_export
/events/bulk-action/                      → event_bulk_action
```

**Proyectos**
```
/projects/                                → projects
/projects/create/                         → project_create
/projects/<int:project_id>/detail/        → project_detail
/projects/<int:project_id>/edit/          → project_edit
/projects/<int:project_id>/delete/        → project_delete
/projects/<int:project_id>/status/        → change_project_status
/projects/panel/                          → project_panel
/projects/export/                         → project_export
/projects/bulk-action/                    → project_bulk_action
```

**Tareas**
```
/tasks/                                   → tasks
/tasks/create/                            → task_create
/tasks/<int:task_id>/edit/                → task_edit
/tasks/<int:task_id>/delete/              → task_delete
/tasks/<int:task_id>/status/              → change_task_status
/tasks/panel/                             → task_panel
/tasks/export/                            → task_export
/tasks/bulk-action/                       → task_bulk_action
/tasks/status/ajax/                       → task_change_status_ajax
```

**GTD / Inbox**
```
/inbox/                                   → inbox
/inbox/process/<int:item_id>/             → process_inbox_item
/inbox/api/tasks/                         → inbox_api_tasks
/inbox/api/projects/                      → inbox_api_projects
/inbox/api/stats/                         → inbox_api_stats
/inbox/api/create-from-inbox/             → inbox_api_create_from_inbox
/inbox/api/assign-item/                   → inbox_api_assign_item
/inbox/admin/                             → inbox_admin_dashboard
/inbox/admin/<int:item_id>/               → inbox_item_detail_admin
/inbox/management/                        → inbox_management_panel
/inbox/classify/<int:item_id>/            → classify_inbox_item_ajax
/inbox/api/consensus/<int:item_id>/       → get_consensus_api
```

**Herramientas**
```
/kanban/                                  → kanban_board
/kanban/project/<int:project_id>/         → kanban_project
/eisenhower/                              → eisenhower_matrix
/eisenhower/move/<int:task_id>/<str:quadrant>/ → move_task_eisenhower
/dependencies/                            → task_dependencies_list
/dependencies/create/<int:task_id>/       → create_task_dependency
/dependencies/graph/<int:task_id>/        → task_dependency_graph
/templates/                               → project_templates
/reminders/                               → reminders_dashboard
```

---

## 5. Convenciones Críticas

### Namespace

```python
# CORRECTO — siempre con prefijo events:
{% url 'events:projects' %}
{% url 'events:task_create' %}
{% url 'events:inbox' %}

# INCORRECTO — sin namespace (rompe desde Sprint 8)
{% url 'projects' %}
```

### PKs: int, no UUID

```python
task = get_object_or_404(Task, pk=task_id)          # task_id es int
project = get_object_or_404(Project, pk=project_id) # project_id es int
```

### Propietario: `host`, no `created_by`

```python
task = get_object_or_404(Task, pk=task_id, host=request.user)
project = get_object_or_404(Project, pk=project_id, host=request.user)
# InboxItem es la excepción:
item = get_object_or_404(InboxItem, pk=item_id, created_by=request.user)
```

### Importar User

```python
# En views.py, forms.py — CORRECTO
from django.contrib.auth import get_user_model
User = get_user_model()

# models.py usa User directo — deuda técnica, no replicar
```

---

## 6. Sistema GTD

### Flujo principal

```
InboxItem (pendiente)
    │
    ├── Clasificación manual (process_inbox_item)
    ├── Clasificación automática (GTDClassificationPattern)
    ├── Clasificación colaborativa (InboxItemClassification)
    └── Procesamiento final → processed_to → Task o Project
```

### Permisos en Inbox

```python
InboxItemAuthorization.permission_level:
  'view'     → solo lectura
  'classify' → puede votar clasificación
  'edit'     → puede editar campos
  'admin'    → control total
```

---

## 7. Bugs Conocidos

| # | Estado | Descripción |
|---|--------|-------------|
| B1 | ✅ resuelto | `energy_required` y `estimated_time` duplicados en `InboxItem` — limpiado en Sprint 8 |
| B2 | ⬜ activo | `from django.contrib.auth.models import User` directo en models.py |
| B3 | ✅ resuelto | `Room` y `Message` en `events/models.py` — eliminados en Sprint 8 |
| B4 | ⬜ activo | `assign_to_available_user()` importa `User` dentro del método |
| B5 | ⬜ activo | `related_name='managed_projets'` — typo histórico en Project.assigned_to |
| B9 | ⬜ activo | N+1 en dashboard de proyectos — Sprint 9 |
| B10 | ✅ resuelto | `events` sin namespace — declarado en Sprint 8, ~520 url tags corregidos |

---

## 8. Deuda Técnica

**Alta prioridad (Sprint 9):**
- Fix N+1 en `projects_views.py` (`select_related`/`prefetch_related`)
- Migrar PKs de int a UUID (alinear con el resto del proyecto)

**Media prioridad:**
- Reemplazar `from django.contrib.auth.models import User` por `get_user_model()` en models.py
- Auditar `_old_scripts/` — `views_bkup.py` tiene 3847 líneas

**Baja prioridad:**
- Unificar las dos CBV de edición de TaskSchedule
- Limpiar rutas legacy en `urls.py`
- Ampliar tests: vistas, GTD, TaskSchedule
