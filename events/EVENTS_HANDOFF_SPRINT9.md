# Handoff — App `events` · Sprint 9

> **Fecha:** 2026-03-20
> **Branch:** `main`
> **Estado al cierre:** Sistema check limpio, servidor corriendo sin errores

---

## Trabajo realizado

### EVENTS-AI-1 — Report functions GTD en `analyst` ✅

**Entregable:** `analyst/report_functions_events.py`

5 funciones registradas bajo categoría "Events / GTD" en `/analyst/reports/build/`:

| key | descripción |
|-----|-------------|
| `events_inbox_summary` | Distribución de InboxItems por categoría GTD y tipo de acción |
| `events_task_backlog` | Backlog de tareas con detección de vencidas e importantes |
| `events_project_status` | Proyectos por estado con progreso promedio |
| `events_agenda` | Eventos próximos con ventana de días configurable |
| `events_gtd_health` | Score 0–100 combinando inbox + tasks + projects |

**Integración:** una línea al final de `analyst/report_functions.py`:
```python
from analyst import report_functions_events  # noqa: F401
```

**Verificación:**
```bash
python manage.py shell -c "
from analyst.report_functions import get_registry
print({k: v['label'] for k, v in get_registry().items() if 'events' in k})
"
# → 5 keys confirmadas
```

---

### EVENTS-AI-2 — Asistente IA GTD en inbox ✅

**Entregables:**
- `events/views/ai_assistant.py` — 2 endpoints
- `events/urls.py` — 2 URLs nuevas + import explícito
- `events/templates/events/inbox.html` — panel sidebar + JS/CSS

**Endpoints:**
```
GET  /events/inbox/ai/summary/  → análisis automático del estado GTD
POST /events/inbox/ai/chat/     → chat con contexto GTD en tiempo real
```

**Comportamiento:**
- Con Ollama activo: llama a `chat.ollama_api.generate_response` con prompt contextualizado
- Sin Ollama: fallback a análisis estático basado en datos reales (no crashea)
- Contexto incluye: inbox por categoría/acción, tasks vencidas/importantes, proyectos por estado, próximos eventos

**Panel sidebar:** card "Asistente GTD" en `col-lg-3` de `inbox.html` con botón de análisis + chat histórico + input Enter-to-send.

**Verificación:**
```bash
python manage.py shell -c "
from django.urls import reverse
print(reverse('events:inbox_ai_summary'))
print(reverse('events:inbox_ai_chat'))
"
# → /events/inbox/ai/summary/
# → /events/inbox/ai/chat/
```

---

### EVENTS-BUG-FK — (completado Sprint 8, confirmado Sprint 9) ✅

FKs de `events_*` apuntaban a `auth_user` en vez de `accounts_user`. Migración `0004` aplicada. Pipeline `Lead → InboxItem → BotTaskAssignment` desbloqueado.

---

## Archivos modificados / creados

```
analyst/report_functions_events.py   ← NUEVO
analyst/report_functions.py          ← +1 línea import al final
events/views/ai_assistant.py         ← NUEVO
events/urls.py                       ← +import explícito + 2 URLs inbox/ai/
events/templates/events/inbox.html   ← +panel sidebar Asistente GTD + JS/CSS
```

---

## Estado de bugs

| # | Estado anterior | Estado actual |
|---|----------------|---------------|
| B1 | ✅ resuelto | Sin cambio |
| B2 | ⬜ activo | ⬜ activo — `from django.contrib.auth.models import User` en models.py |
| B3 | ✅ resuelto | Sin cambio |
| B4 | ⬜ activo | ⬜ activo — import lazy en `assign_to_available_user()` |
| B5 | ⬜ activo | ⬜ activo — typo `managed_projets` |
| B9 | ⬜ activo | ⬜ activo — N+1 en `projects_views.py` (próxima sesión) |
| B10 | ✅ resuelto | Sin cambio |

---

## Próxima sesión — Sprint 9 continuación

**Prioridad 1 — EVENTS-AI-3:**
Crear los ETL Sources y el Dashboard "GTD Overview" en `/analyst/`:
- ETL Source: `events.InboxItem` (filtro por `created_by_id`)
- ETL Source: `events.Task` (filtro por `host_id`)
- ETL Source: `events.Project` (filtro por `host_id`)
- ETL Source: `events.Event`
- Dashboard con widgets: `events_gtd_health` (kpi_card) + `events_task_backlog` (bar_chart) + `events_inbox_summary` (pie_chart)

**Prioridad 2 — EV-2:**
Fix N+1 en `projects_views.py`.

**Archivos a subir:**
```bash
cat events/views/projects_views.py | termux-clipboard-set
cat analyst/views/etl.py | termux-clipboard-set
cat analyst/views/dashboards.py | termux-clipboard-set
```
