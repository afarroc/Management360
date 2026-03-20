# PROMPT — Sesión Dev · Management360

> **Cómo usar:** Pega este archivo completo al inicio de una nueva conversación con Claude.
> **Rol:** Desarrollador senior Django · Análisis, implementación, refactor
> **Foco:** Sprint 5 — SIM-7e + SIM-7c (app `sim`)

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
| `sim` | `acd_trainner.html` — doble `n` es el nombre real del archivo en disco, no corregir |
| `kpis` | Usa `fecha` (DateField), NO `start_time` |

---

## App asignada esta sesión

**App:** `sim`
**Sprint:** 5 — primera sesión

---

## Estado al inicio de esta sesión

Sprint 3 (SIM-6a + SIM-6b) y Sprint 4 (SIM-7a/b/d) completados. Los archivos
entregados en la sesión anterior ya están commiteados:

```
sim/views/acd.py        — bugs #6/8/9/10 corregidos
sim/views/gtr.py        — DEFAULT_THRESHOLDS_OUTBOUND en contexto
sim/templates/sim/gtr.html — SIM-6b: csrf, DOM, CSS, modal dentro de #gtr-root
```

**Bugs pendientes en `sim` (pre-Sprint 5):**

| # | Archivo | Descripción |
|---|---------|-------------|
| 5 | `tests/test_gtr_engine.py` | Tests no cubren los 7 eventos SIM-6b ni overrides en generadores |
| 7 | `templates/sim/acd_agent.html` | Nivel `advanced` sin implementar — target de SIM-7c |

---

## Orden de trabajo

### Tarea 1 — SIM-7e: Agentes simulados perfilados en sesión ACD

Los agentes simulados (`agent_type='simulated'`) en `ACDAgentSlot` ya tienen FK
a `SimAgentProfile`, y `_resolve_simulated_slot()` en `acd.py` ya lee el perfil.
Lo que falta es que el **motor de tick ACD use los tiers reales** para calibrar
el comportamiento diferenciado por agente a lo largo de la sesión.

**Criterios de aceptación:**
- Agente tier `top` resuelve llamadas más rápido (aht_factor 0.85×), menor hold, mayor conv_rate
- Agente tier `bajo` tiene más rechazos, más hold, más cortes, menor conv_rate
- El grid del trainer refleja diferencias visibles de AHT entre tiers en sesiones largas
- Sin migración nueva — `SimAgentProfile` ya existe en 0003

**Verificar con:**
```bash
python manage.py shell -c "
from sim.models import ACDSession, ACDAgentSlot, SimAgentProfile
# Crear sesión test, agregar slots top vs bajo, correr 10 ticks, comparar AHT
"
```

---

### Tarea 2 — SIM-7c: Pantalla agente avanzado

Nivel `advanced` en `acd_agent.html` — actualmente sin implementar (bug #7).

**Funcionalidades a implementar:**
- Selector de agentes disponibles para transferencia (usa `available_slots` del poll)
- Botón conference (registra `doAction('conference', {})`)
- Notas de llamada inline (campo de texto antes de tipificar)
- Hold con música — visual diferenciado (timer visible en pantalla)

**El backend ya está completo** — `acd.py` maneja `transfer`, `conference`, `unhold`
con `to_slot_id`. Solo falta el frontend en `acd_agent.html`.

**Criterios de aceptación:**
- Nivel `advanced` muestra controles adicionales que `basic`/`intermediate` no tienen
- Transfer a otro agente disponible funciona end-to-end
- Conference registra en stats del slot

---

### Tarea 3 — Bug #5: Tests SIM-6b (si queda tiempo)

Agregar cobertura en `tests/test_gtr_engine.py` para los 7 eventos nuevos:
`set_vol_pct`, `set_aht`, `set_acw`, `set_hold_rate`, `agent_break`, `agent_return`,
`set_skill_weight`. También los overrides en `_generate_window_inbound/outbound`.

---

## Contexto rápido `sim`

```
GTRSession.kpis overrides (SIM-6b — ya en producción):
  _vol_override      float  (default 1.0) → % volumen base
  _aht_override      float  (default 1.0) → multiplicador AHT
  _acw_override      float  (default 1.0) → multiplicador ACW
  _hold_rate_override float (default None) → fracción llamadas en hold
  _agents_on_break   int    (default 0)
  _skill_overrides   dict   skill→weight (inbound only)

SimAgentProfile.tier: 'top' | 'alto' | 'medio' | 'bajo'
  aht_factor: 0.85 / 0.95 / 1.05 / 1.30
  acw_factor: 0.80 / 0.90 / 1.05 / 1.25
  conv_rate:  2.5% / 1.5% / 0.8% / 0.3%
  hold_rate:  2%   / 5%   / 10%  / 18%
  answer_rate:99%  / 97%  / 93%  / 85%

ACDAgentSlot.agent_type: 'real' | 'simulated'
ACDAgentSlot.level:      'basic' | 'intermediate' | 'advanced'
ACDAgentSlot.stats:      JSONField — atendidas, tmo_sum_s, tmo_count, ventas, hold_count...

acd.py:  _resolve_simulated_slot() ya lee SimAgentProfile
         _route_interaction() prefiere agentes reales OJT, luego skill match, luego menor carga
         acd_agent_poll() ya devuelve available_slots para nivel advanced
         acd_agent_action() ya maneja transfer/conference/unhold

Template:
  acd_trainner.html  — 665 líneas (doble n — nombre real en disco)
  acd_agent.html     — 392 líneas
```

---

## Archivos a subir

```bash
# Modelos y motor:
cat sim/models.py | termux-clipboard-set
cat sim/views/acd.py | termux-clipboard-set

# Templates:
cat sim/templates/sim/acd_agent.html | termux-clipboard-set
cat sim/templates/sim/acd_trainner.html | termux-clipboard-set   # solo si SIM-7e toca el grid

# Documentación:
# SIM_DESIGN.md + SIM_DEV_REFERENCE.md + SIM_CONTEXT.md
# PROJECT_DEV_REFERENCE.md
```
