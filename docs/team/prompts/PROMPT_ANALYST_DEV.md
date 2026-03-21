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
**20 apps** · ~710 archivos Python+HTML · Documentación: 20/20 ✅

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
| `board` | `Board.owner` y `Activity.user` — NO `created_by` (deuda documentada) |
| `cv` | `Curriculum.user` OneToOne — NO `created_by` |
| `campaigns` | Sin propietario — datos globales de contact center (diseño intencional) |
| `chat` | `Conversation`, `CommandLog`, `AssistantConfiguration` usan `user` — NO `created_by` |
| `memento` | `MementoConfig` usa `user` — NO `created_by` |
| `courses` | `Course.tutor`, `Lesson.author`, `Enrollment.student` — NO `created_by` |

---

## Estado del Sprint 9 — Backlog activo

### Fixes críticos heredados (ordenar por impacto antes de features)

| Bug | App | Fix | Esfuerzo |
|-----|-----|-----|---------|
| #114 | `panel` | Completar `get_connection_token` — nunca retorna, Centrifugo roto | 2 min |
| #107 | `help` | Crear 3 templates faltantes: `faq_list.html`, `video_tutorials.html`, `quick_start.html` | ~1.5h |
| #84 | `board` | IDOR en `BoardDetailView` — sin verificación de propietario | 5 min |
| #85 | `board` | `BOARD_CONFIG` no definido en settings — KeyError en runtime | 2 min |
| #96 | `passgen` | `password_help` siempre 500 — `self.CATEGORIES` no definido | 3 min |
| #98 | `passgen` | `MIN_ENTROPY=60` bloquea 5/7 patrones predefinidos | 1 min |
| #75 | `cv` | Imports de `events.management` a nivel de módulo — cadena de fallo | 15 min |
| #76 | `cv` | `reverse('project_detail')` sin namespace — NoReverseMatch probable | 5 min |
| #115 | `panel` | `DatabaseSelectorMiddleware` referencia DBs inexistentes | 2 min |
| #117 | `panel` | `RedisTestView` sin `@login_required` | 2 min |
| #102 | `help` | `article_feedback_stats` sin `@login_required` — acceso anónimo | 1 min |
| #104 | `help` | `submit_feedback` sin `update_fields` — sobreescribe todos los campos | 3 min |
| #101 | `help` | Import `courses.models` a nivel de módulo — cadena de fallo si courses falla | 5 min |

### Features Sprint 9

| ID | App | Tarea | Depende de | Prioridad |
|----|-----|-------|------------|-----------|
| BOT-2 | `bots` + `sim` | Integración BotInstance ↔ ACDAgentSlot | BOT-1 ✅ | 🔴 |
| BOT-3 | `bots` + `campaigns` | Pipeline DiscadorLoad → LeadCampaign → Lead | BOT-1 ✅ | 🟠 |
| BOT-5 | `bots` + `sim` | Reglas distribución por skills | BOT-1 ✅ | 🟡 |
| SIM-7e | `sim` | Agentes simulados perfilados en ACD | — | 🔴 (sesión separada) |
| SIM-6b | `sim` | GTR Interactivo con sliders | — | 🟠 (sesión separada) |
| BIT-17 | `bitacora` | Nav prev/next filtrar por created_by+is_active | — | 🟡 (sesión separada) |
| API-ARCH | `api` | Decisión arquitectura: eliminar `api/urls.py` redundante o completar migración | — | 🟠 |
| PNL-4 | `panel` | `print()` → `logger` en `storages.py` (~30 prints en producción) | — | 🟠 |
| REFACTOR-1 | `chat` | Dividir views.py (2017 líneas) en módulos | — | 🟠 |
| REFACTOR-2 | `rooms` | Dividir views.py (2858 líneas) en módulos | — | 🟠 |
| REFACTOR-3 | `courses` | Dividir views.py (2309 líneas) en módulos | — | 🟠 |
| HELP-1 | `help` | Template `faq_list.html` | — | 🔴 |
| HELP-2 | `help` | Template `video_tutorials.html` | — | 🔴 |
| HELP-3 | `help` | Template `quick_start.html` | — | 🔴 |

---

## Contexto rápido — Estado actual de bots (Sprint 8 completado)

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
