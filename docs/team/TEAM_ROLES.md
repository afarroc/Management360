# Equipo de Análisis — Management360

> **Actualizado:** 2026-03-19 (sesión Manager tarde)
> **Proyecto:** Management360 — Django 5.1 / 20 apps / ~710 archivos
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
**Referencia de formato:** `EVENTS_DEV_REFERENCE.md` + `EVENTS_DESIGN.md`

---

## Asignaciones — Sprint 8 (2026-03-19 →)

### Activas

| App | Tarea | Rol | Estado |
|-----|-------|-----|--------|
| `bots` | BOT-AUDIT: auditoría + documentación | 📝 Analista Doc | ⬜ **PRÓXIMA SESIÓN** |
| `bots` | BOT-1: motor asignación de leads | 🔬 Analista Dev | ⬜ Espera BOT-AUDIT |
| `bots` | BOT-2: integración con sim | 🔬 Analista Dev | ⬜ Espera BOT-1 |
| `bots` | BOT-3: pipeline campañas outbound | 🔬 Analista Dev | ⬜ Espera BOT-1 |
| `bots` | BOT-4: dashboard rendimiento | 🔬 Analista Dev | ⬜ Espera BOT-1+2 |
| `bots` | BOT-5: reglas por skills | 🔬 Analista Dev | ⬜ Espera BOT-1 |
| `sim` | SIM-7e: agentes simulados perfilados | 🔬 Analista Dev | ⬜ Sesión separada |
| `sim` | SIM-6b: GTR Interactivo sliders | 🔬 Analista Dev | ⬜ Sesión separada |
| `bitacora` | BIT-17: nav prev/next por created_by | 🔬 Analista Dev | ⬜ Sesión separada |
| `simcity` | SC-8: tests básicos proxy | 🧪 Analista QA | ⬜ Paralelo |

### Documentación pendiente (Tier 1 — críticas)

| App | Rol | Estado |
|-----|-----|--------|
| `chat` | 📝 Analista Doc | ⬜ |
| `rooms` | 📝 Analista Doc | ⬜ |

### Documentación pendiente (Tier 2)

| App | Rol | Estado |
|-----|-----|--------|
| `courses` | 📝 Analista Doc | ⬜ |
| `cv` | 📝 Analista Doc | ⬜ |
| `core` | 📝 Analista Doc | ⬜ |
| `accounts` | 🧪 Analista QA | ⬜ |

### Documentación pendiente (Tier 3 — infraestructura)

| App | Rol | Estado |
|-----|-----|--------|
| `panel` | 📝 Analista Doc | ⬜ |
| `campaigns` | 📝 Analista Doc | ⬜ |
| `help` | 📝 Analista Doc | ⬜ |
| `memento` | 📝 Analista Doc | ⬜ |
| `passgen` | 📝 Analista Doc | ⬜ |
| `api` | 📝 Analista Doc | ⬜ |
| `board` | 📝 Analista Doc | ⬜ |

---

## Documentación Completada

| App | DEV_REFERENCE | DESIGN | Sesión |
|-----|--------------|--------|--------|
| `analyst` | ✅ | ✅ | Anterior |
| `sim` | ✅ | ✅ | Anterior |
| `bitacora` | ✅ | ✅ | Anterior |
| `simcity` | ✅ | ✅ | Anterior |
| `events` | ✅ | ✅ | 2026-03-19 tarde |

---

## Reglas de Operación

1. **Una sesión = un rol = un foco** — no mezclar
2. **Siempre cargar el contexto completo** al inicio de sesión (ver prompts)
3. **Siempre terminar con un handoff** — qué se hizo, qué queda pendiente
4. **Los bugs se registran siempre** — aunque no se resuelvan en la sesión
5. **El Manager aprueba** cambios de arquitectura o que afecten múltiples apps
6. **BOT-AUDIT primero** — no desarrollar en `bots` sin auditoría previa
7. **Commits atómicos** — un commit por tarea, mensaje descriptivo

---

## Stack de Referencia Rápida

| Componente | Detalle |
|------------|---------|
| Backend | Django 5.1.7 (Python 3.13) |
| DB | MariaDB 12.2.2 + Redis 7 |
| Frontend | Bootstrap 5 + HTMX + Chart.js 4.4.1 |
| RT | Django Channels + Daphne 4.2.1 |
| Entorno dev | Termux / Android 15 / Lineage OS 22.2 |
| Repo | GitHub — branch main |
| PK estándar | UUIDField (excepto `events` int y `simcity` AutoField) |
| Propietario estándar | `created_by` (excepto `events`: host, `rooms`: owner) |
| Respuesta JSON | `{"success": true/false, ...}` siempre |
