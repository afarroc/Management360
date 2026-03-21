# Management360 — Diseño, Roadmap y Estado de Implementación

> **Última actualización:** 2026-03-21 (Sesión Manager — Sprint 9 planificado, API-ARCH decidido)
> **Contexto:** Plataforma SaaS de Workforce Management (WFM) y Customer Experience (CX)
> **Apps activas:** 20 | **Archivos Python+HTML:** ~710
> **Metodología:** Scrum — sprints semanales sincronizados entre apps

---

## Visión General del Proyecto

Management360 es una plataforma integral de Workforce Management que combina:

- **Business Intelligence** (app `analyst`) - Procesamiento de datos, ETL, reportes, dashboards
- **Customer Experience** (app `events`) - Gestión de proyectos, tareas, inbox GTD
- **Simulación WFM** (app `sim`) - Generación de datos realistas, training, GTR, ACD
- **Simulador Urbano** (app `simcity`) - Micropolis + ABM, tablero Monopoly peruano
- **Comunicación** (apps `chat`, `rooms`) - Tiempo real, espacios virtuales
- **Aprendizaje** (app `courses`) - Sistema de cursos y lecciones
- **Métricas de Contacto** (app `kpis`) - CallRecord, AHT, SL, abandono
- **Automatización** (app `bots`) - Bots y asignación de leads
- **Campañas Outbound** (app `campaigns`) - Leads, contactos, discador
- **Perfil Profesional** (app `cv`) - Currículum dinámico
- **GTD Personal** (apps `bitacora`, `board`, `memento`) - Productividad personal
- **Utilidades** (apps `passgen`, `panel`, `help`) - Herramientas de soporte
- **API** (app `api`) - ⚠️ Consolidando en `panel` (API-ARCH Opción A aprobada 2026-03-21)

### Stack Tecnológico Unificado

| Componente | Detalle |
|------------|---------|
| Backend | Django 5.1.7 (Python 3.13) |
| Base de datos | MariaDB 12.2.2 (principal) + Redis 7 (cache/sesiones) |
| Frontend | Bootstrap 5, HTMX (interactividad parcial), Chart.js 4.4.1 |
| Tiempo real | Django Channels + Daphne 4.2.1 (ASGI) — app `chat` + `board` (pendiente activar) |
| Tiempo real (rooms) | Centrifugo (CentrifugoMixin, Outbox, CDC) — app `rooms` |
| IA local | Ollama (localhost:11434) — app `chat`, subsistema asistente |
| Procesamiento de datos | pandas, numpy, openpyxl |
| Almacenamiento | RemoteMediaStorage (dev: 192.168.18.51) / S3 (prod) |
| Cache | Redis (sesiones GTR, previews analyst, portapapeles, rate limit) |
| API | Django REST Framework (endpoints internos + rooms ViewSets) |
| Tareas asíncronas | (pendiente implementar Celery) |
| Despliegue | Termux/Daphne (dev) / Render (prod) |
| **Engine externo** | **micropolisengine (proot Ubuntu :8001) — solo para `simcity`** |

---

## Estado por Fase del Proyecto

| Fase | Descripción | Sprint | Estado |
|------|-------------|--------|--------|
| **Fase 1** | Fundación: apps core (accounts, core, panel) | S1 | ✅ |
| **Fase 2** | Gestión de proyectos y tareas (events) | S2 | ✅ |
| **Fase 3** | Comunicación en tiempo real (chat, rooms) | S3 | ✅ |
| **Fase 4** | Plataforma de datos (analyst) | S4 | ✅ |
| **Fase 5** | Simulador WFM (sim) SIM-1→SIM-7a completo (ACD multi-agente) | S5 | ✅ |
| **Fase 6** | Sistema de aprendizaje (courses) | S6 | ✅ |
| **Fase 7** | Métricas de contacto (kpis) + estabilización bitacora + simcity | S7 | ✅ |
| **Fase 8** | Automatización y bots (bots) | S8 | ✅ BOT-1/BOT-4/BOT-AUDIT |
| **Fase 9** | Optimización y escalado | S9 | 🔄 En curso |

---

## Sprint 7 — Completado ✅

### Objetivo: Optimización de KPIs + Estabilización bitacora + Integración simcity

| Tarea | Prioridad | Estado |
|-------|-----------|--------|
| **BIT-1: Refactor `models.py` bitacora** | 🔴 | ✅ |
| **BIT-2: Refactor `views.py` bitacora** | 🔴 | ✅ |
| **BIT-3: Migraciones 0003+0004 bitacora** | 🔴 | ✅ |
| **BIT-4: Refactor `bitacora_tags.py`** | 🟠 | ✅ |
| **BIT-5: Auditoría templates bitacora** | 🟡 | ✅ |
| **BIT-6: urls.py `<int:pk>` → `<uuid:pk>`** | 🟡 | ✅ |
| **SC-0: Migración simcity_web → M360 (proxy híbrido)** | 🔴 | ✅ |
| **SC-1: generate_zr_block URL+view en M360** | 🟠 | ✅ `bf037497` |
| **SC-2: mobMoneyBtn → llamar add_money API** | 🟠 | ✅ `bf037497` |
| **SC-3: EngineUnavailableError → HTTP 503** | 🔴 | ✅ `bf037497` |
| **SC-4: Nav link SimCity en sidebar core** | 🟡 | ✅ `fa01b4f9` |
| **SC-5: Slot /admin/simcity/ — GameAdmin** | 🟡 | ✅ `fa01b4f9` |
| **SC-6: Exportar partida a analyst dataset** | 🟠 | ✅ `c0f8c47c` |
| **SC-7: Script inicio automático** | 🟡 | ✅ `scripts/start_simcity.sh` |
| KPI-1: UUID PK + `fecha` DateField + 5 índices + `created_by` | 🔴 | ✅ |
| KPI-2: Cache Redis 5min `kpis:dashboard:{user}:{desde}:{hasta}` | 🔴 | ✅ |
| KPI-3: `/kpis/api/` JSON + 3 funciones WFM en Report Builder analyst | 🟠 | ✅ |
| KPI-4: Dashboard sat promedio + top/bottom servicio + total eventos | 🟠 | ✅ |
| KPI-5: `kpis_aht_report` — agrupa por agente/supervisor/canal/servicio/semana | 🟡 | ✅ |
| KPI-6: `StreamingHttpResponse` + filtros fecha + chunk_size=500 | 🟡 | ✅ |
| Namespace `kpis:` + `login_required` + nav template corregido | 🔴 | ✅ |

---

## Sprint 7.5 — Documentación ✅ COMPLETO

### Objetivo: Documentar las 20 apps del proyecto

| App | DEV_REFERENCE | DESIGN | CONTEXT | Sesión |
|-----|:---:|:---:|:---:|--------|
| `analyst` | ✅ | ✅ | ✅ | Lote 1 |
| `sim` | ✅ | ✅ | ✅ | Lote 1 |
| `bitacora` | ✅ | ✅ | ✅ | Lote 1 |
| `simcity` | ✅ | ✅ | ✅ | Lote 1 |
| `events` | ✅ | ✅ | ✅ | Lote 1 |
| `accounts` | ✅ | ✅ | ✅ auto | Lote 2 (2026-03-19) |
| `core` | ✅ | ✅ | ✅ auto | Lote 2 (2026-03-19) |
| `memento` | ✅ | ✅ | ✅ auto | Lote 2 (2026-03-19) |
| `chat` | ✅ | ✅ | ✅ auto | Lote 2 (2026-03-19) |
| `rooms` | ✅ | ✅ | ✅ auto | Lote 2 (2026-03-19) |
| `courses` | ✅ | ✅ | ✅ auto | Lote 2 (2026-03-19) |
| `bots` | ✅ | ✅ | ✅ auto | Lote 3 (2026-03-20) |
| `kpis` | ✅ | ✅ | ✅ auto | Lote 3 (2026-03-20) |
| `cv` | ✅ | ✅ | ✅ auto | Lote 3 (2026-03-20) |
| `board` | ✅ | ✅ | ✅ auto | Lote 3 (2026-03-20) |
| `campaigns` | ✅ | ✅ | ✅ auto | Lote 3 (2026-03-20) |
| `passgen` | ✅ | ✅ | ✅ auto | Lote 3 (2026-03-20) |
| `help` | ✅ | ✅ | ✅ auto | Lote 4 (2026-03-20) |
| `api` | ✅ | ✅ | ✅ auto | Lote 4 (2026-03-20) |
| `panel` | ✅ | ✅ | ✅ auto | Lote 4 (2026-03-20) |

**Bugs críticos descubiertos durante documentación (lotes 1-4):** 120 registrados (#1–#120).
**Progreso: 20 / 20 apps (100%) ✅**

---

## Sprint 8 — Completado ✅ (mínimo exitoso)

### Objetivo: Activar y conectar el sistema `bots`

| Tarea | Prioridad | Estado |
|-------|-----------|--------|
| BOT-AUDIT: Auditoría + documentación `bots` | 🔴 | ✅ |
| BOT-1: Motor de asignación de leads | 🔴 | ✅ Pipeline Lead→GTD verificado end-to-end |
| BOT-4: Dashboard de rendimiento de bots | 🟠 | ✅ HTMX poll 30s |
| EVENTS-BUG-FK: FKs events → accounts_user | 🔴 | ✅ migración 0004 |
| BOT-2: Integración bots ↔ sim | 🔴 | ⬜ Pasa a Sprint 9 |
| BOT-3: Pipeline campañas outbound | 🟠 | ⬜ Pasa a Sprint 9 |
| BOT-5: Reglas distribución por skills | 🟡 | ⬜ Pasa a Sprint 9 |

### Pre-Sprint 8 — Bugs críticos (estado final)

#### Seguridad 🔴

| ID | App | Descripción | Fix |
|----|-----|-------------|-----|
| ACC-B4 / #36 | `accounts` | Contraseña `"DefaultPassword123"` hardcodeada | `get_random_string(12)` |
| ACC-B3 / #37 | `accounts` | Open redirect — `next` sin validar | `url_has_allowed_host_and_scheme()` |
| MEM-B3 / #46 | `memento` | IDOR en `MementoConfigUpdateView` | `filter(user=request.user)` |
| CORE-SEC-1 / #43 | `core` | `url_map_view` sin `@login_required` | Agregar decorador |
| CORE-SEC-2 / #43 | `core` | `search_view` sin `@login_required` | Agregar decorador |
| ROOMS-SEC-1 / #60 | `rooms` | Vistas sin `@login_required` | Agregar decorador |
| CHAT-SEC-1 / #53 | `chat` | 20+ endpoints con `@csrf_exempt` | Eliminar, usar cookie CSRF |
| CORE-SEC-3 / #42 | `core` | `refresh_dashboard_data` con `@csrf_exempt` | Eliminar |
| BOARD-SEC-1 / #84 | `board` | `BoardDetailView` sin verificar propietario — IDOR | `get_queryset(owner=user)` |

#### Runtime 🔴

| ID | App | Descripción | Fix |
|----|-----|-------------|-----|
| ROOMS-B5 / #56 | `rooms` | `room_comments` campo `text` inexistente | `Comment.objects.create(comment=...)` |
| ROOMS-B10 / #57 | `rooms` | `navigate_room` — `str.opposite()` | Dict de opuestos |
| ROOMS-B9 / #58 | `rooms` | `calculate_new_position` EAST/WEST retorna None | Agregar ramas |
| ROOMS-B11-13 / #59 | `rooms` | 3 ViewSets ordenan por `-created_at` inexistente | Agregar campo o cambiar ordering |
| CRS-B2 / #63 | `courses` | `standalone_lessons_list` inaccesible | Mover URL |
| CRS-B4 / #64 | `courses` | `mark_lesson_complete` falla en lecciones independientes | Guard `module is None` |
| CHAT-B10 / #52 | `chat` | Template `edit_assistant_configuration.html` inexistente | Crear template |
| PASSGEN-96 / #96 | `passgen` | `password_help` — `AttributeError: CATEGORIES` | Definir `self.CATEGORIES` |
| PASSGEN-98 / #98 | `passgen` | 5/7 patrones predefinidos fallan por `MIN_ENTROPY=60` | Bajar umbral a 20 |
| BOARD-85 / #85 | `board` | `settings.BOARD_CONFIG` — KeyError si no definido | Agregar a settings |
| CV-76 / #76 | `cv` | `reverse('project_detail')` sin namespace | Corregir con `events:` |
| CV-75 / #75 | `cv` | Imports de managers a nivel de módulo en views.py | Mover a lazy imports |

---

## Sprint 9 — En curso 🔄 (inicio 2026-03-21)

### Objetivo: Estabilizar bugs críticos + completar integración bots + QA analyst

### Decisiones de arquitectura aprobadas (Manager 2026-03-21)

| ID | Decisión | Impacto |
|----|----------|---------|
| **API-ARCH** | **Opción A** — Eliminar `api/urls.py`. Consolidar todos los endpoints en `panel/urls.py`. Eliminar `include('api.urls')` del router raíz. | Bug #112 resuelto. Eliminación de duplicados. |
| **PRIORIDAD** | Bugs críticos heredados primero, luego BOT-2/3 | Estabilidad antes que features |
| **QA** | Sesión dedicada a `analyst` para cerrar INC-004 | Cerrar incidente activo |

### Orden de ejecución — Semana 1

```
Día 1     │ 🔬 Dev   → Bloque fixes críticos: passgen + board + panel (< 1h total)
Día 1-2   │ 🔬 Dev   → API-ARCH: consolidar api → panel, limpiar router raíz
Día 1-2   │ 🔬 Dev   → cv + help: romper cadena de fallo imports (#75, #76, #101)
Día 2-3   │ 🔬 Dev   → BOT-2: BotInstance ↔ ACDAgentSlot (sim)
Día 3-4   │ 🔬 Dev   → BOT-3: pipeline DiscadorLoad → LeadCampaign → Lead
Día 4     │ 📝 Doc   → help: crear 3 templates faltantes (#107)
Día 4-5   │ 🧪 QA    → analyst: tests reales — cerrar INC-004
Día 5     │ 🔬 Dev   → BOT-5 (si hay tiempo) / BIT-17
```

### Tareas Sprint 9 — detalle completo

| ID | Tarea | Rol | Prioridad | Estado |
|----|-------|-----|-----------|--------|
| **FIX-S9-1** | passgen: `self.CATEGORIES`, `MIN_ENTROPY=20`, `app_name` (#95, #96, #98) | 🔬 Dev | 🔴 | ⬜ |
| **FIX-S9-2** | board: IDOR `BoardDetailView` (#84) + `BOARD_CONFIG` en settings (#85) | 🔬 Dev | 🔴 | ⬜ |
| **FIX-S9-3** | panel: `get_connection_token` return (#114) + middleware (#115) + `@login_required` RedisTest (#117) | 🔬 Dev | 🔴 | ⬜ |
| **FIX-S9-4** | panel: `print()` → `logger.debug()` en `storages.py` (PNL-4) | 🔬 Dev | 🟠 | ⬜ |
| **API-ARCH** | Eliminar `api/urls.py`, consolidar en `panel/urls.py` (#112) | 🔬 Dev | 🔴 | ⬜ |
| **CV-1** | Lazy imports `events.management.*` en `cv/views.py` (#75) | 🔬 Dev | 🔴 | ⬜ |
| **CV-2** | `reverse('events:project_detail', ...)` con namespace (#76) | 🔬 Dev | 🔴 | ⬜ |
| **HELP-1** | Mover `from courses.models import ...` fuera del nivel módulo (#101) | 🔬 Dev | 🔴 | ⬜ |
| **HELP-2** | `@login_required` en `article_feedback_stats` (#102) + `update_fields` en save (#104) | 🔬 Dev | 🟠 | ⬜ |
| **HELP-3** | Crear 3 templates faltantes: `faq_list`, `video_tutorials`, `quick_start` (#107) | 📝 Doc/Dev | 🔴 | ⬜ |
| **BOT-2** | `BotInstance` ↔ `ACDAgentSlot` en `sim` | 🔬 Dev | 🟠 | ⬜ |
| **BOT-3** | Pipeline `DiscadorLoad → LeadCampaign → Lead` | 🔬 Dev | 🟠 | ⬜ |
| **BOT-5** | Reglas distribución por skills (`LeadDistributionRule`) | 🔬 Dev | 🟡 | ⬜ |
| **NEW-T1** | Tests reales `analyst` — cerrar INC-004 (mínimo 10 tests) | 🧪 QA | 🔴 | ⬜ |
| **SC-8** | Tests básicos proxy `simcity` | 🧪 QA | 🟡 | ⬜ |
| **SIM-7e** | Agentes simulados perfilados en ACD | 🔬 Dev | 🔴 | ⬜ sesión separada |
| **SIM-6b** | GTR Interactivo sliders | 🔬 Dev | 🟠 | ⬜ sesión separada |
| **BIT-17** | Nav prev/next filtrar por `created_by`+`is_active` | 🔬 Dev | 🟡 | ⬜ |
| **REFACTOR-1** | Dividir `rooms/views.py` (2858L) | 🔬 Dev | 🟠 | ⬜ |
| **REFACTOR-2** | Dividir `courses/views.py` (2309L) | 🔬 Dev | 🟠 | ⬜ |
| **REFACTOR-3** | Dividir `chat/views.py` (2017L) | 🔬 Dev | 🟠 | ⬜ |

### Definición de "Sprint 9 Completado"

| Nivel | Criterio |
|-------|---------|
| ✅ Mínimo | Bugs críticos #75–#117 resueltos + API-ARCH ejecutado |
| ✅ Completo | + BOT-2 + BOT-3 + INC-004 cerrado |
| ✅ Excepcional | + BOT-5 + HELP-3 + BIT-17 |

### Pendientes técnicos heredados (no bloquean Sprint 9)

| ID | App | Descripción |
|----|-----|-------------|
| SCA-1 | global | Implementar Celery para tareas asíncronas |
| SCA-2 | global | Particionamiento de tablas grandes |
| BIT-18 | `bitacora` | TinyMCE CDN usa `no-api-key` — registrar en tiny.cloud |
| ResourceLock | `bots` | `acquire_lock()` usa `timezone.timedelta` (bug heredado) |
| KPI-7 | `kpis` | Unificar `SERVICE_CHOICES` (#69) |
| KPI-8 | `kpis` | Vista upload CSV (#68) |
| BOARD-3 | `board` | CRUD completo (editar/eliminar Board) (#87) |
| CMP-1 | `campaigns` | Fix `hasattr` → `try/except` en `campaign_detail` (#93) |

---

## Integraciones Críticas entre Apps

### Matriz de Dependencias

```
accounts ──┬──> events (propietario de proyectos/tareas)
           ├──> analyst (creador de datasets)
           ├──> sim (creador de cuentas)
           ├──> simcity (propietario de partidas)
           ├──> courses (tutor de cursos)
           ├──> cv (propietario del CV)
           └──> bots (via GenericUser OneToOne)

analyst ───┬──> sim (ETL source + dashboard widgets)
           ├──> events (análisis de proyectos/tareas)
           ├──> simcity (recibe exports de partidas ✅ SC-6)
           └──> kpis (reportes avanzados de llamadas)

sim ───────┬──> analyst (datos para reportes)
           └──> bots (BOT-2 — ACDAgentSlot, ⬜ Sprint 9)

simcity ───┬──> proot:8001 (micropolisengine — engine externo)
           ├──> analyst (exportar partida ✅ SC-6)
           └──> kpis (KPIs urbanos — ⬜ SC-9)

events ────┬──> chat (notificaciones de tareas)
           ├──> rooms (salas para proyectos)
           └──> bots (InboxItem ✅ EVENTS-BUG-FK resuelto)

bots ──────┬──> events (InboxItem, Task, Project ✅)
           ├──> accounts (GenericUser OneToOne ✅)
           └──> campaigns (BOT-3 ⬜ — ContactRecord → Lead)

campaigns ──> bots (BOT-3 ⬜ — pipeline pendiente)

kpis ──────┬──> analyst (datasets de métricas)
           └──> sim (comparación con simulaciones)

courses ───┬──> cv (import directo en models.py — CRÍTICO)
           └──> analyst (análisis de progreso — pendiente)

cv ────────┬──> accounts (User OneToOne)
           └──> events (managers importados en views — Bug #75 ⬜ Sprint 9)

core ──────┬──> events (import directo — si events falla, core no carga)
           └──> ← todas las apps (provee layouts/templates globales)

chat ──────┬──> rooms (consume Room, Message, RoomMember)
           └──> rooms.Notification (⬜ pendiente CHAT-B1 / Bug #5)

board ─────> (sin dependencias externas — app independiente)
bitacora ──> events + rooms + courses (relaciones opcionales)

api ───────> panel (⚠️ API-ARCH Opción A: api/urls.py a eliminar en Sprint 9)
```

### Cadena de fallo crítica (⬜ pendiente Sprint 9)

```
events.management.* (falla)
  → cv no carga (bug #75)
      → courses no carga (import de cv)
          → help no carga (import de courses, bug #101)
```
Fix: lazy imports en `cv/views.py` + `help/models.py`.

---

## Estado de Documentación por App

| App | CONTEXT.md | DEV_REFERENCE.md | DESIGN.md | Tests | Cobertura |
|-----|:---:|:---:|:---:|-------|-----------|
| analyst | ✅ auto | ✅ | ✅ | ⚠️ stub (3L) | ❌ 0% — **INC-004 activo** |
| sim | ✅ auto | ✅ | ✅ | ✅ 3 archivos | 100% |
| bitacora | ✅ auto | ✅ | ✅ | ⚠️ stub (3L) | ❌ 0% |
| simcity | ✅ auto | ✅ | ✅ | ⚠️ stub (3L) | ❌ 0% (SC-8 pendiente) |
| events | ✅ auto | ✅ | ✅ | ✅ 9 archivos | — |
| accounts | ✅ auto | ✅ | ✅ | ✅ tests.py (212L) | — |
| core | ✅ auto | ✅ | ✅ | ✅ test_performance.py | — |
| memento | ✅ auto | ✅ | ✅ | ✅ tests.py (68L) | — |
| chat | ✅ auto | ✅ | ✅ | ❌ sin tests | — |
| rooms | ✅ auto | ✅ | ✅ | ❌ sin tests | — |
| courses | ✅ auto | ✅ | ✅ | ❌ sin tests | — |
| bots | ✅ auto | ✅ | ✅ | ⚠️ stub (3L) | ❌ 0% |
| kpis | ✅ auto | ✅ | ✅ | ❌ sin tests | — |
| cv | ✅ auto | ✅ | ✅ | ❌ sin tests | — |
| board | ✅ auto | ✅ | ✅ | ⚠️ stub (3L) | ❌ 0% |
| campaigns | ✅ auto | ✅ | ✅ | ❌ sin tests | — |
| passgen | ✅ auto | ✅ | ✅ | ❌ sin tests | — |
| help | ✅ auto | ✅ | ✅ | ⚠️ stub | ❌ 0% |
| api | ✅ auto | ✅ | ✅ | ❌ sin tests | — |
| panel | ✅ auto | ✅ | ✅ | ✅ test_urls.py (58L) | — |

**Progreso doc: 20 / 20 apps documentadas (100%) ✅**
**Cobertura real de tests: 6 / 20 apps con tests funcionales (30%)** — `sim`, `events`, `accounts`, `core`, `memento`, `panel`

---

## Incidentes Registrados

### INC-001 — 2026-03-17: `accounts_user` inexistente en BD
**Síntoma:** `500 Internal Server Error` en cualquier URL autenticada.
**Causa:** `accounts/migrations/` nunca fue commiteada.
**Resolución:** `makemigrations accounts` + INSERT manual en `django_migrations` + SQL directo.
**Prevención:** `accounts/migrations/` commiteada. `.gitignore` corregido (commit `2ea63279`).

### INC-002 — 2026-03-18: `Duplicate column name created_at` en kpis.0002
**Síntoma:** Error al aplicar migración 0002 de kpis.
**Resolución:** `RunSQL IF NOT EXISTS` + `SeparateDatabaseAndState`.

### INC-003 — 2026-03-20: API key expuesta en output de terminal
**Síntoma:** Output de `sed -n '95,110p' .env` pegado en chat incluyó `ANTHROPIC_API_KEY` en texto plano.
**Causa:** Bloque de comandos bash estaba incrustado en el `.env`.
**Resolución:** Key revocada. Nueva key generada. Bloque bash eliminado del `.env`.
**Prevención:** Nunca pegar output de `.env` directamente en chats.

### INC-004 — 2026-03-20: Tests de `analyst` inexistentes ⬜ ACTIVO
**Síntoma:** `analyst/tests.py` tiene 3 líneas (stub). El documento indicaba 34/50 tests al 68%.
**Resolución:** Pendiente — crear tests reales (NEW-T1, Sprint 9, QA prioritario).
**Impacto:** Cobertura real del proyecto es 30% (6/20 apps), no 68%.

---

## Notas para Claude

- **Fechas en `sim`:** usar `fecha` (DateField) + `hora_inicio` (DateTimeField) — NO `started_at`
- **CSRF en JS:** siempre `csrf()` desde cookie, nunca `CSRF_TOKEN` hardcoded
- **Respuestas JSON:** siempre `{"success": true/false, ...}`
- **`timedelta`:** importar desde `datetime`, NO desde `django.utils.timezone`
- **`events` usa `host`**, **`rooms` usa `owner`**, **`board` usa `owner`** — no son errores
- **`accounts/migrations/`** debe estar en git — nunca ignorar carpetas migrations
- **`accounts.User`** tiene campos extra: `phone`, `avatar`, `created_at`, `updated_at`
- **`simcity`** requiere proot Ubuntu corriendo en :8001 — sin él todos los endpoints dan 503
- **`micropolisengine`** solo disponible en `/root/micropolis/venv` (proot) — nunca importar en M360/Termux
- **`bitacora.CategoriaChoices`** es módulo-level — NO `BitacoraEntry.CategoriaChoices`
- **`core` importa directamente de `events`** — si events falla, core no carga
- **`courses` importa directamente de `cv`** — si cv falla, courses no carga
- **`cv.views` importa managers de `events` a nivel de módulo** — si events.management falla, cv no carga (bug #75 ⬜)
- **`chat.HardcodedNotificationManager`** es un stub — todas las notificaciones son falsas (bug #5/#50)
- **`passgen` solo funciona con patrones `strong` y `secure`** — los demás fallan por MIN_ENTROPY=60 (bug #98 ⬜)
- **`passgen.password_help`** siempre da 500 — `CATEGORIES` no definido (bug #96 ⬜)
- **`board.BoardDetailView`** sin verificación de propietario — IDOR activo (bug #84 ⬜)
- **`board` requiere `settings.BOARD_CONFIG`** — KeyError si no está definido (bug #85 ⬜)
- **`campaigns`** son datos globales — sin `created_by`, todos los usuarios ven todo (diseño intencional)
- **`kpis.CallRecord.created_by`** es `null=True, SET_NULL` — intencional para preservar métricas históricas
- **`board.cards.all()`** ya viene ordenado por `['-is_pinned', '-created_at']`
- **`cv.skills_list`** — el related_name es `skills_list`, NO `skills`
- **`bots` PK int** en todos los modelos — FKs desde otras apps deben usar int
- **`events.InboxItem` usa `created_by`** (no `host`) — los bots pueden crear InboxItems
- **Pipeline bots verificado end-to-end:** Lead → InboxItem → BotTaskAssignment → GTDProcessor → Task
- **`help` tiene 3 templates faltantes** — `faq_list`, `video_tutorials`, `quick_start` dan 500 al visitarlos (bug #107 ⬜)
- **`help` depende de `courses` en import de módulo** — si `courses` falla, `help` no carga (bug #101 ⬜)
- **`help.author`/`help.user`** en vez de `created_by` — es la convención de esta app
- **`api/views.py` está vacío** — toda la lógica de `/api/*` vive en `panel/views.py`
- **`api/urls.py` a eliminar** — API-ARCH Opción A aprobada 2026-03-21 (bug #112 ⬜)
- **`panel.get_connection_token` no retorna nada** — endpoint Centrifugo inaccesible (bug #114 ⬜)
- **`panel.DatabaseSelectorMiddleware`** referencia `postgres_online` y `sqlite` no definidos (bug #115 ⬜)
- **`panel.RemoteMediaStorage`** requiere `192.168.18.51:8000` activo para uploads — en offline todos los uploads fallan
- **`BOARD_CONFIG`** debe estar en `settings.py` con `CARDS_PER_PAGE` — KeyError si falta (bug #85 ⬜)
- **`CENTRIFUGO_TOKEN_SECRET`** debe estar en `.env` — requerido por `rooms` y `panel/views.get_subscription_token`
- **`panel/tests/test_urls.py`** existe (58L) — única app con tests de resolución de URLs

---

## 🔄 Handoff — Sesión 2026-03-21 (Manager)

### Completado esta sesión

- Revisión completa del estado del proyecto vs los 4 handoffs de documentación
- Detección de discrepancias en documentación (TEAM_ROLES 17/20 desactualizado, Sprint 9 sin plan formal)
- **Sprint 9 planificado en detalle** con orden de ejecución, criterios de aceptación por tarea
- **Decisiones de arquitectura aprobadas:** API-ARCH Opción A, QA prioridad INC-004, orden de prioridad Sprint 9
- Generados archivos actualizados: `PROJECT_DESIGN.md`, `TEAM_ROLES.md`, `PROJECT_DEV_REFERENCE.md`

### Pendiente antes de arrancar sesiones Dev/QA

```bash
# Push obligatorio — 15+ commits locales sin subir
git push origin main
git log --oneline -5   # verificar estado
```

### Próxima acción recomendada

**Sesión 🔬 Analista Dev — Bloque fixes críticos (Día 1)**
Subir: `passgen/generators.py` · `passgen/urls.py` · `board/views.py` · `panel/views.py` · `panel/middleware.py` · `panel/storages.py` · `settings.py`
Prompt: aplicar FIX-S9-1, FIX-S9-2, FIX-S9-3 en ese orden. Commit atómico por app.
