# Handoff — App `bots` · Sprint 8 — CERRADO
> **Sesión:** 2026-03-19 · **Rol:** Dev  
> **Próxima sesión:** Dev · Sprint 9 — EVENTS-SIG, EVENTS-SIG-2, BOT-BUG-19, deuda técnica  
> **Docs de referencia:** `BOTS_DEV_REFERENCE.md` · `BOTS_DESIGN.md` · `PROJECT_DEV_REFERENCE.md` · `EVENTS_DEV_REFERENCE.md`

---

## Estado final del Sprint 8

```
EVENTS-BUG-FK  ✅  Migración 0004 aplicada — 26 FKs → accounts_user + INT→BIGINT
gtd_processor  ✅  5 bugs corregidos
BOT-4          ✅  Dashboard + API + template HTMX
BOT-BUG-21     ✅  working_hours 00:00–23:59 en setup_bots
setup_bots     ✅  3 bots activos (gtd_processor, project_manager, task_executor)
run_bots       ✅  ciclo limpio, pipeline verificado end-to-end

Pipeline completo — verificado con run_bots --once:
  Lead (new)
    → LeadDistributor.distribute_leads(force=True)
      → Lead.assign_to_bot(Bot_FTE_3)           ✅
        → InboxItem.create(created_by=bot_user)  ✅  (EVENTS-BUG-FK resuelto)
        → BotLog(lead_distribution)              ✅
        → BotTaskAssignment(Bot_FTE_1, status=assigned)  ✅
          → run_bots ciclo 60s
            → GTDProcessor.process_inbox_item()  ✅
              → Task creada en events             ✅
```

---

## Qué se hizo esta sesión

### EVENTS-BUG-FK ✅

**Causa raíz:** `auth_user.id` es `INT` (Django < 3.2), `accounts_user.id` es `BIGINT` (Django >= 3.2). MariaDB rechaza FK entre tipos distintos → errno 150.

**Fix:** `events/migrations/0004_fix_fk_auth_user_to_accounts_user.py`
- Detecta constraints en runtime vía `information_schema` (idempotente — soporta DROP previo)
- `MODIFY COLUMN INT → BIGINT` preservando `NULL`/`NOT NULL` por columna
- 26 constraints procesados, 25 detectados en vivo + 1 ya dropeado reconstruido

### gtd_processor.py ✅ — 5 bugs

| # | Bug | Fix |
|---|-----|-----|
| 1 | `task_status_id cannot be null` | `_get_default_task_status()` + `_get_default_project_status()` — buscan primer estado activo en DB |
| 2 | `KeyError: 'action'` | `result.get('action', 'error')` en L53 + `'action': 'error'` en todos los `except` de retorno |
| 3 | `Task.get_content_type()` no existe | `ContentType.objects.get_for_model(Task/Project)` |
| 4 | `created_at=item.created_at` en `create()` | Eliminado — `auto_now_add` no acepta valor externo |
| 5 | `timezone.timedelta` en `_incubate_item` | `from datetime import timedelta` (convención del proyecto) |

### BOT-4 ✅

- Vista `bot_dashboard` — KPIs globales, grid de bots, tabla de campañas
- API `api_bot_status` — JSON para HTMX poll cada 30s
- `bots/urls.py` — rutas `dashboard/` y `api/status/` añadidas
- Template `bot_dashboard.html` — Bootstrap 5 + HTMX `hx-swap="none"` + JS DOM update

### BOT-BUG-21 ✅

`setup_bots.py` — `defaults` de `BotInstance.get_or_create()` actualizado:
```python
'working_hours_start': '00:00',
'working_hours_end': '23:59',
```
Los bots existentes se actualizan con:
```bash
python manage.py shell -c "
from bots.models import BotInstance
from datetime import time
BotInstance.objects.all().update(working_hours_start=time(0,0), working_hours_end=time(23,59))
"
```

---

## Archivos modificados esta sesión

```
events/migrations/0004_fix_fk_auth_user_to_accounts_user.py   ← NUEVO
bots/gtd_processor.py                                          ← 5 bugs corregidos
bots/views.py                                                  ← bot_dashboard + api_bot_status
bots/urls.py                                                   ← 2 rutas nuevas
bots/templates/bots/bot_dashboard.html                        ← NUEVO
bots/management/commands/setup_bots.py                        ← working_hours
```

---

## Bugs activos para Sprint 9

| # | App | Descripción | Impacto | Prioridad |
|---|-----|-------------|---------|-----------|
| **EVENTS-SIG** | `events` | Signal `create_credit_account` crea `CreditAccount` para usuarios bot → falla con FK. Guard pendiente en el signal. | Alto | 1 |
| **EVENTS-SIG-2** | `events` | `signals.py` L130: reverse query sobre `GenericForeignKey processed_to` → ERROR en logs en cada Task creada por bot. Fix: `ContentType.objects.get_for_model()` + `filter(processed_to_content_type=ct, processed_to_object_id=id)` | Medio | 2 |
| **BOT-BUG-19** | `bots` | `BotTaskQueue` en `deque` memoria — se pierde al reiniciar. Fix: añadir `status='queued'` a `BotTaskAssignment` y persistir en DB. | Medio | 3 |
| **ResourceLock timedelta** | `bots` | `acquire_lock()` usa `timezone.timedelta` → `AttributeError`. Fix: `from datetime import timedelta`. | Bajo | 4 |

---

## Fixes para Sprint 9 — referencia rápida

### EVENTS-SIG
```python
# events/signals.py (o templatetags/signals.py)
@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_credit_account(sender, instance, created, **kwargs):
    if not created:
        return
    # Guard: no crear CreditAccount para usuarios bot
    if hasattr(instance, 'generic_user_profile') and instance.generic_user_profile.is_bot_user:
        return
    CreditAccount.objects.get_or_create(user=instance)
```

### EVENTS-SIG-2
```python
# events/signals.py L130 — reverse query sobre GenericFK
# INCORRECTO:
InboxItem.objects.filter(processed_to=task)

# CORRECTO:
from django.contrib.contenttypes.models import ContentType
ct = ContentType.objects.get_for_model(task.__class__)
InboxItem.objects.filter(
    processed_to_content_type=ct,
    processed_to_object_id=task.id
)
```

### BOT-BUG-19 — sketch
```python
# 1. Añadir choice en BotTaskAssignment.status:
('queued', 'En Cola')

# 2. Generar migración:
python manage.py makemigrations bots

# 3. En BotCoordinatorService.assign_task_to_bot(), si no hay bot disponible:
BotTaskAssignment.objects.create(
    bot_instance=None,   # ← requiere null=True en el campo (deuda adicional)
    task_type=task_data['type'],
    task_id=task_data['object_id'],
    status='queued',
    priority=task_data.get('priority', 1),
    assignment_reason=task_data.get('reason', ''),
)

# 4. En run_bots._get_pending_tasks_for_bot(), incluir 'queued':
BotTaskAssignment.objects.filter(
    bot_instance=bot,
    status__in=['assigned', 'in_progress', 'queued']
)
```

---

## Contexto rápido

```
AUTH_USER_MODEL = 'accounts.User'  →  tabla: accounts_user
auth_user                          →  tabla legacy (2 superusers)

get_bot_coordinator()  →  BotCoordinatorService (utils.py)
                          NO el modelo BotCoordinator

Bots activos:
  Bot_FTE_1  gtd_processor    user=bot_user_1
  Bot_FTE_2  project_manager  user=bot_user_2
  Bot_FTE_3  task_executor    user=bot_user_3
  Horario:   00:00–23:59 UTC

Pipeline (estado final Sprint 8):
  LeadCampaign → Lead → assign_to_bot → InboxItem → BotTaskAssignment
    → run_bots --once  → GTDProcessor → Task/Project en events  ✅ COMPLETO

bots — int PK (AutoField) en todos los modelos — deuda documentada
events — int PK (AutoField) en todos los modelos — deuda documentada
events.InboxItem  → created_by (no host)
events.Task / Project / Event  → host (no created_by)
```

---

## Archivos a subir en la próxima sesión

```
bots/models.py
bots/views.py
bots/utils.py
bots/urls.py
bots/gtd_processor.py
bots/lead_distributor.py
bots/management/commands/setup_bots.py
bots/management/commands/run_bots.py
events/models.py
events/signals.py  (o events/templatetags/signals.py — donde esté create_credit_account)

BOTS_DEV_REFERENCE.md
BOTS_DESIGN.md
BOTS_HANDOFF.md
EVENTS_DEV_REFERENCE.md
PROJECT_DEV_REFERENCE.md
```
