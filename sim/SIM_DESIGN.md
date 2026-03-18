# `sim` — Simulador de Interacciones WFM
## Diseño, Fases e Implementación

> **Inicio:** 2026-03-15
> **Última actualización:** 2026-03-17
> **Contexto:** App Django independiente dentro de Management360.
> Genera datos de contact center realistas para análisis, training y demo.
> Calibrada con datos reales de operaciones bancarias y telco (2018-2020).
> **Metodología:** Scrum — sprints de 1 semana.

---

## Propósito

El simulador resuelve el problema del analista WFM que no tiene datos para trabajar.
En lugar de depender de exportaciones de ACD externos, `sim` genera el mismo tipo
de datos que producen sistemas como Genesys, ININ, PureCloud o VICIdial.

**Dos modos de operación base:**

| Modo | Descripción | Uso principal |
|------|-------------|---------------|
| **Histórico** | Genera N días de interacciones en batch | Cargar datasets, probar reportes, demo |
| **GTR** | Corre en clock acelerado (1min real = X min simulado) | Training de reacción intraday, alertas |

---

## Estado general de fases

| Fase | Descripción | Sprint | Estado |
|------|-------------|--------|--------|
| **SIM-1** | Simulador histórico (3 canales + presets) | S1 | ✅ |
| **SIM-2** | GTR Engine (clock acelerado, alertas, eventos) | S1 | ✅ |
| **SIM-3** | Account Editor (parámetros personalizables) | S1 | ✅ |
| **SIM-4** | ETL Source type `sim` nativo en analyst | S2 | ✅ |
| **SIM-4b** | Dashboard widgets fuente `sim` | S2 | ✅ |
| **SIM-5** | Training Mode (escenarios + sesiones + score) | S2 | ✅ |
| **SIM-6a** | Persistencia GTR en BD + SimAgentProfile | S3 | ✅ |
| **SIM-6b** | GTR Interactivo (controles en tiempo real) | S3 | ⬜ |
| **SIM-7a** | ACD Session + enrutamiento multi-agente | S4 | ✅ |
| **SIM-7b** | Pantalla agente OJT básico + intermedio | S4 | ✅ |
| **SIM-7c** | Pantalla agente avanzado + multi-skill | S5 | ⬜ |
| **SIM-7d** | Dashboard trainer interactivo | S4 | ✅ |
| **SIM-7e** | Agentes simulados perfilados en sesión ACD | S5 | ⬜ |

---

## Sprints

### Sprint 1 — Completado ✅
| Tarea | Estado |
|-------|--------|
| SIM-1: Generadores inbound / outbound / digital | ✅ |
| SIM-2: GTR Engine (clock, alertas, eventos discretos) | ✅ |
| SIM-3: Account Editor | ✅ |
| Migración 0001_initial | ✅ |
| 21 endpoints bajo `sim/` | ✅ |

**Resultado:** 37,881 interacciones generadas en 21.2s. GTR panel funcionando.

### Sprint 2 — Completado ✅
| Tarea | Estado |
|-------|--------|
| SIM-4: ETL Source type `sim` (migración 0013 analyst) | ✅ |
| SIM-4b: Dashboard widgets fuente `sim` | ✅ |
| SIM-5: Training Mode completo | ✅ |
| Outbound GTR tick generator | ✅ |
| Tests 157/157 OK | ✅ |
| GTR autostart desde Training Mode | ✅ |
| Migración 0002_add_training | ✅ |
| Bug fix: `started_at` → `fecha` + `hora_inicio` | ✅ |

### Sprint 3 — En curso 🔵
| Tarea | Prioridad | Estado |
|-------|-----------|--------|
| SIM-6a: `persist_session()` — GTR → BD bulk_create | 🔴 | ✅ |
| SIM-6a: `SimAgentProfile` modelo + migración 0003 | 🔴 | ✅ |
| SIM-6a: `seed_agent_profiles` command — presets tier | 🔴 | ✅ |
| SIM-6b: GTR Interactivo — controles flujo (vol, AHT, ACW) | 🟠 | ⬜ |
| SIM-6b: GTR Interactivo — gestión agentes (break, skill) | 🟠 | ⬜ |
| Sidebar nav Training Mode | 🟡 | ⬜ |

### Sprint 4 — Completado ✅

| Tarea | Prioridad | Estado |
|-------|-----------|--------|
| SIM-7a: Modelos ACD (ACDSession, ACDAgentSlot, ACDInteraction, ACDAgentAction) + migración 0004 | 🔴 | ✅ |
| SIM-7a: Motor enrutamiento skill-based, preferencia OJT real, menor carga | 🔴 | ✅ |
| SIM-7a: Discado predictivo / progresivo / manual | 🔴 | ✅ |
| SIM-7a: Resolución automática agentes simulados via SimAgentProfile | 🔴 | ✅ |
| SIM-7b: Pantalla agente nivel básico (answer/reject/hold/tipify/break) | 🔴 | ✅ |
| SIM-7b: Pantalla agente nivel intermedio (tipif select + timer ACW auto) | 🟠 | ✅ |
| SIM-7d: Dashboard trainer — grid agentes + KPIs + cola + controles slot | 🔴 | ✅ |
| SIM-7d: Link directo pantalla OJT desde card de agente | 🟠 | ✅ |
| Archivos: `sim/views/acd.py` + `acd_trainer.html` + `acd_agent.html` | 🔴 | ✅ |

### Sprint 5 — Planificado ⬜

| Tarea | Prioridad | Estado |
|-------|-----------|--------|
| SIM-7c: Pantalla agente avanzado (multi-skill + inline + conference) | 🟠 | ⬜ |
| SIM-7e: Agentes simulados perfilados en sesión ACD (tiers top/alto/medio/bajo) | 🔴 | 🔵 parcial |
| SIM-7d: Dashboard trainer — controles interactivos por slot | 🟠 | ⬜ |
| Evaluación OJT vs perfil esperado | 🟡 | ⬜ |

---

## Backlog priorizado

| ID | Historia | Prioridad | Esfuerzo | Sprint |
|----|----------|-----------|----------|--------|
| B-01 | Como trainer, quiero que GTR persista en BD para analizar después | 🔴 | M | S3 ✅ |
| B-02 | Como trainer, quiero perfiles conductuales (top/alto/medio/bajo) reutilizables | 🔴 | M | S3 ✅ |
| B-03 | Como analista, quiero controlar flujo GTR en tiempo real (vol, AHT, ACW, hold) | 🟠 | L | S3 |
| B-04 | Como trainer, quiero gestionar agentes GTR en tiempo real (break, skill, ausencia) | 🟠 | L | S3 |
| B-05 ✅ | Como trainer, quiero crear sesión ACD multi-agente con slots reales y simulados | 🔴 | XL | S4 |
| B-06 ✅ | Como OJT básico, quiero ver y gestionar mis llamadas con botones predeterminados | 🔴 | L | S4 |
| B-07 ✅ | Como OJT intermedio, quiero tipificar con inputs ACD y timer de ACW | 🟠 | L | S4 |
| B-08 ✅ | Como trainer, quiero ver grid de todos los agentes con estado en tiempo real | 🔴 | L | S4 |
| B-09 | Como OJT avanzado, quiero gestionar multi-skill, hold, transferencia y conference | 🟠 | XL | S5 |
| B-10 | Como trainer, quiero asignar llamadas manualmente y forzar eventos por agente | 🟠 | M | S5 |
| B-11 | Como trainer, quiero ver evaluación del OJT vs perfil esperado al finalizar | 🟡 | M | S5 |

---

## Canales soportados — calibración detallada

### Inbound — Voz
Calibrado con Banca Telefónica (Pichincha), Julio 2020.

| Parámetro | Valor |
|-----------|-------|
| Horario operación | 09:00 – 18:00 (9h) |
| Volumen weekday | 1,490 llamadas/día (±150) |
| Volumen weekend | 883 llamadas/día (factor 0.59×) |
| TMO (talk time) | 313s — rango 291–340s |
| ACW (after call work) | 18s |
| Agentes típicos | 22 (rango 20–24) |
| Abandono rate | 3.9% global / 4.5% en hora 15:00 |
| SL threshold | 20 segundos |
| SL histórico | 87.3% |

**Perfil intradía (pesos reales):**

| Hora | Peso | Vol. promedio |
|------|------|--------------|
| 09:00 | 12.3% | 167 |
| 10:00 | 13.5% | 185 ← pico |
| 11:00 | 13.6% | 185 ← pico |
| 12:00 | 11.6% | 158 |
| 13:00 | 10.2% | 139 ← valle almuerzo |
| 14:00 | 9.6%  | 131 |
| 15:00 | 9.6%  | 131 |
| 16:00 | 10.9% | 148 |
| 17:00 | 8.7%  | 119 ← cierre |

**Skills y tipificaciones (jerarquía padre → hijo):**

```
PLD (65.7%)
  ├── CUOTA MENSUAL                47.3%
  ├── INFORMATIVA                  20.7%
  ├── OFERTA PRESTAMO LIBRE DISP.  13.5%
  ├── LIQUIDACION TOTAL            11.3%
  └── INGRESO DE REGULAR            7.2%

CONVENIOS (9.8%)
  ├── CUOTA MENSUAL                58.3%
  ├── SE BRINDA TELEFONOS          17.1%
  ├── TASAS/COMISIONES/PORTES      15.2%
  ├── INGRESO DE REGULAR            4.7%
  └── SOLICITA HOJA RESUMEN         4.7%

HIPOTECARIO MI VIVIENDA (8.5%)
  ├── CUOTA MENSUAL                46.9%
  ├── SOLICITA HOJA RESUMEN        20.4%
  ├── INGRESO DE REGULAR           19.8%
  ├── TASAS/COMISIONES/PORTES       6.9%
  └── INFORMACIÓN SOBRE EL RECLAMO  5.9%

HIPOTECARIO BANCO (5.4%)
  ├── CUOTA MENSUAL                49.9%
  ├── INGRESO DE REGULAR           14.2%
  ├── SOLICITA HOJA RESUMEN        13.8%
  ├── TASAS/COMISIONES/PORTES      11.0%
  └── OPC 3 - ASESOR RECLAMO       11.0%

CREDICARSA (4.5%)   — tipificación libre
COMPRA DE CARTERA (4.4%)
MICROFINANZAS (1.7%)
VEHICULAR (0.1%)
```

**AHT por tipificación (segundos):**

| Tipificación | Media | Sigma |
|--------------|-------|-------|
| CUOTA MENSUAL | 270 | 0.18 |
| INFORMATIVA | 155 | 0.20 |
| OFERTA PRESTAMO LIBRE DISPONIBILIDAD | 350 | 0.20 |
| LIQUIDACION TOTAL | 360 | 0.20 |
| INGRESO DE REGULAR | 240 | 0.18 |
| SOLICITA HOJA RESUMEN | 200 | 0.18 |
| TASAS/COMISIONES/PORTES | 220 | 0.18 |
| RECLAMO / ASESOR | 480 | 0.22 |
| SE BRINDA TELEFONOS | 120 | 0.15 |
| CONSULTA GENERAL | 300 | 0.20 |

**Abandono por hora:**

| Hora | Tasa |
|------|------|
| 09:00 | 2.0% |
| 10:00 | 3.0% |
| 11:00 | 3.5% |
| 12:00 | 4.0% |
| 13:00 | 3.8% |
| 14:00 | 4.0% |
| 15:00 | 5.5% ← pico |
| 16:00 | 3.5% |
| 17:00 | 2.5% |

---

### Digital — Chat / Mail / App
Calibrado con Banca Digital (Pichincha), Julio 2020.

| Parámetro | Valor |
|-----------|-------|
| Volumen diario | 203 interacciones/día |
| HomeBank BXI | 84.9% del canal |
| APP Pichincha | 15.1% (lanzamiento 5-Jul-2020) |
| Top tipificación | BXI_ACTIVACION USUARIO NUEVO (63.4%) |
| Duración sesión | 180–300s (estimado) |

**Tipificaciones BXI (25 total):**
```
BXI_ACTIVACION USUARIO NUEVO      63.4%
BXI_DESEA INFO GRAL                4.6%
BXI_COMO INGRESAR (LOGUEO)         4.4%
BXI_INCIDENCIA LOGUEO              2.6%
BXI_TRANSACCIONAR                  2.6%
BXI_DESBLOQUEO DE USUARIO          1.9%
BXI_CLAVE DE 6 DIGITOS             1.9%
... (18 tipificaciones menores)

APP_ACTIVACION USUARIO             4.5%
APP_DESEA INFO GRAL                3.0%
APP_COMO INGRESAR                  2.8%
... (12 tipificaciones APP)
```

---

### Outbound — Discador
Calibrado con Conduent (ENTEL/Telefónica), Agosto 2018.

| Parámetro | Valor |
|-----------|-------|
| Volumen diario marcaciones | ~131,400 |
| Contactabilidad real | 27.6% |
| No contacto | 71.3% |
| Tasa de venta (sobre contactados) | 0.84% |
| Tasa de agenda/callback | 12.8% |
| Agentes dimensionados | 435 |
| Agentes activos promedio | 322 (74%) |
| Ausencia rate | 5.0% semanal |
| SPH Bruto | 0.128 |
| SPH Neto | 0.086 |
| ARPU por venta | S/ 37.95 |
| Turnos | MAÑANA / TARDE |

**Funnel real mensual:**
```
Marcaciones:   3,547,790  100%
  └── Contacto efectivo:   980,834   27.6%
        └── Venta:           7,033    0.84% (sobre contactados)
        └── Agenda:        106,721   12.8%
        └── Rechazo:       180,210   21.6%
        └── Cliente corta: 346,187   41.5%  ← AHT corto
        └── Línea ocupada: 191,426   22.9%
  └── No contacto:       2,528,681   71.3%
        └── No contesta:  1,325,715  52.4%
        └── Buzón:          829,343  32.8%
        └── Desconectada:    84,769   3.4%
        └── Timeout:        134,671   5.3%
```

**Producto:**
```
PORTABILIDAD: 92%
LINEA NUEVA:   8%
  ├── CHIP:   87%
  └── PACK:   13%
```

**Funnel de calidad (venta → entrega):**
```
Pre-ventas:  6,039  →  Validadas: 5,606 (93%)  →  Entregadas: 4,007 (66%)
```

**Performance por turno:**

| Turno | Agentes | SPH Bruto | VTS/agente | Productividad |
|-------|---------|-----------|------------|---------------|
| MAÑANA | 33 | 0.185 | 8.8 | 104.5% |
| TARDE  | 17 | 0.177 | 8.8 | 103.8% |

**Segmentación por antigüedad:**

| Antigüedad | N | SPH | Adherencia |
|------------|---|-----|------------|
| > 3 meses  | 41 | 0.092 | 92.4% |
| < 3 meses  |  9 | 0.065 | 95.9% |

---

## Arquitectura actual

```
sim/
├── generators/
│   ├── base.py         ✅ weighted_choice, gaussian_duration, intraday_slot
│   ├── inbound.py      ✅ calibrado Banca Telefónica
│   ├── outbound.py     ✅ calibrado Conduent/ENTEL
│   └── digital.py      ✅ calibrado Banca Digital
├── engine.py           ✅ HistoricalEngine — batch N días
├── gtr_engine.py       ✅ GTREngine inbound + outbound
│                          ✅ persist_session() — Redis → BD (SIM-6a)
├── models.py
│   ├── SimAccount       ✅
│   ├── SimAgent         ✅
│   ├── Interaction      ✅ campos: fecha, hora_inicio, hora_fin
│   ├── SimRun           ✅ canales=['gtr'] identifica sesiones GTR
│   ├── TrainingScenario ✅
│   ├── TrainingSession  ✅
│   └── SimAgentProfile  ✅ SIM-6a
├── views/
│   ├── simulator.py     ✅
│   ├── gtr.py           ✅ autostart + persist en gtr_stop
│   ├── dashboard.py     ✅
│   ├── account_editor.py✅
│   └── training.py      ✅
├── templates/sim/
│   ├── simulator.html   ✅
│   ├── gtr.html         ✅ outbound KPIs + autostart
│   ├── dashboard.html   ✅
│   ├── account_editor.html ✅
│   └── training.html    ✅
├── tests/
│   ├── test_generators.py  ✅ 99 tests
│   └── test_gtr_engine.py  ✅ 58 tests
├── management/commands/
│   └── seed_agent_profiles.py ✅ 8 presets (4 inbound + 4 outbound)
├── migrations/
│   ├── 0001_initial         ✅
│   ├── 0002_add_training    ✅
│   └── 0003_add_sim_agent_profile ✅
└── urls.py                  ✅ 31 rutas
```

---

## Modelos de datos

### `SimAccount` — Cuenta/Campaña
```python
name            CharField       # "Banca Telefónica", "ENTEL Portabilidad"
canal           CharField       # inbound / outbound / digital / mixed
account_type    CharField       # banking / telco / retail / generic
config          JSONField       # parámetros calibrados por canal
is_active       BooleanField
created_by      ForeignKey(User)
```

### `SimAgent` — Agente simulado
```python
account         ForeignKey(SimAccount)
codigo          CharField       # AGT-001 ... AGT-NNN
turno           CharField       # MAÑANA / TARDE / NOCHE
antiguedad      CharField       # junior (<3m) / senior (>3m)
sph_base        FloatField      # velocidad base del agente
adherencia_base FloatField      # 0.696 – 0.998 (rango real)
tmo_factor      FloatField      # factor sobre TMO base
is_active       BooleanField
```

### `Interaction` — Contacto generado
```python
account         ForeignKey(SimAccount)
agent           ForeignKey(SimAgent, null=True)
canal           CharField       # inbound / outbound / digital
skill           CharField       # PLD / CONVENIOS / PORTABILIDAD / etc.
sub_canal       CharField       # bxi / app / chip / pack
fecha           DateField       # ← CAMPO DE FECHA (no started_at)
hora_inicio     DateTimeField   # ← HORA DE INICIO
hora_fin        DateTimeField
duracion_s      IntegerField
acw_s           IntegerField
tipificacion    CharField
status          CharField       # atendida/abandonada/venta/agenda/no_contacto/rechazo
lead_id         CharField
intento_num     IntegerField
is_simulated    BooleanField    # siempre True
generated_at    DateTimeField
```

> **CRÍTICO:** Usar `fecha` para filtros de fecha, `hora_inicio`/`hora_fin` para tiempo.
> El campo `started_at` **NO EXISTE** en este modelo.

### `SimRun` — Ejecución
```python
account         ForeignKey(SimAccount)
date_from/to    DateField
canales         JSONField       # ["inbound"] o ["inbound","gtr"] para sesiones GTR
status          CharField       # running / done / error
interactions_generated  IntegerField
agents_generated        IntegerField
duration_s      FloatField
triggered_by    ForeignKey(User)
```

### `TrainingScenario` — Escenario de training
```python
name, description, canal, difficulty   # easy/medium/hard
account         ForeignKey(SimAccount, null=True)
clock_speed     IntegerField
thresholds      JSONField
events          JSONField       # [{at_sim_min, type, params, hint, auto}]
expected_actions JSONField      # [{after_event_idx, within_min, description}]
is_public       BooleanField
created_by      ForeignKey(User)
```

### `TrainingSession` — Sesión de training
```python
scenario        ForeignKey(TrainingScenario)
trainee         ForeignKey(User)
gtr_session_id  CharField       # Redis key de la sesión GTR
sim_date        DateField
status          CharField       # active/completed/abandoned
score           IntegerField    # 0-100
score_detail    JSONField
alerts_count    IntegerField
events_responded IntegerField
actions_log     JSONField       # [{sim_time, real_ts, action, event_ref}]
final_kpis      JSONField
trainer_notes   TextField
```

### `SimAgentProfile` — Perfil conductual (SIM-6a)
```python
name, description, tier, canal    # top/alto/medio/bajo
# Velocidad
aht_factor, acw_factor, available_pct
# Comportamiento
answer_rate, hold_rate, hold_dur_s, transfer_rate, corte_rate
# Resultados outbound
conv_rate, agenda_rate
# Ausencias
break_freq, break_dur_s, shrinkage
# Multi-skill
skills          JSONField       # ["PORTABILIDAD", "LINEA NUEVA"]
skill_priority  JSONField       # {"PORTABILIDAD": 1}
is_preset       BooleanField    # presets del sistema no editables
```

**Presets del sistema:**

| Atributo | top | alto | medio | bajo |
|----------|-----|------|-------|------|
| aht_factor | 0.85 | 0.95 | 1.05 | 1.30 |
| acw_factor | 0.80 | 0.90 | 1.05 | 1.25 |
| conv_rate | 2.5% | 1.5% | 0.8% | 0.3% |
| hold_rate | 2% | 5% | 10% | 18% |
| corte_rate | 1% | 3% | 8% | 15% |
| available_pct | 92% | 87% | 80% | 70% |
| break_freq | 0.5/h | 0.8/h | 1.2/h | 2.0/h |
| transfer_rate | 2% | 4% | 7% | 12% |
| answer_rate | 99% | 97% | 93% | 85% |

---

## Presets de cuenta incluidos

```python
PRESETS = {
    'banking_inbound': {
        'name':        'Banca Inbound',
        'canal':       'inbound',
        'account_type':'banking',
        'weekday_vol': 1490,
        'weekend_vol': 883,
        'tmo_s':       313,
        'acw_s':       18,
        'agents':      22,
        'abandon_rate':0.039,
        'sl_s':        20,
        'schedule':    ('09:00', '18:00'),
        'intraday':    {9:0.123,10:0.135,11:0.136,12:0.116,
                        13:0.102,14:0.096,15:0.096,16:0.109,17:0.087},
        'skills':      { ... },  # jerarquía completa arriba
    },
    'telco_outbound': {
        'name':        'Telco Outbound',
        'canal':       'outbound',
        'account_type':'telco',
        'daily_marc':  131400,
        'contact_rate':0.276,
        'conv_rate':   0.0084,
        'agenda_rate': 0.128,
        'agents':      322,
        'absence_rate':0.050,
        'sph_base':    0.128,
        'turnos':      ['MAÑANA','TARDE'],
        'arpu':        37.95,
        'no_contact':  {'no_contesta':0.524,'buzon':0.328,'otros':0.148},
    },
    'banking_digital': {
        'name':        'Banca Digital',
        'canal':       'digital',
        'account_type':'banking',
        'daily_vol':   203,
        'channels':    {'bxi':0.849,'app':0.151},
        'duration_s':  240,
    },
}
```

---

## GTR Engine — arquitectura

```
Clock speeds:
  5x  → 1 min real = 5 min simulados
  15x → 1 min real = 15 min simulados  ← recomendado
  60x → 1 min real = 1 hora simulada   ← demo rápido

Redis keys:
  gtr:session:{sid}       → GTRSession.to_dict()   TTL 4h
  gtr:interactions:{sid}  → list[dict]              TTL 4h

Ciclo tick:
  GET /sim/gtr/<sid>/tick/ cada 3s
    → _generate_window() según canal
    → _update_kpis()
    → _check_alerts()
    → save_session() + add_interactions()
    → si finished → persist_session() auto

persist_session() (SIM-6a):
  get_interactions() → Redis
  → bulk_create Interaction en BD (batches 2000)
  → crear SimRun(canales=['canal','gtr'])
  → delete_session() → limpiar Redis
```

**Thresholds por canal:**

```python
DEFAULT_THRESHOLDS = {          # inbound
    'sl_min':       80.0,
    'abandon_max':   8.0,
    'na_min':       85.0,
    'queue_max':    15,
}

DEFAULT_THRESHOLDS_OUTBOUND = {
    'contact_min':  22.0,
    'conv_min':      0.5,
    'no_contact_max': 75.0,
}
```

---

## Integración con analyst

### ETL Source type `sim`
`ETLSource.sim_account` FK → `sim.SimAccount` (migración 0013 analyst).
Filtro de fecha: `fecha__gte / fecha__lte`. Orden: `fecha`, `hora_inicio`.

### Dashboard widgets
`source = {"type": "sim", "id": "<SimAccount UUID>"}` → `_load_df` carga
`Interaction.objects.filter(account=account).order_by('fecha', 'hora_inicio')`.

### Report Builder — funciones WFM

| key | label | category | Columnas |
|-----|-------|----------|---------|
| `sim_agent_performance` | Performance por Agente | WFM | `agente`, `duracion_s`, `status` |
| `sim_inbound_daily` | KPIs Inbound Diarios | WFM | `fecha`, `status`, `duracion_s` |
| `sim_contact_funnel` | Embudo Contactabilidad | WFM | `status` |

**Output `sim_agent_performance`:**
```
rank  agente   total  atendidas  aten_%  aban_%  sl_%  aht_min  aht_s
   1  AGT-001     42         36   85.7%    0.0%   0.0%     6.08    365
```

**Output `sim_inbound_daily`:**
```
fecha       dia        entrantes  atendidas  na_%  sl_%  aban_%  tmo_min
2026-03-16  Monday          1490       1432  96.1%  87.3    3.9%     5.22
```

**Output `sim_contact_funnel`:**
```
etapa                  cantidad  pct_total  pct_anterior
Marcaciones               131400      100.0          —
Contacto efectivo          36266       27.6         27.6
└─ Venta                     305        0.23         0.84
└─ Agenda/Callback          4642        3.53        12.80
No contacto                93735       71.3         71.3
```

---

## SIM-7 — Diseño preliminar (Sprint 4-5)

### Modos de discado ACD

| Modo | Comportamiento |
|------|---------------|
| **Predictivo** | Motor lanza N llamadas simultáneas por agente según ocupación |
| **Progresivo** | Una llamada por agente libre. Motor espera liberación |
| **Manual** | El agente decide cuándo marcar |

### Actores

```
Trainer
  └── crea ACDSession (escenario + config + modo discado)
        ├── ACDAgentSlot[]
        │     ├── type: 'real' → User Django (OJT)
        │     └── type: 'simulated' → SimAgentProfile
        └── motor GTR clock (1x / 5x / 15x)
```

### Pantalla agente OJT — 3 niveles

```
Básico:     [Atender][Venta][No interesado][Agenda][Hold][Transferir][Cortar]
Intermedio: select motivo + submotivo + observación + timer ACW + [Listo][Extender]
Avanzado:   multi-skill + transferencia inline + conference + notas + hold música
```

### Dashboard trainer

```
KPIs:    Marcaciones · Contactos · Ventas · Contactabilidad% · Conv%
         En cola · En llamada · ACW · Disponibles · Ausentes · Break

Grid:    [AGT-01][real/sim][AVAILABLE] AHT:4:32 Conv:2 ████
         [AGT-02][sim-top ][ON CALL  ] AHT:3:55 Conv:5 ██████

Control: Asignar llamada · Forzar break · Cambiar skill
         Inyectar evento · Pausar agente · Mensaje al agente
```

---

## Tests

```bash
python manage.py test sim.tests.test_generators sim.tests.test_gtr_engine -v 2
# Ran 157 tests in 72s — OK
```

| Archivo | Tests | Qué cubre |
|---------|-------|-----------|
| `test_generators.py` | 99 | base, inbound, outbound, digital |
| `test_gtr_engine.py` | 58 | GTRSession, KPIs, alertas, eventos, cache |

---

## Bugs corregidos

| Bug | Archivo | Descripción |
|-----|---------|-------------|
| `started_at` inexistente | `dashboard.py`, `etl_manager.py` | Corregido a `fecha__gte/lte` y `order_by('fecha','hora_inicio')` |
| `@keyframes` en `<script>` | `training.html` | Movido al bloque `<style>` |
| `openConfigModal` undefined | `gtr.html` | Función duplicada por str_replace — corregido |

---

## 🔄 Handoff — Cambio de sesión

> Estado: SIM-1 a SIM-6a completas. Sprint 3 continúa con SIM-6b.

### Archivos para próxima sesión

```bash
bash m360_map.sh app ./sim        # SIM_CONTEXT.md
bash m360_map.sh app ./analyst    # ANALYST_CONTEXT.md
# Adjuntar SIM_DESIGN.md + ANALYST_PLATFORM_DESIGN.md
```

Para SIM-6b (GTR Interactivo):
```bash
cat sim/gtr_engine.py | termux-clipboard-set
cat sim/templates/sim/gtr.html | termux-clipboard-set
```

### Comandos post-deploy SIM-6a

```bash
python manage.py migrate sim
python manage.py seed_agent_profiles
```
