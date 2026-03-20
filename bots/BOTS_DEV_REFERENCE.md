# Referencia de Desarrollo — App `bots`

> **Actualizado:** 2026-03-19 (v4 — Sprint 8 CERRADO)
> **Audiencia:** Desarrolladores del proyecto y asistentes de IA (Claude)
> **Sprint:** S8 — COMPLETO. Pipeline Lead→GTD verificado end-to-end.
> **Stats:** 15 archivos · models.py 693 L · views.py ~430 L · lead_distributor.py 390 L · gtd_processor.py ~250 L · run_bots.py 341 L · setup_bots.py 189 L
> **Namespace:** `bots` ✅

---

## Índice

| # | Sección | Contenido |
|---|---------|-----------|
| 1 | Resumen | Qué hace la app, sus tres pilares |
| 2 | Modelos | 10 modelos — campo por campo |
| 3 | Vistas | 13 vistas organizadas por módulo |
| 4 | URLs | Mapa completo de endpoints |
| 5 | Servicios | LeadDistributor, BulkLeadImporter, GTDProcessor |
| 6 | Management Commands | run_bots, setup_bots, setup_leads_demo |
| 7 | Sistema GTD — Flujo completo | Fases, decisiones, integración con events |
| 8 | Sistema de Distribución de Leads | Estrategias, reglas, flujo completo |
| 9 | Convenciones críticas y violaciones | Gotchas, bugs de convención |
| 10 | Bugs conocidos | Tabla con estado |
| 11 | Deuda técnica | Clasificada por prioridad |

---

## 1. Resumen

La app `bots` implementa **tres subsistemas interrelacionados** dentro de Management360:

### Pilar 1 — Sistema Multi-Bot FTE
Infraestructura para crear, coordinar y monitorear bots autónomos que ejecutan tareas dentro del ecosistema M360. Cada bot es un `BotInstance` asociado a un `GenericUser` (usuario Django real) con especialización, horario laboral, y capacidad de adquirir bloqueos distribuidos sobre recursos. Un `BotCoordinator` centraliza la lógica de auto-escalado y carga del sistema.

### Pilar 2 — Gestión de Leads y Campañas
Sistema completo de CRM ligero para importar, distribuir y hacer seguimiento de leads a través de campañas. Los leads se distribuyen automáticamente entre bots disponibles usando estrategias configurables (round-robin, equal-split, priority-based, skill-based) y reglas personalizadas por campaña.

### Pilar 3 — Procesador GTD (`gtd_processor.py`)
Implementa la metodología Getting Things Done sobre `events.InboxItem`. Para cada item capturado en el inbox de un bot, el procesador decide si es accionable (análisis de keywords + scoring), aplica la regla de los 2 minutos, y convierte el item en `events.Task` o `events.Project` con subtareas automáticas.

### Integración clave con `events`
Cuando un `Lead` es asignado a un `BotInstance`, se crea automáticamente un `InboxItem` en la app `events` usando el usuario Django del bot (`bot.generic_user.user`) como `created_by`. Ese InboxItem es luego recogido por `run_bots` vía `BotTaskAssignment`, procesado por `GTDProcessor`, y convertido en `Task` o `Project`. El bot actúa como propietario (`host`) de todos los objetos que crea en `events`.

✅ **Pipeline verificado end-to-end** (Sprint 8): Lead → InboxItem → BotTaskAssignment → GTDProcessor → Task.

---

## 2. Modelos

### 2.1 `GenericUser`

Perfil extendido de usuario Django para que los bots tengan identidad en el sistema.

| Campo | Tipo | Notas |
|-------|------|-------|
| `user` | `OneToOneField(User)` | `related_name='generic_user_profile'` |
| `is_bot_user` | `BooleanField(default=False)` | Distingue bot vs humano |
| `role_description` | `CharField(200, blank=True)` | Descripción libre del rol |
| `is_available` | `BooleanField(default=True)` | Disponibilidad operativa |
| `allowed_operations` | `JSONField(default=list)` | Lista de operaciones permitidas |
| `tasks_completed` | `IntegerField(default=0)` | Contador acumulado |
| `last_activity` | `DateTimeField(auto_now=True)` | Se actualiza en cada save |

⚠️ **Sin `created_at`** — solo tiene `last_activity` (auto_now, no auto_now_add).
⚠️ **Sin PK UUID** — usa AutoField por defecto (violación de convención del proyecto).

---

### 2.2 `BotCoordinator`

Coordinador central del sistema. Singleton en la práctica (se espera una sola instancia activa).

| Campo | Tipo | Notas |
|-------|------|-------|
| `name` | `CharField(200)` | Default `"Main Bot Coordinator"` |
| `is_active` | `BooleanField(default=True)` | — |
| `min_bots` | `IntegerField(default=1)` | Mínimo de bots en el sistema |
| `max_bots` | `IntegerField(default=10)` | Máximo de bots |
| `scale_up_threshold` | `FloatField(default=0.8)` | Carga para escalar up (0-1) |
| `scale_down_threshold` | `FloatField(default=0.2)` | Carga para escalar down (0-1) |
| `auto_scaling_enabled` | `BooleanField(default=False)` | El auto-scaling está OFF por defecto |
| `active_bots_count` | `IntegerField(default=0)` | Se actualiza manualmente |
| `system_load` | `FloatField(default=0.0)` | Calculado por `get_system_load()` |
| `last_health_check` | `DateTimeField(auto_now=True)` | — |

**Métodos relevantes:**
- `get_system_load()` — calcula carga como `active_tasks / (active_bots * 5)`, persiste en DB.
- `should_scale_up()` / `should_scale_down()` — devuelven bool según umbrales.

⚠️ `get_system_load()` hace `self.save()` dentro del método — efecto secundario en cada consulta.
⚠️ Capacidad hardcoded: 5 tareas por bot.
⚠️ **Sin PK UUID**, sin `created_at`/`updated_at`.

---

### 2.3 `BotInstance`

Instancia individual de bot. Es la entidad central del Pilar 1.

| Campo | Tipo | Notas |
|-------|------|-------|
| `name` | `CharField(100, unique=True)` | Identificador único |
| `generic_user` | `FK(GenericUser, CASCADE)` | `related_name='bot_instances'` |
| `specialization` | `CharField(50, choices)` | Ver opciones abajo |
| `priority_level` | `IntegerField(default=1)` | 1-10, mayor = más prioritario |
| `is_active` | `BooleanField(default=True)` | — |
| `current_status` | `CharField(20, choices)` | idle/working/paused/error/maintenance |
| `status_message` | `CharField(200, blank=True)` | Mensaje libre de estado |
| `last_heartbeat` | `DateTimeField(auto_now=True)` | — |
| `tasks_completed_today` | `IntegerField(default=0)` | ⚠️ NO se resetea automáticamente |
| `tasks_completed_total` | `IntegerField(default=0)` | Acumulado de vida del bot |
| `error_count` | `IntegerField(default=0)` | Conteo de errores |
| `average_task_time` | `FloatField(default=0.0)` | Segundos por tarea |
| `working_hours_start` | `TimeField(default='09:00')` | Horario inicio (modelo). ✅ `setup_bots` crea con `'00:00'` (BOT-BUG-21) |
| `working_hours_end` | `TimeField(default='18:00')` | Horario fin (modelo). ✅ `setup_bots` crea con `'23:59'` (BOT-BUG-21) |
| `timezone` | `CharField(50, default='UTC')` | ⚠️ Solo almacenado — `is_working_hours()` usa UTC del servidor |
| `max_concurrent_tasks` | `IntegerField(default=1)` | — |
| `capabilities` | `JSONField(default=dict)` | Capacidades libres en JSON |
| `configuration` | `JSONField(default=dict)` | Config personalizada |
| `created_at` | `DateTimeField(auto_now_add=True)` | ✅ |
| `updated_at` | `DateTimeField(auto_now=True)` | ✅ |

**Especializaciones disponibles:**

| Valor | Display | Tareas compatibles |
|-------|---------|-------------------|
| `gtd_processor` | Procesador GTD | process_inbox, create_task, organize_items |
| `project_manager` | Gestor de Proyectos | create_project, update_project, manage_dependencies |
| `task_executor` | Ejecutor de Tareas | execute_task, update_task, complete_task |
| `calendar_optimizer` | Optimizador de Calendario | schedule_task, optimize_calendar, create_event |
| `communication_handler` | Manejador de Comunicación | send_notification, process_message, handle_communication |
| `general_assistant` | Asistente General | Todas (`*`) |

**Métodos relevantes:**
- `is_working_hours()` — compara `timezone.now().time()` con los campos TimeField. **Bug: no respeta el campo `timezone`** — siempre compara en UTC.
- `can_take_task(task_type, priority)` — verifica `is_active`, `is_working_hours()`, límite de tareas concurrentes, y compatibilidad de especialización.
- `update_status(new_status, message)` — actualiza status + heartbeat con `update_fields`.
- `get_performance_metrics()` — devuelve dict con métricas. `_calculate_uptime()` devuelve `95.0` hardcoded (placeholder).

✅ **BOT-BUG-21 resuelto** — `setup_bots` ahora crea bots con `working_hours_start='00:00'` y `working_hours_end='23:59'`.

Para actualizar bots existentes:
```bash
python manage.py shell -c "
from bots.models import BotInstance
from datetime import time
BotInstance.objects.all().update(working_hours_start=time(0,0), working_hours_end=time(23,59))
"
```

⚠️ **Sin PK UUID** — violación de convención.
⚠️ `tasks_completed_today` no tiene reset automático.
⚠️ `_calculate_uptime()` es un placeholder — siempre retorna 95.0.
⚠️ `timezone` field no se usa en `is_working_hours()`.

---

### 2.4 `BotTaskAssignment`

Representa la asignación de una tarea externa a un bot. Usa `task_id` como entero genérico.

| Campo | Tipo | Notas |
|-------|------|-------|
| `bot_instance` | `FK(BotInstance, CASCADE)` | `related_name='task_assignments'` |
| `task_type` | `CharField(50)` | Tipo libre de tarea |
| `task_id` | `IntegerField()` | ID de la tarea externa — genérico |
| `priority` | `IntegerField(default=1)` | — |
| `status` | `CharField(20, choices)` | assigned/in_progress/completed/failed/cancelled |
| `assigned_at` | `DateTimeField(auto_now_add=True)` | — |
| `started_at` | `DateTimeField(null=True)` | — |
| `completed_at` | `DateTimeField(null=True)` | — |
| `deadline` | `DateTimeField(null=True)` | — |
| `result_data` | `JSONField(default=dict)` | Resultado estructurado |
| `error_message` | `TextField(blank=True)` | — |
| `assignment_reason` | `TextField(blank=True)` | — |
| `retry_count` | `IntegerField(default=0)` | — |
| `max_retries` | `IntegerField(default=3)` | — |

**Métodos:** `start_task()`, `complete_task(result_data)`, `fail_task(error_message)`, `can_retry()`.
`complete_task()` incrementa contadores en `BotInstance` directamente (no atómico).

⚠️ `task_id` es un `IntegerField` genérico — no hay FK tipada al objeto referenciado.
⚠️ `complete_task()` actualiza `BotInstance.tasks_completed_total += 1` sin `F()` — race condition posible.

---

### 2.5 `ResourceLock`

Bloqueos distribuidos para que los bots no operen sobre el mismo recurso simultáneamente.

| Campo | Tipo | Notas |
|-------|------|-------|
| `resource_type` | `CharField(50)` | Ej: 'project', 'task', 'event' |
| `resource_id` | `IntegerField()` | ID del recurso |
| `bot_instance` | `FK(BotInstance, CASCADE)` | `related_name='resource_locks'` |
| `lock_type` | `CharField(20)` | exclusive / shared |
| `is_active` | `BooleanField(default=True)` | — |
| `acquired_at` | `DateTimeField(auto_now_add=True)` | — |
| `expires_at` | `DateTimeField()` | Required, calculado al crear |
| `lock_reason` | `TextField(blank=True)` | — |

`unique_together = ['resource_type', 'resource_id', 'bot_instance']`

**Métodos de clase:**
- `ResourceLock.acquire_lock(resource_type, resource_id, bot_instance, lock_type, timeout_minutes=5)` — usa `transaction.atomic()`.

⚠️ `acquire_lock` usa `timezone.timedelta` internamente → `AttributeError` (bug global #11). Fix pendiente: `from datetime import timedelta`.
⚠️ Los bloqueos expirados **no se limpian automáticamente** — `is_expired()` solo verifica, no libera.
⚠️ `acquire_lock` no verifica bloqueos expirados antes de retornar `None`.
⚠️ `resource_id` es `IntegerField` — no compatible con modelos UUID del proyecto.

---

### 2.6 `BotCommunication`

Mensajería entre bots (o broadcast a todos).

| Campo | Tipo | Notas |
|-------|------|-------|
| `sender` | `FK(BotInstance, CASCADE)` | `related_name='sent_messages'` |
| `recipient` | `FK(BotInstance, null=True)` | `null=True` = broadcast |
| `message_type` | `CharField(50, choices)` | task_request/status_update/resource_request/coordination/alert/broadcast |
| `subject` | `CharField(200)` | — |
| `content` | `TextField()` | — |
| `priority` | `CharField(20, choices)` | low/medium/high/urgent |
| `is_read` | `BooleanField(default=False)` | — |
| `sent_at` | `DateTimeField(auto_now_add=True)` | — |
| `read_at` | `DateTimeField(null=True)` | — |
| `metadata` | `JSONField(default=dict)` | Datos extra |

---

### 2.7 `BotLog`

Sistema de logging persistente para actividad de bots.

| Campo | Tipo | Notas |
|-------|------|-------|
| `bot_instance` | `FK(BotInstance, null=True)` | `null=True` permite logs de sistema |
| `category` | `CharField(50, choices)` | task/system/error/communication/performance/lead/**lead_distribution**/**gtd**/coordination |
| `level` | `CharField(20, choices)` | debug/info/warning/error/critical |
| `message` | `TextField()` | — |
| `details` | `JSONField(default=dict)` | Datos estructurados adicionales |
| `task_assignment` | `FK(BotTaskAssignment, null=True)` | — |
| `related_object_type` | `CharField(50, blank=True)` | Ej: 'lead', 'task', 'project' |
| `related_object_id` | `IntegerField(null=True)` | ID del objeto relacionado |
| `created_at` | `DateTimeField(auto_now_add=True)` | — |

**Índices definidos:**
- `(bot_instance, category, created_at)`
- `(category, level, created_at)`

✅ **BOT-BUG-02 resuelto** — `'lead_distribution'` y `'gtd'` añadidos a choices de `BotLog.category` (migración 0002).
⚠️ `related_object_id` es `IntegerField` — incompatible con modelos UUID.

---

### 2.8 `LeadCampaign`

Campaña de distribución de leads. Agrupa leads y define la estrategia de asignación.

| Campo | Tipo | Notas |
|-------|------|-------|
| `name` | `CharField(200)` | — |
| `description` | `TextField(blank=True)` | — |
| `auto_distribute` | `BooleanField(default=True)` | Si false, solo distribución manual |
| `distribution_strategy` | `CharField(50, choices)` | round_robin/equal_split/priority_based/skill_based/custom_rules |
| `assigned_bots` | `ManyToManyField(BotInstance)` | `related_name='lead_campaigns'`, blank=True |
| `max_leads_per_bot` | `IntegerField(default=10)` | Límite de leads activos por bot |
| `leads_per_batch` | `IntegerField(default=5)` | Leads por ejecución de distribución |
| `is_active` | `BooleanField(default=True)` | — |
| `created_at` | `DateTimeField(auto_now_add=True)` | ✅ |
| `updated_at` | `DateTimeField(auto_now=True)` | ✅ |
| `total_leads` | `IntegerField(default=0)` | Contador desnormalizado — se actualiza en import |
| `distributed_leads` | `IntegerField(default=0)` | Contador desnormalizado |
| `converted_leads` | `IntegerField(default=0)` | Contador desnormalizado |

⚠️ `custom_rules` es una estrategia válida en choices pero **no está implementada** en `LeadDistributor.distribute_leads()` — devuelve error `'Estrategia no implementada'`. Las reglas personalizadas se aplican siempre como pre-paso, independientemente de la estrategia.
⚠️ Los contadores son desnormalizados y se actualizan sin transacción atómica.
⚠️ **Sin `created_by`** — violación de convención.
⚠️ **Sin PK UUID** — violación de convención.

---

### 2.9 `Lead`

Lead/Prospect individual, pertenece siempre a una `LeadCampaign`.

| Campo | Tipo | Notas |
|-------|------|-------|
| `name` | `CharField(200)` | — |
| `email` | `EmailField(blank=True)` | — |
| `phone` | `CharField(20, blank=True)` | — |
| `company` | `CharField(200, blank=True)` | — |
| `source` | `CharField(100, blank=True)` | 'CSV Import', 'Manual', 'JSON Import' |
| `notes` | `TextField(blank=True)` | — |
| `custom_data` | `JSONField(default=dict)` | Datos extra; en CSV import se guarda el row completo |
| `status` | `CharField(50, choices)` | new/assigned/in_progress/contacted/qualified/converted/rejected/follow_up/**skipped** |
| `priority` | `CharField(20, choices)` | low/medium/high/urgent |
| `campaign` | `FK(LeadCampaign, CASCADE)` | `related_name='leads'` |
| `assigned_bot` | `FK(BotInstance, SET_NULL, null=True)` | `related_name='assigned_leads'` |
| `assigned_at` | `DateTimeField(null=True)` | — |
| `created_at` | `DateTimeField(auto_now_add=True)` | ✅ |
| `updated_at` | `DateTimeField(auto_now=True)` | ✅ |
| `last_contact` | `DateTimeField(null=True)` | — |
| `converted_at` | `DateTimeField(null=True)` | — |
| `conversion_value` | `DecimalField(10, 2, default=0)` | — |

`ordering = ['-created_at']`

**Métodos:**
- `assign_to_bot(bot_instance)` — asigna bot, cambia status a `'assigned'`, llama `_create_inbox_item_for_bot()`.
- `_create_inbox_item_for_bot()` — crea `events.InboxItem` con `created_by=bot.generic_user.user`. ✅ **EVENTS-BUG-FK resuelto** — FK de `events_inboxitem` apunta ahora a `accounts_user`. Llama a `coordinator.assign_task_to_bot()` si InboxItem se creó exitosamente.
- `mark_converted(value)` — cambia status, sets `converted_at`, incrementa `campaign.converted_leads`.

✅ **BOT-BUG-05 resuelto** — `assign_to_bot()` envuelta en `transaction.atomic()`. `_create_inbox_item_for_bot()` usa savepoint propio.
✅ **BOT-BUG-01 resuelto** — `('skipped', 'Omitido')` añadido a choices (migración 0002).
⚠️ **Sin `created_by`** — violación de convención.
⚠️ **Sin PK UUID** — violación de convención.

---

### 2.10 `LeadDistributionRule`

Reglas condicionales de distribución para una campaña. Se evalúan en orden de `priority` (menor = primero).

| Campo | Tipo | Notas |
|-------|------|-------|
| `campaign` | `FK(LeadCampaign, CASCADE)` | `related_name='distribution_rules'` |
| `condition_field` | `CharField(100)` | Campo a evaluar (ej: `company`, `source`, `priority`) |
| `condition_operator` | `CharField(20, choices)` | equals/contains/starts_with/ends_with/greater_than/less_than |
| `condition_value` | `CharField(200)` | Valor de comparación |
| `action_type` | `CharField(20, choices)` | assign_to_bot/set_priority/add_tag/skip_distribution |
| `action_bot` | `FK(BotInstance, CASCADE, null=True)` | Para `assign_to_bot` |
| `action_priority` | `CharField(20, choices, null=True)` | Para `set_priority` |
| `action_tag` | `CharField(100, blank=True)` | Para `add_tag` |
| `is_active` | `BooleanField(default=True)` | — |
| `priority` | `IntegerField(default=1)` | Orden de evaluación |
| `created_at` | `DateTimeField(auto_now_add=True)` | — |

`ordering = ['priority', 'created_at']`

---

## 3. Vistas

### Módulo: Dashboard de Bots (BOT-4 — Sprint 8)

| Vista | URL pattern | Método | Descripción |
|-------|-------------|--------|-------------|
| `bot_dashboard` | `dashboard/` | GET | KPIs globales, grid de bots con métricas y logs, tabla de campañas |
| `api_bot_status` | `api/status/` | GET | JSON para HTMX poll — estado de todos los bots, carga del sistema, colas |

### Módulo: Campañas

| Vista | URL pattern | Método | Descripción |
|-------|-------------|--------|-------------|
| `lead_campaign_list` | `campaigns/` | GET | Lista campañas + estadísticas globales de leads |
| `lead_campaign_create` | `campaigns/create/` | GET/POST | Crear campaña con selección de bots |
| `lead_campaign_detail` | `campaigns/<int:pk>/` | GET | Detalle, stats por status, distribución por bot |
| `lead_upload` | `campaigns/<pk>/upload/` | GET/POST | Upload CSV o creación manual; auto-distribuye si `campaign.auto_distribute` |
| `lead_distribution_rules` | `campaigns/<pk>/rules/` | GET/POST | CRUD de reglas de distribución |
| `trigger_distribution` | `campaigns/<pk>/distribute/` | GET | Disparar distribución manual (⚠️ debería ser POST) |

### Módulo: Leads

| Vista | URL pattern | Método | Descripción |
|-------|-------------|--------|-------------|
| `lead_list` | `leads/` | GET | Lista paginada (25/pág) con filtros: campaign, status, bot, search |
| `lead_detail` | `leads/<int:pk>/` | GET | Detalle de un lead |
| `lead_export` | `leads/export/` | GET | Export CSV con filtros campaign/status |

### Módulo: API (AJAX)

| Vista | URL pattern | Método | Auth | Descripción |
|-------|-------------|--------|------|-------------|
| `api_campaign_stats` | `api/campaigns/<pk>/stats/` | GET | ✅ `@login_required` | Stats en tiempo real + distribución por bot |
| `api_trigger_distribution` | `api/campaigns/<pk>/distribute/` | POST | ✅ `@login_required` | Disparar distribución desde JS — pasa `force=True` |

✅ **BOT-BUG-03 resuelto** — `@login_required` añadido a ambas vistas API.
⚠️ `trigger_distribution` (vista HTML) acepta GET para ejecutar la distribución — debería ser POST.
⚠️ `lead_campaign_create` procesa `int(request.POST.get('max_leads_per_bot', 10))` sin manejo de `ValueError`.

---

## 4. URLs

Namespace: `bots` ✅ (declarado en `urls.py`)

```
# Dashboard de bots (BOT-4)
bots:bot_dashboard          GET    /bots/dashboard/
bots:api_bot_status         GET    /bots/api/status/

# Campañas
bots:campaign_list          GET    /bots/campaigns/
bots:campaign_create        GET/POST /bots/campaigns/create/
bots:campaign_detail        GET    /bots/campaigns/<int:pk>/
bots:lead_upload            GET/POST /bots/campaigns/<int:campaign_pk>/upload/
bots:distribution_rules     GET/POST /bots/campaigns/<int:campaign_pk>/rules/
bots:trigger_distribution   GET    /bots/campaigns/<int:campaign_pk>/distribute/

# Leads
bots:lead_list              GET    /bots/leads/
bots:lead_detail            GET    /bots/leads/<int:pk>/
bots:lead_export            GET    /bots/leads/export/

# API
bots:api_campaign_stats     GET    /bots/api/campaigns/<int:campaign_pk>/stats/
bots:api_trigger_distribution POST /bots/api/campaigns/<int:campaign_pk>/distribute/
```

⚠️ **URL conflict potencial:** `leads/<int:pk>/` y `leads/export/` — mantener el orden actual (export antes de detail).

---

## 5. Servicios

### 5.1 `LeadDistributor` (`lead_distributor.py`)

Factory: `get_lead_distributor(campaign)` → instancia `LeadDistributor(campaign)`.

**Flujo de `distribute_leads(force=False)`:**
1. Verifica campaña activa. Si `force=False`, verifica `auto_distribute=True`. Los disparos manuales pasan `force=True`.
2. Obtiene leads `status='new'` y `assigned_bot=None` (hasta `leads_per_batch`).
3. Aplica reglas personalizadas (`_apply_custom_rules`) — primera coincidencia, break.
4. Distribuye leads restantes según estrategia.
5. Actualiza `campaign.distributed_leads` y crea `BotLog`.
6. Retorna `{'success': True/False, 'distributed': N, 'strategy': ..., ...}`.

**Estrategias implementadas:**

| Estrategia | Método | Descripción |
|------------|--------|-------------|
| `round_robin` | `_distribute_round_robin` | Rota por índice, skip si bot no puede recibir |
| `equal_split` | `_distribute_equal_split` | División matemática, asigna de a bloques por bot |
| `priority_based` | `_distribute_priority_based` | Asigna al bot con menor carga actual |
| `skill_based` | `_distribute_skill_based` | Clasifica lead y busca bot con especialización compatible |
| `custom_rules` | ❌ No implementado | Devuelve error — las reglas se aplican siempre como pre-paso |

### 5.2 `BulkLeadImporter` (`lead_distributor.py`)

Factory: `get_bulk_importer(campaign)`.

- `import_from_csv(csv_file)` — decode UTF-8, usa `csv.DictReader`. Guarda el row completo en `lead.custom_data`.
- `import_from_json(json_data)` — idem desde lista de dicts.

⚠️ CSV solo soporta UTF-8 — no hay fallback a latin-1.

### 5.3 `GTDProcessor` (`gtd_processor.py`)

Factory: `get_gtd_processor(bot_instance)` → instancia `GTDProcessor(bot_instance)`.

**Punto de entrada único:** `process_inbox_item(inbox_item)` — procesa un `events.InboxItem` completo.

**Helpers de módulo:**
- `_get_default_task_status()` — devuelve el primer `TaskStatus` activo en DB. ✅ Fix BOT-BUG-GTD-1.
- `_get_default_project_status()` — devuelve el primer `ProjectStatus` activo en DB. ✅ Fix BOT-BUG-GTD-1.

**Fases GTD implementadas:**

| Fase GTD | Método | Descripción |
|----------|--------|-------------|
| Capture | — | Ya capturado en InboxItem |
| Clarify | `_classify_actionable(item)` | Scoring por keywords + due_date + estimated_time + context |
| Organize | `_process_actionable()` / `_process_non_actionable()` | Decide destino del item |
| Engage | `_do_it_now()` / `_delegate_or_schedule()` | Ejecuta o delega |
| — | `_log_gtd_phase()` | Log en `BotLog` por cada fase |

**Árbol de decisión GTD:**

```
process_inbox_item(item)
│
├─ _classify_actionable(item)  → score = keyword_score + due_date(+2) + estimated_time(+1) + context(+1)
│   ├─ score >= 1  → actionable
│   └─ score < 1   → no actionable
│
├─ [actionable]
│   ├─ estimated_time <= 2 min → _do_it_now() → _execute_quick_task()
│   │                                         └─ si falla → _delegate_or_schedule()
│   └─ estimated_time > 2 min → _delegate_or_schedule()
│         ├─ _analyze_complexity() → complexity_score >= 2
│         │   ├─ complejo → _convert_to_project()  → Project + N subtareas automáticas
│         │   └─ simple  → _convert_to_task()     → Task + Reminder opcional
│         └─ (usa transaction.atomic() en ambas conversiones)
│
└─ [no actionable]
    ├─ 'spam/basura/eliminar/borrar' → _delete_item()   → item.delete()
    ├─ 'algún día/tal vez/futuro/idea' → _incubate_item() → item.next_review_date = now+30d
    └─ default → _file_for_reference() → item.gtd_category='no_accionable'
```

**Campos de `events.InboxItem` que accede:**

| Campo | Uso |
|-------|-----|
| `title` | Clasificación actionable + complejidad + breakdowns de reunión/proyecto |
| `description` | Ídem |
| `due_date` | +2 puntos al score actionable; crea `Reminder` si existe |
| `estimated_time` | Regla de 2 minutos; +1 punto score; complejidad > 60 min |
| `context` | +1 punto al score actionable |
| `priority` | `item.priority == 'alta'` → `task.important = True` |
| `is_processed` | Se marca `True` al finalizar |
| `processed_at` | `timezone.now()` al finalizar |
| `processed_to_content_type` | ✅ `ContentType.objects.get_for_model(Task/Project)` |
| `processed_to_object_id` | ID del objeto creado |
| `next_review_date` | Fecha de incubación (+30 días) |
| `gtd_category` | Se fija a `'no_accionable'` al archivar |
| `action_type` | Se fija a `'archivar'` al archivar |

**Al crear `events.Task` o `events.Project`:**
- `host = self.bot.generic_user.user` — el bot es el propietario
- `assigned_to = self.bot.generic_user.user` — `_determine_best_assignee()` placeholder
- `task_status` / `project_status` — ✅ se asigna el primer estado activo via `_get_default_task_status()`
- `created_at` — **no se pasa** (era bug #4, campo `auto_now_add`)

**Subtareas automáticas por keyword:**

| Keyword en título | Subtareas creadas |
|------------------|-------------------|
| `'reunión'` | Preparar agenda, Enviar invitaciones, Preparar materiales, Realizar reunión, Seguimiento |
| `'proyecto'` | Definir alcance, Identificar recursos, Crear plan, Ejecutar, Evaluar resultados |
| (default) | Investigar, Planificar, Ejecutar, Verificar |

✅ **5 bugs corregidos en Sprint 8:**
1. `task_status_id cannot be null` — `_get_default_task_status()` y `_get_default_project_status()` añadidos
2. `KeyError: 'action'` — `result.get('action', 'error')` + `'action': 'error'` en todos los `except`
3. `Task.get_content_type()` — reemplazado por `ContentType.objects.get_for_model()`
4. `created_at=item.created_at` en `create()` — eliminado (`auto_now_add` no acepta valores)
5. `timezone.timedelta` en `_incubate_item` — `from datetime import timedelta` (convención del proyecto)

⚠️ **EVENTS-SIG-2**: Cuando `GTDProcessor` crea una `Task`, un signal de `events` intenta hacer reverse query sobre el `GenericForeignKey` `processed_to` con `InboxItem.objects.filter(processed_to=task)` → ERROR en logs. No bloquea la creación de la tarea. Fix Sprint 9: usar `ContentType.objects.get_for_model()` + filtro por `processed_to_content_type` y `processed_to_object_id`.

⚠️ **`_execute_quick_task()`** siempre retorna `True` (stub).
⚠️ **`_determine_best_assignee()`** siempre devuelve el usuario del bot (placeholder).

### 5.4 `utils.py` — `BotCoordinatorService` y `get_bot_coordinator()`

`utils.py` define tres clases y una función factory. El objeto devuelto por `get_bot_coordinator()` **no es un `BotCoordinator` (modelo)** sino una instancia de `BotCoordinatorService` — clase de servicio que envuelve al modelo y añade la lógica operativa. Se instancia como **singleton a nivel de módulo** al importar el módulo.

#### `BotCoordinatorService`

**Métodos públicos:**

| Método | Descripción |
|--------|-------------|
| `get_or_create_coordinator()` | Obtiene/crea el `BotCoordinator` singleton en DB |
| `assign_task_to_bot(task_data)` | Encola tarea + intenta asignación inmediata → `BotTaskAssignment` |
| `process_completed_task(assignment, result_data, error)` | Completa/falla la asignación, actualiza bot, crea `BotLog` |
| `check_system_health()` | Cuenta bots, detecta stale heartbeats, auto-scaling, retorna dict |
| `send_bot_message(sender, recipient, type, content, priority)` | Crea `BotCommunication` |
| `_scale_up_bots()` | Stub — solo loguea |
| `_scale_down_bots()` | Stub — solo loguea |

**`assign_task_to_bot(task_data)` — flujo:**
1. Calcula prioridad de cola (`urgent/high/medium/low`).
2. Agrega tarea a `BotTaskQueue` (cola en memoria, **no persistente**).
3. Busca bot disponible (`is_active=True`, `current_status in ['idle','working']`).
4. Si hay bot → `BotTaskAssignment.objects.create()` + `bot.update_status('working')`.
5. Si no hay bot → tarea queda solo en deque. **Al reiniciar `run_bots`, se pierde** (BOT-BUG-19).

#### `BotTaskQueue`

Cola en memoria por prioridad usando `collections.deque`. **No persistente.**

✅ **BOT-BUG-20 resuelto** — `get_next_task()` ya no llama `can_take_task('any')`. Verifica `bot.is_active` + `is_working_hours()`. La compatibilidad de especialización la valida `_can_assign_to_bot()`.

---

## 6. Management Commands

### 6.1 `setup_bots` — Inicialización del sistema

```bash
python manage.py setup_bots [--reset] [--bots-count N]
```

**Flujo:**
1. Opcional: `--reset` elimina todos los `BotInstance`, `GenericUser`, `BotCoordinator` y usuarios bot.
2. Crea/obtiene `BotCoordinator` singleton.
3. Para cada bot 1..N: crea `User` (bot_user_N), `GenericUser`, `BotInstance`.

**Especializaciones (cíclico):** gtd_processor → project_manager → task_executor → calendar_optimizer → communication_handler → ...

✅ **BOT-BUG-13 resuelto** — campos fantasma eliminados. Signal `create_credit_account` desconectado durante creación de usuarios bot. `connection.close()` antes de `GenericUser.create()`.
✅ **BOT-BUG-21 resuelto** — `BotInstance` se crea con `working_hours_start='00:00'` y `working_hours_end='23:59'`.

⚠️ Password hardcoded `'bot_password_123'` — debe moverse a `.env`.

### 6.2 `run_bots` — Orquestador principal

```bash
python manage.py run_bots [--bot-id ID] [--dry-run] [--once] [--max-items N] [--cycle-time S]
```

**Modos de operación:**

| Flag | Comportamiento |
|------|----------------|
| (ninguno) | Loop continuo, todos los bots activos, ciclo cada 60s |
| `--bot-id N` | Solo el bot con ese ID |
| `--once` | Un solo ciclo y salir |
| `--dry-run` | No guarda cambios |
| `--max-items N` | Máx. items por ciclo (default 10) |
| `--cycle-time S` | Segundos entre ciclos (default 60) |

**Ciclo de ejecución por bot:**
1. Verifica `bot.is_working_hours()` → si no, status `'idle'` y skip.
2. Obtiene `BotTaskAssignment` con `status__in=['assigned', 'in_progress']` ordenados por `(priority, assigned_at)`.
3. Para cada tarea: `start_task()` → dispatcher por `task_type`:
   - `'process_inbox'` → `GTDProcessor.process_inbox_item(InboxItem)` ✅
   - `'create_project'` → stub
   - `'update_task'` → stub
   - cualquier otro → error
4. Llama `coordinator.process_completed_task(task_assignment, result)`.

**Señales:** Maneja `SIGINT` y `SIGTERM` para parada graceful.

⚠️ Multi-bot es **secuencial** — un bot por vez. Para producción se necesitará Celery (SCA-1, Sprint 9).

---

## 7. Sistema GTD — Flujo Completo End-to-End

✅ **Verificado Sprint 8** — pipeline completo funcional con `run_bots --once`.

```
[LEAD PIPELINE]                          [BOT RUNTIME]
                                         run_bots (cada 60s)
Lead.assign_to_bot(bot)                       │
  │                                           │  _get_pending_tasks_for_bot()
  ├─ Lead.status = 'assigned'                 │  → BotTaskAssignment [assigned/in_progress]
  ├─ Lead.assigned_bot = bot                  │
  └─ _create_inbox_item_for_bot()             │  _process_task_for_bot()
       │                                      │    ├─ task_type == 'process_inbox'
       ├─ events.InboxItem.create(            │    │     → GTDProcessor.process_inbox_item()
       │    created_by=bot.generic_user.user, │    │           │
       │    context='lead_processing', ...    │    │      [clarify]  _classify_actionable()
       │  )  ✅ (EVENTS-BUG-FK resuelto)      │    │      [organize] convert_to_task / project
       │                                      │    │      [engage]   Reminder si due_date
       ├─ BotLog(category='lead_distribution')│    │
       │                                      │    └─ coordinator.process_completed_task()
       └─ coordinator.assign_task_to_bot({    │         → task_assignment.complete_task()
            type='process_inbox',             │              → bot.tasks_completed_total += 1
            object_id=inbox_item.id           │
          })  ✅                              │
              → BotTaskAssignment created ✅  │
```

---

## 8. Sistema de Distribución de Leads — Flujo Completo

```
Usuario
  │
  ├─ POST /campaigns/<pk>/upload/ (CSV o manual)
  │     │
  │     ├─ BulkLeadImporter.import_from_csv()
  │     │     └─ Lead.objects.create(..., status='new')
  │     │
  │     └─ if campaign.auto_distribute:
  │           └─ LeadDistributor.distribute_leads()
  │
  └─ GET /campaigns/<pk>/distribute/  (manual, force=True)
        └─ LeadDistributor.distribute_leads(force=True)
              │
              ├─ 1. Aplica LeadDistributionRule (ordenadas por priority)
              │     └─ rule.evaluate(lead) → rule.apply(lead)
              │
              └─ 2. Leads sin asignar → estrategia configurada
                    ├─ round_robin / equal_split / priority_based / skill_based
                    └─ lead.assign_to_bot(bot)
                          ├─ Lead.status = 'assigned'
                          ├─ InboxItem.create() ✅
                          └─ BotTaskAssignment creado ✅
```

---

## 9. Convenciones Críticas y Violaciones

### Violaciones de convención del proyecto

| Convención | Estándar | Estado en `bots` |
|------------|----------|-----------------|
| PK UUID | `UUIDField(primary_key=True)` | ❌ Todos los modelos usan AutoField int |
| `created_by` | `FK(settings.AUTH_USER_MODEL)` | ❌ Ausente en todos los modelos |
| Timestamps `created_at`/`updated_at` | `auto_now_add` / `auto_now` | ⚠️ Parcial — solo `BotInstance`, `LeadCampaign`, `Lead` los tienen completos |
| Namespace | `app_name = 'x'` | ✅ Declarado correctamente |
| JSON response | `{"success": true/false}` | ✅ En endpoints API y `LeadDistributor` |

### Gotchas críticos para devs

1. ✅ **`setup_bots` reparado** (BOT-BUG-13 + BOT-BUG-21) — campos fantasma eliminados; working_hours 00:00–23:59; signal `create_credit_account` desconectado; `connection.close()` antes de `GenericUser`.

2. ✅ **`assign_to_bot()` atómica y tolerante** (BOT-BUG-05) — `transaction.atomic()` + savepoint para InboxItem.

3. ✅ **Pipeline Lead→BotTaskAssignment cerrado y verificado end-to-end** — Lead → InboxItem → BotTaskAssignment → GTDProcessor → Task funcional con `run_bots --once`.

4. ✅ **EVENTS-BUG-FK resuelto** — migración `0004` aplicada. 26 FKs de `events_*` reapuntadas a `accounts_user`. Columnas INT→BIGINT. Los bots pueden crear `InboxItem` sin IntegrityError.

5. **EVENTS-SIG activo** — signal `create_credit_account` en `events` intenta crear `CreditAccount` para usuarios bot. Workaround: desconexión en `setup_bots`. Fix definitivo pendiente Sprint 9.

6. **EVENTS-SIG-2 activo** — signal en `events` hace reverse query sobre `GenericForeignKey processed_to` al crear tareas → ERROR en logs. No bloquea creación. Fix Sprint 9.

7. **`ResourceLock.acquire_lock()` usa `timezone.timedelta`** → `AttributeError` pendiente. No afecta el flujo principal (los bloqueos no están en uso activo).

8. **`tasks_completed_today` no se resetea** — crece indefinidamente.

9. **`resource_id` y `related_object_id` son `IntegerField`** — incompatibles con modelos UUID del proyecto.

---

## 10. Bugs Conocidos

| # | Estado | Descripción | Impacto |
|---|--------|-------------|---------|
| BOT-BUG-01 | ✅ S8 | `status='skipped'` no estaba en choices de `Lead` | Medio |
| BOT-BUG-02 | ✅ S8 | `'lead_distribution'` y `'gtd'` no estaban en choices de `BotLog` | Bajo |
| BOT-BUG-03 | ✅ S8 | APIs sin `@login_required` | **Alto — seguridad** |
| BOT-BUG-04 | ⬜ | `trigger_distribution` acepta GET para acción mutante | Medio |
| BOT-BUG-05 | ✅ S8 | `assign_to_bot()` no atómica | **Alto** |
| BOT-BUG-06 | ⬜ | `ResourceLock.acquire_lock()` no filtra bloqueos expirados | Medio |
| BOT-BUG-07 | ⬜ | `BotInstance.timezone` field nunca se usa en `is_working_hours()` | Bajo |
| BOT-BUG-08 | ⬜ | `_distribute_priority_based` hace 2x `BotInstance.objects.get()` por lead | Bajo |
| BOT-BUG-09 | ⬜ | `lead_campaign_create` crashea con `ValueError` si valor no numérico | Medio |
| BOT-BUG-10 | ⬜ | `complete_task()` y contadores de campaña sin `F()` — race condition | Medio |
| BOT-BUG-11 | ⬜ | `_calculate_uptime()` hardcoded a 95.0 | Bajo |
| BOT-BUG-12 | ⬜ | `get_system_load()` llama `self.save()` como efecto secundario | Bajo |
| BOT-BUG-13 | ✅ S8 | `setup_bots` roto — campos inexistentes en `BotInstance.get_or_create()` | **Crítico** |
| BOT-BUG-14 | ✅ S8 | `_log_error()` usaba `log_level=` en vez de `level=` | Medio |
| BOT-BUG-15 | ✅ S8 | `_incubate_item()` usaba `timezone.timedelta()` → `AttributeError` | Bajo |
| BOT-BUG-16 | ✅ S8 | `BotTaskAssignment` para leads no se creaba en `assign_to_bot()` | **Alto** |
| BOT-BUG-17 | ✅ | `run_bots` llamaba métodos de coordinator no definidos en models.py | — |
| BOT-BUG-18 | ✅ S8 | Doble incremento de `tasks_completed_today` | Medio |
| BOT-BUG-19 | ⬜ | `BotTaskQueue` en memoria — tareas sin bot se pierden al reiniciar | Alto |
| BOT-BUG-20 | ✅ S8 | `get_next_task()` usaba `can_take_task('any')` — bots especializados inoperables via cola | Alto |
| BOT-BUG-21 | ✅ S8 | `setup_bots` creaba bots con `working_hours_end='18:00'` UTC | Medio |
| BOT-BUG-22 | ⬜ | `_scale_up/down_bots()` son stubs — auto-scaling nunca funciona | Medio |
| BOT-BUG-GTD-1 | ✅ S8 | `task_status_id cannot be null` en `_convert_to_task()` | **Crítico** |
| BOT-BUG-GTD-2 | ✅ S8 | `KeyError: 'action'` en `process_inbox_item()` cuando sub-método falla | **Crítico** |
| BOT-BUG-GTD-3 | ✅ S8 | `Task.get_content_type()` no existe — `ContentType.objects.get_for_model()` | **Crítico** |
| BOT-BUG-GTD-4 | ✅ S8 | `created_at=item.created_at` en `Task.objects.create()` — `auto_now_add` ignorado | Bajo |
| EVENTS-BUG-FK | ✅ S8 | FKs de `events` apuntaban a `auth_user` — migración 0004 aplicada | **Crítico** |
| EVENTS-SIG | ⬜ | Signal `create_credit_account` falla para usuarios bot — guard pendiente | Alto |
| EVENTS-SIG-2 | ⬜ | Signal `events` hace reverse query sobre GenericFK → ERROR en logs por cada Task creada | Medio |

---

## 11. Deuda Técnica

### Crítico (bloquea uso básico)

- ~~`setup_bots` roto~~ ✅ **BOT-BUG-13 resuelto S8**
- ~~EVENTS-BUG-FK~~ ✅ **Resuelto S8 — migración 0004 aplicada**
- ~~Pipeline Lead→GTD roto~~ ✅ **Resuelto S8 — verificado end-to-end**
- **Persistir tareas encoladas sin bot** — `BotTaskQueue` en memoria (BOT-BUG-19). Fix: `status='queued'` en `BotTaskAssignment` o Redis sorted set.

### Alta prioridad (Sprint 9)

- **EVENTS-SIG** — guard en `create_credit_account` para usuarios bot
- **EVENTS-SIG-2** — fix reverse query en signal de events al crear Task
- ~~`@login_required` en APIs~~ ✅ **BOT-BUG-03 resuelto S8**
- ~~Atomicidad `assign_to_bot()`~~ ✅ **BOT-BUG-05 resuelto S8**

### Media prioridad (Sprint 9)

- **Agregar PK UUID** a todos los modelos
- **Agregar `created_by`** a `LeadCampaign` y `Lead`
- **`ResourceLock.acquire_lock()` timedelta** — `from datetime import timedelta`
- **Cambiar `trigger_distribution` a POST** (BOT-BUG-04)
- **Implementar estrategia `custom_rules`** en `LeadDistributor` (BOT-5)
- **Limpiar `ResourceLock` expirados** en `acquire_lock()` (BOT-BUG-06)
- **Usar `F()` en contadores** (BOT-BUG-10)
- **Password en `setup_bots`** a variable de entorno

### Baja prioridad (Sprint 9+)

- Implementar `_calculate_uptime()` real desde `BotLog`
- Usar el campo `timezone` en `is_working_hours()` con `zoneinfo`
- Soporte de codificaciones en CSV import (latin-1, cp1252)
- Agregar tests — `tests.py` tiene 3 líneas (stub)
- Registrar bots en `admin.py` — actualmente vacío
- Convertir `resource_id` / `related_object_id` / `task_id` a `CharField` para UUIDs
- Mejorar `_classify_lead_type()` y `_determine_best_assignee()` — placeholders
- Paralelizar `_run_multi_bot_cycle()` con threading o Celery (SCA-1 Sprint 9)
