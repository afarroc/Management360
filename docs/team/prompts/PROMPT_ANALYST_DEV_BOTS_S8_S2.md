# PROMPT — Sesión Dev · Management360

> **Cómo usar:** Pega este archivo completo al inicio de una nueva conversación con Claude.
> **Rol:** Desarrollador senior Django · Análisis, implementación, refactor
> **Foco:** Sprint 8 continuación — EVENTS-BUG-FK + BOT-4 + deuda técnica

---

## Contexto del Proyecto

Proyecto **Management360** — SaaS de Workforce Management / Customer Experience.
**Stack:** Django 5.1.7 · Python 3.13 · MariaDB 12.2.2 · Redis 7 · Bootstrap 5 + HTMX · Django Channels · Daphne 4.2.1
**Entorno:** Termux / Android 15 / Lineage OS 22.2
**Repo:** GitHub · branch `main`

---

## Convenciones que SIEMPRE debes seguir

### Modelos

```python
# PK estándar (todas las apps excepto events y simcity)
id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

# Propietario estándar (excepto events que usa host)
created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

# Timestamps
created_at = models.DateTimeField(auto_now_add=True)
updated_at = models.DateTimeField(auto_now=True)

# Importar User siempre así en models.py:
from django.conf import settings
# En views/forms: from django.contrib.auth import get_user_model
```

### Vistas

```python
@login_required
@require_POST
def api_action(request):
    try:
        data = json.loads(request.body)
        return JsonResponse({'success': True, 'data': result})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)
```

### Seguridad

```python
# Siempre filtrar por usuario
obj = get_object_or_404(MyModel, pk=pk, created_by=request.user)

# CSRF en JS — desde cookie, nunca hardcoded
function csrf() {
    return document.cookie.match(/csrftoken=([^;]+)/)?.[1] || '';
}

# @csrf_exempt PROHIBIDO en vistas con datos de usuario
```

### Fechas

```python
from datetime import timedelta   # CORRECTO
# timezone.timedelta             # INCORRECTO — AttributeError
```

### URLs

```python
# Declarar siempre en urls.py de cada app
app_name = 'nombre_app'
```

### Scripts en Termux

```bash
# /tmp no tiene permisos — usar siempre:
cat > ~/fix_algo.py << 'PYEOF'
# script aquí
PYEOF
python3 ~/fix_algo.py
```

---

## Excepciones documentadas (NO son errores)

| App | Excepción |
|-----|-----------|
| `events` | Usa `host` en vez de `created_by` para Project/Task/Event |
| `events` | PKs son `int`, no UUID |
| `events` | `InboxItem` sí usa `created_by` |
| `rooms` | Usa `owner` en vez de `created_by` para Room |
| `bitacora` | Usa `fecha_creacion`/`fecha_actualizacion` en español |
| `bitacora` | `CategoriaChoices` es módulo-level, NO clase interna |
| `simcity` | `Game` usa `AutoField` (int) como PK |
| `sim` | Usa `fecha` (DateField) + `hora_inicio` (DateTimeField), NO `started_at` |
| `kpis` | Usa `fecha` (DateField), NO `start_time` |
| `bots` | Todos los modelos usan `AutoField` (int) como PK — deuda técnica documentada, no corregir en esta sesión |

---

## Apps asignadas esta sesión

**Apps:** `events` (fix FK) + `bots` (BOT-4 + deuda)
**Sprint:** 8 — segunda sesión de dev

---

## Estado al inicio de esta sesión

La sesión anterior (Sprint 8 Fase 0 + BOT-1) completó todos los fixes críticos de `bots`:

```
setup_bots  OK  3 bots activos (Bot_FTE_1 gtd_processor, Bot_FTE_2 project_manager, Bot_FTE_3 task_executor)
run_bots    OK  dry-run limpio, sin errores
BOT-1       OK  Lead asignado → Bot verificado end-to-end
Migración   OK  0002_alter_botlog_category_alter_lead_status aplicada
```

**Bloqueador activo — EVENTS-BUG-FK:** las FKs de todas las tablas de `events` apuntan a
`auth_user` en vez de `accounts_user` (`AUTH_USER_MODEL = 'accounts.User'`). Los usuarios bot
viven en `accounts_user`, por lo que `InboxItem.objects.create(created_by=bot_user)` falla con
IntegrityError. Bloquea el pipeline Lead→GTD completo.

```
auth_user       → 2 filas (superusers legacy)
accounts_user   → 5 filas (todos los usuarios reales, incluidos bots)
events_inboxitem.created_by_id → FK → auth_user  <- INCORRECTO
```

---

## Orden de trabajo

### Tarea 1 — EVENTS-BUG-FK: reparar FKs en app `events` (crítico)

**Antes de empezar:** hacer backup de la DB.

```bash
mysqldump -u root -p projects > ~/backup_pre_events_fk_$(date +%Y%m%d_%H%M).sql
```

**Paso 1** — inventariar todas las FKs afectadas:

```bash
python manage.py shell -c "
from django.db import connection
with connection.cursor() as c:
    c.execute('''
        SELECT TABLE_NAME, CONSTRAINT_NAME, COLUMN_NAME
        FROM information_schema.KEY_COLUMN_USAGE
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME LIKE 'events_%'
          AND REFERENCED_TABLE_NAME = 'auth_user'
        ORDER BY TABLE_NAME
    ''')
    for row in c.fetchall():
        print(row)
"
```

**Paso 2** — generar migración `RunSQL` en app `events` que reapunte cada FK
de `auth_user` a `accounts_user`. Una operación `DROP FOREIGN KEY` + `ADD CONSTRAINT` por tabla.

**Paso 3** — verificar con InboxItem real:

```bash
python manage.py shell -c "
from events.models import InboxItem
from bots.models import BotInstance

bot = BotInstance.objects.first()
user = bot.generic_user.user
print('User:', user, '| tabla:', user.__class__._meta.db_table)

item = InboxItem.objects.create(title='Test FK fix', created_by=user)
print('InboxItem creado:', item.id)
item.delete()
print('OK — EVENTS-BUG-FK resuelto')
"
```

**Paso 4** — verificar pipeline completo Lead→BotTaskAssignment:

```bash
python manage.py shell -c "
from bots.models import LeadCampaign, Lead, BotTaskAssignment
from bots.lead_distributor import get_lead_distributor

campaign = LeadCampaign.objects.get(name='Campaña Test BOT-1')
Lead.objects.filter(name='Lead Test FK Fix').delete()
lead = Lead.objects.create(name='Lead Test FK Fix', email='fk@test.com', campaign=campaign)

result = get_lead_distributor(campaign).distribute_leads(force=True)
print('Resultado:', result)

lead.refresh_from_db()
print('Lead status:', lead.status, '| Bot:', lead.assigned_bot)

assignments = BotTaskAssignment.objects.filter(task_type='process_inbox').order_by('-assigned_at')[:3]
for a in assignments:
    print(f'  Assignment: {a.bot_instance.name} | task_id={a.task_id} | status={a.status}')
"
```

Esperado: `distributed: 1`, `status: assigned`, al menos un `BotTaskAssignment` con `task_type='process_inbox'`.

---

### Tarea 2 — BOT-4: Dashboard de rendimiento de bots

Con `BotLog` ya indexado y `BotInstance.get_performance_metrics()` disponible:

1. **Vista** `bots:bot_dashboard`:
   - Estado de cada bot (`current_status`, `tasks_completed_today`, `error_count`)
   - Carga del sistema vía `coordinator.get_system_load()`
   - Últimos 10 logs por bot
   - Distribución de leads activos por campaña

2. **URLs** en `bots/urls.py`:
   ```python
   path('dashboard/', views.bot_dashboard, name='bot_dashboard'),
   path('api/status/', views.api_bot_status, name='api_bot_status'),
   ```

3. **API** `api_bot_status` — JSON para HTMX poll:
   ```
   GET /bots/api/status/
   {"success": true, "bots": [...], "system_load": 0.0, "queue_status": {...}}
   ```

4. **Template** `bots/bot_dashboard.html` — Bootstrap 5 + HTMX refresh cada 30s.

Criterios de aceptación:
- Vista carga con los 3 bots activos sin errores
- HTMX poll funciona sin recargar la página
- `api_bot_status` responde `{"success": true}`

---

### Tarea 3 — BOT-BUG-21: horario por defecto en `setup_bots`

En `setup_bots.py`, añadir al `defaults` del `BotInstance.get_or_create()`:

```python
'working_hours_start': '00:00',
'working_hours_end': '23:59',
```

El default del modelo (`09:00`–`18:00` UTC) deja los bots fuera de horario
en producción local por la tarde.

---

## Contexto rápido

```
get_bot_coordinator() → BotCoordinatorService (utils.py), NO el modelo BotCoordinator
                        métodos: assign_task_to_bot(), process_completed_task(),
                                 check_system_health(), send_bot_message()

AUTH_USER_MODEL = 'accounts.User'  → tabla: accounts_user
auth_user                          → tabla legacy (2 superusers antiguos)

Bots activos:
  Bot_FTE_1  gtd_processor    user=bot_user_1
  Bot_FTE_2  project_manager  user=bot_user_2
  Bot_FTE_3  task_executor    user=bot_user_3

Pipeline (estado al inicio):
  Lead → assigned OK
    → InboxItem    BLOQUEADO por EVENTS-BUG-FK
      → BotTaskAssignment  BLOQUEADO
        → run_bots / GTDProcessor  BLOQUEADO

bots — int PK (AutoField) en todos los modelos — deuda documentada, no corregir ahora
events.InboxItem — usa created_by (no host)
events.Task / Project / Event — usan host (no created_by)
```

---

## Criterios de entrega

- EVENTS-BUG-FK: migración aplicada, pipeline Lead→BotTaskAssignment verificado
- BOT-4: vista + API + template funcionando
- BOT-BUG-21: horario corregido en `setup_bots`
- Código listo para commit
- `BOTS_HANDOFF.md` actualizado al cerrar

---

## Archivos a subir

```
# App events (para EVENTS-BUG-FK):
events/models.py

# App bots:
bots/models.py
bots/views.py
bots/utils.py
bots/urls.py
bots/lead_distributor.py
bots/management/commands/setup_bots.py
bots/management/commands/run_bots.py

# Documentación:
BOTS_DEV_REFERENCE.md
BOTS_DESIGN.md
BOTS_HANDOFF.md
PROJECT_DEV_REFERENCE.md
```
