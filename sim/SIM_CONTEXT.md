# Mapa de Contexto — App `sim`

> Generado por `m360_map.sh`  |  2026-03-22 12:39:33
> Ruta: `/data/data/com.termux/files/home/projects/Management360/sim`  |  Total archivos: **37**

---

## Índice

| # | Categoría | Archivos |
|---|-----------|----------|
| 1 | 👁 `views` | 9 |
| 2 | 🎨 `templates` | 8 |
| 3 | 🗃 `models` | 1 |
| 4 | 🔗 `urls` | 1 |
| 5 | 🛡 `admin` | 1 |
| 6 | 📄 `management` | 1 |
| 7 | 🧪 `tests` | 4 |
| 8 | 📄 `other` | 12 |

---

## Archivos por Categoría


### VIEWS (9 archivos)

| Archivo | Líneas | Ruta relativa |
|---------|--------|---------------|
| `views.py` | 3 | `views.py` |
| `__init__.py` | 7 | `views/__init__.py` |
| `account_editor.py` | 235 | `views/account_editor.py` |
| `acd.py` | 964 | `views/acd.py` |
| `dashboard.py` | 185 | `views/dashboard.py` |
| `docs.py` | 60 | `views/docs.py` |
| `gtr.py` | 173 | `views/gtr.py` |
| `simulator.py` | 297 | `views/simulator.py` |
| `training.py` | 451 | `views/training.py` |

### TEMPLATES (8 archivos)

| Archivo | Líneas | Ruta relativa |
|---------|--------|---------------|
| `account_editor.html` | 1110 | `templates/sim/account_editor.html` |
| `acd_agent.html` | 669 | `templates/sim/acd_agent.html` |
| `acd_trainner.html` | 735 | `templates/sim/acd_trainner.html` |
| `dashboard.html` | 765 | `templates/sim/dashboard.html` |
| `docs.html` | 327 | `templates/sim/docs.html` |
| `gtr.html` | 865 | `templates/sim/gtr.html` |
| `simulator.html` | 647 | `templates/sim/simulator.html` |
| `training.html` | 842 | `templates/sim/training.html` |

### MODELS (1 archivos)

| Archivo | Líneas | Ruta relativa |
|---------|--------|---------------|
| `models.py` | 701 | `models.py` |

### URLS (1 archivos)

| Archivo | Líneas | Ruta relativa |
|---------|--------|---------------|
| `urls.py` | 69 | `urls.py` |

### ADMIN (1 archivos)

| Archivo | Líneas | Ruta relativa |
|---------|--------|---------------|
| `admin.py` | 3 | `admin.py` |

### MANAGEMENT (1 archivos)

| Archivo | Líneas | Ruta relativa |
|---------|--------|---------------|
| `seed_agent_profiles.py` | 139 | `management/commands/seed_agent_profiles.py` |

### TESTS (4 archivos)

| Archivo | Líneas | Ruta relativa |
|---------|--------|---------------|
| `tests.py` | 3 | `tests.py` |
| `__init__.py` | 0 | `tests/__init__.py` |
| `test_generators.py` | 543 | `tests/test_generators.py` |
| `test_gtr_engine.py` | 597 | `tests/test_gtr_engine.py` |

### OTHER (12 archivos)

| Archivo | Líneas | Ruta relativa |
|---------|--------|---------------|
| `SIM_CONTEXT.md` | 354 | `SIM_CONTEXT.md` |
| `SIM_DESIGN.md` | 728 | `SIM_DESIGN.md` |
| `SIM_DEV_REFERENCE.md` | 1140 | `SIM_DEV_REFERENCE.md` |
| `SIM_HANDOFF_20260319.md` | 123 | `SIM_HANDOFF_20260319.md` |
| `__init__.py` | 0 | `__init__.py` |
| `apps.py` | 6 | `apps.py` |
| `engine.py` | 233 | `engine.py` |
| `base.py` | 105 | `generators/base.py` |
| `digital.py` | 111 | `generators/digital.py` |
| `inbound.py` | 179 | `generators/inbound.py` |
| `outbound.py` | 135 | `generators/outbound.py` |
| `gtr_engine.py` | 909 | `gtr_engine.py` |

---

## Árbol de Directorios

```
sim/
├── generators
│   ├── base.py
│   ├── digital.py
│   ├── inbound.py
│   └── outbound.py
├── management
│   └── commands
│       └── seed_agent_profiles.py
├── templates
│   └── sim
│       ├── account_editor.html
│       ├── acd_agent.html
│       ├── acd_trainner.html
│       ├── dashboard.html
│       ├── docs.html
│       ├── gtr.html
│       ├── simulator.html
│       └── training.html
├── tests
│   ├── __init__.py
│   ├── test_generators.py
│   └── test_gtr_engine.py
├── views
│   ├── __init__.py
│   ├── account_editor.py
│   ├── acd.py
│   ├── dashboard.py
│   ├── docs.py
│   ├── gtr.py
│   ├── simulator.py
│   └── training.py
├── SIM_CONTEXT.md
├── SIM_DESIGN.md
├── SIM_DEV_REFERENCE.md
├── SIM_HANDOFF_20260319.md
├── __init__.py
├── admin.py
├── apps.py
├── engine.py
├── gtr_engine.py
├── models.py
├── tests.py
├── urls.py
└── views.py
```

---

## Endpoints registrados

Fuente: `urls.py`  |  namespace: `sim`

```python
  path('',                                          simulator.simulator_list,     name='simulator_list'),
  path('api/',                                      simulator.simulator_api,      name='simulator_api'),
  path('gtr/',                                      gtr.gtr_panel,                name='gtr_panel'),
  path('gtr/start/',                                gtr.gtr_start,                name='gtr_start'),
  path('gtr/<str:session_id>/tick/',                gtr.gtr_tick,                 name='gtr_tick'),
  path('gtr/<str:session_id>/state/',               gtr.gtr_state,                name='gtr_state'),
  path('gtr/<str:session_id>/pause/',               gtr.gtr_pause,                name='gtr_pause'),
  path('gtr/<str:session_id>/resume/',              gtr.gtr_resume,               name='gtr_resume'),
  path('gtr/<str:session_id>/event/',               gtr.gtr_event,                name='gtr_event'),
  path('gtr/<str:session_id>/stop/',                gtr.gtr_stop,                 name='gtr_stop'),
  path('gtr/<str:session_id>/interactions/',        gtr.gtr_interactions,         name='gtr_interactions'),
  path('accounts/create/',                          simulator.account_create,     name='account_create'),
  path('accounts/<uuid:account_id>/delete/',        simulator.account_delete,     name='account_delete'),
  path('accounts/<uuid:account_id>/generate/',      simulator.account_generate,   name='account_generate'),
  path('accounts/<uuid:account_id>/clear/',         simulator.account_clear,      name='account_clear'),
  path('accounts/<uuid:account_id>/runs/',          simulator.account_runs,       name='account_runs'),
  path('accounts/<uuid:account_id>/kpis/',          simulator.account_kpis,       name='account_kpis'),
  path('accounts/<uuid:account_id>/export/',        simulator.export_interactions, name='export_interactions'),
  path('accounts/<uuid:account_id>/edit/',          account_editor.account_edit,        name='account_edit'),
  path('accounts/<uuid:account_id>/config/',        account_editor.account_config_save, name='account_config_save'),
  path('dashboard/',      dashboard.sim_dashboard, name='sim_dashboard'),
  path('dashboard/api/',  dashboard.dashboard_api, name='dashboard_api'),
  path('training/',                                      training.training_panel,        name='training_panel'),
  path('training/scenarios/api/',                        training.scenario_list_api,     name='scenario_list_api'),
  path('training/scenarios/create/',                     training.scenario_create,       name='scenario_create'),
  path('training/scenarios/<uuid:scenario_id>/update/',  training.scenario_update,       name='scenario_update'),
  path('training/scenarios/<uuid:scenario_id>/delete/',  training.scenario_delete,       name='scenario_delete'),
  path('training/scenarios/<uuid:scenario_id>/start/',   training.session_start,         name='session_start'),
  path('training/sessions/api/',                         training.session_list_api,      name='session_list_api'),
  path('training/sessions/<uuid:session_id>/complete/',  training.session_complete,      name='session_complete'),
  path('training/sessions/<uuid:session_id>/action/',    training.session_log_action,    name='session_log_action'),
  path('training/sessions/<uuid:session_id>/notes/',     training.session_trainer_notes, name='session_trainer_notes'),
  path('acd/',                                                    acd.acd_panel,           name='acd_panel'),
  path('acd/sessions/api/',                                       acd.acd_sessions_api,    name='acd_sessions_api'),
  path('acd/sessions/create/',                                    acd.acd_session_create,  name='acd_session_create'),
  path('acd/sessions/<uuid:session_id>/state/',                   acd.acd_session_state,   name='acd_session_state'),
  path('acd/sessions/<uuid:session_id>/start/',                   acd.acd_session_start,   name='acd_session_start'),
  path('acd/sessions/<uuid:session_id>/pause/',                   acd.acd_session_pause,   name='acd_session_pause'),
  path('acd/sessions/<uuid:session_id>/resume/',                  acd.acd_session_resume,  name='acd_session_resume'),
  path('acd/sessions/<uuid:session_id>/stop/',                    acd.acd_session_stop,    name='acd_session_stop'),
  path('acd/sessions/<uuid:session_id>/slots/add/',               acd.acd_slot_add,        name='acd_slot_add'),
  path('acd/sessions/<uuid:session_id>/slots/<uuid:slot_id>/remove/',  acd.acd_slot_remove,  name='acd_slot_remove'),
  path('acd/sessions/<uuid:session_id>/slots/<uuid:slot_id>/control/', acd.acd_slot_control, name='acd_slot_control'),
  path('acd/sessions/<uuid:session_id>/interactions/',            acd.acd_interactions,    name='acd_interactions'),
  path('acd/agent/<uuid:slot_id>/',                               acd.acd_agent_panel,     name='acd_agent_panel'),
  path('acd/agent/<uuid:slot_id>/poll/',                          acd.acd_agent_poll,      name='acd_agent_poll'),
  path('acd/agent/<uuid:slot_id>/action/',                        acd.acd_agent_action,    name='acd_agent_action'),
  path('docs/<str:doc_key>/',                            docs.docs_view,                 name='docs_view'),
```

---

## Modelos detectados

**`models.py`**

- línea 41: `class SimAccount(models.Model):`
- línea 99: `class SimAgent(models.Model):`
- línea 127: `class Interaction(models.Model):`
- línea 179: `class SimRun(models.Model):`
- línea 215: `class TrainingScenario(models.Model):`
- línea 279: `class TrainingSession(models.Model):`
- línea 332: `class SimAgentProfile(models.Model):`
- línea 477: `class ACDSession(models.Model):`
- línea 531: `class ACDAgentSlot(models.Model):`
- línea 605: `class ACDInteraction(models.Model):`
- línea 666: `class ACDAgentAction(models.Model):`


---

## Migraciones

| Archivo | Estado |
|---------|--------|
| `0001_initial` | aplicada |
| `0002_add_training` | aplicada |
| `0003_add_sim_agent_profile` | aplicada |
| `0004_remove_simagent_unique_agent_per_account_and_more` | aplicada |
| `0005_add_acd` | aplicada |
| `0006_rename_sim_acdint_sess_status_sim_acdinte_session_03abee_idx_and_more` | aplicada |

---

## Funciones clave (views/ y services/)

**`views/account_editor.py`**

```
136:def _merge_config(canal: str, saved: dict) -> dict:
161:def account_edit(request, account_id):
179:def account_config_save(request, account_id):
206:def _validate_config(canal: str, config: dict) -> list:
```

**`views/acd.py`**

```
53:def _session_row(s: ACDSession) -> dict:
74:def _slot_row(slot: ACDAgentSlot) -> dict:
104:def _interaction_row(ix: ACDInteraction) -> dict:
127:def _acd_state(session: ACDSession, gtr_state: dict = None) -> dict:
166:def slots_in_status(slots, status):
172:def _route_interaction(session: ACDSession, interaction: ACDInteraction) -> ACDAgentSlot | None:
200:def _generate_acd_interactions(session: ACDSession, n: int = 5) -> list:
247:def _get_account_tmo_acw(session: ACDSession) -> tuple:
265:def _resolve_tipificacion(session: ACDSession, conv_rate: float, agenda_rate: float) -> str:
313:def _tick_simulated_breaks(session: ACDSession):
339:def _resolve_simulated_slot(slot: ACDAgentSlot, interaction: ACDInteraction,
444:def acd_panel(request):
476:def acd_sessions_api(request):
485:def acd_session_create(request):
513:def acd_session_start(request, session_id):
553:def acd_session_state(request, session_id):
577:def _do_routing(session: ACDSession, gtr_state: dict):
620:def acd_session_pause(request, session_id):
631:def acd_session_resume(request, session_id):
642:def acd_session_stop(request, session_id):
657:def acd_slot_add(request, session_id):
687:def acd_slot_remove(request, session_id, slot_id):
699:def acd_slot_control(request, session_id, slot_id):
717:def acd_interactions(request, session_id):
736:def acd_agent_panel(request, slot_id):
```

**`views/dashboard.py`**

```
21:def sim_dashboard(request):
35:def dashboard_api(request):
```

**`views/docs.py`**

```
32:def docs_view(request, doc_key):
```

**`views/gtr.py`**

```
32:def gtr_panel(request):
56:def gtr_start(request):
84:def gtr_tick(request, session_id):
97:def gtr_state(request, session_id):
107:def gtr_pause(request, session_id):
116:def gtr_resume(request, session_id):
125:def gtr_event(request, session_id):
146:def gtr_stop(request, session_id):
158:def gtr_interactions(request, session_id):
```

**`views/simulator.py`**

```
71:def _json_safe(obj):
84:def _account_row(acc: SimAccount) -> dict:
100:def _run_row(r: SimRun) -> dict:
122:def simulator_list(request):
134:def simulator_api(request):
141:def account_create(request):
176:def account_delete(request, account_id):
184:def account_generate(request, account_id):
216:def account_clear(request, account_id):
226:def account_runs(request, account_id):
234:def account_kpis(request, account_id):
243:def export_interactions(request, account_id):
```

**`views/training.py`**

```
37:def _scenario_row(s: TrainingScenario, user=None) -> dict:
61:def _session_row(ts: TrainingSession) -> dict:
88:def _calculate_score(ts: TrainingSession, gtr_state: dict) -> dict:
158:def training_panel(request):
205:def scenario_list_api(request):
218:def scenario_create(request):
252:def scenario_update(request, scenario_id):
280:def scenario_delete(request, scenario_id):
288:def session_start(request, scenario_id):
352:def session_list_api(request):
364:def session_complete(request, session_id):
407:def session_log_action(request, session_id):
438:def session_trainer_notes(request, session_id):
```


---

## Compartir con Claude

```bash
cat /data/data/com.termux/files/home/projects/Management360/sim/views/mi_vista.py | termux-clipboard-set
```
