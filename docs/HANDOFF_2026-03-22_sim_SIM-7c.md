# Handoff — 2026-03-22 · `sim` — SIM-7c

**Sprint:** 9 | **Commit:** `99a7524f` | **Bug cerrado:** #7

---

## Qué se hizo

### `sim/templates/sim/acd_agent.html`

| Bug | Severidad | Fix |
|-----|-----------|-----|
| A | 🔴 | `<div id="agent-root">` duplicado (línea 320) eliminado. Modales transfer/conference/skill movidos dentro del `#agent-root` existente antes de su cierre. Idéntico al Bug #14 de gtr.html. |
| B | 🟠 | CSS `conf-banner` añadido (púrpura, análogo al `hold-banner` amarillo). HTML del banner en `oncall-state`. Variable `CONF_ACTIVE`. `confirmConference()` activa el banner con nombre del agente. `showIdle()` lo limpia. |
| D | 🟡 | `showIdle()` resetea `tipif-sel`, `subtipif-sel` y `tipif-notes` a vacío — la próxima llamada no hereda valores de la anterior. |
| E | 🟡 | `_renderSlotList()` aplica clase `slot-disabled` (opacity 0.4, cursor not-allowed, hover neutro) a agentes `absent`/`offline`. Sin `onclick` — no seleccionables. |

### `sim/views/acd.py`

| Bug | Severidad | Fix |
|-----|-----------|-----|
| C — `transfer` | 🟠 | Guard `to_slot.status in ('absent','offline')` → `JsonResponse 400` antes de reasignar. |
| C — `conference` | 🟠 | Mismo guard para `with_slot`. |
| C — `poll` | 🟡 | `available_slots` incluye `can_transfer: bool` — frontend puede distinguir sin consulta extra. |

### `docs/team/prompts/PROMPT_ANALYST_DEV.md`

Actualizado al estado real del Sprint 9:
- Backlog limpiado: todos los bugs/features cerrados movidos a tabla "Completado"
- App count: 20 → 19 (board eliminado)
- Excepción `board` eliminada, excepción `api:` namespace añadida
- Sección `sim` nueva con estado post SIM-7e/7c y convención `can_transfer`
- Deuda técnica: solo bugs realmente abiertos (#5, #74, #105, #106, #108)

---

## Estado bugs `sim` post-sesión

| # | Estado | Descripción |
|---|--------|-------------|
| #5 | ⬜ | `tests/test_gtr_engine.py` — sin cobertura SIM-6b (7 eventos + overrides) |
| #7 | ✅ | Pantalla agente avanzado — cerrado esta sesión |

---

## Archivos modificados

```
sim/templates/sim/acd_agent.html   ← bugs A B D E
sim/views/acd.py                   ← bug C (transfer + conference + poll)
docs/team/prompts/PROMPT_ANALYST_DEV.md  ← actualización Sprint 9
```

---

## Commits

```bash
# SIM-7c — ya pusheado
# 99a7524f  feat(sim): SIM-7c ✅ — pantalla agente avanzado operativa

# PROMPT — pendiente
git add docs/team/prompts/PROMPT_ANALYST_DEV.md
git commit -m "docs: PROMPT_ANALYST_DEV actualizado — Sprint 9 estado real 2026-03-22"
git push origin main
```

---

## Próxima sesión

**BOT-2** 🔴 — BotInstance ↔ ACDAgentSlot

Objetivo: los bots (BotInstance) pueden actuar como agentes en una sesión ACD de `sim`.
Un BotInstance se registra como `ACDAgentSlot` con `agent_type='simulated'` y un perfil
`SimAgentProfile` asignado automáticamente según su `specialization`.

Archivos a adjuntar:
```bash
cat bots/models.py                 # BotInstance, BotCoordinator, GenericUser
cat sim/models.py                  # ACDSession, ACDAgentSlot, SimAgentProfile
cat bots/BOTS_DEV_REFERENCE.md
cat sim/SIM_DEV_REFERENCE.md
# + PROMPT_ANALYST_DEV.md actualizado
```

Considerar también para la misma sesión si queda tiempo:
- **BOT-3** 🟠 — DiscadorLoad → LeadCampaign → Lead
  - Archivos extra: `bots/utils.py` · `campaigns/models.py`
