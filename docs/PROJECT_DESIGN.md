# Management360 — Diseño, Roadmap y Estado de Implementación

> **Última actualización:** 2026-03-19 (Sesión Manager — integración handoff doc lote 2)
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
- **Perfil Profesional** (app `cv`) - Currículum dinámico
- **GTD Personal** (apps `bitacora`, `board`, `memento`) - Productividad personal

### Stack Tecnológico Unificado

| Componente | Detalle |
|------------|---------|
| Backend | Django 5.1.7 (Python 3.13) |
| Base de datos | MariaDB 12.2.2 (principal) + Redis 7 (cache/sesiones) |
| Frontend | Bootstrap 5, HTMX (interactividad parcial), Chart.js 4.4.1 |
| Tiempo real | Django Channels + Daphne 4.2.1 (ASGI) — app `chat` |
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
| **Fase 8** | Automatización y bots (bots) | S8 | ⬜ |
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
| Commits DeepSeek (accounts, sim, events, cv, kpis, docs, core) | 🟠 | ✅ |
| Refactor: Unificar manejo de fechas en todas las apps | 🟡 | ⬜ |

---

## Sprint 7.5 — Documentación (completado ✅)

### Objetivo: Documentar 11 apps del proyecto

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

**Bugs críticos descubiertos durante la documentación:** 32 (ver tabla Sprint 8 abajo)

---

## Sprint 8 — Planificado ⬜

### Objetivo: Automatización y bots (app `bots`) + resolución de bugs críticos

> ⚠️ **Precondición obligatoria:** resolver todos los bugs 🔴 antes de arrancar tareas BOT.

---

### Pre-Sprint 8 — Bugs críticos a resolver (32 bugs)

#### Seguridad 🔴

| ID | App | Descripción | Fix |
|----|-----|-------------|-----|
| ACC-B4 / #36 | `accounts` | Contraseña `"DefaultPassword123"` hardcodeada en `reset_to_default_password` | `get_random_string(12)` o variable de entorno |
| ACC-B3 / #37 | `accounts` | Open redirect en `login_view` — `next` sin validar | `url_has_allowed_host_and_scheme(next_url, request.get_host())` |
| MEM-B3 / #46 | `memento` | IDOR en `MementoConfigUpdateView` — sin filtro de propietario | `get_queryset().filter(user=request.user)` |
| CORE-SEC-1 / #43 | `core` | `url_map_view` sin `@login_required` — expone arquitectura | Agregar `@login_required` |
| CORE-SEC-2 / #43 | `core` | `search_view` sin `@login_required` — expone datos | Agregar `@login_required` |
| ROOMS-SEC-1 / #60 | `rooms` | `room_detail`, `room_list`, `room_comments` sin `@login_required` | Agregar decorador |
| CHAT-SEC-1 / #53 | `chat` | 20+ endpoints POST con `@csrf_exempt` | Eliminar `@csrf_exempt`, usar cookie CSRF estándar |
| CORE-SEC-3 / #42 | `core` | `refresh_dashboard_data` con `@csrf_exempt` en POST autenticado | Eliminar `@csrf_exempt` |

#### Runtime — rompen en ejecución 🔴

| ID | App | Descripción | Fix |
|----|-----|-------------|-----|
| ROOMS-B5 / #56 | `rooms` | `room_comments` llama `room.comments.create(text=...)` — campo incorrecto | `Comment.objects.create(room=room, user=request.user, comment=...)` |
| ROOMS-B10 / #57 | `rooms` | `navigate_room` llama `entrance.face.opposite()` — `str` no tiene ese método | Dict `{'NORTH':'SOUTH','EAST':'WEST',...}` |
| ROOMS-B9 / #58 | `rooms` | `calculate_new_position` retorna `None` para EAST/WEST | Agregar ramas faltantes |
| ROOMS-B11/12/13 / #59 | `rooms` | 3 ViewSets ordenan por `-created_at` en `EntranceExit`, `Portal`, `RoomConnection` — campo inexistente | Agregar `created_at` a los 3 modelos o cambiar ordering |
| CRS-B2 / #63 | `courses` | `standalone_lessons_list` en URL duplicada — vista inaccesible | Mover a `/courses/lessons/` |
| CRS-B4 / #64 | `courses` | `mark_lesson_complete` falla con `AttributeError` en lecciones independientes (`module=None`) | Verificar `lesson.module` antes de acceder |
| CHAT-B10 / #52 | `chat` | Template `edit_assistant_configuration.html` inexistente → 500 | Crear template o redirigir |
| ACC-B5 / #38 | `accounts` | `app_name` no declarado en `urls.py` — namespace `accounts:` frágil | Declarar `app_name = 'accounts'` en `urls.py` |
| ACC-B6 / #40 | `accounts` | Import muerto `file_tree_view` de analyst en `views.py` | Eliminar import |
| MEM-B4 / #47 | `memento` | `MinValueValidator(timezone.now().date())` congelado en tiempo de carga del módulo | Usar `MinValueValidator` dinámico o validar en `clean()` |
| MEM-B5 / #48 | `memento` | `build_memento_context()` sin rama `else` para frecuencia inválida | Agregar rama `else` con valor por defecto |
| MEM-B6 / #49 | `memento` | `LogoutView` propio en `/memento/logout/` — duplica `accounts:logout` | Eliminar, redirigir a `accounts:logout` |
| CORE-B4 / #44 | `core` | `Article.get_absolute_url()` hace reverse de URL inexistente → `NoReverseMatch` | Corregir name de URL o crear la vista |

#### Funcionalidad falsa en producción 🟠

| ID | App | Descripción | Acción |
|----|-----|-------------|--------|
| CHAT-B1 / #50 | `chat` | `HardcodedNotificationManager` — notificaciones siempre falsas, `mark_as_read` no persiste. **Es la causa raíz del Bug global #5.** | Conectar con `rooms.Notification` (modelo real ya existe) |
| CORE-B3 / #41 | `core` | `upcoming_events` filtra por `created_at__gte=now()` en lugar de `start_date` — siempre vacío | Cambiar a `start_date__gte=timezone.now()` |
| ACC-B7 / #39 | `accounts` | `email` sin `unique=True` en modelo — validación solo en form | Agregar `unique=True` + migración |

#### Código duplicado silencioso 🟠

| ID | App | Funciones duplicadas | Impacto |
|----|-----|---------------------|---------|
| CHAT-B2 / #51 | `chat` | `room_admin`, `reset_unread_count_api`, `room_notifications_api`, `mark_notifications_read_api`, `last_room_api` — 5 defs dobles | Python usa la segunda; primera es código muerto con lógica diferente |
| ROOMS-B14 / #61 | `rooms` | `portal_list`, `portal_detail` — 2 defs dobles | Ídem |

#### Deuda técnica 🟡

| ID | App | Descripción | Acción |
|----|-----|-------------|--------|
| CHAT-B3 / #54 | `chat` | `moderate_message()` con `['badword1', 'badword2']` — placeholder | Implementar o desactivar |
| CHAT-B4 / #55 | `chat` | URL Ollama hardcodeada en `ollama_api.py` | Mover a `settings.OLLAMA_API_URL` |
| ROOMS-B15 / #62 | `rooms` | `CENTRIFUGU_OUTBOX_PARTITIONS` — typo doble U en settings key | Verificar en `settings.py` real y corregir si aplica |
| CRS-B5 / #65 | `courses` | `LessonAttachment.get_file_size_display()` retorna string literal `.1f` | Formatear correctamente |
| CRS-B6 / #66 | `courses` | `Review.save()` y signal duplican recálculo de rating | Eliminar una de las dos |
| CRS-B7 / #67 | `courses` | Switch de 20 tipos duplicado entre `create_content_block` y `edit_content_block` | Extraer a función compartida |
| CORE-B5 / #45 | `core` | `'home'` e `'index'` apuntan al mismo path — redundante | Documentar; nunca eliminar `'index'` |

---

### Tareas Sprint 8 — App `bots`

| Tarea | Prioridad |
|-------|-----------|
| BOT-0: Verificar arquitectura frontend de `bots` — solo existe `bot_dashboard.html` | 🔴 |
| BOT-1: Documentar `bots` (CONTEXT + DEV_REFERENCE + DESIGN) antes de codear | 🔴 |
| BOT-2: Mejorar motor de asignación de leads en `bots` | 🔴 |
| BOT-3: Integrar bots con eventos de `sim` | 🔴 |
| BOT-4: Pipeline de procesamiento de campañas outbound | 🟠 |
| BOT-5: Dashboard de rendimiento de bots | 🟠 |
| BOT-6: Reglas de distribución basadas en skills | 🟡 |
| SC-8: Tests básicos del proxy simcity | 🟡 |
| SC-9: KPIs urbanos (población, energía) → app kpis | 🟠 |

### Pendientes técnicos heredados (pre-Sprint 8)

| ID | App | Descripción |
|----|-----|-------------|
| SIM-7e | `sim` | Agentes simulados perfilados |
| SIM-6b | `sim` | GTR Interactivo con sliders |
| BIT-17 | `bitacora` | Nav prev/next — filtrar por `created_by`+`is_active` |
| BIT-18 | `bitacora` | TinyMCE CDN usa `no-api-key` — registrar en tiny.cloud |

---

## Sprint 9 — Planificado ⬜

| Tarea | Prioridad |
|-------|-----------|
| SCA-1: Implementar Celery para tareas asíncronas | 🔴 |
| SCA-2: Particionamiento de tablas grandes | 🔴 |
| SCA-3: Estrategia de archivado para datos históricos | 🟠 |
| SCA-4: Read replicas para reportes pesados | 🟠 |
| SCA-5: Migración a S3 para archivos media | 🟡 |
| SCA-6: Optimización de queries N+1 en todas las apps | 🟡 |
| REFACTOR-1: Dividir `chat/views.py` (2017 líneas) en módulos | 🟠 |
| REFACTOR-2: Dividir `rooms/views.py` (2858 líneas) en módulos | 🟠 |
| REFACTOR-3: Dividir `courses/views.py` (2309 líneas) — monolito descubierto en auditoría | 🟠 |
| REFACTOR-4: Dividir `cv/views.py` (873 líneas) | 🟡 |
| NEW-T1: Crear tests reales para `analyst` — los 34 documentados no existen (INC-004) | 🟠 |
| NEW-T3: Agregar regla de seguridad al README — nunca pegar output de `.env` en chats | 🟡 |

---

## Integraciones Críticas entre Apps

### Matriz de Dependencias

    accounts ──┬──> events (propietario de proyectos/tareas)
               ├──> analyst (creador de datasets)
               ├──> sim (creador de cuentas)
               ├──> simcity (propietario de partidas)
               ├──> courses (tutor de cursos)
               └──> cv (propietario del CV)

    analyst ──┬──> sim (ETL source + dashboard widgets)
              ├──> events (análisis de proyectos/tareas)
              ├──> simcity (recibe exports de partidas ✅ SC-6)
              └──> kpis (reportes avanzados de llamadas)

    sim ──────┬──> analyst (datos para reportes)
              └──> events (creación de tareas desde training?)

    simcity ──┬──> proot:8001 (micropolisengine — engine externo)
              ├──> analyst (exportar partida como dataset ✅ SC-6)
              └──> kpis (KPIs urbanos — ⬜ SC-9)

    events ───┬──> chat (notificaciones de tareas)
              └──> rooms (salas para proyectos)

    kpis ─────┬──> analyst (datasets de métricas)
              └──> sim (comparación con simulaciones)

    courses ──┬──> cv   (import directo en models.py — dependencia CRÍTICA)
              ├──> analyst (análisis de progreso — pendiente formalizar)
              └──> cv (certificaciones — pendiente formalizar)

    bitacora ─┬──> events (related_event, related_task, related_project)
              ├──> rooms (related_room)
              ├──> events.Tag (tags M2M)
              └──> courses.ContentBlock (structured_content)

    core ─────┬──> events (import directo de Event, Project, Task, Status en utils.py — SI events falla, core no carga)
              └──> ← todas las apps (provee layouts/templates globales)

    chat ─────┬──> rooms (consume Room, Message, MessageRead, RoomMember)
              └──> rooms.Notification (⬜ pendiente CHAT-B1 / Bug global #5)

    rooms ────┬──> chat.UserPresence (FK a rooms.Room)
              └──> chat.MessageReaction (FK a rooms.Message)

### Convenciones de Nombres de Campos

| Concepto | Campo estándar | Tipo | Notas |
|----------|----------------|------|-------|
| PK pública | `id` | `UUIDField(primary_key=True)` | Todas las apps excepto `events` (int) y `simcity` (AutoField int) |
| Usuario creador | `created_by` | `ForeignKey(User)` | Convención general |
| Timestamps | `created_at` / `updated_at` | `DateTimeField` | auto_now_add / auto_now |
| Soft delete | `is_active` | `BooleanField(default=True)` | Donde aplica |

> **Excepciones confirmadas en auditoría (NO cambiar):**
> - `events` usa `host` para Project/Task/Event
> - `events` usa PKs int (AutoField)
> - `rooms` usa `owner` + `creator` para Room — `owner` es el propietario real
> - `bitacora` usa `fecha_creacion`/`fecha_actualizacion` (en español)
> - `simcity.Game` usa `AutoField` (int) como PK — heredado del engine original
> - `courses` usa `tutor` (Course), `author` (Lesson standalone / ContentBlock), `student` (Enrollment)
> - `chat` usa `user` en Conversation, CommandLog, AssistantConfiguration
> - `memento` usa `user` en MementoConfig

### Sistemas de tiempo real coexistentes

> **⚠️ Dos sistemas distintos — no son intercambiables:**

| Sistema | App | Uso |
|---------|-----|-----|
| Django Channels (WebSocket) | `chat` | Chat en tiempo real, notificaciones push |
| Centrifugo (HTTP broadcast) | `rooms` | Broadcast de mensajes y eventos de sala |

Centrifugo requiere en settings: `CENTRIFUGO_HTTP_API_ENDPOINT`, `CENTRIFUGO_HTTP_API_KEY`, `CENTRIFUGO_BROADCAST_MODE`, `CENTRIFUGU_OUTBOX_PARTITIONS` (⚠️ typo con doble U — verificar consistencia en `settings.py` real).

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
| kpis | ⬜ | 🔵 parcial | ⬜ | ❌ sin tests | — |
| bots | ⬜ | ⬜ | ⬜ | ⚠️ stub (3L) | ❌ 0% |
| board | ⬜ | ⬜ | ⬜ | ⚠️ stub (3L) | ❌ 0% |
| cv | ⬜ | ⬜ | ⬜ | ❌ sin tests | — |
| campaigns | ⬜ | ⬜ | ⬜ | ❌ sin tests | — |
| help | ⬜ | ⬜ | ⬜ | ⚠️ stub (3L) | ❌ 0% |
| passgen | ⬜ | ⬜ | ⬜ | ❌ sin tests | — |
| api | ⬜ | ⬜ | ⬜ | ❌ sin tests | — |
| panel | ⬜ | ⬜ | ⬜ | ⚠️ existe | — |

**Progreso doc:** 11 / 20 apps documentadas (55%)
**Cobertura real de tests:** 5 / 20 apps con tests funcionales (25%) — `sim`, `events`, `accounts`, `core`, `memento`

### Apps pendientes — próximas sesiones de documentación

| App | Complejidad | Prioridad | Notas |
|-----|-------------|-----------|-------|
| `kpis` | Baja | 🔴 | DEV_REFERENCE parcial ya existe — completar |
| `bots` | Alta | 🔴 | Target Sprint 8 — documentar ANTES de codear |
| `cv` | Media | 🟠 | Dependencia de `courses` — documentar pronto |
| `board` | Baja | 🟡 | Kanban simple, 3 modelos |
| `campaigns` | Baja | 🟡 | 3 modelos, 6 endpoints |
| `help` | Media | 🟡 | 7 modelos, 10 endpoints |
| `api` | Baja | 🟢 | 0 modelos, 4 endpoints |
| `passgen` | Muy baja | 🟢 | 0 modelos, 2 endpoints |
| `panel` | Baja | 🟢 | 0 modelos, 28 endpoints |

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
**Causa:** Bloque de comandos bash (`export SHELL=...`, `export ANTHROPIC_API_KEY=...`) estaba incrustado en el `.env` a partir de la línea 99, causando además 3 warnings de `python-dotenv` al arrancar.
**Resolución:** Key revocada en `console.anthropic.com`. Nueva key generada. Bloque bash eliminado del `.env`.
**Prevención:** Nunca pegar output de `.env` directamente en chats. Revisar `.env` antes de ejecutar `sed` o `cat`. El `.env` confirmado como nunca commiteado a git (`.gitignore` correcto).

### INC-004 — 2026-03-20: Tests de `analyst` inexistentes
**Síntoma:** Auditoría reveló que `analyst/tests.py` tiene 3 líneas (stub). El documento indicaba 34/50 tests al 68%.
**Causa:** Los tests fueron eliminados o nunca migrados al refactorizar la app.
**Resolución:** Pendiente — crear tests reales (NEW-T1, Sprint 9).
**Impacto:** La cobertura real del proyecto es 25% (5/20 apps), no la estimada previamente.

---

## Notas para Claude

- **Fechas en `sim`:** usar `fecha` (DateField) + `hora_inicio` (DateTimeField) — NO `started_at`
- **CSRF en JS:** siempre `csrf()` desde cookie, nunca `CSRF_TOKEN` hardcoded
- **Respuestas JSON:** siempre `{"success": true/false, ...}`
- **`timedelta`:** importar desde `datetime`, NO desde `django.utils.timezone`
- **`events` usa `host`**, **`rooms` usa `owner`** — no son errores
- **`accounts/migrations/`** debe estar en git — nunca ignorar carpetas migrations
- **`accounts.User`** tiene campos extra: `phone`, `avatar`, `created_at`, `updated_at`
- **`simcity`** requiere proot Ubuntu corriendo en :8001 — sin él todos los endpoints dan 503
- **`micropolisengine`** solo disponible en `/root/micropolis/venv` (proot) — nunca importar en M360/Termux
- **`proot-distro login ubuntu -- <cmd>`** es el método correcto para ejecutar en proot desde Termux
- **`simcity` arranque:** aliases `engine` y `m360` en `~/.zshrc` — dos terminales Termux
- **`bitacora.CategoriaChoices`** es módulo-level — NO `BitacoraEntry.CategoriaChoices`
- **`bitacora` templates** usan `categoria_choices` del contexto — NO `entry.CATEGORIA_CHOICES`
- **`core` importa directamente de `events`** — si events falla, core no carga
- **`courses` importa directamente de `cv`** — si cv falla, courses no carga
- **`upcoming_events` en `core`** filtra por `created_at__gte=now()` (bug #41) — no refleja eventos futuros reales
- **`chat.HardcodedNotificationManager`** es un stub — todas las notificaciones son falsas. El modelo real es `rooms.Notification` (bug global #5 / #50)
- **Ollama debe estar en :11434** para que el asistente de chat funcione — URL hardcodeada en `ollama_api.py` (bug #55)
- **`rooms.navigate_room`** está roto — `entrance.face.opposite()` lanza `AttributeError` (bug #57)
- **`rooms.room_comments`** está roto — campo `text` no existe, lanza `TypeError` (bug #56)
- **`courses.standalone_lessons_list`** es inaccesible — URL duplicada con `content_manager` (bug #63)
- **`courses.mark_lesson_complete`** falla con lecciones independientes (`module=None`) (bug #64)
- **`memento.MementoConfigUpdateView`** sin filtro de propietario — IDOR activo (bug #46)
- **`accounts.reset_to_default_password`** tiene contraseña hardcodeada `"DefaultPassword123"` (bug #36)
- **`chat/views.py`** tiene 5 funciones duplicadas — Python usa la segunda definición (bug #51)
- **`rooms/views.py`** tiene 2 funciones duplicadas — ídem (bug #61)
- **`courses` no puede cargar si `cv` falla** — `from cv.models import Curriculum` en línea 9 de `courses/models.py`

---

## 🔄 Handoff — Sesión 2026-03-19 (Manager — integración doc lote 2)

### Completado esta sesión
- Integrado handoff del analista doc lote 2 (6 apps documentadas)
- Actualizado estado de documentación: 11/20 apps (55%)
- Expandida tabla de bugs pre-Sprint 8: de 11 a 32 bugs registrados
- Actualizadas notas para Claude con hallazgos de la sesión de documentación
- Agregadas tareas de refactor monolitos (chat/rooms views.py) al Sprint 9
- **Auditoría de estado de apps** ejecutada con scripts en vivo (2026-03-20):
  - Confirmada cobertura real de tests: 25% (5/20 apps) — no 68% como documentado
  - Tests de `analyst` son stub (3L) — los 34 tests documentados no existen → INC-004
  - `courses/views.py` descubierto como monolito de 2309 líneas → REFACTOR-3
  - `bots` tiene solo 1 template → BOT-0 agregado al Sprint 8
  - `cv/views.py` 873 líneas → REFACTOR-4
  - API key expuesta en output de terminal → revocada → INC-003
  - `.env` tenía bloque bash incrustado → corregido → warnings de dotenv resueltos
  - 13/20 apps con `app_name` declarado correctamente en urls.py

### Próximos pasos — rol Dev

1. `git push` — commits locales sin pushear
2. Bugs 🔴 de seguridad: ACC-B4, ACC-B3, MEM-B3, ROOMS-SEC-1, CORE-SEC-1/2 — **resolver antes de arrancar Sprint 8**
3. Bugs 🔴 de runtime: ROOMS-B5/B10/B9/B11-13, CRS-B2/B4, CHAT-B10 — **resolver antes de arrancar Sprint 8**
4. Sprint 8 task BOT-1: documentar `bots` primero, luego codear

### Próximos pasos — rol Analista Doc

1. Generar CONTEXT.md de `kpis`, `bots`, `cv` con `bash scripts/m360_map.sh app ./nombre_app`
2. Documentar `kpis` (completar DEV_REFERENCE parcial)
3. Documentar `bots` (alta prioridad — target Sprint 8)
4. Documentar `cv` (dependencia de `courses`)
5. Verificar `CENTRIFUGU_OUTBOX_PARTITIONS` en `settings.py` real antes de documentar `rooms`

### Comandos para arrancar próxima sesión de código

```bash
# Terminal 1 — engine simcity
engine   # alias: ubuntu + activate + runserver 0.0.0.0:8001

# Terminal 2 — M360
m360     # alias: cd M360 + activate + runserver

# Push pendiente
git push origin main

# Ver estado
git log --oneline -15
git status --short
```
