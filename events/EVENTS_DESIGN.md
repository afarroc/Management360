# Diseño y Roadmap — App `events`

> **Actualizado:** 2026-03-20 (Sprint 9 — EVENTS-AI)
> **Estado:** Funcional en producción
> **Sprint actual:** 9 activo

---

## Visión General

`events` es el **núcleo operativo** de Management360. Mientras `analyst` y `sim` son las apps de datos e inteligencia, `events` es donde ocurre el trabajo real: proyectos, tareas, comunicación y productividad personal (GTD).

### Pilares funcionales

```
┌──────────────────────────────────────────────────────────┐
│                      APP EVENTS                          │
│                                                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────────────────┐   │
│  │  Eventos │  │Proyectos │  │       Tareas         │   │
│  │(venue,   │  │(estado,  │  │(schedule, deps,      │   │
│  │asistentes│  │historial)│  │kanban, eisenhower)   │   │
│  └──────────┘  └──────────┘  └──────────────────────┘   │
│                                                          │
│  ┌───────────────────────────────────────────────────┐   │
│  │              GTD / INBOX                          │   │
│  │  InboxItem → clasificar → procesar → Task/Proj    │   │
│  │  Colaborativo · Automático · Con aprendizaje      │   │
│  └───────────────────────────────────────────────────┘   │
│                                                          │
│  ┌───────────────────────────────────────────────────┐   │
│  │           ASISTENTE IA GTD  ← Sprint 9            │   │
│  │  Ollama · análisis en tiempo real · chat inbox    │   │
│  │  5 report functions en analyst · GTD Health Score │   │
│  └───────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────┘
```

---

## Estado de Implementación

| Módulo | Estado | Observaciones |
|--------|--------|---------------|
| CRUD Eventos | ✅ Completo | history, assign, export, bulk |
| CRUD Proyectos | ✅ Completo | history, alerts, export, bulk, templates |
| CRUD Tareas | ✅ Completo | history, export, bulk, ajax status |
| TaskSchedule (recurrente) | ✅ Completo | CBV + vista enhanced, admin dashboard |
| TaskDependency | ✅ Completo | grafo visual incluido |
| GTD Inbox básico | ✅ Completo | process, classify, bulk |
| GTD Colaborativo | ✅ Completo | autorización, votos, consenso |
| GTD Automático (patrones) | ✅ Modelo completo | integración con UI — revisar |
| GTD Aprendizaje | ✅ Modelo completo | integración con UI — revisar |
| Kanban | ✅ Completo | unificado + por proyecto |
| Eisenhower Matrix | ✅ Completo | move AJAX incluido |
| Reminders | ✅ Completo | email/push/both, bulk |
| Project Templates | ✅ Completo | use_template, TemplateTask |
| CreditAccount | ✅ Modelo completo | integración parcial |
| **Namespace URLs** | ✅ Sprint 8 | `app_name = 'events'`, ~520 url tags actualizados |
| **Tests** | ✅ Sprint 8 | 28 tests base — CRUD Project, Task, InboxItem |
| **Limpieza legacy** | ✅ Sprint 8 | Room/Message eliminados de models/admin/forms |
| **Asistente IA GTD** | ✅ Sprint 9 | Ollama + fallback estático, panel sidebar inbox |
| **Report functions analyst** | ✅ Sprint 9 | 5 funciones GTD en `/analyst/reports/build/` |

---

## Arquitectura de Datos

### Jerarquía principal

```
Event (opcional)
  └── Project
        └── Task
              ├── TaskState (historial estados)
              ├── TaskHistory (historial ediciones)
              ├── TaskProgram (bloques de tiempo)
              ├── TaskSchedule (recurrencia)
              ├── TaskDependency (deps entre tareas)
              └── Tag (M2M)

InboxItem
  └── processed_to → Task | Project (GenericFK)
  └── InboxItemClassification (votos colaborativos)
  └── InboxItemAuthorization (permisos)
  └── InboxItemHistory (audit log)
  └── ← Asistente IA GTD lee este modelo en tiempo real (Sprint 9)
```

### Dependencias con otras apps

```
events ──→ chat      (notificaciones de tareas — pendiente formalizar)
events ──→ rooms     (salas para proyectos — pendiente formalizar)
events ──→ bitacora  (related_event, related_task, related_project)
events ──→ analyst   (5 report functions GTD — Sprint 9 ✅)
events ──→ chat      (Ollama via chat.ollama_api — asistente IA Sprint 9 ✅)
accounts ──→ events  (host de Project/Task/Event)
bots    ──→ events   (InboxItem.created_by = bot_user — EVENTS-BUG-FK resuelto Sprint 8)
```

---

## Roadmap

### ✅ Sprint 8 completado

| ID | Tarea | Resultado |
|----|-------|-----------|
| EV-1 | Declarar `app_name = 'events'` en urls.py | ✅ ~520 url tags actualizados en 112 templates |
| EV-3 | Remover `Room`/`Message` legacy de models.py | ✅ limpiado de admin.py y forms.py |
| EV-4 | Tests base: CRUD Project + Task + InboxItem | ✅ 28 tests en `events/tests/test_models.py` |
| EVENTS-BUG-FK | FKs apuntaban a `auth_user` en vez de `accounts_user` | ✅ migración 0004 aplicada |
| EV-2 | Fix N+1 en dashboard de proyectos | ⏭ Movido a Sprint 9 |

### ✅ Sprint 9 — EVENTS-AI (completado en sesión 2026-03-20)

| ID | Tarea | Resultado |
|----|-------|-----------|
| EVENTS-AI-1 | 5 report functions GTD en `analyst` | ✅ `analyst/report_functions_events.py` |
| EVENTS-AI-2 | Asistente IA GTD en inbox (Ollama + fallback) | ✅ `events/views/ai_assistant.py` |

### Sprint 9 — Pendiente

| ID | Tarea | Prioridad |
|----|-------|-----------|
| EV-2 | Fix N+1 en `projects_views.py` | 🔴 |
| EV-OPT-2 | `select_related`/`prefetch_related` en vistas de lista | 🔴 |
| EVENTS-AI-3 | Crear ETL Sources + Dashboard "GTD Overview" en analyst | 🟠 |
| EV-OPT-1 | Migrar PKs int → UUID | 🟠 |
| EV-OPT-3 | Unificar dos CBV de TaskSchedule edit | 🟡 |
| EV-OPT-4 | Audit y limpieza de `_old_scripts/` | 🟡 |

### Sprint 10 — Integración con `bots`

| ID | Tarea | Prioridad |
|----|-------|-----------|
| EV-BOT-1 | Conectar `bot_views.py` con app `bots` real | 🔴 |
| EV-BOT-2 | InboxItem → trigger bot assignment via `bots` | 🟠 |
| EV-BOT-3 | GTDProcessingSettings → conectar con `bots.BotCoordinator` | 🟠 |

---

## Notas para Claude

- **PKs son int** — NO uuid. Usar `<int:project_id>` en urls, no `<uuid:...>`
- **`host`** es el propietario — NO usar `created_by` para Project/Task/Event
- **`InboxItem`** sí usa `created_by` — es la excepción
- **Namespace declarado** — usar `{% url 'events:nombre' %}` en todos los templates
- **`related_name='managed_projets'`** — typo histórico, no corregir sin migración
- **`_old_scripts/`** — ignorar para cualquier análisis o referencia de código
- **`Room`/`Message`** — eliminados de `events`. Los modelos reales viven en `rooms` y `chat`
- **`from django.contrib.auth.models import User`** — deuda técnica en models.py, no replicar
- **`ai_assistant.py`** — importar explícitamente en `urls.py` (`from .views.ai_assistant import ...`), no está en el `__init__` del paquete views
- **`report_functions_events.py`** — no es una vista, no tiene URLs. Se auto-registra al importarse desde `analyst/report_functions.py`
