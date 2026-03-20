# PROMPT — Sesión Dev · Management360

> **Cómo usar:** Pega este archivo completo al inicio de una nueva conversación con Claude.
> **Rol:** Desarrollador senior Django · Análisis, implementación, refactor
> **Foco:** Sprint 9 — EVENTS-SIG + EVENTS-SIG-2 + BOT-BUG-19 + ResourceLock timedelta

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

**Apps:** `events` (EVENTS-SIG + EVENTS-SIG-2) + `bots` (BOT-BUG-19 + ResourceLock timedelta)
**Sprint:** 9 — primera sesión

---

## Estado al inicio de esta sesión

Sprint 8 completado y verificado. Pipeline Lead→GTD funcional end-to-end:

```
setup_bots  OK  3 bots activos (Bot_FTE_1 gtd_processor, Bot_FTE_2 project_manager, Bot_FTE_3 task_executor)
run_bots    OK  --once limpio, pipeline completo Lead → InboxItem → BotTaskAssignment → Task
EVENTS-BUG-FK  RESUELTO  migración 0004 aplicada — 26 FKs → accounts_user, INT→BIGINT
BOT-4       OK  Dashboard + api_bot_status + template HTMX
BOT-BUG-21  OK  working_hours 00:00–23:59 en setup_bots y bots existentes
gtd_processor  OK  5 bugs corregidos (task_status, KeyError, ContentType, created_at, timedelta)
```

**Bugs activos — orden de ataque esta sesión:**

```
EVENTS-SIG    ACTIVO  Signal create_credit_account crea CreditAccount para bots
                      → falla FK en MariaDB, corrompe la conexión
                      → workaround actual: desconexión manual en setup_bots (frágil)

EVENTS-SIG-2  ACTIVO  Signal en events hace reverse query sobre GenericFK processed_to
                      → ERROR en logs en cada Task creada por bot
                      → InboxItem.objects.filter(processed_to=task) — no soportado por Django

BOT-BUG-19    ACTIVO  BotTaskQueue es deque en memoria
                      → tareas sin bot disponible se pierden al reiniciar run_bots
                      → las que tienen BotTaskAssignment en DB sobreviven

ResourceLock  ACTIVO  acquire_lock() usa timezone.timedelta → AttributeError latente
timedelta               → no afecta flujo principal (locks no están en uso activo)
```

---

## Orden de trabajo

### Tarea 1 — EVENTS-SIG: guard en `create_credit_account`

**Localizar el signal:**

```bash
grep -rn "create_credit_account" ~/projects/Management360/events/
```

Probable ubicación: `events/templatetags/signals.py` o `events/signals.py`.

**Fix:** añadir guard para usuarios bot antes de crear el `CreditAccount`:

```python
@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_credit_account(sender, instance, created, **kwargs):
    if not created:
        return
    # Guard: no crear CreditAccount para usuarios bot
    if hasattr(instance, 'generic_user_profile') and instance.generic_user_profile.is_bot_user:
        return
    CreditAccount.objects.get_or_create(user=instance)
```

**Verificar:**

```bash
python manage.py shell -c "
from django.contrib.auth import get_user_model
from bots.models import BotInstance
User = get_user_model()

# Verificar que los bots existentes no tienen CreditAccount creado erróneamente
from events.models import CreditAccount
for bot in BotInstance.objects.all():
    user = bot.generic_user.user
    has_credit = CreditAccount.objects.filter(user=user).exists()
    print(f'{bot.name}: has_credit={has_credit}')

# Simular creación de nuevo usuario bot (no debe crear CreditAccount)
print('Probando guard...')
user = User.objects.create_user('bot_test_sig', 'test@bot.local', 'pass')
user.generic_user_profile  # Si no existe, el guard no aplica — OK
has_credit = CreditAccount.objects.filter(user=user).exists()
print(f'bot_test_sig: CreditAccount creado = {has_credit}  (esperado: False)')
user.delete()
"
```

Con el guard en su lugar, también se puede simplificar `setup_bots.py`: ya no es necesario desconectar el signal manualmente (`_disconnect_credit_signal` / `_reconnect_credit_signal`). Evaluar si simplificar o mantener como defensa en profundidad.

---

### Tarea 2 — EVENTS-SIG-2: fix reverse query GenericFK en signal de events

**Localizar:**

```bash
grep -n "processed_to" ~/projects/Management360/events/templatetags/signals.py
# o en events/signals.py
```

El signal probablemente hace algo como:

```python
# INCORRECTO — Django no soporta reverse query directa sobre GenericForeignKey
InboxItem.objects.filter(processed_to=task)
```

**Fix:**

```python
from django.contrib.contenttypes.models import ContentType

# CORRECTO
ct = ContentType.objects.get_for_model(task.__class__)
InboxItem.objects.filter(
    processed_to_content_type=ct,
    processed_to_object_id=task.id
)
```

**Verificar** que el ERROR desaparece de los logs en el siguiente `run_bots --once`:

```bash
python manage.py run_bots --once 2>&1 | grep -E "(ERROR|INFO bots.gtd)"
```

Esperado: líneas `INFO bots.gtd_processor` sin ningún `ERROR events.templatetags.signals`.

---

### Tarea 3 — BOT-BUG-19: persistir `BotTaskQueue` en DB

El problema: si `assign_task_to_bot()` se llama y no hay bot disponible, la tarea queda en el `deque` en memoria y se pierde al reiniciar `run_bots`.

**Fix mínimo — 3 pasos:**

**Paso 1:** Añadir `'queued'` a `BotTaskAssignment.status` choices en `models.py`:

```python
status = models.CharField(max_length=20, choices=[
    ('queued', 'En Cola'),        # ← NUEVO
    ('assigned', 'Asignada'),
    ('in_progress', 'En Progreso'),
    ('completed', 'Completada'),
    ('failed', 'Fallida'),
    ('cancelled', 'Cancelada')
], default='assigned')
```

**Paso 2:** Generar y aplicar migración:

```bash
python manage.py makemigrations bots --name alter_bottaskassignment_status_add_queued
python manage.py migrate bots
```

**Paso 3:** En `utils.py`, método `assign_task_to_bot()`, cuando no hay bot disponible crear un `BotTaskAssignment` con `status='queued'` en vez de solo encolar en memoria:

```python
def assign_task_to_bot(self, task_data):
    priority = self._calculate_queue_priority(task_data)
    self.task_queue.add_task(task_data, priority)

    available_bot = self._find_available_bot(task_data)
    if available_bot:
        return self._create_task_assignment(task_data, available_bot)

    # BOT-BUG-19 FIX: persistir en DB para sobrevivir reinicios
    queued = BotTaskAssignment.objects.create(
        bot_instance=None,          # ← requiere null=True (ver nota abajo)
        task_type=task_data['type'],
        task_id=task_data['object_id'],
        priority=task_data.get('priority', 1),
        status='queued',
        assignment_reason=task_data.get('reason', ''),
    )
    logger.info(f"Tarea encolada en DB (sin bot disponible): {task_data['type']} id={queued.id}")
    return queued
```

**Nota:** `BotTaskAssignment.bot_instance` debe aceptar `null=True` para el estado `'queued'`. Añadir al campo en models.py y generar migración adicional si es necesario.

**Paso 4:** En `run_bots._get_pending_tasks_for_bot()`, incluir asignaciones `'queued'` sin bot asignado en el ciclo de cada bot:

```python
def _get_pending_tasks_for_bot(self, bot):
    # Tareas ya asignadas a este bot
    assigned = BotTaskAssignment.objects.filter(
        bot_instance=bot,
        status__in=['assigned', 'in_progress']
    )
    # Tareas en cola sin bot — asignarlas si este bot puede tomarlas
    queued = BotTaskAssignment.objects.filter(
        bot_instance__isnull=True,
        status='queued'
    ).order_by('priority', 'assigned_at')

    # Intentar asignar las queued a este bot
    for q in queued[:self.max_items]:
        if bot.can_take_task(q.task_type):
            q.bot_instance = bot
            q.status = 'assigned'
            q.save(update_fields=['bot_instance', 'status'])

    return BotTaskAssignment.objects.filter(
        bot_instance=bot,
        status__in=['assigned', 'in_progress']
    ).order_by('priority', 'assigned_at')[:self.max_items]
```

**Verificar:**

```bash
python manage.py shell -c "
from bots.models import BotTaskAssignment, BotInstance
from bots.utils import get_bot_coordinator

# Pausar todos los bots para forzar estado sin bot disponible
BotInstance.objects.all().update(current_status='paused')

# Encolar una tarea — debe persistir en DB con status='queued'
coordinator = get_bot_coordinator()
coordinator.assign_task_to_bot({
    'type': 'process_inbox',
    'object_id': 999,
    'priority': 3,
    'reason': 'Test BOT-BUG-19'
})

q = BotTaskAssignment.objects.filter(status='queued').last()
print('Queued en DB:', q.id if q else 'NO CREADO — bug no resuelto')

# Restaurar bots
BotInstance.objects.all().update(current_status='idle')
"
```

---

### Tarea 4 — ResourceLock `timedelta`

Fix de una línea en `bots/models.py`, método `ResourceLock.acquire_lock()`:

```python
# Cambiar:
expires_at = timezone.now() + timezone.timedelta(minutes=timeout_minutes)

# Por:
from datetime import timedelta
expires_at = timezone.now() + timedelta(minutes=timeout_minutes)
```

El import `from datetime import timedelta` ya existe en `run_bots.py` — verificar si ya está en `models.py`; si no, añadirlo al tope del archivo junto a los demás imports.

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
  Horario:   00:00–23:59 UTC

Pipeline (estado al inicio de Sprint 9):
  Lead → assigned ✅
    → InboxItem ✅  (EVENTS-BUG-FK resuelto)
      → BotTaskAssignment ✅
        → run_bots / GTDProcessor ✅
          → events.Task creada ✅
          → Signal create_credit_account ⚠️  EVENTS-SIG activo
          → Signal reverse GenericFK    ⚠️  EVENTS-SIG-2 activo

Migraciones bots aplicadas:
  0001_initial
  0002_alter_botlog_category_alter_lead_status

events migration aplicada:
  0004_fix_fk_auth_user_to_accounts_user

bots — int PK (AutoField) en todos los modelos — deuda documentada, no corregir ahora
events.InboxItem — usa created_by (no host)
events.Task / Project / Event — usan host (no created_by)
```

---

## Criterios de entrega

- EVENTS-SIG: guard en `create_credit_account`, signal no falla para usuarios bot
- EVENTS-SIG-2: ERROR desaparece de logs al crear Task desde bot
- BOT-BUG-19: tareas sin bot disponible persisten en DB con `status='queued'`
- ResourceLock timedelta: `acquire_lock()` sin `AttributeError`
- Código listo para commit
- `BOTS_HANDOFF.md` + `BOTS_DEV_REFERENCE.md` + `BOTS_DESIGN.md` actualizados al cerrar

---

## Archivos a subir

```
# App events (para EVENTS-SIG + EVENTS-SIG-2):
events/models.py
events/signals.py              ← o events/templatetags/signals.py — donde esté create_credit_account

# App bots:
bots/models.py
bots/views.py
bots/utils.py
bots/urls.py
bots/lead_distributor.py
bots/gtd_processor.py
bots/management/commands/setup_bots.py
bots/management/commands/run_bots.py

# Documentación:
BOTS_DEV_REFERENCE.md
BOTS_DESIGN.md
BOTS_HANDOFF.md
PROJECT_DEV_REFERENCE.md
EVENTS_DEV_REFERENCE.md
```
