# Sprint 8 — Plan Detallado

> **Manager:** M360 Project
> **Fecha inicio:** 2026-03-19
> **Duración estimada:** 1 semana
> **Objetivo:** Activar y conectar el sistema `bots` con el resto de la plataforma

---

## Contexto Pre-Sprint

La app `bots` tiene infraestructura existente no documentada ni conectada:
- Motor de distribución de leads (`lead_distributor.py`) — existe pero no está validado
- Procesador GTD (`gtd_processor.py`) — existe, conexión con `events` por verificar
- Comando `run_bots.py` — ejecuta bots manualmente, sin scheduler
- 10 modelos definidos (bots + leads + campañas)
- 0 tests

**Implicación:** El sprint no es "construir desde cero" — es **auditar, conectar y estabilizar**.

---

## Orden de Ejecución

```
Semana 1:
  Día 1-2 │ BOT-AUDIT  Auditoría + documentación (Analista Doc + QA)
  Día 2-3 │ BOT-1      Motor de asignación de leads (Analista Dev)
  Día 3-4 │ BOT-2      Integración con sim (Analista Dev)
  Día 4-5 │ BOT-3      Pipeline campañas outbound (Analista Dev)
  Día 5   │ BOT-4      Dashboard rendimiento (Analista Dev)
  Día 5   │ BOT-5      Reglas por skills (Analista Dev) — si queda tiempo
```

---

## Tareas Detalladas

---

### BOT-AUDIT — Auditoría inicial (ANTES de cualquier desarrollo)
**Rol:** Analista Doc + Analista QA
**Prioridad:** 🔴 Bloquea todo lo demás
**Archivos:** models.py · views.py · lead_distributor.py · gtd_processor.py · run_bots.py

**Criterios de aceptación:**
- [ ] `BOTS_DEV_REFERENCE.md` generado
- [ ] `BOTS_DESIGN.md` generado
- [ ] Lista de bugs con severidad entregada al Manager
- [ ] Confirmado: ¿`lead_distributor.py` funciona end-to-end?
- [ ] Confirmado: ¿`gtd_processor.py` está conectado a `events.InboxItem`?
- [ ] Confirmado: ¿`run_bots.py` puede ejecutarse desde Termux sin errores?

**Brief para Analista Doc:**
```
App: bots
Subir: models.py, urls.py, views.py, lead_distributor.py, gtd_processor.py, run_bots.py
Foco extra: documentar cómo se relacionan BotCoordinator → BotInstance → BotTaskAssignment
```

---

### BOT-1 — Motor de asignación de leads
**Rol:** Analista Dev
**Prioridad:** 🔴
**Depende de:** BOT-AUDIT
**Archivos clave:** `lead_distributor.py`, `models.py` (Lead, LeadCampaign, LeadDistributionRule)

**Contexto:** `lead_distributor.py` tiene 390 líneas — revisar si implementa correctamente:
- Distribución por skills/capacidad del agente
- Balanceo de carga entre agentes disponibles
- Registro de asignaciones en `BotTaskAssignment`

**Criterios de aceptación:**
- [ ] Un lead de `LeadCampaign` puede ser asignado automáticamente a un agente
- [ ] La asignación respeta las `LeadDistributionRule` configuradas
- [ ] La asignación queda registrada en `BotTaskAssignment`
- [ ] Si no hay agente disponible, el lead queda en cola (no se pierde)
- [ ] Endpoint `POST /bots/api/campaigns/<pk>/distribute/` responde `{"success": true}`
- [ ] Mínimo 3 tests unitarios del distribuidor

**Brief para Analista Dev:**
```
App: bots
Tarea: BOT-1 — revisar y completar lead_distributor.py
Subir: models.py, lead_distributor.py, views.py, urls.py
Pregunta clave: ¿LeadDistributionRule ya se aplica en el distribuidor o es solo modelo?
```

---

### BOT-2 — Integración bots ↔ sim
**Rol:** Analista Dev
**Prioridad:** 🔴
**Depende de:** BOT-1
**Archivos clave:** `bots/models.py`, `sim/models.py` (ACDSession, ACDAgentSlot)

**Objetivo:** Los bots deben poder actuar como agentes en sesiones ACD de `sim`.

**Criterios de aceptación:**
- [ ] `BotInstance` puede registrarse como slot en `ACDSession`
- [ ] Un bot puede recibir `ACDInteraction` y responder con acción (accept/complete)
- [ ] El resultado de la interacción se registra en `BotLog`
- [ ] Endpoint o management command para activar bots en una sesión ACD
- [ ] No rompe el flujo de agentes humanos en `sim`

**Brief para Analista Dev:**
```
App: bots (principal) + sim (soporte)
Tarea: BOT-2 — conectar BotInstance con ACDAgentSlot
Subir: bots/models.py, sim/models.py (ACDSession, ACDAgentSlot, ACDInteraction)
Referencia: SIM_DEV_REFERENCE.md para entender el flujo ACD
```

---

### BOT-3 — Pipeline campañas outbound
**Rol:** Analista Dev
**Prioridad:** 🟠
**Depende de:** BOT-1
**Archivos clave:** `bots/lead_distributor.py`, `campaigns/models.py` (ProviderRawData, ContactRecord, DiscadorLoad)

**Objetivo:** Procesar registros de `campaigns` como leads distribuibles via `bots`.

**Criterios de aceptación:**
- [ ] `DiscadorLoad` → genera `LeadCampaign` automáticamente
- [ ] `ContactRecord` → genera `Lead` asociado a la campaña
- [ ] Pipeline completo: carga → distribución → asignación → log
- [ ] Vista o endpoint para disparar el pipeline manualmente
- [ ] Estado del pipeline visible en `BotLog`

---

### BOT-4 — Dashboard de rendimiento de bots
**Rol:** Analista Dev
**Prioridad:** 🟠
**Depende de:** BOT-1, BOT-2
**Archivos clave:** `bots/views.py`, `bots/models.py` (BotLog, BotTaskAssignment)

**Objetivo:** Vista web con métricas de actividad de los bots.

**Criterios de aceptación:**
- [ ] Vista `/bots/dashboard/` con login_required
- [ ] Métricas mínimas: leads asignados hoy, tasa de éxito, bots activos/inactivos
- [ ] Filtro por rango de fechas
- [ ] Datos via AJAX (endpoint `/bots/api/dashboard/`)
- [ ] Responsive con Bootstrap 5 (igual que el resto del proyecto)

---

### BOT-5 — Reglas de distribución basadas en skills
**Rol:** Analista Dev
**Prioridad:** 🟡
**Depende de:** BOT-1
**Archivos clave:** `bots/models.py` (LeadDistributionRule), `sim/models.py` (SimAgentProfile)

**Objetivo:** `LeadDistributionRule` puede filtrar agentes por skill.

**Criterios de aceptación:**
- [ ] `LeadDistributionRule` tiene campo `required_skill` (o similar)
- [ ] El distribuidor filtra agentes que no tienen el skill requerido
- [ ] Compatible con `SimAgentProfile.skills` de la app `sim`
- [ ] UI para configurar reglas desde `/bots/campaigns/<pk>/rules/`

---

## Tareas Paralelas (no bloquean el sprint)

| ID | Tarea | Rol | Prioridad |
|----|-------|-----|-----------|
| SC-8 | Tests básicos del proxy simcity | Analista QA | 🟡 |
| BIT-17 | Nav prev/next filtrar por created_by+is_active | Analista Dev | 🟡 |
| SIM-7e | Agentes simulados perfilados en ACD | Analista Dev | 🔴 — asignar sesión separada |
| SIM-6b | GTR Interactivo sliders | Analista Dev | 🟠 — asignar sesión separada |

---

## Pendiente Pre-Sprint (hacer AHORA)

```bash
# Push pendiente del sprint anterior
git push origin main

# Verificar estado
git log --oneline -5
git status --short
```

---

## Definición de "Sprint Completado"

- BOT-1 ✅ + BOT-2 ✅ + BOT-AUDIT ✅ → Sprint exitoso mínimo
- BOT-3 ✅ → Sprint completo
- BOT-4 ✅ + BOT-5 ✅ → Sprint excepcional

---

## Handoff para Próxima Sesión Manager

Al finalizar Sprint 8 actualizar:
- `PROJECT_DESIGN.md` → marcar Sprint 8 como ✅
- `TEAM_ROLES.md` → actualizar tabla de asignaciones
- Registrar incidentes si los hubo
