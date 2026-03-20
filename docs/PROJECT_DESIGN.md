# Management360 — Diseño, Roadmap y Estado de Implementación

> **Última actualización:** 2026-03-20 (Sesión Analista Doc — lote 4: help, api, panel — documentación 20/20 ✅)
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
- **Utilidades** (apps `passgen`, `api`, `panel`, `help`) - Herramientas de soporte

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
| **Fase 9** | Optimización y escalado | S9 | ⬜ |

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
| KPI-1: UUID PK + `fecha` DateField + 5 índices + `created_by` (MySQL IF NOT EXISTS) | 🔴 | ✅ |
| KPI-2: Cache Redis 5min `kpis:dashboard:{user}:{desde}:{hasta}`, colores fijos | 🔴 | ✅ |
| KPI-3: `/kpis/api/` JSON + 3 funciones WFM en Report Builder analyst | 🟠 | ✅ |
| KPI-4: Dashboard sat promedio + top/bottom servicio + total eventos | 🟠 | ✅ |
| KPI-5: `kpis_aht_report` — agrupa por agente/supervisor/canal/servicio/semana | 🟡 | ✅ |
| KPI-6: `StreamingHttpResponse` + filtros fecha + chunk_size=500 | 🟡 | ✅ |
| Namespace `kpis:` + `login_required` + nav template corregido | 🔴 | ✅ |

---

## Sprint 7.5 — Documentación ✅ COMPLETO

### Objetivo: Documentar apps del proyecto

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
| `help` | ✅ | ✅ | ✅ auto | **Lote 4 (2026-03-20)** |
| `api` | ✅ | ✅ | ✅ auto | **Lote 4 (2026-03-20)** |
| `panel` | ✅ | ✅ | ✅ auto | **Lote 4 (2026-03-20)** |

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
| BOT-3: Pipeline campañas outbound / custom_rules | 🟠 | ⬜ Pasa a Sprint 9 |
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
| PASSGEN-98 / #98 | `passgen` | 5/7 patrones predefinidos fallan por `MIN_ENTROPY=60` | Bajar umbral |
| BOARD-85 / #85 | `board` | `settings.BOARD_CONFIG` — KeyError si no definido | Agregar a settings |
| CV-76 / #76 | `cv` | `reverse('project_detail')` sin namespace | Corregir con `events:` |
| CV-75 / #75 | `cv` | Imports de managers a nivel de módulo en views.py | Mover a lazy imports |

---

## Sprint 9 — Planificado ⬜

### Objetivo: Optimización, estabilización de bugs heredados, completar bots

| ID | Tarea | Prioridad |
|----|-------|-----------|
| **EVENTS-SIG** | Guard `create_credit_account` para usuarios bot | 🔴 |
| **EVENTS-SIG-2** | Fix reverse query GenericFK en signal de events | 🟠 |
| **BOT-BUG-19** | Persistir BotTaskQueue en DB (`status='queued'`) | 🟠 |
| **BOT-2** | Integrar bots ↔ sim (ACDAgentSlot) | 🟠 |
| **BOT-3** | Pipeline `ContactRecord → Lead` + `DiscadorLoad → LeadCampaign` | 🟠 |
| **BOT-5** | Reglas de distribución por skills | 🟡 |
| SCA-1 | Implementar Celery para tareas asíncronas | 🔴 |
| SCA-2 | Particionamiento de tablas grandes | 🔴 |
| REFACTOR-1 | Dividir `chat/views.py` (2017 líneas) en módulos | 🟠 |
| REFACTOR-2 | Dividir `rooms/views.py` (2858 líneas) en módulos | 🟠 |
| REFACTOR-3 | Dividir `courses/views.py` (2309 líneas) en módulos | 🟠 |
| NEW-T1 | Crear tests reales para `analyst` (INC-004) | 🟠 |
| KPI-7 | Unificar `SERVICE_CHOICES` en `kpis/forms.py` (Bug #69) | 🟠 |
| KPI-8 | Implementar vista de upload CSV en `kpis` (Bug #68) | 🟠 |
| CV-1 | Fix `reverse()` sin namespace en `CorporateDataMixin` (Bug #76) | 🔴 |
| CV-2 | Imports lazy de `events.management.*` en `cv/views.py` (Bug #75) | 🔴 |
| BOARD-1 | Fix IDOR en `BoardDetailView` (Bug #84) | 🔴 |
| BOARD-2 | Agregar `BOARD_CONFIG` en settings (Bug #85) | 🔴 |
| BOARD-3 | CRUD completo de Board (editar/eliminar) | 🟠 |
| CMP-1 | Fix `hasattr` → `try/except` en `campaign_detail` (Bug #93) | 🟠 |
| PG-1 | Fix `CATEGORIES` en `PasswordGenerator` (Bug #96) | 🔴 |
| PG-2 | Fix `MIN_ENTROPY` en `passgen` (Bug #98) | 🔴 |
| SIM-7e | Agentes simulados perfilados en ACD | 🔴 |
| BIT-17 | Nav prev/next filtrar por `created_by`+`is_active` | 🟡 |
| SC-8 | Tests básicos del proxy simcity | 🟡 |
| ~~DOC-FINAL~~ | ~~Documentar `help`, `api`, `panel`~~ | ✅ Completado lote 4 |

### Pendientes técnicos heredados

| ID | App | Descripción |
|----|-----|-------------|
| SIM-6b | `sim` | GTR Interactivo con sliders |
| BIT-18 | `bitacora` | TinyMCE CDN usa `no-api-key` |
| ResourceLock | `bots` | `acquire_lock()` usa `timezone.timedelta` |

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
           └──> bots (BOT-2 — ACDAgentSlot, pendiente)

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
           └──> events (managers importados en views — Bug #75)

core ──────┬──> events (import directo — si events falla, core no carga)
           └──> ← todas las apps (provee layouts/templates globales)

chat ──────┬──> rooms (consume Room, Message, RoomMember)
           └──> rooms.Notification (⬜ pendiente CHAT-B1 / Bug #5)

board ─────> (sin dependencias externas — app independiente)
bitacora ──> events + rooms + courses (relaciones opcionales)
```

### Convenciones de Nombres de Campos

| Concepto | Campo estándar | Tipo | Notas |
|----------|----------------|------|-------|
| PK pública | `id` | `UUIDField(primary_key=True)` | Todas excepto `events` (int), `simcity` (AutoField), `bots` (AutoField), `board` (AutoField), `cv` (AutoField) |
| Usuario creador | `created_by` | `ForeignKey(User)` | Convención general — excepciones en §3 de DEV_REFERENCE |
| Timestamps | `created_at` / `updated_at` | `DateTimeField` | auto_now_add / auto_now |
| Soft delete | `is_active` | `BooleanField(default=True)` | Donde aplica |

### Sistemas de tiempo real coexistentes

> **⚠️ Dos sistemas activos — no son intercambiables:**

| Sistema | App | Uso |
|---------|-----|-----|
| Django Channels (WebSocket) | `chat` | Chat en tiempo real, notificaciones push |
| Centrifugo (HTTP broadcast) | `rooms` | Broadcast de mensajes y eventos de sala |
| Django Channels (WebSocket) | `board` | Movimiento de cards — ⚠️ infraestructura lista, sin activar |

---

## Estado de Documentación por App

| App | CONTEXT.md | DEV_REFERENCE.md | DESIGN.md | Tests | Cobertura |
|-----|:---:|:---:|:---:|-------|-----------|
| analyst | ✅ auto | ✅ | ✅ | ⚠️ stub (3L) | ❌ 0% — **los 34 tests documentados no existen** |
| sim | ✅ auto | ✅ | ✅ | ✅ 3 archivos | 100% |
| bitacora | ✅ auto | ✅ | ✅ | ⚠️ stub (3L) | ❌ 0% |
| simcity | ✅ auto | ✅ | ✅ | ⚠️ stub (3L) | ❌ 0% (SC-8 pendiente) |
| events | ✅ auto | ✅ | ✅ | ✅ 9 archivos | — |
| accounts | ✅ auto | ✅ | ✅ | ✅ tests.py (212 líneas) | — |
| core | ✅ auto | ✅ | ✅ | ✅ test_performance.py | — |
| memento | ✅ auto | ✅ | ✅ | ✅ tests.py (68 líneas) | — |
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
| panel | ✅ auto | ✅ | ✅ | ✅ test_urls.py | — |

**Progreso doc: 20 / 20 apps documentadas (100%) ✅**
**Cobertura real de tests: 6 / 20 apps con tests funcionales (30%)** — `sim`, `events`, `accounts`, `core`, `memento`, `panel`

### Apps pendientes — próxima sesión de documentación

**Ninguna — documentación 20/20 completa ✅**

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

### INC-004 — 2026-03-20: Tests de `analyst` inexistentes
**Síntoma:** `analyst/tests.py` tiene 3 líneas (stub). El documento indicaba 34/50 tests al 68%.
**Resolución:** Pendiente — crear tests reales (NEW-T1, Sprint 9).
**Impacto:** Cobertura real del proyecto es 25% (5/20 apps).

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
- **`cv.views` importa managers de `events` a nivel de módulo** — si events.management falla, cv no carga (bug #75)
- **`chat.HardcodedNotificationManager`** es un stub — todas las notificaciones son falsas (bug #5/#50)
- **`passgen` solo funciona con patrones `strong` y `secure`** — los demás fallan por MIN_ENTROPY=60 (bug #98)
- **`passgen.password_help`** siempre da 500 — `CATEGORIES` no definido (bug #96)
- **`board.BoardDetailView`** sin verificación de propietario — IDOR activo (bug #84)
- **`board` requiere `settings.BOARD_CONFIG`** — KeyError si no está definido (bug #85)
- **`campaigns`** son datos globales — sin `created_by`, todos los usuarios ven todo (diseño intencional)
- **`kpis.CallRecord.created_by`** es `null=True, SET_NULL` — intencional para preservar métricas históricas
- **`board.cards.all()`** ya viene ordenado por `['-is_pinned', '-created_at']`
- **`cv.skills_list`** — el related_name es `skills_list`, NO `skills`
- **`bots` PK int** en todos los modelos — FKs desde otras apps deben usar int
- **`events.InboxItem` usa `created_by`** (no `host`) — los bots pueden crear InboxItems
- **Pipeline bots verificado end-to-end:** Lead → InboxItem → BotTaskAssignment → GTDProcessor → Task
- **`help` tiene 3 templates faltantes** — `faq_list`, `video_tutorials`, `quick_start` dan 500 al visitarlos (bug #107)
- **`help` depende de `courses` en import de módulo** — si `courses` falla, `help` no carga (bug #101)
- **`help.author`/`help.user`** en vez de `created_by` — es la convención de esta app
- **`api/views.py` está vacío** — toda la lógica de `/api/*` vive en `panel/views.py`
- **Rutas `/api/*` están duplicadas** — registradas en `panel/urls.py` directamente Y via `include('api.urls')` (bug #112)
- **`panel.get_connection_token` no retorna nada** — endpoint Centrifugo inaccesible (bug #114)
- **`panel.DatabaseSelectorMiddleware`** referencia `postgres_online` y `sqlite` no definidos — activo pero sin efecto útil (bug #115)
- **`panel.RemoteMediaStorage`** requiere `192.168.18.51:8000` activo para uploads — en offline todos los uploads fallan
- **`BOARD_CONFIG`** ya definido en `settings.py` con `CARDS_PER_PAGE: 12` (fix bug #85)
- **`CENTRIFUGO_TOKEN_SECRET`** debe estar en `.env` — requerido por `rooms` y `panel/views.get_subscription_token`
- **`panel/tests/test_urls.py`** existe (58L) — única app con tests de resolución de URLs

---

## 🔄 Handoff — Sesión 2026-03-20 (Analista Doc — lote 3)

### Completado esta sesión

- Revisado estado de `bots` (Sprint 8 cerrado, documentación completa)
- Generada documentación completa para **6 apps**: `kpis`, `cv`, `board`, `campaigns`, `passgen`
- Registrados **32 bugs nuevos** (#68–#99)
- Actualizado `PROJECT_DEV_REFERENCE.md` — bugs #68–#99 integrados
- Actualizado `PROJECT_DESIGN.md` — doc 17/20 (85%), Sprint 8 cerrado, Sprint 9 planificado
- Documentación global: **17/20 apps (85%)** — sube desde 55% (inicio de sesión)

### Hallazgos críticos de esta sesión

- **`passgen` más rota de lo esperado** — 5/7 patrones fallan, `password_help` da 500 siempre. Fixes son de 1–3 líneas.
- **`board` IDOR activo** — `BoardDetailView` sin verificación de propietario (Bug #84).
- **`cv` imports frágiles** — managers de `events` importados a nivel de módulo (Bug #75/#76).
- **`board.BOARD_CONFIG`** — KeyError potencial si no está en settings (Bug #85).

### Próximos pasos — rol Dev

1. **Fixes inmediatos `passgen`** (3 líneas cada uno):
   - `self.CATEGORIES = {...}` en `PasswordGenerator.__init__` (Bug #96)
   - `self.MIN_ENTROPY = 20` en `PasswordGenerator.__init__` (Bug #98)
   - `app_name = 'passgen'` en `urls.py` (Bug #95)
2. **Fix IDOR `board`** — `get_queryset(owner=request.user)` en `BoardDetailView` (Bug #84)
3. **Fix imports `cv`** — mover imports de managers a lazy en `get_context_data` (Bug #75)
4. Verificar `BOARD_CONFIG` en `settings.py` (Bug #85)
5. Bugs de seguridad heredados: ACC-B4, ACC-B3, MEM-B3, ROOMS-SEC-1, CORE-SEC-1/2

### Próximos pasos — rol Analista Doc

**Ninguno — documentación 20/20 completada ✅**

### Comandos para arrancar próxima sesión

```bash
# Terminal 1 — engine simcity
engine

# Terminal 2 — M360
m360

# Push documentación lote 4
git add help/ api/ panel/ docs/
git add PROJECT_DEV_REFERENCE.md PROJECT_DESIGN.md TEAM_ROLES.md
git commit -m "docs: documentación completa lote 4 (help, api, panel) — 20/20 apps, bugs #100-#120"
git push origin main
```

---

## 🔄 Handoff — Sesión 2026-03-20 (Analista Doc — lote 4)

### Completado esta sesión

- Generada documentación completa para **3 apps**: `help`, `api`, `panel`
- Registrados **21 bugs nuevos** (#100–#120)
- Actualizado `PROJECT_DEV_REFERENCE.md` — bugs #100–#120 integrados, app table actualizada, sección 20 a 20/20
- Actualizado `PROJECT_DESIGN.md` — doc 20/20, Sprint 7.5 cerrado, Sprint 9 DOC-FINAL marcado ✅
- Actualizado `TEAM_ROLES.md` — Sprint 8 completo, asignaciones Sprint 9
- **Documentación global: 20/20 apps (100%)** — Sprint 7.5 oficialmente cerrado

### Hallazgos críticos de esta sesión

- **`panel.get_connection_token` roto** — no retorna respuesta. Fix: 2 líneas (Bug #114)
- **`help` tiene 3 templates faltantes** — `faq_list`, `video_tutorials`, `quick_start` crashean en runtime (Bug #107)
- **`api` es un placeholder vacío** — requiere decisión de arquitectura: consolidar en `panel` o completar migración (Bug #112)
- **`panel.DatabaseSelectorMiddleware`** activo pero referencia BDs inexistentes — candidato a desactivar (Bug #115)
- **`panel.RemoteMediaStorage`** tiene ~30 `print()` activos en producción (Bug #116)

### Próximos pasos — rol Dev

1. **Fix inmediato `panel`** — completar `get_connection_token` con `jwt.encode()` + `return JsonResponse({'token': token})` (Bug #114, ~2 líneas)
2. **Crear 3 templates `help`** — `faq_list.html`, `video_tutorials.html`, `quick_start.html` (Bug #107, ~1.5h)
3. **Decisión arquitectura `api`** — Opción A (eliminar `include`) o Opción B (migrar vistas) (Bug #112)
4. **Limpiar `DatabaseSelectorMiddleware`** — quitar `postgres_online`/`sqlite` del `db_order` (Bug #115, 1 línea)
5. Bugs críticos heredados Sprint 8: #84 (IDOR board), #96/#98 (passgen), #75/#76 (cv)

### Estado final del proyecto

| Métrica | Valor |
|---------|-------|
| Apps documentadas | 20 / 20 (100%) ✅ |
| Bugs registrados | #1 – #120 (120 total) |
| Bugs críticos 🔴 activos | #84, #96, #98, #107, #114 |
| Apps con tests funcionales | 6 / 20 (30%) |
| Sprint activo | Sprint 9 |
