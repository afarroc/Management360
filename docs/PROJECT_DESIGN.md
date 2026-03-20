# Management360 — Diseño, Roadmap y Estado de Implementación

> **Última actualización:** 2026-03-19 (Sesión Analista Doc — lote 2)
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

## Sprint 8 — Planificado ⬜

### Tareas originales

| Tarea | Prioridad |
|-------|-----------|
| BOT-1: Mejorar motor de asignación de leads en `bots` | 🔴 |
| BOT-2: Integrar bots con eventos de `sim` | 🔴 |
| BOT-3: Pipeline de procesamiento de campañas outbound | 🟠 |
| BOT-4: Dashboard de rendimiento de bots | 🟠 |
| BOT-5: Reglas de distribución basadas en skills | 🟡 |
| SC-8: Tests básicos del proxy simcity | 🟡 |
| SC-9: KPIs urbanos (población, energía) → app kpis | 🟠 |

### Bugs críticos a resolver antes de arrancar Sprint 8
> Descubiertos en la sesión de documentación 2026-03-19

| ID | App | Bug | Prioridad |
|----|-----|-----|-----------|
| ACC-SEC-1 | `accounts` | Contraseña `"DefaultPassword123"` hardcodeada en `reset_to_default_password` | 🔴 |
| ACC-SEC-2 | `accounts` | Open redirect en `login_view` — param `next` sin validar | 🔴 |
| MEM-SEC-1 | `memento` | IDOR en `MementoConfigUpdateView` — sin filtro de propietario | 🔴 |
| ROOMS-RT-1 | `rooms` | `room_comments` falla con `TypeError` — campo `text` inexistente | 🔴 |
| ROOMS-RT-2 | `rooms` | `navigate_room` falla con `AttributeError` — `str.opposite()` no existe | 🔴 |
| ROOMS-RT-3 | `rooms` | 3 ViewSets CRUD ordenan por `-created_at` en modelos sin ese campo | 🔴 |
| CRS-RT-1 | `courses` | `standalone_lessons_list` inaccesible — URL duplicada con `content_manager` | 🔴 |
| CRS-RT-2 | `courses` | `mark_lesson_complete` falla con `AttributeError` en lecciones independientes | 🔴 |
| CHAT-RT-1 | `chat` | Template `edit_assistant_configuration.html` no existe — vista da 500 | 🔴 |
| CHAT-PROD-1 | `chat` | `HardcodedNotificationManager` en producción — notificaciones falsas | 🔴 |
| CORE-SEM-1 | `core` | `upcoming_events` filtra por `created_at` en lugar de `start_date` | 🟠 |

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

    courses ──┬──> cv   (import directo en models.py — dependencia crítica)
              ├──> analyst (análisis de progreso — pendiente formalizar)
              └──> cv (certificaciones — pendiente formalizar)

    bitacora ─┬──> events (related_event, related_task, related_project)
              ├──> rooms (related_room)
              ├──> events.Tag (tags M2M)
              └──> courses.ContentBlock (structured_content)

    core ─────┬──> events (import directo de Event, Project, Task, Status en utils.py)
              └──> ← todas las apps (provee layouts/templates globales)

    chat ─────┬──> rooms (consume Room, Message, MessageRead, RoomMember)
              └──> ← rooms.Notification (fix pendiente CHAT-PROD-1)

    rooms ────┬──> chat.UserPresence (FK a rooms.Room)
              └──> chat.MessageReaction (FK a rooms.Message)

### Convenciones de Nombres de Campos

| Concepto | Campo estándar | Tipo | Notas |
|----------|----------------|------|-------|
| PK pública | `id` | `UUIDField(primary_key=True)` | Todas las apps excepto `events` (int) y `simcity` (AutoField int) |
| Usuario creador | `created_by` | `ForeignKey(User)` | Convención general |
| Timestamps | `created_at` / `updated_at` | `DateTimeField` | auto_now_add / auto_now |
| Soft delete | `is_active` | `BooleanField(default=True)` | Donde aplica |

> **Excepciones documentadas (todas confirmadas en auditoría 2026-03-19):**
> - `events` usa `host` para Project/Task/Event — NO cambiar
> - `events` usa PKs int (AutoField) — NO cambiar
> - `rooms` usa `owner` + `creator` para Room — `owner` es el propietario real
> - `bitacora` usa `fecha_creacion`/`fecha_actualizacion` (en español) — convención interna
> - `simcity.Game` usa `AutoField` (int) como PK — heredado del engine original
> - `courses` usa `tutor` para Course, `author` para Lesson/ContentBlock, `student` para Enrollment
> - `chat` usa `user` en Conversation, CommandLog, AssistantConfiguration
> - `memento` usa `user` en MementoConfig

### `accounts.User` — Campos del modelo custom

```python
class User(AbstractUser):
    phone      = models.CharField(max_length=20, blank=True, null=True)
    avatar     = models.ImageField(upload_to='avatars/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

### Sistemas de tiempo real coexistentes

> **⚠️ Dos sistemas distintos — no son intercambiables:**

| Sistema | App | Uso |
|---------|-----|-----|
| Django Channels (WebSocket) | `chat` | Chat en tiempo real, notificaciones push |
| Centrifugo (HTTP broadcast) | `rooms` | Broadcast de mensajes y eventos de sala |

Centrifugo requiere en settings: `CENTRIFUGO_HTTP_API_ENDPOINT`, `CENTRIFUGO_HTTP_API_KEY`, `CENTRIFUGO_BROADCAST_MODE`, `CENTRIFUGU_OUTBOX_PARTITIONS` (⚠️ typo con doble U — verificar consistencia).

---

## Estado de Documentación por App

| App | CONTEXT.md | DEV_REFERENCE.md | DESIGN.md | Tests | Cobertura |
|-----|:---:|:---:|:---:|-------|-----------|
| analyst | ✅ auto | ✅ | ✅ | 34/50 | 68% |
| sim | ✅ auto | ✅ | ✅ | 157/157 | 100% |
| bitacora | ✅ auto | ✅ | ✅ | — | — |
| simcity | ✅ auto | ✅ | ✅ | — | — |
| events | ✅ auto | ✅ | ✅ | — | — |
| accounts | ✅ auto | ✅ | ✅ | tests.py (212 líneas) | — |
| core | ✅ auto | ✅ | ✅ | test_performance.py (249 líneas) | — |
| memento | ✅ auto | ✅ | ✅ | tests.py (68 líneas) | — |
| chat | ✅ auto | ✅ | ✅ | — | — |
| rooms | ✅ auto | ✅ | ✅ | management commands | — |
| courses | ✅ auto | ✅ | ✅ | management commands | — |
| kpis | ⬜ | 🔵 parcial | ⬜ | — | — |
| bots | ⬜ | ⬜ | ⬜ | — | — |
| board | ⬜ | ⬜ | ⬜ | — | — |
| cv | ⬜ | ⬜ | ⬜ | — | — |
| campaigns | ⬜ | ⬜ | ⬜ | — | — |
| help | ⬜ | ⬜ | ⬜ | — | — |
| passgen | ⬜ | ⬜ | ⬜ | — | — |
| api | ⬜ | ⬜ | ⬜ | — | — |
| panel | ⬜ | ⬜ | ⬜ | — | — |

**Progreso:** 11 / 20 apps documentadas (55%)

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
- **`upcoming_events` en `core`** filtra por `created_at__gte=now()` (bug) — no refleja eventos futuros reales
- **`chat.HardcodedNotificationManager`** es un stub — todas las notificaciones son falsas. El modelo real es `rooms.Notification`
- **Ollama debe estar en :11434** para que el asistente de chat funcione
- **`rooms.navigate_room`** está roto — `entrance.face.opposite()` lanza `AttributeError`
- **`rooms.room_comments`** está roto — campo `text` no existe, lanza `TypeError`
- **`courses.standalone_lessons_list`** es inaccesible — URL duplicada con `content_manager`
- **`courses.mark_lesson_complete`** falla con lecciones independientes (`module=None`)
- **`memento.MementoConfigUpdateView`** sin filtro de propietario — IDOR activo
- **`accounts.reset_to_default_password`** tiene contraseña hardcodeada `"DefaultPassword123"`

---

## 🔄 Handoff — Sesión 2026-03-19 (Analista Doc lote 2)

### Apps documentadas esta sesión
`accounts`, `core`, `memento`, `chat`, `rooms`, `courses` — 12 documentos generados

### Pendiente próxima sesión de código

1. **`git push`** — commits locales sin pushear
2. **Bugs críticos** de la tabla Sprint 8 antes de arrancar el sprint
3. **Sprint 8** — app `bots`: motor de asignación + integración sim
4. **SC-8** — tests básicos del proxy simcity
5. **BIT-17** — navegación prev/next filtrar por `created_by`+`is_active`

### Pendiente próxima sesión de documentación

Prioridad sugerida: `kpis` → `cv` → `bots` → `board` → resto

```bash
# Generar CONTEXT antes de cada sesión de doc:
bash scripts/m360_map.sh app ./kpis
bash scripts/m360_map.sh app ./cv
bash scripts/m360_map.sh app ./bots
```

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
