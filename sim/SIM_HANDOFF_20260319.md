# SIM — Handoff Sesión 2026-03-19

> **App:** `sim` · **Sesión:** Sprint 3 cierre + Sprint 4 mantenimiento
> **Próxima sesión:** Sprint 5 — SIM-7e + SIM-7c
> **Commit pendiente:** ver sección final

---

## Completado esta sesión

### `sim/views/acd.py` — 4 bugs corregidos

| # | Función | Fix |
|---|---------|-----|
| 6 | `_generate_acd_interactions()` | `account.config.get(canal)` → `(config or {}).get(canal, {})` + fallbacks de skill por canal (`GENERAL`/`OUTBOUND`/`DIGITAL`) |
| 8 | `_get_tipificaciones()` | Agregada rama `digital` (`tipificaciones_bxi` + `tipificaciones_app`). Fallback activado solo si lista vacía, no siempre |
| 9 | `acd_agent_poll()` | Indentación rota en bloque `available_slots` — 0 spaces → 4 spaces dentro de la función |
| 10 | Top del archivo | `get_user_model()` inline en 2 funciones → movido al tope, `User = get_user_model()` global |

### `sim/views/gtr.py` — 1 fix

| Fix | Descripción |
|-----|-------------|
| `gtr_panel()` | `DEFAULT_THRESHOLDS_OUTBOUND` agregado al contexto del template — los inputs `thr-contact-input` y `thr-conv-input` del modal ahora renderizan `22.0` y `0.5` en lugar de vacío |

### `sim/templates/sim/gtr.html` — SIM-6b completo (3 fixes + 1 regresión)

| Fix | Descripción |
|-----|-------------|
| CSRF | `csrf()` desde `querySelector('[name=csrfmiddlewaretoken]')` → cookie (convención del proyecto) |
| DOM | `<div id="gtr-root">` duplicado eliminado. Modal movido **dentro** del `#gtr-root` existente antes de su cierre — el CSS scoped `#gtr-root .modal` aplica correctamente |
| CSS | `.events-panel` sin marco visual → agregado `background`, `border`, `border-radius`, `padding` |
| Regresión | Fix anterior sacó el modal del scope → botón "Iniciar sesión" dejó de abrir el modal. Corregido reubicando el modal dentro del root |

### Documentación actualizada

- `SIM_DESIGN.md` — SIM-6b ✅, Sprint 3 ✅, B-03/B-04 ✅, bugs y handoff actualizados
- `SIM_DEV_REFERENCE.md` — bugs #6–#14 registrados, fecha actualizada

---

## Estado final de sprints

| Sprint | Estado | Contenido |
|--------|--------|-----------|
| S1 | ✅ | SIM-1/2/3 — generadores, GTR engine, account editor |
| S2 | ✅ | SIM-4/4b/5 — ETL, dashboard widgets, training mode |
| S3 | ✅ | SIM-6a/6b — persistencia GTR, SimAgentProfile, controles interactivos |
| S4 | ✅ | SIM-7a/b/d — ACD multi-agente, pantalla OJT básico/intermedio, dashboard trainer |
| S5 | ⬜ | SIM-7e/7c — agentes perfilados, pantalla avanzada |

---

## Bugs pendientes en `sim`

| # | Archivo | Descripción | Target |
|---|---------|-------------|--------|
| 5 | `tests/test_gtr_engine.py` | Sin cobertura para 7 eventos SIM-6b ni overrides en generadores | S9 |
| 7 | `acd_agent.html` | Nivel `advanced` sin implementar — transfer/conference/hold visual | SIM-7c |

---

## Próxima sesión — Sprint 5

**Tareas en orden de prioridad:**

1. **SIM-7e** 🔴 — Agentes simulados perfilados en ACD
   - `_resolve_simulated_slot()` ya lee `SimAgentProfile` pero el motor de tick no diferencia bien entre tiers en sesiones largas
   - Sin migración nueva — `SimAgentProfile` (migración 0003) ya existe
   - Archivos: `sim/views/acd.py` + `sim/models.py`

2. **SIM-7c** 🟠 — Pantalla agente avanzado
   - Backend completo (`transfer`, `conference`, `unhold` en `acd_agent_action`)
   - `acd_agent_poll()` ya devuelve `available_slots` para nivel advanced
   - Solo falta frontend: `sim/templates/sim/acd_agent.html`
   - Bug #7 queda cerrado al completar SIM-7c

3. **Bug #5** 🟡 — Tests SIM-6b (si queda tiempo)
   - `tests/test_gtr_engine.py` — agregar los 7 eventos nuevos + overrides

---

## Archivos modificados esta sesión

```
sim/views/acd.py
sim/views/gtr.py
sim/templates/sim/gtr.html
sim/SIM_DESIGN.md
sim/SIM_DEV_REFERENCE.md
```

## Commit pendiente

```bash
git add sim/views/acd.py \
        sim/views/gtr.py \
        sim/templates/sim/gtr.html \
        sim/SIM_DESIGN.md \
        sim/SIM_DEV_REFERENCE.md

git commit -m "sim: SIM-6b ✅ + acd.py bug fixes (config fallback, tipif digital, indent, imports)

- gtr.html: csrf desde cookie, modal dentro de #gtr-root, events-panel con marco
- gtr.py: DEFAULT_THRESHOLDS_OUTBOUND en contexto del template
- acd.py: fallback config por canal, rama digital en tipificaciones,
  indentación acd_agent_poll, get_user_model al tope"

git push origin main
```

---

## Archivos para próxima sesión

```bash
cat sim/models.py                          | termux-clipboard-set
cat sim/views/acd.py                       | termux-clipboard-set
cat sim/templates/sim/acd_agent.html       | termux-clipboard-set
cat sim/templates/sim/acd_trainner.html    | termux-clipboard-set  # si SIM-7e toca el grid
```

Adjuntar también: `SIM_DESIGN.md` · `SIM_DEV_REFERENCE.md` · `SIM_CONTEXT.md` · `PROJECT_DEV_REFERENCE.md`
