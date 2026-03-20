# Diseño y Roadmap — App `events`

> **Actualizado:** 2026-03-20  
> **Estado:** Funcional en producción  
> **Sprint actual:** 8 completado | Próximo: Sprint 9

---

## Visión General

`events` es el **núcleo operativo** de Management360. Mientras `analyst` y `sim` son las apps de datos e inteligencia, `events` es donde ocurre el trabajo real: proyectos, tareas, comunicación y productividad personal (GTD).

### Pilares funcionales

```
┌─────────────────────────────────────────────────────┐
│                    APP EVENTS                       │
│                                                     │
│  ┌──────────┐  ┌──────────┐  ┌──────────────────┐  │
│  │  Eventos │  │Proyectos │  │     Tareas       │  │
│  │(venue,   │  │(estado,  │  │(schedule, deps,  │  │
│  │asistentes│  │historial)│  │kanban, eisenhow.)│  │
│  └──────────┘  └──────────┘  └──────────────────┘  │
│                                                     │
│  ┌────────────────────────────────────────────────┐ │
│  │           GTD / INBOX                          │ │
│  │  InboxItem → clasificar → procesar → Task/Proj │ │
│  │  Colaborativo · Automático · Con aprendizaje   │ │
│  └────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────┘
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
| Kanban | ✅ Completo | unificado + por proyecto (versión modern) |
| Eisenhower Matrix | ✅ Completo | move AJAX incluido |
| Reminders | ✅ Completo | email/push/both, bulk |
| Project Templates | ✅ Completo | use_template, TemplateTask |
| CreditAccount | ✅ Modelo completo | integración parcial |
| **Namespace URLs** | ✅ Sprint 8 | `app_name = 'events'` declarado, ~520 url tags actualizados |
| **Tests** | ✅ Sprint 8 | 28 tests base — CRUD Project, Task, InboxItem |
| **Limpieza legacy** | ✅ Sprint 8 | Room/Message eliminados de models/admin/forms |

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
```

### Dependencias con otras apps

```
events ──→ chat      (notificaciones de tareas — pendiente formalizar)
events ──→ rooms     (salas para proyectos — pendiente formalizar)
events ──→ bitacora  (related_event, related_task, related_project)
events ──→ analyst   (análisis de proyectos/tareas)
accounts ──→ events  (host de Project/Task/Event)
```

---

## Roadmap

### ✅ Sprint 8 completado — Deuda técnica inmediata

| ID | Tarea | Resultado |
|----|-------|-----------|
| EV-1 | Declarar `app_name = 'events'` en urls.py | ✅ Hecho — ~520 url tags actualizados en 112 templates |
| EV-3 | Remover `Room`/`Message` legacy de models.py | ✅ Hecho — también limpiado de admin.py y forms.py |
| EV-4 | Tests base: CRUD Project + Task + InboxItem | ✅ Hecho — 28 tests en `events/tests/test_models.py` |
| EV-2 | Fix N+1 en dashboard de proyectos | ⏭ Movido a Sprint 9 |

### Sprint 9 — Optimización

| ID | Tarea | Prioridad |
|----|-------|-----------|
| EV-2 | Fix N+1 en `projects_views.py` (`select_related`/`prefetch_related`) | 🔴 |
| EV-OPT-1 | Migrar PKs int → UUID | 🟠 |
| EV-OPT-2 | select_related/prefetch_related en vistas de lista | 🔴 |
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
