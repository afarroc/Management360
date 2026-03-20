# Equipo de Análisis — Management360

> **Actualizado:** 2026-03-20 (sesión Analista Doc — lote 3: kpis, cv, board, campaigns, passgen)
> **Proyecto:** Management360 — Django 5.1.7 / 20 apps / ~710 archivos
> **Metodología:** Sprints semanales | Sesiones Claude especializadas por rol

---

## Estructura del Equipo

```
📋 MANAGER
└── Visión general, prioridades, coordinación entre roles

    ├── 🔬 ANALISTA DEV
    │   └── Análisis de código, desarrollo, refactor, nuevas features
    │
    ├── 🧪 ANALISTA QA
    │   └── Tests, bugs, cobertura, estabilidad
    │
    └── 📝 ANALISTA DOC
        └── Documentación técnica, context maps, dev references
```

Cada rol es una **sesión Claude dedicada**. Una sesión = un rol = un foco.
No mezclar roles en la misma sesión.

---

## Roles y Responsabilidades

### 📋 MANAGER

**Responsabilidades:**
- Definir prioridades de sprint
- Asignar apps a analistas
- Revisar entregables de cada sesión
- Mantener `PROJECT_DESIGN.md` actualizado
- Tomar decisiones de arquitectura
- Aprobar cambios que afecten múltiples apps
- Coordinar el handoff entre sesiones

**Prompt:** `docs/team/prompts/PROMPT_MANAGER.md`
**Contexto a cargar:** `PROJECT_CONTEXT.md` · `PROJECT_DESIGN.md` · `PROJECT_DEV_REFERENCE.md` · `TEAM_ROLES.md`

---

### 🔬 ANALISTA DEV

**Responsabilidades:**
- Analizar código de una app específica
- Implementar features del sprint activo
- Refactorizar código con deuda técnica
- Resolver bugs asignados
- Escribir código siguiendo convenciones del proyecto
- Reportar hallazgos al Manager al final de sesión

**Foco por sesión:** UNA app principal + máximo una de soporte.
**NO hace:** Tests (QA), documentación formal (DOC), decisiones de prioridad (Manager).

**Prompt:** `docs/team/prompts/PROMPT_ANALYST_DEV.md`
**Contexto a cargar:** `PROJECT_DEV_REFERENCE.md` + `APP_DEV_REFERENCE.md` de la app asignada + fuentes relevantes

---

### 🧪 ANALISTA QA

**Responsabilidades:**
- Escribir tests para apps sin cobertura
- Reproducir y documentar bugs reportados
- Auditar N+1 queries, imports incorrectos, patrones inseguros
- Mantener sección de bugs en `PROJECT_DEV_REFERENCE.md`

**Foco por sesión:** UNA app o UN módulo específico.
**NO hace:** Features nuevas, refactor mayor, decisiones de diseño.

**Prompt:** `docs/team/prompts/PROMPT_ANALYST_QA.md`
**Contexto a cargar:** `PROJECT_DEV_REFERENCE.md` + `APP_DEV_REFERENCE.md` + fuentes

---

### 📝 ANALISTA DOC

**Responsabilidades:**
- Generar `APP_DEV_REFERENCE.md` y `APP_DESIGN.md`
- Identificar deuda técnica y clasificarla
- Documentar decisiones de arquitectura

**Foco por sesión:** UNA o DOS apps relacionadas.
**NO hace:** Código de producción, tests, decisiones de prioridad.

**Prompt:** `docs/team/prompts/PROMPT_ANALYST_DOC.md`
**Contexto a cargar:** `PROJECT_DEV_REFERENCE.md` + `PROJECT_DESIGN.md` + fuentes de la app
**Referencia de formato:** `KPIS_DEV_REFERENCE.md` · `CV_DEV_REFERENCE.md` · `BOARD_DEV_REFERENCE.md`

---

## Asignaciones — Sprint 9 (activo)

### Dev — Pasan de Sprint 8

| App | Tarea | Rol | Estado |
|-----|-------|-----|--------|
| `bots` | BOT-2: integración bots ↔ sim | 🔬 Analista Dev | ⬜ Espera sesión |
| `bots` | BOT-3: pipeline campañas outbound | 🔬 Analista Dev | ⬜ Espera BOT-2 |
| `bots` | BOT-5: reglas distribución por skills | 🔬 Analista Dev | ⬜ Espera BOT-1 |
| `sim` | SIM-7e: agentes simulados perfilados en ACD | 🔬 Analista Dev | ⬜ Sesión separada |
| `sim` | SIM-6b: GTR Interactivo sliders | 🔬 Analista Dev | ⬜ Sesión separada |
| `bitacora` | BIT-17: nav prev/next filtrar por created_by+is_active | 🔬 Analista Dev | ⬜ Sesión separada |

### Dev — Fixes críticos heredados (bugs #36–#99)

| Bug | App | Descripción | Prioridad |
|-----|-----|-------------|-----------|
| #84 | `board` | IDOR — `BoardDetailView` sin verificar propietario | 🔴 |
| #96 | `passgen` | `password_help` siempre 500 — `CATEGORIES` no definido | 🔴 |
| #98 | `passgen` | `MIN_ENTROPY=60` bloquea 5/7 patrones | 🔴 |
| #85 | `board` | `BOARD_CONFIG` no definido en settings — KeyError | 🔴 |
| #75 | `cv` | Managers de `events` importados a nivel de módulo | 🔴 |
| #76 | `cv` | `reverse('project_detail')` sin namespace — NoReverseMatch | 🔴 |
| #95 | `passgen` | Sin `app_name` en urls.py | 🟡 |
| #97 | `passgen` | `PasswordForm.length` y `exclude_ambiguous` nunca leídos | 🟠 |

### QA — Pendiente

| App | Tarea | Rol | Estado |
|-----|-------|-----|--------|
| `simcity` | SC-8: tests básicos proxy | 🧪 Analista QA | ⬜ Paralelo |
| `chat` | Tests — 0 cobertura actual | 🧪 Analista QA | ⬜ |
| `rooms` | Tests — 0 cobertura actual | 🧪 Analista QA | ⬜ |
| `courses` | Tests — 0 cobertura actual | 🧪 Analista QA | ⬜ |
| `analyst` | Tests reales — stub 3 líneas (INC-004) | 🧪 Analista QA | ⬜ |

### Doc — Última tanda (3 apps pendientes)

| App | Complejidad | Rol | Estado |
|-----|-------------|-----|--------|
| `help` | 🟠 Media — 7 modelos, 10 endpoints | 📝 Analista Doc | ⬜ **PRÓXIMA SESIÓN** |
| `api` | 🟢 Baja — 0 modelos, 4 endpoints | 📝 Analista Doc | ⬜ **PRÓXIMA SESIÓN** |
| `panel` | 🟡 Media — 0 modelos, 28 endpoints | 📝 Analista Doc | ⬜ **PRÓXIMA SESIÓN** |

---

## Documentación Completada — 17 / 20 apps (85%)

| App | DEV_REFERENCE | DESIGN | Sesión | Bugs registrados |
|-----|:---:|:---:|--------|-----------------|
| `analyst` | ✅ | ✅ | Lote 1 | — |
| `sim` | ✅ | ✅ | Lote 1 | — |
| `bitacora` | ✅ | ✅ | Lote 1 | — |
| `simcity` | ✅ | ✅ | Lote 1 | — |
| `events` | ✅ | ✅ | Lote 1 | — |
| `accounts` | ✅ | ✅ | Lote 2 (2026-03-19) | #36, #37 |
| `core` | ✅ | ✅ | Lote 2 (2026-03-19) | #42, #43 |
| `memento` | ✅ | ✅ | Lote 2 (2026-03-19) | #46 |
| `chat` | ✅ | ✅ | Lote 2 (2026-03-19) | #50–#55 |
| `rooms` | ✅ | ✅ | Lote 2 (2026-03-19) | #56–#67 |
| `courses` | ✅ | ✅ | Lote 2 (2026-03-19) | — |
| `bots` | ✅ revisado | ✅ revisado | Lote 3 (2026-03-20) — Sprint 8 audit | — |
| `kpis` | ✅ | ✅ | Lote 3 (2026-03-20) | #68–#72 |
| `cv` | ✅ | ✅ | Lote 3 (2026-03-20) | #73–#80 |
| `board` | ✅ | ✅ | Lote 3 (2026-03-20) | #81–#89 |
| `campaigns` | ✅ | ✅ | Lote 3 (2026-03-20) | #90–#94 |
| `passgen` | ✅ | ✅ | Lote 3 (2026-03-20) | #95–#99 |
| `help` | ⬜ | ⬜ | Pendiente lote 4 | — |
| `api` | ⬜ | ⬜ | Pendiente lote 4 | — |
| `panel` | ⬜ | ⬜ | Pendiente lote 4 | — |

**Bugs registrados globales: #1–#99 (99 bugs). Próximos desde #100.**

---

## Sprint 8 — Completado ✅ (2026-03-19 → 2026-03-20)

| Tarea | Estado |
|-------|--------|
| BOT-AUDIT: auditoría + documentación `bots` | ✅ |
| BOT-1: motor de asignación de leads | ✅ Pipeline Lead→GTD verificado end-to-end |
| BOT-4: dashboard de rendimiento de bots | ✅ HTMX poll 30s |
| EVENTS-BUG-FK: FKs events → accounts_user | ✅ migración 0004 |
| BOT-2: integración bots ↔ sim | ⏭️ Pasa a Sprint 9 |
| BOT-3: pipeline campañas outbound | ⏭️ Pasa a Sprint 9 |
| BOT-5: reglas distribución por skills | ⏭️ Pasa a Sprint 9 |
| DOC Sprint 7.5: lote 3 (kpis, cv, board, campaigns, passgen) | ✅ |

---

## Reglas de Operación

1. **Una sesión = un rol = un foco** — no mezclar
2. **Siempre cargar el contexto completo** al inicio de sesión (ver prompts)
3. **Siempre terminar con un handoff** — qué se hizo, qué queda pendiente
4. **Los bugs se registran siempre** — aunque no se resuelvan en la sesión — numeración desde #100
5. **El Manager aprueba** cambios de arquitectura o que afecten múltiples apps
6. **Commits atómicos** — un commit por tarea, mensaje descriptivo
7. **Documentar antes de desarrollar** — no tocar una app sin su DEV_REFERENCE

---

## Stack de Referencia Rápida

| Componente | Detalle |
|------------|---------|
| Backend | Django 5.1.7 (Python 3.13) |
| DB | MariaDB 12.2.2 + Redis 7 |
| Frontend | Bootstrap 5 + HTMX + Chart.js 4.4.1 |
| RT (chat) | Django Channels + Daphne 4.2.1 |
| RT (rooms) | Centrifugo (CentrifugoMixin, Outbox, CDC) |
| RT (board) | Django Channels — infraestructura lista, sin activar (bug #86) |
| IA local | Ollama (localhost:11434) — app `chat` |
| Entorno dev | Termux / Android 15 / Lineage OS 22.2 |
| Repo | GitHub — branch main |

### Excepciones de convención (tabla consolidada)

| Convención | Estándar | Excepciones |
|------------|----------|-------------|
| PK | `UUIDField` | `events` (int), `simcity`/`bots`/`board`/`cv` (AutoField int), `campaigns` mixto |
| Propietario | `created_by` | `events` → `host`; `rooms` → `owner`/`creator`; `courses` → `tutor`/`author`; `chat`/`memento` → `user`; `board` → `owner`; `cv` → `user` OneToOne; `campaigns` → sin propietario (global) |
| Timestamps | `created_at`/`updated_at` | `bitacora` en español; `board.Activity` → `timestamp`; `campaigns` → `upload_date`/`load_date` |
| Namespace `app_name` | declarado en urls.py | `core`, `events`, `memento` (include externo); `passgen` (bug #95) |
| Respuesta JSON | `{"success": true/false}` | — |
| `@csrf_exempt` | PROHIBIDO en POST con datos | `chat` (20+ endpoints bug #53), `core` (bug #42) |
