# Referencia de Desarrollo — App `sim`

> **Audiencia:** Desarrolladores del proyecto y asistentes de IA (Claude, Copilot, etc.)
> **Actualizado:** 2026-03-19 | **Archivos cubiertos:** 24 / 24
> **Proyecto:** Management360 · Django app

---

## Índice rápido

| Sección | Contenido |
|---------|-----------|
| 1. Visión general | Qué hace la app, stack |
| 2. Estructura de directorios | Árbol completo comentado |
| 3. Modelos | SimAccount · SimAgent · Interaction · SimRun · TrainingScenario · TrainingSession · SimAgentProfile |
| 4. Flujo histórico | HistoricalEngine — batch N días |
| 5. Flujo GTR | Clock acelerado, Redis, tick, persist |
| 6. Flujo Training Mode | Escenarios, sesiones, score |
| 7. GTR Interactivo (SIM-6b) | Controles continuos en tiempo real |
| 8. Generadores | base · inbound · outbound · digital |
| 9. GTR Engine — internos | kpis dict, overrides, alertas |
| 10. Integración analyst | ETL · Dashboard · Report Builder |
| 11. Endpoints completos | Todas las rutas |
| 12. Estado JS | Variables por panel |
| 13. Convenciones CSS / UI | Dark mode GTR, Training, colores |
| 14. Constantes | GTR_TTL, CLOCK_SPEEDS, thresholds |
| 15. Convenciones del proyecto | Patrones, nomenclatura |
| 16. Bugs conocidos | Issues activos y corregidos |
| 17. Archivos pendientes de documentar | |

---

## 1. Visión general

`sim` es una app Django de **simulación de interacciones WFM** que:

- Genera datasets de contact center realistas calibrados con datos reales (Banca Pichincha 2020, Conduent/ENTEL 2018)
- Soporta 3 canales: **inbound voz**, **outbound discador**, **digital chat/mail/app**
- Opera en modo **histórico** (batch N días) y **GTR** (clock acelerado con polling)
- Persiste interacciones GTR en BD al finalizar la sesión
- Proporciona **Training Mode** con escenarios grabados, evaluación de analistas y score automático
- Expone datos directamente a `analyst` vía ETL, Dashboard y Report Builder

### Stack técnico relevante

| Componente | Detalle |
|------------|---------|
| Framework | Django (`login_required` en todas las vistas) |
| Cache | Redis — estado GTR (`gtr:session:{sid}`, `gtr:interactions:{sid}`, TTL 4h) |
| Generación | Python `random` + `math` — sin dependencias externas |
| Persistencia | `Interaction.objects.bulk_create()` — batches de 2000 |
| Frontend GTR | Dark mode SPA con polling cada 3s |
| Frontend Training | Dark mode SPA multi-tab |
| Charts | Ninguno en sim — los gráficos son responsabilidad de `analyst/dashboard` |

---

## 2. Estructura de directorios

```
sim/
├── models.py                  # 7 modelos + choices
├── apps.py
├── admin.py
├── urls.py                    # 34 rutas bajo sim/
│
├── generators/
│   ├── __init__.py
│   ├── base.py                # Utilidades puras: weighted_choice, gaussian_duration, etc.
│   ├── inbound.py             # Generador voz — calibrado Banca Telefónica
│   ├── outbound.py            # Generador discador — calibrado Conduent/ENTEL
│   └── digital.py             # Generador chat/mail — calibrado Banca Digital
│
├── engine.py                  # HistoricalEngine — batch N días + get_account_kpis()
├── gtr_engine.py              # GTREngine — clock acelerado, persist, controles SIM-6b
│
├── views/
│   ├── __init__.py
│   ├── simulator.py           # Panel histórico — 8 endpoints
│   ├── gtr.py                 # Panel GTR — 9 endpoints + autostart
│   ├── dashboard.py           # Sim Dashboard — KPIs resumen
│   ├── account_editor.py      # Editor de cuenta — parámetros personalizables
│   ├── training.py            # Training Mode — 10 endpoints
│   ├── acd.py                 # ACD Simulator — 17 endpoints + motor enrutamiento
│   └── docs.py                # Sirve los 3 MDs como HTML renderizado
│
├── templates/sim/
│   ├── simulator.html         # SPA panel histórico
│   ├── gtr.html               # SPA GTR dark mode + panel control SIM-6b
│   ├── dashboard.html         # KPIs resumen cuenta
│   ├── account_editor.html    # Editor de cuenta (~1110 líneas)
│   ├── training.html          # Training Mode SPA dark mode
│   ├── acd_trainer.html       # Panel trainer ACD dark mode
│   ├── acd_agent.html         # Pantalla agente OJT (básico/intermedio)
│   └── docs.html              # Visor de documentación MD
│
├── tests/
│   ├── __init__.py
│   ├── test_generators.py     # 99 tests — base, inbound, outbound, digital
│   └── test_gtr_engine.py     # 58 tests — GTRSession, KPIs, alertas, cache
│
├── management/commands/
│   └── seed_agent_profiles.py # Crea 8 presets del sistema
│
├── migrations/
│   ├── 0001_initial
│   ├── 0002_add_training
│   └── 0003_add_sim_agent_profile
│
├── SIM_CONTEXT.md             # Auto-generado por m360_map.sh
├── SIM_DESIGN.md              # Diseño, fases, roadmap, sprints
└── SIM_DEV_REFERENCE.md       # Este archivo
```

### Migraciones aplicadas

| Migración | Contenido | Estado |
|-----------|-----------|--------|
| `0001_initial` | SimAccount · SimAgent · Interaction · SimRun | ✅ |
| `0002_add_training` | TrainingScenario · TrainingSession | ✅ |
| `0003_add_sim_agent_profile` | SimAgentProfile | ✅ |
| `0004_add_acd` | ACDSession · ACDAgentSlot · ACDInteraction · ACDAgentAction | ✅ |

---

## 3. Modelos

### `SimAccount`

Cuenta o campaña simulada. Contiene la configuración completa para generación de datos.

```python
class SimAccount(models.Model):
    id           = UUIDField PK
    name         = CharField(200)
    canal        = CharField  # inbound / outbound / digital / mixed
    account_type = CharField  # banking / telco / retail / generic
    preset       = CharField  # banking_inbound / telco_outbound / banking_digital
    config       = JSONField  # parámetros calibrados — ver SIM_DESIGN.md
    is_active    = BooleanField
    created_by   = FK User
```

**config JSONField por canal:**
```python
# inbound
{
    'weekday_vol': 1490, 'weekend_vol': 883, 'tmo_s': 313, 'acw_s': 18,
    'agents': 22, 'abandon_rate': 0.039, 'sl_s': 20,
    'schedule_start': 9, 'schedule_end': 18,
    'intraday': {9: 0.123, 10: 0.135, ...},
    'skills': {'PLD': {'weight': 0.657, 'tipificaciones': {'CUOTA MENSUAL': 0.473, ...}}}
}

# outbound
{
    'daily_marcaciones': 131400, 'contact_rate': 0.276, 'conv_rate': 0.0084,
    'sph_base': 0.128, 'agents': 322, 'turnos': ['MANANA','TARDE'],
    'tipif_contacto': {'Venta': 0.008, 'Agenda (Usuario)': 0.090, ...},
    'tipif_no_contacto': {'No contesta': 0.524, 'Buzon de voz': 0.328, ...},
    'producto': {'PORTABILIDAD': 0.92, 'LINEA NUEVA': 0.08}
}

# digital
{
    'daily_vol': 203, 'channels': {'bxi': 0.849, 'app': 0.151}, 'duration_s': 240,
    'tipificaciones_bxi': {'BXI_ACTIVACION USUARIO NUEVO': 0.634, ...},
    'tipificaciones_app': {'APP_ACTIVACION USUARIO NUEVO': 0.295, ...}
}
```

---

### `SimAgent`

Agente simulado con perfil de rendimiento individual.

```python
class SimAgent(models.Model):
    id              = UUIDField PK
    account         = FK SimAccount
    codigo          = CharField   # AGT-001, AGT-002, ...
    turno           = CharField   # MANANA / TARDE / NOCHE
    antiguedad      = CharField   # junior (<3m) / senior (>3m)
    sph_base        = FloatField  # velocidad base (distribución gaussiana σ=0.02)
    adherencia_base = FloatField  # 0.696–0.998 (rango real calibrado)
    tmo_factor      = FloatField  # multiplicador sobre TMO base (1.0 = promedio)
    is_active       = BooleanField
```

---

### `Interaction`

> **CRÍTICO:** campo de fecha = `fecha` (DateField). Hora = `hora_inicio`/`hora_fin` (DateTimeField).
> El campo `started_at` **NO EXISTE** — causará error si se usa en filtros o order_by.

```python
class Interaction(models.Model):
    id           = UUIDField PK
    account      = FK SimAccount
    agent        = FK SimAgent (null=True — nulo en abandonadas/no_contacto)

    # Canal
    canal        = CharField   # inbound / outbound / digital
    skill        = CharField   # PLD / CONVENIOS / PORTABILIDAD / CANALES DIGITALES
    sub_canal    = CharField   # bxi / app / chip / pack / ''

    # Tiempo — CAMPOS REALES
    fecha        = DateField          # ← filtros de fecha aquí
    hora_inicio  = DateTimeField      # ← hora de inicio de la interacción
    hora_fin     = DateTimeField
    duracion_s   = IntegerField
    acw_s        = IntegerField

    # Resultado
    tipificacion = CharField
    status       = CharField   # atendida / abandonada / venta / agenda / no_contacto / rechazo
    lead_id      = CharField   # ID sintético "CLI-00000001", "LID-00000001", "DIG-00000001"

    # Outbound
    intento_num  = IntegerField  # 1–5

    # Meta
    is_simulated = BooleanField  # siempre True — permite coexistir con datos ACD reales
    generated_at = DateTimeField auto_now_add
```

**Índices definidos:**
```python
indexes = [
    Index(fields=['account', 'fecha']),
    Index(fields=['account', 'canal', 'fecha']),
    Index(fields=['agent', 'fecha']),
]
```

---

### `SimRun`

Registro de cada ejecución del generador.

```python
class SimRun(models.Model):
    id           = UUIDField PK
    account      = FK SimAccount
    date_from    = DateField
    date_to      = DateField
    canales      = JSONField   # ["inbound"] | ["inbound","gtr"] ← GTR sessions
    status       = CharField   # running / done / error
    interactions_generated = IntegerField
    agents_generated       = IntegerField
    duration_s   = FloatField
    error_msg    = TextField blank
    triggered_by = FK User
    started_at   = DateTimeField auto_now_add
    finished_at  = DateTimeField null=True
```

> **Identificar sesiones GTR:** `SimRun.objects.filter(canales__contains='gtr')`

---

### `TrainingScenario`

Escenario de training reutilizable con eventos programados.

```python
class TrainingScenario(models.Model):
    id          = UUIDField PK
    name        = CharField(200)
    description = TextField blank
    canal       = CharField   # inbound / outbound
    difficulty  = CharField   # easy / medium / hard
    account     = FK SimAccount null=True  # null = genérico
    clock_speed = IntegerField  # 5 / 15 / 60
    thresholds  = JSONField
    events      = JSONField
    # [{at_sim_min, type, params, hint, auto}]
    # types disponibles (SIM-6b incluidos):
    #   volume_spike, agent_absent, sl_drop, reset_kpis
    #   set_vol_pct, set_aht, set_acw, set_hold_rate
    #   agent_break, agent_return, set_skill_weight
    expected_actions = JSONField
    # [{after_event_idx, within_min, description}]
    is_public   = BooleanField
    created_by  = FK User
```

---

### `TrainingSession`

Ejecución de un escenario por un trainee.

```python
class TrainingSession(models.Model):
    id               = UUIDField PK
    scenario         = FK TrainingScenario
    trainee          = FK User
    gtr_session_id   = CharField   # Redis key — vacío si sesión ya expiró
    sim_date         = DateField null=True
    status           = CharField   # active / completed / abandoned
    score            = IntegerField  # 0–100
    score_detail     = JSONField
    # {base:100, alert_penalty:-20, sl_bonus:+10, action_bonus:+15,
    #  events_responded_bonus:+5, total:110→capped 100}
    alerts_count     = IntegerField
    events_responded = IntegerField
    actions_log      = JSONField
    # [{sim_time:"10:45", real_ts:"ISO", action:"texto", event_ref:0|null}]
    final_kpis       = JSONField
    trainer_notes    = TextField blank
    started_at       = DateTimeField auto_now_add
    finished_at      = DateTimeField null=True
```

---

### `SimAgentProfile`

Perfil conductual reutilizable para agentes simulados (SIM-6a).

```python
class SimAgentProfile(models.Model):
    id          = UUIDField PK
    name        = CharField(200)
    description = TextField blank
    tier        = CharField   # top / alto / medio / bajo
    canal       = CharField   # inbound / outbound / digital / mixed

    # Velocidad
    aht_factor    = FloatField   # multiplicador sobre AHT base (0.85–1.30)
    acw_factor    = FloatField
    available_pct = FloatField   # % tiempo en Available (0.70–0.92)

    # Comportamiento en llamada
    answer_rate    = FloatField  # % que atiende vs rechaza (0.85–0.99)
    hold_rate      = FloatField  # % llamadas puestas en hold
    hold_dur_s     = IntegerField
    transfer_rate  = FloatField
    corte_rate     = FloatField  # % que corta antes de finalizar ACW

    # Resultados outbound
    conv_rate    = FloatField  # ventas / contactos
    agenda_rate  = FloatField

    # Ausencias
    break_freq   = FloatField   # breaks no programados / hora
    break_dur_s  = IntegerField
    shrinkage    = FloatField

    # Multi-skill
    skills         = JSONField  # ["PORTABILIDAD", "LINEA NUEVA"]
    skill_priority = JSONField  # {"PORTABILIDAD": 1}

    is_preset  = BooleanField   # True = preset del sistema (no editable)
    created_by = FK User
```

**Crear presets:**
```bash
python manage.py seed_agent_profiles
# Crea 8 presets (4 inbound + 4 outbound) — idempotente
```

---

### `ACDSession`

Sesión ACD multi-agente. Coordina N `ACDAgentSlot` sobre un motor GTR subyacente.

```python
class ACDSession(models.Model):
    id             = UUIDField PK
    name           = CharField(200)
    account        = FK SimAccount
    dialing_mode   = CharField  # predictive / progressive / manual
    canal          = CharField  # inbound / outbound
    clock_speed    = IntegerField
    sim_date       = DateField null
    status         = CharField  # config / active / paused / finished
    gtr_session_id = CharField  # Redis key del GTR subyacente
    thresholds     = JSONField
    config         = JSONField  # {agents_target, max_queue_time, routing}
    created_by     = FK User
    started_at     = DateTimeField auto
    finished_at    = DateTimeField null
```

---

### `ACDAgentSlot`

Slot de agente dentro de una `ACDSession`. Puede ser OJT real o simulado.

```python
class ACDAgentSlot(models.Model):
    session      = FK ACDSession
    slot_number  = IntegerField
    agent_type   = CharField  # real / simulated
    user         = FK User null           # OJT real
    profile      = FK SimAgentProfile null # agente simulado
    display_name = CharField blank
    skill        = CharField blank
    status       = CharField  # offline/available/ringing/on_call/acw/break/absent
    level        = CharField  # basic/intermediate/advanced  (solo OJT real)
    stats        = JSONField  # {atendidas, ventas, tmo_sum_s, tmo_count, hold_count, transfer_count}
```

**property `aht_s`:** `stats['tmo_sum_s'] / stats['tmo_count']`

---

### `ACDInteraction`

Interacción asignada a un slot. Ciclo: `queued → ringing → on_call → acw → completed`.

```python
class ACDInteraction(models.Model):
    session      = FK ACDSession
    slot         = FK ACDAgentSlot null
    canal        = CharField
    skill        = CharField
    lead_id      = CharField
    status       = CharField  # queued/ringing/on_call/acw/completed/abandoned/rejected
    queued_at    = DateTimeField auto
    assigned_at  = DateTimeField null
    answered_at  = DateTimeField null
    ended_at     = DateTimeField null
    duration_s   = IntegerField
    acw_s        = IntegerField
    hold_s       = IntegerField
    tipificacion     = CharField
    sub_tipificacion = CharField
    notes            = TextField
    is_simulated = BooleanField

    # Índices: (session, status) · (slot, queued_at)
```

**property `wait_s`:** `(answered_at - queued_at).total_seconds()`

---

### `ACDAgentAction`

Acción registrada por agente OJT durante una interacción (para evaluación del trainer).

```python
class ACDAgentAction(models.Model):
    interaction = FK ACDInteraction
    slot        = FK ACDAgentSlot
    action_type = CharField  # answer/reject/hold/unhold/transfer/tipify/end_acw/break/return/note
    params      = JSONField  # {tipificacion, to_slot_id, reason, text, ...}
    sim_time    = CharField(5)  # "10:45"
    created_at  = DateTimeField auto
```


---

## 4. Flujo histórico

```
POST /sim/accounts/<id>/generate/
  → HistoricalEngine(account, user)
  → engine.generate(date_from, date_to, canales)

  HistoricalEngine.generate():
    1. Recuperar/crear SimAgent pool para la cuenta
    2. Por cada día en el rango:
       → inbound_gen.generate_day(dt, agent_pool, cfg)  si 'inbound' in canales
       → outbound_gen.generate_day(...)                  si 'outbound' in canales
       → digital_gen.generate_day(...)                   si 'digital' in canales
       → convertir dicts → Interaction objects
       → buffer.append(Interaction(...))
    3. Interaction.objects.bulk_create(buffer[:2000]) — por batches
    4. SimRun.status = 'done'
```

---

## 5. Flujo GTR

```
POST /sim/gtr/start/
  → engine.create_session(account, user, clock_speed, sim_date)
  → GTRSession guardado en Redis gtr:session:{sid}
  → retorna {session_id, state}

GET /sim/gtr/<sid>/tick/  ← polling cada 3s
  → engine.tick(sid)
  → _generate_window(session, from_h, from_m, to_h, to_m)
     → dispatcher: inbound → _generate_window_inbound()
                   outbound → _generate_window_outbound()
  → _update_kpis(session, interactions)
  → _check_alerts(session)  ← canal-aware
  → save_session() + add_interactions()  → Redis
  → si session.status == 'finished':
       persist_session(sid)  ← auto-persist 18:00

persist_session(sid):
  1. load_session + get_interactions de Redis
  2. Por cada row: parsear hora_str + sim_date → hora_inicio DateTimeField
  3. hora_fin = hora_inicio + timedelta(duracion_s + acw_s)
  4. bulk_create Interaction (batches 2000)
  5. SimRun(canales=[canal,'gtr'], status='done')
  6. delete_session() en finally → limpiar Redis

POST /sim/gtr/<sid>/stop/
  → persist_session(sid)   ← mismo flujo, manual
  → JsonResponse({'success': True})
```

**Autostart desde Training Mode:**
```
GET /sim/gtr/?autostart=<gtr_session_id>
  → IIFE en gtr.html lee URLSearchParams
  → fetch(URLS.tick(autoSid))
  → updateUI(d) + startPolling() + enableControls(true)
```

---

## 6. Flujo Training Mode

```
POST /sim/training/scenarios/<id>/start/
  → session_start view
  → engine.create_session(account, user, clock_speed, sim_date)
  → TrainingSession.objects.create(gtr_session_id=gtr.session_id)
  → window.open('/sim/gtr/?autostart=<sid>', '_blank')

Mientras sesión activa:
  POST /sim/training/sessions/<id>/action/
    → registra acción en actions_log
    → si event_ref != null: events_responded += 1

POST /sim/training/sessions/<id>/complete/
  → load_session(gtr_sid) → kpis finales
  → engine.delete_session(gtr_sid)
  → _calculate_score(ts, gtr_state)
    → base 100
    → -8 por cada alerta (max -40)
    → +10 si KPIs sobre umbral
    → +5 por acción registrada (max +15)
    → +5 por evento respondido
  → ts.score = score_detail['total']
  → ts.status = 'completed'
```

---

## 7. GTR Interactivo — SIM-6b

### Controles continuos — `inject_event()`

Todos los controles se persisten en `session.kpis` como claves `_*`:

```python
# Flujo de llamadas
'set_vol_pct'      → session.kpis['_vol_override']         = pct / 100
'set_aht'          → session.kpis['_aht_override']         = factor
'set_acw'          → session.kpis['_acw_override']         = factor
'set_hold_rate'    → session.kpis['_hold_rate_override']   = rate

# Agentes
'agent_break'      → session.kpis['_agents_on_break']     += n
'agent_return'     → session.kpis['_agents_on_break']     -= n (min 0)

# Skills (inbound)
'set_skill_weight' → session.kpis['_skill_overrides'][skill] = weight
```

### Cómo los leen los generadores

```python
# _generate_window_inbound()
vol_override = session.kpis.get('_vol_override', 1.0)
expected_vol = vol_per_min * mins_elapsed * spike * vol_override

tmo_mean = cfg['tmo_s'] * session.kpis.get('_aht_override', 1.0)
acw_mean = cfg['acw_s'] * session.kpis.get('_acw_override', 1.0)

# hold en loop:
effective_hold = session.kpis.get('_hold_rate_override', 0.0)
if effective_hold > 0 and random.random() < effective_hold:
    dur += gaussian_duration(30, 0.40, 10, 180)

# skill weights con override:
skill_overrides = session.kpis.get('_skill_overrides', {})
skill_weights = {k: skill_overrides.get(k, v['weight']) for k,v in skills_cfg.items()}

# _generate_window_outbound()
vol_override = session.kpis.get('_vol_override', 1.0)
absent = session.kpis.get('_absent_agents',0) + session.kpis.get('_agents_on_break',0)
contact_rate *= max(0.5, 1 - absent / 100)
```

### `_state_response()` — campo `controls`

```python
'controls': {
    'vol_pct':         round(session.kpis.get('_vol_override', 1.0) * 100),
    'aht_factor':      round(session.kpis.get('_aht_override', 1.0), 2),
    'acw_factor':      round(session.kpis.get('_acw_override', 1.0), 2),
    'hold_rate':       round(session.kpis.get('_hold_rate_override', 0.0), 2),
    'agents_on_break': session.kpis.get('_agents_on_break', 0),
    'skill_overrides': session.kpis.get('_skill_overrides', {}),
}
```

Usado por `syncControls(d)` en JS para sincronizar sliders al reconectar o autostart.

---

## 8. Generadores

### `generators/base.py` — Utilidades puras (sin Django)

```python
weighted_choice(weights: dict) -> str
# Elige clave por peso relativo. {'A':0.6,'B':0.3,'C':0.1}

gaussian_duration(mean_s, sigma_factor=0.15, min_s=30, max_s=1800) -> int
# Duración gaussiana con clamp. sigma = mean × factor

intraday_slot(intraday: dict, date: datetime) -> datetime
# Hora aleatoria dentro del día según pesos intradía. intraday={9:0.123,...}

daily_volume(base_vol, weekday, weekend_factor=0.59, variance=0.08) -> int
# Volumen con varianza gaussiana y factor weekend

synthetic_lead_id(canal, index) -> str
# "CLI-00000001" | "LID-00000001" | "DIG-00000001"

agent_tmo_factor(antiguedad) -> float   # senior=1.0, junior=1.15
agent_sph_factor(antiguedad) -> float   # senior=1.0, junior=0.71

is_working_day(date, include_saturday=False) -> bool

generate_agent_pool(n_agents, turnos, sph_base, adherencia_base, senior_ratio=0.82) -> list[dict]
# Genera N perfiles con varianza gaussiana. Devuelve dicts, NO instancias Django.
```

### `generators/inbound.py`

```python
DEFAULT_CONFIG = { 'weekday_vol': 1490, 'tmo_s': 313, 'acw_s': 18, ... }

_get_config(account_config: dict) -> dict
# Merge account_config over DEFAULT_CONFIG

generate_day(date, agent_pool, account_config, lead_offset=0) -> list[dict]
# Retorna lista de dicts listos para Interaction.objects.bulk_create()
# Cada dict incluye: canal, skill, sub_canal, fecha, hora_inicio, hora_fin,
#                    duracion_s, acw_s, tipificacion, status, lead_id,
#                    agent_codigo, intento_num, is_simulated
```

### `generators/outbound.py`

```python
generate_day(date, agent_pool, account_config, lead_offset=0) -> list[dict]
# Domingo → retorna [] siempre
# Sábado  → factor 0.70
# ~131,400 marcaciones/día en preset
```

### `generators/digital.py`

```python
_match_tmo(tipif: str, tmo_map: dict) -> dict
# Fuzzy match case-insensitive sobre keys del tmo_map

generate_day(date, agent_pool, account_config, lead_offset=0) -> list[dict]
# status siempre 'atendida' — canal digital no tiene abandono
# sub_canal: 'bxi' (84.9%) | 'app' (15.1%)
```

---

## 9. GTR Engine — estado interno

### `GTRSession.kpis` dict completo

```python
# Contadores de negocio (visibles en API)
kpis = {
    'entrantes':   int,
    'atendidas':   int,
    'abandonadas': int,
    'ventas':      int,
    'agenda':      int,
    'no_contacto': int,
    'tmo_sum_s':   int,
    'tmo_count':   int,

    # Eventos discretos (temporales)
    '_spike_factor':    float,   # volumen × factor (default 1.0)
    '_spike_ticks':     int,     # ticks restantes del spike (decae)
    '_high_aht_ticks':  int,     # ticks con AHT elevado × 1.8 (sl_drop)
    '_absent_agents':   int,     # agentes permanentemente ausentes

    # Controles continuos SIM-6b (persistentes hasta cambio)
    '_vol_override':         float,   # multiplica expected_vol (default 1.0 = 100%)
    '_aht_override':         float,   # multiplica tmo_mean (default 1.0)
    '_acw_override':         float,   # multiplica acw_mean (default 1.0)
    '_hold_rate_override':   float,   # tasa de hold adicional (default 0.0)
    '_agents_on_break':      int,     # agentes en break (reduce contact_rate outbound)
    '_skill_overrides':      dict,    # {'PLD': 0.3, 'CONVENIOS': 0.8}
}
```

### KPI properties (`GTRSession`)

```python
@property def na_pct(self) -> float      # atendidas / entrantes × 100
@property def sl_pct(self) -> float      # estimado: na_pct × 0.873 (calibrado)
@property def abandon_pct(self) -> float  # abandonadas / entrantes × 100
@property def aht_s(self) -> int          # tmo_sum_s / tmo_count
# Outbound:
@property def contact_pct(self) -> float  # (atendidas+ventas+agenda) / entrantes × 100
@property def conv_pct(self) -> float     # ventas / contactos × 100
@property def no_contact_pct(self) -> float  # no_contacto / entrantes × 100
```

### `_check_alerts()` — thresholds por canal

```python
# Inbound
if session.sl_pct      < thr['sl_min']:      → alerta tipo 'sl'      level 'danger'
if session.abandon_pct > thr['abandon_max']:  → alerta tipo 'abandon' level 'warning'
if session.na_pct      < thr['na_min']:       → alerta tipo 'na'      level 'warning'

# Outbound
if session.contact_pct    < thr['contact_min']:    → 'contact'    'danger'
if session.conv_pct       < thr['conv_min']:        → 'conv'       'warning'
if session.no_contact_pct > thr['no_contact_max']:  → 'no_contact' 'warning'

# Guard: session.kpis['entrantes'] < 20 → retorna []
```

---

## 10. Integración analyst

### ETL — `_extract_sim_account()` en `analyst/views/etl_manager.py`

```python
# Prioridad 1 en _run_extraction()
if getattr(source, 'sim_account_id', None):
    return _extract_sim_account(source, runtime_params, user)

# Filtros disponibles
qs = Interaction.objects.filter(account=account)
if date_from: qs = qs.filter(fecha__gte=date_from)   # ← fecha, no started_at
if date_to:   qs = qs.filter(fecha__lte=date_to)
if run_id:    qs = qs.filter(run_id=run_id)
qs = qs.order_by('fecha', 'hora_inicio')
```

### Dashboard — `_load_df()` en `analyst/views/dashboard.py`

```python
if src_type == 'sim':
    account = SimAccount.objects.get(id=src_id, created_by=user)
    qs = Interaction.objects.filter(account=account).order_by('fecha', 'hora_inicio')
    return pd.DataFrame(list(qs.values()))
```

### Report Builder — funciones WFM registradas

```python
# analyst/report_functions.py
@register(key='sim_agent_performance', ...)   # Performance por Agente
@register(key='sim_inbound_daily', ...)        # KPIs Inbound Diarios
@register(key='sim_contact_funnel', ...)       # Embudo Contactabilidad Outbound
```

---

## 11. Endpoints completos

**Simulador histórico:**
```
GET  sim/                              → simulator_list
GET  sim/api/                          → simulator_api
POST sim/accounts/create/              → account_create
POST sim/accounts/<id>/delete/         → account_delete
POST sim/accounts/<id>/generate/       → account_generate
POST sim/accounts/<id>/clear/          → account_clear
GET  sim/accounts/<id>/runs/           → account_runs
GET  sim/accounts/<id>/kpis/           → account_kpis
GET  sim/accounts/<id>/export/         → export_interactions
GET  sim/accounts/<id>/edit/           → account_edit
POST sim/accounts/<id>/config/         → account_config_save
```

**Dashboard sim:**
```
GET  sim/dashboard/                    → sim_dashboard
GET  sim/dashboard/api/                → dashboard_api
```

**GTR:**
```
GET  sim/gtr/                          → gtr_panel
POST sim/gtr/start/                    → gtr_start
GET  sim/gtr/<sid>/tick/               → gtr_tick  (polling cada 3s)
GET  sim/gtr/<sid>/state/              → gtr_state
POST sim/gtr/<sid>/pause/              → gtr_pause
POST sim/gtr/<sid>/resume/             → gtr_resume
POST sim/gtr/<sid>/event/              → gtr_event  (inject_event)
POST sim/gtr/<sid>/stop/               → gtr_stop + persist_session
GET  sim/gtr/<sid>/interactions/       → gtr_interactions ?since=N
```

**Training Mode:**
```
GET  sim/training/                                     → training_panel
GET  sim/training/scenarios/api/                       → scenario_list_api
POST sim/training/scenarios/create/                    → scenario_create
POST sim/training/scenarios/<id>/update/               → scenario_update
POST sim/training/scenarios/<id>/delete/               → scenario_delete
POST sim/training/scenarios/<id>/start/                → session_start
GET  sim/training/sessions/api/                        → session_list_api
POST sim/training/sessions/<id>/complete/              → session_complete
POST sim/training/sessions/<id>/action/                → session_log_action
POST sim/training/sessions/<id>/notes/                 → session_trainer_notes
```

**ACD Simulator — Trainer (13 endpoints):**
```
GET  sim/acd/                                              → acd_panel
GET  sim/acd/sessions/api/                                 → acd_sessions_api
POST sim/acd/sessions/create/                              → acd_session_create
GET  sim/acd/sessions/<id>/state/                          → acd_session_state  ← polling 3s
POST sim/acd/sessions/<id>/start/                          → acd_session_start
POST sim/acd/sessions/<id>/pause/                          → acd_session_pause
POST sim/acd/sessions/<id>/resume/                         → acd_session_resume
POST sim/acd/sessions/<id>/stop/                           → acd_session_stop  + persist GTR
POST sim/acd/sessions/<id>/slots/add/                      → acd_slot_add
POST sim/acd/sessions/<id>/slots/<sid>/remove/             → acd_slot_remove
POST sim/acd/sessions/<id>/slots/<sid>/control/            → acd_slot_control  (break/available/absent)
GET  sim/acd/sessions/<id>/interactions/                   → acd_interactions  ?since=
```

**ACD Simulator — Agente OJT (3 endpoints):**
```
GET  sim/acd/agent/<slot_id>/        → acd_agent_panel  (nivel básico/intermedio/avanzado)
GET  sim/acd/agent/<slot_id>/poll/   → acd_agent_poll   ← polling 2s
POST sim/acd/agent/<slot_id>/action/ → acd_agent_action (answer/reject/hold/tipify/end_acw/break/return)
```

**Documentación:**
```
GET  sim/docs/<key>/   → docs_view   key: context | reference | design
```

---

## 12. Estado JS

### `acd_trainer.html`

```javascript
let SESSION_ID = null;   // ACDSession uuid
let POLL_TIMER = null;   // setInterval estado (3s)
let IS_PAUSED  = false;
// URLS.state(id), URLS.slotAdd(id), URLS.agentPanel(slotId)
```

**Funciones clave:**
```javascript
createSession()          // POST /sim/acd/sessions/create/
startSession()           // POST /sim/acd/sessions/<id>/start/ → arranca polling
doPoll()                 // GET  /sim/acd/sessions/<id>/state/ → updateUI()
updateUI(d)              // KPIs + queue + agent grid
renderSlotCard(s)        // genera HTML de cada card de agente
slotControl(slotId, st)  // POST break/available/absent
addSlot()                // POST slots/add/ con type real/simulated
loadSession(id)          // carga sesión previa y arranca polling
```

### `acd_agent.html`

```javascript
let CURRENT_IX  = null;  // ACDInteraction activa
let CALL_START  = null;  // timestamp answered_at
let CALL_TIMER  = null;  // interval timer on_call
let ACW_SECS    = 0;
// Polling cada 2s → doPoll() → showRinging/showOnCall/showACW/showIdle
```

**Funciones clave:**
```javascript
doPoll()              // GET /sim/acd/agent/<slot>/poll/ → updateClock + updateStats + show*
doAction(type, extra) // POST /sim/acd/agent/<slot>/action/
endCall()             // tipify + end_acw secuencial
showRinging(ix)       // muestra botones answer/reject
showOnCall(ix)        // inicia timer, muestra tipificación (level != basic)
showACW(ix)           // countdown 18s → auto end_acw
```

### `gtr.html`

```javascript
let SESSION_ID    = null;      // GTRSession Redis id
let POLL_TIMER    = null;      // setInterval para polling
let IS_PAUSED     = false;
let TOTAL_INTER   = 0;         // contador acumulado de interacciones
let SESSION_CANAL = 'inbound'; // 'inbound' | 'outbound' | 'digital'
let THRESHOLDS    = { sl_min: 80, abandon_max: 8, na_min: 85 };
```

**Funciones clave:**
```javascript
runDemo()                        // no existe — es startSession()
startSession()                   // crea sesión, configura canal, arranca polling
startPolling() / stopPolling()   // setInterval/clearInterval 3000ms
doPoll()                         // GET /sim/gtr/<sid>/tick/ → updateUI + appendFeed
updateUI(d)                      // actualiza KPIs (inbound o outbound según SESSION_CANAL)
_relabelKpis(canal)              // cambia labels KPI cards según canal
populateSkillSelect(canal)       // muestra/oculta selector skill (solo inbound)
syncControls(d)                  // sincroniza sliders con d.controls
sendControl(event_type, params)  // POST /sim/gtr/<sid>/event/
onSlider(ctrl, val)              // actualiza label del slider en tiempo real
enableControls(active)           // habilita/deshabilita botones y sliders
```

### `training.html`

```javascript
let SELECTED_SCENARIO = null;   // objeto completo del escenario seleccionado
let ACTIVE_SESSION_ID = null;   // TrainingSession id (BD)
let ACTIVE_GTR_SID    = null;   // GTR Redis session id
let POLL_TIMER        = null;   // polling del reloj GTR (cada 5s)
let EDIT_MODE         = false;  // true = editar escenario existente
```

**Funciones clave:**
```javascript
selectScenario(id)       // fetch scenario_list_api → renderDetail()
openCreateModal()        // limpia form + abre modal
openEditModal()          // pre-rellena form con SELECTED_SCENARIO
saveScenario()           // POST create/update
startSession()           // POST session_start → open GTR tab
openActionModal()        // abre modal para registrar acción
logAction()              // POST session_log_action
completeSession()        // POST session_complete → renderResult()
syncControls(d)          // sync sliders de control
```

### `simulator.html`

```javascript
// Sin estado global relevante — operación por buttons directos
// Cada acción es POST independiente con reload de página
```

---

## 13. Convenciones CSS / UI

### Scopes y CSS root

| Panel | Root CSS | Tema |
|-------|----------|------|
| `simulator.html` | `#sim-root` | Claro (`--surface:#fff`) |
| `gtr.html` | `#gtr-root` | Dark (`--g-bg:#0f172a`) |
| `training.html` | `#tr-root` | Dark (`--t-bg:#0f172a`) |
| `acd_trainer.html` | `#acd-root` | Dark (`--a-bg:#0b1120`) |
| `acd_agent.html` | `#agent-root` | Dark (`--g-bg:#0f172a`) |
| `dashboard.html` | `#sim-dash-root` | Claro |
| `account_editor.html` | `#editor-root` | Claro |
| `docs.html` | `#sim-docs-root` | Claro |

### Variables CSS GTR dark

```css
#gtr-root {
  --g-bg: #0f172a;     --g-surface: #1e293b;  --g-surface2: #263548;
  --g-border: #334155;
  --g-primary: #3b82f6; --g-primary-l: #60a5fa;
  --g-success: #10b981; --g-warning: #f59e0b;  --g-danger: #ef4444;
  --g-text: #f1f5f9;   --g-text-s: #94a3b8;   --g-text-m: #64748b;
}
```

### Status pills (gtr.html)

```css
.status-pill.atendida  { background:#10b98122; color:#10b981 }
.status-pill.abandonada{ background:#ef444422; color:#ef4444 }
.status-pill.venta     { background:#8b5cf622; color:#a78bfa }
.status-pill.no_contacto{background:#64748b22; color:#94a3b8 }
.status-pill.rechazo   { background:#f59e0b22; color:#f59e0b }
.status-pill.agenda    { background:#3b82f622; color:#60a5fa }
```

### Badges dificultad (training.html)

```css
.badge-easy  { background:#10b98122; color:#10b981 }
.badge-medium{ background:#f59e0b22; color:#f59e0b }
.badge-hard  { background:#ef444422; color:#ef4444 }
```

### Sliders de control (gtr.html — SIM-6b)

Los sliders CSS usan `-webkit-slider-thumb` con `appearance:none`. Si se añaden
nuevos sliders, mantener la clase `.ctrl-slider` y el patrón `oninput/onchange` separado:
- `oninput` → solo actualiza el label visual (sin fetch)
- `onchange` → dispara `sendControl()` → POST al backend

---

## 14. Constantes

```python
# gtr_engine.py
GTR_TTL = 60 * 60 * 4   # 4 horas — TTL Redis de sesión GTR

CLOCK_SPEEDS = {1: 1, 5: 5, 15: 15, 60: 60}

DEFAULT_THRESHOLDS = {
    'sl_min': 80.0, 'abandon_max': 8.0, 'na_min': 85.0, 'queue_max': 15
}

DEFAULT_THRESHOLDS_OUTBOUND = {
    'contact_min': 22.0, 'conv_min': 0.5, 'no_contact_max': 75.0
}

# engine.py
HistoricalEngine.BATCH_SIZE = 2000   # bulk_create batch size

# persist_session()
BATCH = 2000   # batch de escritura a BD
```

---

## 15. Convenciones del proyecto

1. **Respuesta JSON:** siempre `{'success': True/False, ...}`.
2. **Fecha en Interaction:** usar `fecha` (DateField). Nunca `started_at` — no existe.
3. **Orden temporal:** `order_by('fecha', 'hora_inicio')` — no `order_by('started_at')`.
4. **Generadores:** devuelven `list[dict]`, nunca instancias Django. El engine los convierte.
5. **CSRF:** `document.cookie.match(/csrftoken=([^;]+)/)?.[1]` en sim templates.
6. **Polling:** siempre con `clearInterval` en `stopPolling()` antes de nueva sesión.
7. **persist_session:** llamar desde `finally` — siempre limpia Redis aunque falle BD.
8. **sim_date vs fecha:** `session.sim_date` es `date`. `Interaction.fecha` es `DateField`. Son el mismo valor.
9. **agent_codigo → SimAgent PK:** los generadores producen `agent_codigo` string. El engine hace el lookup `agent_pk_map[codigo]` para el FK.
10. **Identificar interacciones GTR:** `SimRun.objects.filter(canales__contains='gtr')` o `Interaction.objects.filter(run__canales__contains='gtr')`.

---

## 16. Bugs conocidos

| # | Estado | Archivo | Descripción |
|---|--------|---------|-------------|
| 1 | ✅ Corregido | `dashboard.py`, `etl_manager.py` | `started_at` inexistente. Corregido a `fecha__gte/lte` y `order_by('fecha','hora_inicio')` |
| 2 | ✅ Corregido | `training.html` | `@keyframes dotPulse` estaba dentro del `<script>`. Movido al `<style>`. |
| 3 | ✅ Corregido | `gtr.html` | `openConfigModal()` duplicada por str_replace parcial. Corregido. |
| 4 | ✅ Corregido | `gtr_engine.py` | `expected_vol` podía ser negativo → `random.gauss(neg, neg*0.10)` producía error. Corregido con `max(0.0, expected_vol)` y `max(0.1, ...)` en sigma. |
| 5 | ⬜ Pendiente | `test_gtr_engine.py` | Tests no cubren los 7 nuevos tipos de evento SIM-6b ni los overrides en generadores. |
| 6 | ✅ Corregido | `views/acd.py` | `_generate_acd_interactions()` usaba `account.config.get(canal, {})` — fallaba si `config` era `None`. Corregido con `(config or {}).get(canal, {})` + fallbacks de skill por canal (`GENERAL` / `OUTBOUND` / `DIGITAL`). |
| 7 | ⬜ Pendiente | `acd_agent.html` | Nivel `advanced` no implementado — `doAction('transfer')` con `to_slot_id` no renderiza selector de agentes. Target SIM-7c. |
| 8 | ✅ Corregido | `views/acd.py` | `_get_tipificaciones()` sin rama `digital` → retornaba `[]` sin caer al fallback. Agregada rama digital (`tipificaciones_bxi` + `tipificaciones_app`) + fallback activado solo si lista vacía. |
| 9 | ✅ Corregido | `views/acd.py` | Indentación rota en `acd_agent_poll` — bloque `available_slots` flotaba fuera del cuerpo de la función (0 spaces vs 4). |
| 10 | ✅ Corregido | `views/acd.py` | `get_user_model()` importado inline en 2 funciones distintas. Movido al tope del archivo. |
| 11 | ✅ Corregido | `views/gtr.py` | `gtr_panel()` no pasaba `DEFAULT_THRESHOLDS_OUTBOUND` al template — inputs de umbral outbound renderizaban vacíos. |
| 12 | ✅ Corregido | `gtr.html` | `csrf()` leía desde `[name=csrfmiddlewaretoken]` — cambiado a cookie (convención del proyecto). |
| 13 | ✅ Corregido | `gtr.html` | `<div id="gtr-root">` duplicado envolviendo el modal — ID inválido + CSS scoped roto. Modal movido dentro del `#gtr-root` existente. |
| 14 | ✅ Corregido | `gtr.html` | `.events-panel` sin `background`/`border`/`border-radius` — panel sin marco visual. Estilos agregados. |

---

## 17. Archivos pendientes de documentar

| Prioridad | Archivo | Notas |
|-----------|---------|-------|
| Alta | `views/account_editor.py` | `_merge_config`, `_validate_config` — lógica de merge de presets |
| Alta | `views/simulator.py` | `_account_row`, `_run_row`, lógica de generación histórica vía HTTP |
| Media | `views/dashboard.py` | Vista de resumen KPIs de cuenta sim |
| Media | `gtr_engine.py` | Documentar `GTRSession.from_dict` y serialización completa |
| Baja | `models.py` | `SimAccount.interaction_count` property |
| Baja | `templates/account_editor.html` | ~1110 líneas — formularios de skill/tipificación |
