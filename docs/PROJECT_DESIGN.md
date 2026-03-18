# Management360 — Diseño, Roadmap y Estado de Implementación

> **Última actualización:** 2026-03-18
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
| Tiempo real | Django Channels + Daphne 4.2.1 (ASGI) |
| Procesamiento de datos | pandas, numpy, openpyxl |
| Almacenamiento | RemoteMediaStorage (dev: 192.168.18.51) / S3 (prod) |
| Cache | Redis (sesiones GTR, previews analyst, portapapeles) |
| API | Django REST Framework (endpoints internos) |
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
| **SC-0: Migración simcity_web → M360 (proxy híbrido)** | 🔴 | ✅ |
| **BIT-5: Auditoría templates bitacora** | 🟡 | ⬜ |
| **BIT-6: urls.py `<int:pk>` → `<uuid:pk>`** | 🟡 | ⬜ |
| KPI-1: UUID PK + `fecha` DateField + 5 índices + `created_by` (MySQL IF NOT EXISTS) | 🔴 | ✅ |
| KPI-2: Cache Redis 5min `kpis:dashboard:{user}:{desde}:{hasta}`, colores fijos | 🔴 | ✅ |
| KPI-3: `/kpis/api/` JSON + 3 funciones WFM en Report Builder analyst | 🟠 | ✅ |
| KPI-4: Dashboard sat promedio + top/bottom servicio + total eventos | 🟠 | ✅ |
| KPI-5: `kpis_aht_report` — agrupa por agente/supervisor/canal/servicio/semana | 🟡 | ✅ |
| KPI-6: `StreamingHttpResponse` + filtros fecha + chunk_size=500 | 🟡 | ✅ |
| Namespace `kpis:` + `login_required` + nav template corregido | 🔴 | ✅ |
| Refactor: Unificar manejo de fechas en todas las apps | 🟡 | ⬜ |

---

## Sprint 8 — Planificado ⬜

| Tarea | Prioridad |
|-------|-----------|
| BOT-1: Mejorar motor de asignación de leads en `bots` | 🔴 |
| BOT-2: Integrar bots con eventos de `sim` | 🔴 |
| BOT-3: Pipeline de procesamiento de campañas outbound | 🟠 |
| BOT-4: Dashboard de rendimiento de bots | 🟠 |
| BOT-5: Reglas de distribución basadas en skills | 🟡 |
| SC-1: Nav link en core dashboard para simcity | 🟡 |
| SC-2: Exportar partida simcity a dataset analyst | 🟠 |

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
               ├──> courses (autor de cursos)
               └──> cv (propietario del CV)

    analyst ──┬──> sim (ETL source + dashboard widgets)
              ├──> events (análisis de proyectos/tareas)
              ├──> simcity (exportar datos de partidas — pendiente)
              └──> kpis (reportes avanzados de llamadas)

    sim ──────┬──> analyst (datos para reportes)
              └──> events (creación de tareas desde training?)

    simcity ──┬──> proot:8001 (micropolisengine — engine externo)
              ├──> analyst (exportar partida como dataset — pendiente)
              └──> kpis (KPIs urbanos — pendiente)

    events ───┬──> chat (notificaciones de tareas)
              └──> rooms (salas para proyectos)

    kpis ─────┬──> analyst (datasets de métricas)
              └──> sim (comparación con simulaciones)

    courses ──┬──> analyst (análisis de progreso de estudiantes)
              └──> cv (certificaciones)

    bitacora ─┬──> events (related_event, related_task, related_project)
              ├──> rooms (related_room)
              ├──> events.Tag (tags M2M)
              └──> courses.ContentBlock (structured_content)

### Convenciones de Nombres de Campos

| Concepto | Campo estándar | Tipo | Notas |
|----------|----------------|------|-------|
| PK pública | `id` | `UUIDField(primary_key=True)` | Todas las apps excepto `simcity` |
| Usuario creador | `created_by` | `ForeignKey(User)` | Convención general |
| Timestamps | `created_at` / `updated_at` | `DateTimeField` | auto_now_add / auto_now |
| Soft delete | `is_active` | `BooleanField(default=True)` | Donde aplica |

> **Excepciones documentadas:**
> - `events` usa `host` para Project/Task/Event — NO cambiar
> - `rooms` usa `owner` para Room — NO cambiar
> - `bitacora` usa `fecha_creacion`/`fecha_actualizacion` (en español) — convención interna
> - `simcity.Game` usa `AutoField` (int) como PK — heredado del engine original

### `accounts.User` — Campos del modelo custom

```python
class User(AbstractUser):
    phone      = models.CharField(max_length=20, blank=True, null=True)
    avatar     = models.ImageField(upload_to='avatars/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

> Heredado de `AbstractUser`: `username`, `email`, `first_name`, `last_name`,
> `is_staff`, `is_active`, `date_joined`, `last_login`, `groups`, `user_permissions`.

---

## Estado de Documentación por App

| App | CONTEXT.md | DEV_REFERENCE.md | DESIGN.md | Tests | Cobertura |
|-----|-----------|-------------------|-----------|-------|-----------|
| analyst | ✅ auto | ✅ | ✅ | 34/50 | 68% |
| sim | ✅ auto | ✅ | ✅ | 157/157 | 100% |
| bitacora | ✅ auto | ✅ | ✅ | — | — |
| simcity | ✅ auto | ✅ | ✅ | — | — |
| events | ⬜ | ⬜ | ⬜ | — | — |
| chat | ⬜ | ⬜ | ⬜ | — | — |
| rooms | ⬜ | ⬜ | ⬜ | — | — |
| courses | ⬜ | ⬜ | ⬜ | — | — |
| kpis | ⬜ | 🔵 parcial | ⬜ | — | — |
| bots | ⬜ | ⬜ | ⬜ | — | — |
| board | ⬜ | ⬜ | ⬜ | — | — |
| cv | ⬜ | ⬜ | ⬜ | — | — |
| accounts | ⬜ | ⬜ | ⬜ | — | — |
| core | ⬜ | ⬜ | ⬜ | — | — |
| campaigns | ⬜ | ⬜ | ⬜ | — | — |
| help | ⬜ | ⬜ | ⬜ | — | — |
| memento | ⬜ | ⬜ | ⬜ | — | — |
| passgen | ⬜ | ⬜ | ⬜ | — | — |
| api | ⬜ | ⬜ | ⬜ | — | — |
| panel | ⬜ | ⬜ | ⬜ | — | — |

---

## Estructura de `docs/`

```
docs/
├── PROJECT_DESIGN.md
├── PROJECT_DEV_REFERENCE.md
├── plan_gestion_proyectos.md
├── architecture/
│   └── README-JS-ARCHITECTURE.md
├── chat/
│   └── CHAT_COMMANDS_EXAMPLES.md
├── courses/
│   └── COURSE_EDITOR_OPTIMIZATIONS.md
├── events/
│   ├── CX_EMAIL_PROCESSING_README.md
│   └── README-SCHEDULING-SYSTEM.md
├── faq/
│   └── gtd_inbox_processing_guide.md
├── guides/
│   └── MEDIA_UPLOAD_FIX_README.md
└── rooms/
    ├── NAVIGATION_TEST_ZONE_README.md
    └── README_NAVIGATION.md
```

---

## Incidentes Registrados

### INC-001 — 2026-03-17: `accounts_user` inexistente en BD
**Síntoma:** `500 Internal Server Error` en cualquier URL autenticada.
```
django.db.utils.ProgrammingError: (1146, "Table 'projects.accounts_user' doesn't exist")
```
**Causa:** `accounts/migrations/` nunca fue commiteada. Al recrear la BD, Django no pudo
regenerar las tablas de `accounts`. La tabla `auth_user` (Django default) existía pero
el proyecto usa `AUTH_USER_MODEL = 'accounts.User'`.

**Resolución:**
1. `python manage.py makemigrations accounts` → `0001_initial.py`
2. INSERT manual en `django_migrations` (fake) por `InconsistentMigrationHistory`
3. SQL manual en dbshell para crear tablas físicas
4. Usuarios restaurados desde `backup_cv_users.json` (hashes intactos)

**Prevención:** `accounts/migrations/` commiteada. `.gitignore` corregido (commit `2ea63279`).

**Estado BD actual:** 141+ tablas. `auth_user` (legacy Django) coexiste con `accounts_user` — a limpiar eventualmente.

---

## Notas para Claude

- **Fechas en `sim`:** usar `fecha` (DateField) + `hora_inicio` (DateTimeField) — NO `started_at`
- **CSRF en JS:** siempre `csrf()` desde cookie, nunca `CSRF_TOKEN` hardcoded
- **Respuestas JSON:** siempre `{"success": true/false, ...}`
- **`timedelta`:** importar desde `datetime`, NO desde `django.utils.timezone`
- **`events` usa `host`**, **`rooms` usa `owner`** — no son errores
- **`accounts/migrations/`** debe estar en git — nunca ignorar carpetas migrations
- **`.gitignore`:** regla `*/migrations/*` primero, excepciones `!app/migrations/**` después
- **`accounts.User`** tiene campos extra: `phone`, `avatar`, `created_at`, `updated_at`
- **`simcity`** requiere proot Ubuntu corriendo en :8001 — sin él, todos los endpoints del juego fallan
- **`micropolisengine`** solo disponible en `/root/micropolis/venv` (proot) — nunca importar en M360/Termux
- **`simcity.Game`** tiene `engine_game_id` (FK lógica al SQLite de proot) — puede ser `None` si el engine no respondió al crear

---

## 🔄 Handoff — Sesión 2026-03-18

### Commits pusheados (sesión completa)

| Hash | Descripción |
|------|-------------|
| `2f326224` | fix(accounts): migrations faltantes — INC-001 |
| `720aff10` | refactor(bitacora): modelos, vistas, tags, docs |
| `6f060e90` | docs(project): PROJECT_DESIGN + DEV_REFERENCE |
| `9683cd41` | fix(bitacora): migraciones 0003+0004 force-add |
| `2ea63279` | fix(.gitignore): lógica de migraciones corregida |
| `a9f6ccf4` | feat(simcity): app migrada desde simcity_web — proxy híbrido Termux/proot |
| _(pendiente)_ | docs(simcity): DESIGN + DEV_REFERENCE |
| _(pendiente)_ | docs(project): PROJECT_DESIGN + DEV_REFERENCE actualizados |

### Trabajo de DeepSeek — SIN commitear (~300 archivos)

| Área | Cambios |
|------|---------|
| `accounts/models.py` | User custom: phone, avatar, created_at, updated_at |
| `sim` | SIM-7a ACD completo — migraciones 0005+0006 aplicadas |
| `events` | 6 bugs corregidos en forms/views |
| `cv` | Admin con campos incorrectos corregido |
| `kpis` | Migración con dependencia incorrecta corregida |
| `docs/` | READMEs reorganizados en subcarpetas |
| ~58 archivos más | FKs actualizadas a `settings.AUTH_USER_MODEL` en todo el proyecto |

> ⚠️ TODO el trabajo de DeepSeek está en la rama local sin commitear.
> INC-002 (2026-03-18): `Duplicate column name created_at` en kpis.0002 — resuelto con `RunSQL IF NOT EXISTS` + `SeparateDatabaseAndState`.
> Hacer commits progresivos por app antes de la próxima sesión de desarrollo.

### Pendiente próxima sesión

1. **Commits pendientes** — hacer commits por app (accounts, sim, events, cv, kpis, docs)
2. **BIT-5** — auditoría de 6 templates de bitacora
3. **BIT-6** — `urls.py` `<int:pk>` → `<uuid:pk>`
4. **Sprint 8** — app `bots`: motor de asignación + integración sim
5. **simcity bugs SC-1/SC-2/SC-3** — ver SIMCITY_DEV_REFERENCE.md

### Comandos para arrancar próxima sesión

```bash
# PRIMERO — levantar engine simcity en proot
ubuntu
cd /root/micropolis/simcity_web && source /root/micropolis/venv/bin/activate
python manage.py runserver 0.0.0.0:8001 &

# LUEGO — M360 en Termux
cd ~/projects/Management360 && source venv/bin/activate

# Ver qué hay sin commitear por app
git diff --stat HEAD | grep "\.py" | head -30

# Mapa actualizado
bash scripts/m360_map.sh

# Templates bitacora
ls bitacora/templates/bitacora/
```