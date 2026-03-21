# Equipo de Análisis — Management360

> **Actualizado:** 2026-03-21 (Sesión Manager — Sprint 9 planificado, API-ARCH decidido)
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

## Asignaciones — Sprint 9 (activo desde 2026-03-21)

### Decisiones de arquitectura aprobadas (Manager 2026-03-21)

| ID | Decisión |
|----|----------|
| API-ARCH | **Opción A** — Eliminar `api/urls.py`, consolidar en `panel/urls.py`. Eliminar `include('api.urls')` del router raíz. |
| PRIORIDAD | Bugs críticos heredados primero → BOT-2/3 → resto |
| QA Sprint 9 | Sesión dedicada a `analyst` — cerrar INC-004 |

---

### Dev — Semana 1 (orden de ejecución)

| Día | App(s) | Tarea | ID | Prioridad |
|-----|--------|-------|----|-----------|
| 1 | `passgen`, `board`, `panel` | Bloque fixes críticos | #84, #85, #95, #96, #98, #114, #115, #117, PNL-4 | 🔴 |
| 1-2 | `api` + `panel` | API-ARCH Opción A — consolidar urls | API-ARCH | 🔴 |
| 1-2 | `cv` + `help` | Romper cadena de fallo imports | #75, #76, #101, #102, #104 | 🔴 |
| 2-3 | `bots` + `sim` | BOT-2: BotInstance ↔ ACDAgentSlot | BOT-2 | 🟠 |
| 3-4 | `bots` + `campaigns` | BOT-3: pipeline DiscadorLoad → LeadCampaign | BOT-3 | 🟠 |
| 4 | `help` | Crear 3 templates faltantes | #107 | 🔴 |
| 5 | `bots` | BOT-5: reglas por skills (si hay tiempo) | BOT-5 | 🟡 |

### Dev — Backlog Sprint 9

| App | Tarea | ID | Prioridad |
|-----|-------|----|-----------|
| `sim` | Agentes simulados perfilados en ACD | SIM-7e | 🔴 sesión separada |
| `sim` | GTR Interactivo sliders | SIM-6b | 🟠 sesión separada |
| `bitacora` | Nav prev/next filtrado | BIT-17 | 🟡 |
| `rooms` | Dividir views.py (2858L) | REFACTOR-1 | 🟠 |
| `courses` | Dividir views.py (2309L) | REFACTOR-2 | 🟠 |
| `chat` | Dividir views.py (2017L) | REFACTOR-3 | 🟠 |

### Dev — Bugs críticos heredados pendientes (seguridad)

| Bug | App | Descripción | Prioridad |
|-----|-----|-------------|-----------|
| #84 | `board` | IDOR — `BoardDetailView` sin verificar propietario | 🔴 |
| #96 | `passgen` | `password_help` siempre 500 — `CATEGORIES` no definido | 🔴 |
| #98 | `passgen` | `MIN_ENTROPY=60` bloquea 5/7 patrones | 🔴 |
| #114 | `panel` | `get_connection_token` sin return — Centrifugo roto | 🔴 |
| #75 | `cv` | Managers de `events` importados a nivel de módulo | 🔴 |
| #76 | `cv` | `reverse('project_detail')` sin namespace | 🔴 |
| #107 | `help` | 3 templates faltantes → TemplateDoesNotExist | 🔴 |
| #101 | `help` | Import `courses` a nivel módulo — cadena de fallo | 🔴 |
| #115 | `panel` | `DatabaseSelectorMiddleware` con BDs inexistentes | 🟠 |
| #117 | `panel` | `RedisTestView` sin `@login_required` | 🟠 |
| #36 | `accounts` | Contraseña `"DefaultPassword123"` hardcodeada | 🔴 |
| #37 | `accounts` | Open redirect en `login_view` — `next` sin validar | 🔴 |
| #46 | `memento` | IDOR en `MementoConfigUpdateView` | 🔴 |
| #43 | `core` | `search_view` y `url_map_view` sin `@login_required` | 🔴 |

### QA — Sprint 9

| App | Tarea | Estado | Prioridad |
|-----|-------|--------|-----------|
| `analyst` | Tests reales — cerrar INC-004 (stub de 3 líneas) | ⬜ **PRIORIDAD** | 🔴 |
| `simcity` | SC-8: tests básicos proxy | ⬜ Paralelo | 🟡 |
| `chat` | Tests — 0 cobertura actual | ⬜ | 🟠 |
| `rooms` | Tests — 0 cobertura actual | ⬜ | 🟠 |
| `courses` | Tests — 0 cobertura actual | ⬜ | 🟠 |

### Doc — Sprint 9

**Documentación 20/20 completada ✅ — sin tareas pendientes para Analista Doc en Sprint 9.**

---

## Historial de Sprints

### Sprint 8 — Completado ✅ (2026-03-19 → 2026-03-20)

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

### Sprint 7.5 — Documentación ✅ COMPLETO (2026-03-19 → 2026-03-20)

| Lote | Apps | Bugs registrados |
|------|------|-----------------|
| Lote 1 | analyst, sim, bitacora, simcity, events | #1–#35 |
| Lote 2 | accounts, core, memento, chat, rooms, courses | #36–#67 |
| Lote 3 | bots (revisión), kpis, cv, board, campaigns, passgen | #68–#99 |
| Lote 4 | help, api, panel | #100–#120 |

**Resultado: 20 / 20 apps documentadas (100%) ✅ — 120 bugs registrados**

---

## Documentación — Estado final

| App | DEV_REFERENCE | DESIGN | Tests |
|-----|:---:|:---:|-------|
| analyst | ✅ | ✅ | ⚠️ stub — **INC-004 activo** |
| sim | ✅ | ✅ | ✅ 100% |
| bitacora | ✅ | ✅ | ⚠️ stub |
| simcity | ✅ | ✅ | ⚠️ stub |
| events | ✅ | ✅ | ✅ |
| accounts | ✅ | ✅ | ✅ |
| core | ✅ | ✅ | ✅ |
| memento | ✅ | ✅ | ✅ |
| chat | ✅ | ✅ | ❌ |
| rooms | ✅ | ✅ | ❌ |
| courses | ✅ | ✅ | ❌ |
| bots | ✅ | ✅ | ⚠️ stub |
| kpis | ✅ | ✅ | ❌ |
| cv | ✅ | ✅ | ❌ |
| board | ✅ | ✅ | ⚠️ stub |
| campaigns | ✅ | ✅ | ❌ |
| passgen | ✅ | ✅ | ❌ |
| help | ✅ | ✅ | ⚠️ stub |
| api | ✅ | ✅ | ❌ |
| panel | ✅ | ✅ | ✅ test_urls.py (58L) |

**Documentación: 20 / 20 apps (100%) ✅**
**Cobertura tests real: 6 / 20 apps (30%) — analyst stub no cuenta**

---

## Reglas de Operación

1. **Una sesión = un rol = un foco** — no mezclar
2. **Siempre cargar el contexto completo** al inicio de sesión (ver prompts)
3. **Siempre terminar con un handoff** — qué se hizo, qué queda pendiente
4. **Los bugs se registran siempre** — aunque no se resuelvan en la sesión — numeración desde #121
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
| PK | `UUIDField` | `events` (int), `simcity`/`bots`/`board`/`cv`/`help` (AutoField int), `campaigns` mixto |
| Propietario | `created_by` | `events` → `host`; `rooms` → `owner`/`creator`; `courses` → `tutor`/`author`; `chat`/`memento` → `user`; `board` → `owner`; `cv` → `user` OneToOne; `help` → `author`/`user`; `campaigns` → sin propietario (global) |
| Timestamps | `created_at`/`updated_at` | `bitacora` en español; `board.Activity` → `timestamp`; `campaigns` → `upload_date`/`load_date` |
| Namespace `app_name` | declarado en urls.py | `core`, `events`, `memento` (include externo); `passgen` (bug #95 — pendiente fix) |
| Respuesta JSON | `{"success": true/false}` | — |
| `@csrf_exempt` | PROHIBIDO en POST con datos | `chat` (20+ endpoints bug #53), `core` (bug #42) |
| `api/urls.py` | consolidado en `panel` | **API-ARCH Opción A aprobada 2026-03-21** — eliminar `include('api.urls')` |
