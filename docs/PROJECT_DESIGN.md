# Management360 — Diseño, Roadmap y Estado de Implementación

> **Última actualización:** 2026-03-19
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

| Tarea | Prioridad |
|-------|-----------|
| BOT-1: Mejorar motor de asignación de leads en `bots` | 🔴 |
| BOT-2: Integrar bots con eventos de `sim` | 🔴 |
| BOT-3: Pipeline de procesamiento de campañas outbound | 🟠 |
| BOT-4: Dashboard de rendimiento de bots | 🟠 |
| BOT-5: Reglas de distribución basadas en skills | 🟡 |
| SC-8: Tests básicos del proxy simcity | 🟡 |
| SC-9: KPIs urbanos (población, energía) → app kpis | 🟠 |

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

---

## 🔄 Handoff — Sesión 2026-03-19

### Commits de esta sesión

| Hash | Descripción |
|------|-------------|
| `19578101` | docs: remove obsolete root READMEs, update project docs |
| `93414566` | accounts: minor fixes (forms, views, tests) |
| `b439d8a8` | events: refactor views into modules, clean old views, update urls/templates |
| `7e564670` | cv: refactor templates (remove legacy edit pages), update views/forms/urls |
| _(kpis)_ | kpis: refactor models, views, urls; remove upload_csv template |
| _(bitacora)_ | bitacora: update dev docs, forms, templates (Sprint 7 refactor) |
| _(sim)_ | sim: add sim app (initial) |
| _(chore)_ | chore: remove debug/test scripts, update staticfiles + requirements |
| `2b84db3c` | core/chat/rooms/courses: minor updates across apps |
| `fbf2c544` | bitacora: BIT-6 — change `<int:pk>` to `<uuid:pk>` in urls.py |
| `e16ab499` | bitacora: BIT-5 — fix entry.autor→created_by, mood raw→get_mood_display in entry_detail |
| _(list)_ | bitacora: BIT-5 — fix CATEGORIA_CHOICES context + mood display in entry_list |
| _(dashboard)_ | bitacora: BIT-5 — fix get_categoria_choices in dashboard |
| _(views)_ | bitacora: BIT-5 — fix CategoriaChoices import in views.py |
| _(docs)_ | bitacora: update design and dev reference docs (Sprint 7 close) |

### Pendiente próxima sesión

1. **`git push`** — 15+ commits locales sin pushear
2. **Sprint 8** — app `bots`: motor de asignación + integración sim
3. **Sprint 7 KPIs** — revisión de métricas / cierre formal
4. **SC-8** — tests básicos del proxy simcity
5. **BIT-17** — navegación prev/next filtrar por `created_by`+`is_active`

### Comandos para arrancar próxima sesión

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
