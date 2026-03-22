# Handoff — 2026-03-22 · Sesión multi-app

**Sprint:** 9 | **Apps tocadas:** `cv` · `analyst` · `sim`

---

## Qué se hizo

### `cv` — Actualización DEV_REFERENCE

| Acción | Detalle |
|--------|---------|
| Bugs ✅ aplicados | #73, #75, #76, #77, #78, #79, #80 |
| Único pendiente | #74 — UUID PKs (requiere migración coordinada con `courses` y `events`) |
| Archivo entregado | `CV_DEV_REFERENCE.md` |

---

### `analyst` — Actualización DEV_REFERENCE

Commits base: `ef3678e7` · `4b7a0219` (2026-03-21) + EVENTS-AI-3 + ANALYST-GTD + ANALYST-ACD

**Bugs aplicados en el DEV_REFERENCE:**

| ID | Archivo | Descripción |
|----|---------|-------------|
| #1 | `forms.py` | Comentarios huérfanos de `clean_file()` eliminados |
| #2 | `file_processor_service.py` | `process_excel()`: `@classmethod`, firma corregida, retorno `(records, preview, columns)` |
| #3 | `file_processor_service.py` | `no_header` propagado correctamente a `ExcelProcessor` |
| B-1 | `views/dashboard.py` | `Project.start_date` / `Event.start_time` → `created_at` (FieldError) |
| B-2 | `views/etl_manager.py` | `_source_row()` faltaba `events_model` → JS no podía editar fuentes events |
| B-NEW | `views/dashboard.py` | `Task order_field due_date` → `created_at` (FieldError) |
| T-1…T-4 | templates | Hints incorrectos, `get_events_model_display` sin choices, sim labels, fuente events ausente del modal |

**Features documentadas:**
- EVENTS-AI-3 end-to-end (ETL + dashboard + `_source_row`)
- GTD Overview — `POST /analyst/dashboards/gtd-overview/` — preset 6 widgets (3 KPI + 3 tablas)
- ACD widget UI — labels `[canal · status]` + hints `_SRC_TYPE_HINTS`
- Arquitectura dual Excel: `ExcelProcessor` (preview) vs `FileProcessorService` (bulk import)

| Archivo entregado | Estado |
|-------------------|--------|
| `ANALYST_DEV_REFERENCE.md` | ✅ bugs abiertos: NINGUNO |

---

### `sim` — SIM-7e + actualización DEV_REFERENCE

**Código entregado: `acd.py`**

| Cambio | Descripción |
|--------|-------------|
| `SIM_TICK_S = 60` | Constante para probabilidades por tick |
| `_get_account_tmo_acw()` | TMO/ACW desde `account.config` por canal — elimina hardcoded 313/18 |
| `_resolve_tipificacion()` | Tipificaciones reales por canal con `weighted_choice` |
| `_tick_simulated_breaks()` | `break_freq`/`break_dur_s` activos — diferencia tiers en sesiones largas |
| `_resolve_simulated_slot()` | Reescrito: `transfer_rate` activo, `available_pct` post-llamada, `agenda_rate` outbound |
| `_do_routing()` | Llama `_tick_simulated_breaks()` en cada ciclo |

Sin migraciones nuevas.

**DEV_REFERENCE actualizado:** directorio, nueva subsección "Motor de agentes simulados", convención 11, bug #11 (SIM-7e ✅), renumeración #12–#15.

---

## Estado bugs post-sesión

| App | Bugs abiertos |
|-----|--------------|
| `cv` | #74 (UUID PKs — deuda) |
| `analyst` | ninguno |
| `sim` | #5 (tests SIM-6b), #7 (acd_agent.html nivel advanced — SIM-7c) |

---

## Archivos entregados

| Archivo | App | Tipo |
|---------|-----|------|
| `CV_DEV_REFERENCE.md` | cv | Documentación |
| `ANALYST_DEV_REFERENCE.md` | analyst | Documentación |
| `acd.py` | sim | Código — `sim/views/acd.py` |
| `SIM_DEV_REFERENCE.md` | sim | Documentación |

---

## Commits pendientes

```bash
# sim — SIM-7e
git add sim/views/acd.py
git commit -m "feat(sim): SIM-7e — agentes simulados perfilados en ACD

- _get_account_tmo_acw(): TMO/ACW por canal desde account.config
- _resolve_tipificacion(): tipificaciones reales por canal via weighted_choice
- _tick_simulated_breaks(): break_freq y break_dur_s activos — diferencia tiers
- _resolve_simulated_slot(): transfer_rate activo, available_pct post-llamada
- _do_routing(): llama _tick_simulated_breaks en cada ciclo

Sprint 9 · SIM-7e completo · sin migraciones"
```

---

## Próxima sesión sugerida

| Prioridad | Tarea | Archivos necesarios |
|-----------|-------|---------------------|
| 🔴 | **SIM-7c** — pantalla agente avanzado (bug #7) | `acd_agent.html` · `SIM_DEV_REFERENCE.md` |
| 🔴 | **BOT-2** — BotInstance ↔ ACDAgentSlot | `bots/models.py` · `sim/models.py` · `BOTS_DEV_REFERENCE.md` |
| 🟠 | **BOT-3** — DiscadorLoad → LeadCampaign | `bots/` · `campaigns/` |
| 🟠 | **Bugs panel** — #114 #115 #117 | `panel/views/` · `PANEL_DEV_REFERENCE.md` |
| 🟠 | **Bugs help** — #101 #102 #104 + templates | `help/views.py` · templates |
| 🟡 | Bugs board/passgen — #84 #85 #96 #98 | archivos respectivos |
