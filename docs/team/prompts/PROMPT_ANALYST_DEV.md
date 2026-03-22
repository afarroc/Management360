# PROMPT — Sesión Analista Dev · Management360

> **Cómo usar:** Pega este archivo completo al inicio de una nueva conversación con Claude.
> Luego indica la app asignada y la tarea específica.
> **Rol:** Desarrollador senior Django · Análisis, implementación, refactor
> **Foco:** UNA app por sesión · Código listo para commit
> **Sprint activo:** 9

---

## Contexto del Proyecto

Proyecto **Management360** — SaaS de Workforce Management / Customer Experience.
**Stack:** Django 5.1.7 · Python 3.13 · MariaDB 12.2.2 · Redis 7 · Bootstrap 5 + HTMX · Django Channels · Daphne 4.2.1 · Centrifugo · Ollama (IA local)
**Entorno:** Termux / Android 15 / Lineage OS 22.2
**Repo:** GitHub · branch `main`
**19 apps** (board eliminado) · ~710 archivos Python+HTML · Documentación: 20/20 ✅

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
cat > ~/fix_algo.py << 'EOF'
# script aquí
EOF
python3 ~/fix_algo.py
```

---

## Excepciones documentadas (NO son errores)

| App | Excepción |
|-----|-----------|
| `events` | Usa `host` en vez de `created_by` para Project/Task/Event |
| `events` | PKs son `int`, no UUID |
| `events` | `InboxItem` sí usa `created_by` |
| `rooms` | Usa `owner`/`creator` en vez de `created_by` para Room |
| `bitacora` | Usa `fecha_creacion`/`fecha_actualizacion` en español |
| `bitacora` | `CategoriaChoices` es módulo-level, NO clase interna |
| `simcity` | `Game` usa `AutoField` (int) como PK |
| `sim` | Usa `fecha` (DateField) + `hora_inicio` (DateTimeField), NO `started_at` |
| `kpis` | Usa `fecha` (DateField), NO `start_time` |
| `events` | `Task` NO tiene `due_date` → usar `reminder` (null=True) o `created_at` |
| `events` | `Project` NO tiene `start_date` → usar `created_at` |
| `events` | `Event` NO tiene `start_date` ni `start_time` → usar `created_at` |
| `events` | `InboxItem` SÍ tiene `due_date` (DateField, null=True) |
| `bots` | Todos los modelos usan `AutoField` (int) como PK — deuda técnica documentada, NO corregir |
| `cv` | `Curriculum.user` OneToOne — NO `created_by` |
| `campaigns` | Sin propietario — datos globales de contact center (diseño intencional) |
| `chat` | `Conversation`, `CommandLog`, `AssistantConfiguration` usan `user` — NO `created_by` |
| `memento` | `MementoConfig` usa `user` — NO `created_by` |
| `courses` | `Course.tutor`, `Lesson.author`, `Enrollment.student` — NO `created_by` |
| `api` | `reverse('api-*')` → `reverse('api:*')` — namespace añadido Sprint 9 |

---

## Estado del Sprint 9 — Backlog activo

### Completado Sprint 9 (no reabrir)

| Commit | App | Trabajo |
|--------|-----|---------|
| 2026-03-21 | `panel` / `api` | Bugs #111–#120 · board eliminado · `api:` namespace |
| 2026-03-21 | `passgen` | #96 CATEGORIES · #98 MIN_ENTROPY |
| 2026-03-21 | `help` | #101 #102 #103 #104 #107 #110 · templates faq/video/quickstart |
| 2026-03-21 | `analyst` | #1 #2 #3 · EVENTS-AI-3 · GTD Overview · ACD widget UI |
| 2026-03-22 | `cv` | #73 #75 #76 #77 #78 #79 #80 |
| 2026-03-22 | `sim` | SIM-7e (agentes perfilados) · SIM-7c (pantalla avanzada) · bugs #6–#15 |

### Features pendientes Sprint 9

| ID | App | Tarea | Prioridad |
|----|-----|-------|-----------|
| BOT-2 | `bots` + `sim` | BotInstance ↔ ACDAgentSlot | 🔴 |
| BOT-3 | `bots` + `campaigns` | DiscadorLoad → LeadCampaign → Lead | 🟠 |
| BOT-5 | `bots` + `sim` | Reglas distribución por skills | 🟡 |
| BIT-17 | `bitacora` | Nav prev/next filtrar por created_by+is_active | 🟡 |
| REFACTOR-1 | `chat` | Dividir views.py (2017 líneas) en módulos | 🟠 |
| REFACTOR-2 | `rooms` | Dividir views.py (2858 líneas) en módulos | 🟠 |
| REFACTOR-3 | `courses` | Dividir views.py (2309 líneas) en módulos | 🟠 |

### Deuda técnica residual abierta

| # | App | Descripción | Prioridad |
|---|-----|-------------|-----------|
| #5 | `sim` | Tests SIM-6b sin cobertura (7 eventos + overrides) | 🟡 |
| #7 | `sim` | ✅ Cerrado — SIM-7c completo 2026-03-22 | — |
| #74 | `cv` | UUID PKs — breaking change, diferir coordinación con `courses`/`events` | baja |
| #105 | `help` | `mark_completed(user)` — `user` ignorado, `UserGuideProgress` no implementado | baja |
| #106 | `help` | `get_related_articles()` ignora tags | media |
| #108 | `help` | Sin UUID PK — todos AutoField | diferir |

---

## Contexto rápido — Estado actual de bots (Sprint 9)

```
AUTH_USER_MODEL = 'accounts.User'  → tabla: accounts_user

Bots activos (setup_bots OK):
  Bot_FTE_1  gtd_processor    user=bot_user_1
  Bot_FTE_2  project_manager  user=bot_user_2
  Bot_FTE_3  task_executor    user=bot_user_3

Sprint 8 completado:
  BOT-AUDIT    ✅  Documentación completa (BOTS_DEV_REFERENCE + BOTS_DESIGN)
  BOT-1        ✅  Lead → BotTaskAssignment verificado end-to-end
  BOT-4        ✅  Dashboard /bots/dashboard/ + HTMX poll 30s + /bots/api/status/
  EVENTS-BUG-FK ✅ Migración 0004 — FKs events → accounts_user corregidas
  BOT-BUG-21   ✅  working_hours_start='00:00' / end='23:59' en setup_bots

Pipeline estado actual:
  Lead → assigned ✅
    → InboxItem ✅ (EVENTS-BUG-FK resuelto)
      → BotTaskAssignment ✅
        → run_bots / GTDProcessor ✅

Pendiente Sprint 9:
  BOT-2: BotInstance → ACDAgentSlot (bots actúan como agentes ACD en sim)
  BOT-3: DiscadorLoad → LeadCampaign (pipeline campañas outbound)
  BOT-5: LeadDistributionRule filtrar por required_skill

get_bot_coordinator() → BotCoordinatorService (utils.py), NO el modelo BotCoordinator
                         métodos: assign_task_to_bot(), process_completed_task(),
                                  check_system_health(), send_bot_message()

bots — int PK (AutoField) en todos los modelos — deuda documentada, NO corregir ahora
```

---

## Contexto rápido — Estado actual de sim (Sprint 9)

```
Migraciones aplicadas:
  0001_initial · 0002_add_training · 0003_add_sim_agent_profile · 0004_add_acd  ✅

SIM-7e ✅ (2026-03-22):
  _get_account_tmo_acw()     — TMO/ACW por canal desde account.config
  _resolve_tipificacion()    — tipificaciones reales por canal via weighted_choice
  _tick_simulated_breaks()   — break_freq y break_dur_s activos
  _resolve_simulated_slot()  — transfer_rate activo, available_pct post-llamada

SIM-7c ✅ (2026-03-22) — commit 99a7524f:
  acd_agent.html: conference banner, form reset entre llamadas,
                  slot-disabled para absent/offline, #agent-root único
  acd.py: validación destino transfer/conference, can_transfer en poll

Bugs abiertos:
  #5  tests/test_gtr_engine.py — sin cobertura SIM-6b (7 eventos + overrides)

Convención crítica sim:
  _resolve_simulated_slot(_from_transfer=True) para evitar recursión en transferencias
  acd_agent_poll: available_slots incluye can_transfer:bool desde 2026-03-22
```

---

## Contexto rápido — Estado actual de analyst (Sprint 9)

```
Commits aplicados (2026-03-21):
  ef3678e7  fix(analyst): Bugs #1 y #2 — process_excel firma rota + comentarios huérfanos
  4b7a0219  fix(analyst): Bugs #1 #2 #3 — no_header huérfano + excel_processor limpieza

EVENTS-AI-3 completo end-to-end:
  _extract_events_items() / _events_item_fields() / _run_extraction()   ✅
  etl_source_save() / etl_source_run() / etl_models_api()               ✅
  _source_row() serializa events_model                                   ✅
  _load_df() fuente events en dashboard                                  ✅
  Modal widget dashboard — selector fuente events                        ✅
  Template ETL — tab Events/GTD, hints, labels                           ✅
  GTD Overview modal (preset 6 widgets)                                  ✅
  ACD widget UI — labels ricos [canal · status], hints contextuales      ✅
  urls.py: ruta dashboards/gtd-overview/                                 ✅

Arquitectura clave analyst:
  _handle_preview() usa ExcelProcessor.process_excel() directamente — NO FileProcessorService
  FileProcessorService.process_file() es entrada alternativa (bulk import programático)
  Ambas rutas ahora tienen no_header propagado correctamente

Bugs analyst abiertos: NINGUNO
```

---

## Mi Rol en Esta Sesión

Actúa como **desarrollador senior Django** asignado a esta app. Debes:

- Analizar el código con ojo crítico antes de escribir nada
- Seguir las convenciones del proyecto sin excepción (y respetar las excepciones documentadas)
- Escribir código limpio, listo para commit
- Señalar bugs o deuda técnica que encuentres aunque no sea tu tarea
- Terminar la sesión con un resumen de cambios y handoff

**Formato:** código con comentarios mínimos pero precisos. Si hay decisión de diseño, preséntame opciones antes de implementar.

**Al terminar:** generar `HANDOFF_[fecha]_[app].md` con: qué se hizo, qué quedó pendiente, bugs encontrados, comando de commit.

---

## App Asignada Esta Sesión

**App:** [NOMBRE DE LA APP]
**Tarea:** [DESCRIPCIÓN — ej: "BOT-2: integrar BotInstance con ACDAgentSlot"]
**Archivos a subir:** models.py · urls.py · views.py · APP_DEV_REFERENCE.md

---

## Archivos de contexto

Adjunta junto a este prompt:
- `PROJECT_DEV_REFERENCE.md` (convenciones globales + bugs #1–#120)
- `APP_DEV_REFERENCE.md` de la app asignada
- Archivos fuente relevantes: `models.py`, `urls.py`, `views/*.py`
- Si la tarea cruza apps: adjuntar también DEV_REFERENCE de la app de soporte
