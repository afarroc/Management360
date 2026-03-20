# Diseño y Roadmap — App `bots`

> **Actualizado:** 2026-03-19 (Sprint 8 CERRADO)
> **Estado:** Pipeline Lead→GTD verificado end-to-end ✅
> **Fase del proyecto:** Fase 8 — Automatización y Bots
> **Migraciones:** `0001_initial` · `0002_alter_botlog_category_alter_lead_status` · `bots/0003 si existe` aplicadas

---

## Visión General

La app `bots` resuelve dos necesidades complementarias de Management360:

**1. Motor de Automatización (Multi-Bot FTE)**
Permite que el sistema opere con "empleados virtuales" — instancias de bot que tienen identidad Django real, horario laboral, especialización, y pueden adquirir bloqueos sobre recursos compartidos. Es la infraestructura para que M360 sea autónomo en tareas repetitivas.

**2. Pipeline de Leads (CRM Ligero)**
Gestión completa del ciclo de vida de un lead: importación masiva (CSV/JSON), distribución automática entre bots según estrategia configurable, seguimiento de estado, y conversión. El puente entre este pipeline y el motor de automatización es `Lead.assign_to_bot()` → `events.InboxItem` → `BotTaskAssignment` → `GTDProcessor`.

```
                    ┌─────────────────────────────────┐
                    │         BotCoordinator           │
                    │   (singleton, auto-scaling)      │
                    └───────────────┬─────────────────┘
                                    │ supervisa
              ┌─────────────────────┼─────────────────────┐
              │                     │                     │
     ┌────────▼──────┐    ┌────────▼──────┐    ┌────────▼──────┐
     │  BotInstance  │    │  BotInstance  │    │  BotInstance  │
     │ gtd_processor │    │project_manager│    │task_executor  │
     └───────┬───────┘    └───────┬───────┘    └───────┬───────┘
             │                   │                     │
        GenericUser          GenericUser          GenericUser
        (accounts.User)      (accounts.User)      (accounts.User)
             │
             │ assign_to_bot()
             │
     ┌───────▼──────────────────────────────────┐
     │            Lead (en campaña)              │
     │  new → assigned → in_progress → converted│
     └───────┬──────────────────────────────────┘
             │ _create_inbox_item_for_bot()
             ▼
     ┌───────────────────┐
     │  events.InboxItem  │   ← Integración con app events / GTD
     │ created_by=bot.user│   ✅ EVENTS-BUG-FK resuelto — FK → accounts_user
     └───────┬───────────┘
             │ coordinator.assign_task_to_bot()
             ▼
     ┌───────────────────┐
     │ BotTaskAssignment  │   ← run_bots lo recoge cada 60s
     │  status=assigned   │
     └───────┬───────────┘
             │ GTDProcessor.process_inbox_item()
             ▼
     ┌───────────────────┐
     │  events.Task /     │   ✅ Creada correctamente
     │  events.Project    │
     └───────────────────┘
```

---

## Estado de Implementación

| Módulo | Componente | Estado | Notas |
|--------|-----------|--------|-------|
| **Modelos Bot** | `GenericUser` | ✅ Funcional | Sin UUID, sin created_by |
| **Modelos Bot** | `BotCoordinator` | ✅ Funcional | Auto-scaling desactivado por defecto |
| **Modelos Bot** | `BotInstance` | ✅ Funcional | ✅ working_hours 00:00–23:59 (BOT-BUG-21) · timezone field no funcional |
| **Modelos Bot** | `BotTaskAssignment` | ✅ Funcional | task_id genérico (int) |
| **Modelos Bot** | `ResourceLock` | ✅ Funcional | Sin limpieza de expirados · `acquire_lock` usa `timezone.timedelta` (bug pendiente) |
| **Modelos Bot** | `BotCommunication` | ✅ Funcional | Sin UI de lectura de mensajes |
| **Modelos Bot** | `BotLog` | ✅ Funcional | ✅ choices corregidos S8 |
| **Modelos Leads** | `LeadCampaign` | ✅ Funcional | Sin created_by, sin UUID |
| **Modelos Leads** | `Lead` | ✅ Funcional | ✅ 'skipped', atomicidad, pipeline end-to-end |
| **Modelos Leads** | `LeadDistributionRule` | ✅ Funcional | — |
| **Vistas** | Campañas CRUD | ✅ Funcional | — |
| **Vistas** | Lead list/detail/export | ✅ Funcional | — |
| **Vistas** | API stats/distribute | ✅ Funcional | ✅ @login_required · force=True |
| **Vistas** | Dashboard bots (BOT-4) | ✅ S8 | KPIs + grid + HTMX poll 30s |
| **Vistas** | API bot status (BOT-4) | ✅ S8 | JSON {success, bots, system_load, queue_status} |
| **Distribución** | round_robin | ✅ Implementado | — |
| **Distribución** | equal_split | ✅ Implementado | Default |
| **Distribución** | priority_based | ✅ Implementado | 2x queries por lead |
| **Distribución** | skill_based | ✅ Implementado | Clasificación simplista |
| **Distribución** | custom_rules | ❌ No implementado | Devuelve error |
| **Importación** | CSV | ✅ Funcional | Solo UTF-8 |
| **Importación** | JSON | ✅ Funcional | — |
| **GTD Processor** | `gtd_processor.py` | ✅ S8 — 5 bugs corregidos | task_status · KeyError · ContentType · created_at · timedelta |
| **Commands** | `run_bots.py` | ✅ Funcional | Multi-bot secuencial · pipeline verificado end-to-end |
| **Commands** | `setup_bots.py` | ✅ Funcional | ✅ BOT-BUG-13 · BOT-BUG-21 · signal · connection.close() |
| **Commands** | `setup_leads_demo.py` | ❓ No analizado | 215 líneas — datos de demo |
| **Utils** | `utils.py` | ✅ Funcional | ✅ doble incremento · can_take_task · BotTaskQueue en memoria (BOT-BUG-19) |
| **Admin** | `admin.py` | ❌ Vacío | Solo stub — 3 líneas |

---

## Arquitectura de Datos

### Jerarquía de modelos

```
BotCoordinator (singleton)
└── supervisa (lógica) ──► BotInstance (N bots)
                                ├── GenericUser (1:1 con accounts.User)
                                ├── BotTaskAssignment (tareas asignadas)
                                ├── ResourceLock (bloqueos activos)
                                ├── BotCommunication (mensajes enviados/recibidos)
                                ├── BotLog (logs de actividad)
                                └── Lead.assigned_bot (leads asignados)

LeadCampaign
├── BotInstance (M2M assigned_bots)
├── LeadDistributionRule (reglas de la campaña)
└── Lead (leads de la campaña)
      └── BotInstance (assigned_bot FK)
```

### Dependencias con otras apps

| Dependencia | Dirección | Punto de integración | Estado |
|-------------|-----------|---------------------|--------|
| `accounts.User` | bots → accounts | `GenericUser.user` (OneToOne) | ✅ Estable |
| `events.InboxItem` | bots → events | `Lead._create_inbox_item_for_bot()` | ✅ **EVENTS-BUG-FK resuelto S8** |
| `events.Task/Project` | bots → events | `GTDProcessor._convert_to_task/project()` | ✅ Funcional — ⚠️ EVENTS-SIG-2 genera ERROR en logs |
| `bots` ← `events` | events → bots | Signal `create_credit_account` en bots | ⚠️ EVENTS-SIG pendiente |

---

## Roadmap Sprint 8

| ID | Tarea | Prioridad | Estado | Notas |
|----|-------|-----------|--------|-------|
| BOT-1 | Motor de asignación de leads | 🔴 | ✅ S8 | Pipeline end-to-end verificado |
| BOT-2 | Integrar bots con eventos de `sim` | 🔴 | ⬜ | Añadir task_type `'sim_event'` en `run_bots` |
| BOT-3 | Pipeline outbound / custom_rules | 🟠 | ⬜ | Implementar `custom_rules` en `LeadDistributor` |
| BOT-4 | Dashboard de rendimiento de bots | 🟠 | ✅ S8 | Vista + API + template HTMX 30s |
| BOT-5 | Reglas de distribución por skills | 🟡 | ⬜ | Mejorar `_classify_lead_type()` |

### Pre-requisitos Sprint 8 — estado final

| # | Bug | Estado |
|---|-----|--------|
| 1 | BOT-BUG-13 — `setup_bots` roto | ✅ S8 |
| 2 | BOT-BUG-16 — pipeline Lead→GTD roto | ✅ S8 |
| 3 | BOT-BUG-20 — `can_take_task('any')` | ✅ S8 |
| 4 | BOT-BUG-03 — APIs sin auth | ✅ S8 |
| 5 | BOT-BUG-05 — `assign_to_bot()` no atómica | ✅ S8 |
| 6 | BOT-BUG-18 — doble incremento contador | ✅ S8 |
| 7 | BOT-BUG-01/02/14 — choices + migración | ✅ S8 |
| 8 | BOT-BUG-21 — working_hours 18:00 UTC | ✅ S8 |
| 9 | BOT-BUG-GTD-1/2/3/4 — gtd_processor | ✅ S8 |
| 10 | **EVENTS-BUG-FK** — FKs → accounts_user | ✅ S8 — migración 0004 |
| 11 | BOT-BUG-19 — BotTaskQueue en memoria | ⬜ Sprint 9 |

---

## Roadmap Sprint 9

| ID | Tarea | Prioridad |
|----|-------|-----------|
| EVENTS-SIG | Guard en `create_credit_account` para bots | 🔴 |
| EVENTS-SIG-2 | Fix reverse query GenericFK en signal de events | 🟠 |
| BOT-BUG-19 | Persistir BotTaskQueue en DB (`status='queued'`) | 🟠 |
| ResourceLock timedelta | `from datetime import timedelta` en `acquire_lock()` | 🟡 |
| BOT-2 | Integrar `sim` events con bots | 🟠 |

---

## Notas para Claude

**Al trabajar en esta app, tener en cuenta:**

1. **Todos los modelos tienen PK `int` (AutoField)** — al hacer FK desde otras apps o desde código nuevo, usar `int`, no UUID.

2. ✅ **`setup_bots` reparado** (BOT-BUG-13 + BOT-BUG-21) — funciona con `--reset`. Crea bots con `working_hours 00:00–23:59`. Desconecta temporalmente el signal `create_credit_account` de `events` (EVENTS-SIG workaround).

3. ✅ **`assign_to_bot()` atómica** (BOT-BUG-05) — `transaction.atomic()`. `InboxItem.create()` en savepoint propio.

4. **Import de `events.InboxItem` es lazy** — dentro de `_create_inbox_item_for_bot()`. No mover al tope sin validar circular import.

5. ✅ **`events.InboxItem` usa `created_by`** — `events.Task/Project/Event` usan `host`. ✅ **EVENTS-BUG-FK resuelto** — migración 0004 aplicada. Los usuarios bot (en `accounts_user`) pueden crear InboxItems.

6. **La estrategia `custom_rules`** en `LeadCampaign` falla con error actualmente. Las `LeadDistributionRule` se aplican siempre como pre-paso.

7. **`BotCoordinator` es singleton** — `get_bot_coordinator()` en `utils.py`. Los métodos `check_system_health()`, `process_completed_task()`, `assign_task_to_bot()` están en `BotCoordinatorService` (`utils.py`), **no en el modelo**.

8. ✅ **`BotLog` choices corregidos** (BOT-BUG-02) — `'lead_distribution'` y `'gtd'` en migración 0002.

9. ✅ **`_log_error()` corregido** (BOT-BUG-14) — `level='error'`.

10. **`run_bots` es secuencial** — un bot a la vez. Para producción se necesitará Celery.

11. ✅ **`timedelta` en `_incubate_item()`** corregido (BOT-BUG-15) — usa `from datetime import timedelta`. Para cualquier duración en bots siempre usar `from datetime import timedelta`, nunca `timezone.timedelta`.

12. **`get_bot_coordinator()` devuelve `BotCoordinatorService`**, no un `BotCoordinator` (modelo).

13. ✅ **`BotTaskQueue` y reinicio**: las tareas con `BotTaskAssignment` en DB (`status='assigned'`) **sobreviven** al reiniciar `run_bots` — `_get_pending_tasks_for_bot()` las lee de DB. Solo se pierden las que quedaron en `deque` sin llegar a crear el assignment (BOT-BUG-19).

14. ✅ **Doble incremento corregido** (BOT-BUG-18) — solo `complete_task()` incrementa `tasks_completed_today`.

15. ✅ **Pipeline Lead→GTD verificado end-to-end** — `run_bots --once` procesa un lead completo hasta crear `events.Task`.

16. **EVENTS-SIG activo** — al crear cualquier `User`, el signal `create_credit_account` intenta crear un `CreditAccount`. Para usuarios bot el workaround es desconectar el signal en `setup_bots`. El fix definitivo (Sprint 9) es añadir un guard en el signal.

17. **EVENTS-SIG-2 activo** — signal de `events` hace `InboxItem.objects.filter(processed_to=task)` → `ERROR` en logs. No bloquea. Fix Sprint 9: `ContentType.objects.get_for_model(task.__class__)` + `filter(processed_to_content_type=ct, processed_to_object_id=task.id)`.

18. **`ResourceLock.acquire_lock()`** usa `timezone.timedelta` → `AttributeError`. No afecta el flujo principal. Fix Sprint 9: `from datetime import timedelta`.
