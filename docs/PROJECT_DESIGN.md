# Management360 — Diseño, Roadmap y Estado de Implementación

> **Última actualización:** 2026-03-17
> **Contexto:** Plataforma SaaS de Workforce Management (WFM) y Customer Experience (CX)
> **Apps activas:** 19 | **Archivos Python+HTML:** 693
> **Metodología:** Scrum — sprints semanales sincronizados entre apps

---

## Visión General del Proyecto

Management360 es una plataforma integral de Workforce Management que combina:

- **Business Intelligence** (app `analyst`) - Procesamiento de datos, ETL, reportes, dashboards
- **Customer Experience** (app `events`) - Gestión de proyectos, tareas, inbox GTD
- **Simulación WFM** (app `sim`) - Generación de datos realistas, training, GTR
- **Comunicación** (apps `chat`, `rooms`) - Tiempo real, espacios virtuales
- **Aprendizaje** (app `courses`) - Sistema de cursos y lecciones
- **Métricas de Contacto** (app `kpis`) - CallRecord, AHT, SL, abandono
- **Automatización** (app `bots`) - Bots y asignación de leads
- **Perfil Profesional** (app `cv`) - Currículum dinámico
- **GTD Personal** (apps `bitacora`, `board`, `memento`) - Productividad personal

### Stack Tecnológico Unificado

| Componente | Detalle |
|------------|---------|
| Backend | Django 4.2+ (Python 3.11) |
| Base de datos | PostgreSQL 15 (principal) + Redis 7 (cache/sesiones) |
| Frontend | Bootstrap 5, HTMX (interactividad parcial), Chart.js 4.4.1 |
| Tiempo real | Django Channels + WebSockets (chat, rooms) |
| Procesamiento de datos | pandas, numpy, openpyxl |
| Almacenamiento | Media local (desarrollo) / S3 (producción) |
| Cache | Redis (sesiones GTR, previews analyst, portapapeles) |
| API | Django REST Framework (endpoints internos) |
| Tareas asíncronas | (pendiente implementar Celery) |
| Despliegue | Termux (dev) / Render (prod) |

---

## Estado por Fase del Proyecto

| Fase | Descripción | Sprint | Estado |
|------|-------------|--------|--------|
| **Fase 1** | Fundación: apps core (accounts, core, panel) | S1 | ✅ |
| **Fase 2** | Gestión de proyectos y tareas (events) | S2 | ✅ |
| **Fase 3** | Comunicación en tiempo real (chat, rooms) | S3 | ✅ |
| **Fase 4** | Plataforma de datos (analyst) | S4 | ✅ |
| **Fase 5** | Simulador WFM (sim) SIM-1→SIM-6b + integración analyst | S5 | ✅ |
| **Fase 6** | Sistema de aprendizaje (courses) | S6 | ✅ |
| **Fase 7** | Métricas de contacto (kpis) | S7 | 🔵 |
| **Fase 8** | Automatización y bots (bots) | S8 | ⬜ |
| **Fase 9** | Optimización y escalado | S9 | ⬜ |

---

## Sprints Completados

### Sprint 1 — Fundación (✅)
- Configuración inicial Django
- Apps: `accounts`, `core`, `panel`
- Sistema de autenticación
- Template base NiceAdmin
- Namespaces de URLs establecidos

### Sprint 2 — Gestión de Proyectos (✅)
- App `events` con modelos: Project, Task, Event, Status
- Sistema de dependencias entre tareas
- Inbox GTD con procesamiento de emails CX
- Kanban board y matriz Eisenhower
- Programación recurrente de tareas (TaskSchedule)

### Sprint 3 — Comunicación (✅)
- App `chat` con WebSockets
- App `rooms` para espacios virtuales
- Sistema de notificaciones en tiempo real
- Presencia de usuarios
- Comandos del asistente IA

### Sprint 4 — Plataforma de Datos (✅)
- App `analyst` completa (ver ANALYST_PLATFORM_DESIGN.md)
- Fases 1-5 implementadas: AnalystBase, CrossSource, Report, Dashboard, Pipeline
- Integración con modelos Django vía ETL

### Sprint 5 — Simulador WFM + Integración (✅)
- App `sim` completa (ver SIM_DESIGN.md)
- SIM-1 a SIM-6a implementados
- Integración nativa con analyst: ETL, Dashboard, Report Builder
- Training Mode con escenarios y evaluación

### Sprint 6 — Sistema de Aprendizaje (✅)
- App `courses` con modelos: Course, Module, Lesson, ContentBlock
- Editor de cursos con bloques reutilizables
- Sistema de lecciones y progreso
- Gestor de contenido (CMS)
- Vista previa en tiempo real

---

## Sprint 7 — En Curso 🔵

### Objetivo: Optimización de KPIs y Métricas de Contacto

| Tarea | Prioridad | Estado |
|-------|-----------|--------|
| KPI-1: Optimizar modelo `CallRecord` con índices compuestos | 🔴 | ⬜ |
| KPI-2: Implementar caching en dashboard de KPIs | 🔴 | ⬜ |
| KPI-3: Integrar `CallRecord` con analyst ETL | 🟠 | ⬜ |
| KPI-4: Dashboard de SL (Service Level) en tiempo real | 🟠 | ⬜ |
| KPI-5: Reportes de AHT por agente/skill/franja | 🟡 | ⬜ |
| KPI-6: Exportación optimizada de datos de llamadas | 🟡 | ⬜ |
| Refactor: Unificar manejo de fechas en todas las apps | 🟡 | ⬜ |

---

## Sprint 8 — Planificado ⬜

### Automatización y Bots

| Tarea | Prioridad |
|-------|-----------|
| BOT-1: Mejorar motor de asignación de leads en `bots` | 🔴 |
| BOT-2: Integrar bots con eventos de `sim` (agentes automáticos) | 🔴 |
| BOT-3: Pipeline de procesamiento de campañas outbound | 🟠 |
| BOT-4: Dashboard de rendimiento de bots | 🟠 |
| BOT-5: Reglas de distribución basadas en skills | 🟡 |

---

## Sprint 9 — Planificado ⬜

### Optimización y Escalado

| Tarea | Prioridad |
|-------|-----------|
| SCA-1: Implementar Celery para tareas asíncronas | 🔴 |
| SCA-2: Particionamiento de tablas grandes (Interaction, CallRecord) | 🔴 |
| SCA-3: Estrategia de archivado para datos históricos | 🟠 |
| SCA-4: Read replicas para reportes pesados | 🟠 |
| SCA-5: Migración a S3 para archivos media | 🟡 |
| SCA-6: Optimización de queries N+1 en todas las apps | 🟡 |

---

## Backlog Priorizado del Proyecto

| ID | Historia | Prioridad | Esfuerzo | Sprint |
|----|----------|-----------|----------|--------|
| P-01 | Como analista WFM, quiero ver SL en tiempo real por skill | 🔴 | M | S7 |
| P-02 | Como supervisor, quiero dashboard unificado con KPIs de sim + reales | 🔴 | L | S7 |
| P-03 | Como trainer, quiero asignar agentes reales a sesiones GTR | 🔴 | XL | S8 |
| P-04 | Como admin, quiero que las tareas pesadas se ejecuten en background | 🔴 | L | S9 |
| P-05 | Como analista, quiero exportar dashboards a PDF | 🟠 | M | S8 |
| P-06 | Como usuario, quiero notificaciones push en móvil | 🟠 | L | S9 |
| P-07 | Como trainer, quiero reporte comparativo agente vs perfil esperado | 🟠 | M | S8 |
| P-08 | Como admin, quiero auditoría de todas las acciones críticas | 🟠 | M | S9 |
| P-09 | Como analista, quiero programar reportes automáticos por email | 🟡 | L | S9 |
| P-10 | Como usuario, quiero tema oscuro en todas las apps | 🟡 | M | S8 |

---

## Integraciones Críticas entre Apps

### Matriz de Dependencias

    accounts ──┬──> events (propietario de proyectos/tareas)
               ├──> analyst (creador de datasets)
               ├──> sim (creador de cuentas)
               ├──> courses (autor de cursos)
               └──> cv (propietario del CV)

    analyst ──┬──> sim (ETL source + dashboard widgets)
              ├──> events (análisis de proyectos/tareas)
              └──> kpis (reportes avanzados de llamadas)

    sim ──────┬──> analyst (datos para reportes)
              └──> events (creación de tareas desde training?)

    events ───┬──> chat (notificaciones de tareas)
              └──> rooms (salas para proyectos)

    kpis ─────┬──> analyst (datasets de métricas)
              └──> sim (comparación con simulaciones)

    courses ──┬──> analyst (análisis de progreso de estudiantes)
              └──> cv (certificaciones)

### Convenciones de Nombres de Campos

| Concepto | App origen | Campo estándar | Apps que deben usarlo |
|----------|------------|----------------|----------------------|
| Fecha de inicio | sim | `fecha` (DateField) + `hora_inicio` (DateTimeField) | analyst, kpis |
| Usuario creador | Todas | `created_by` (ForeignKey User) | Todas |
| Identificador público | Todas | `id` = UUIDField primary_key=True | Todas |
| Soft delete | events | `is_active` BooleanField | analyst (en algunos) |
| Historial de cambios | events | `*History` models | — |
| Cache key | analyst | `cache_key` CharField unique | — |

---

## Estado de Documentación por App

| App | CONTEXT.md | DEV_REFERENCE.md | DESIGN.md | Tests | Cobertura |
|-----|-----------|-------------------|-----------|-------|-----------|
| analyst | ✅ auto | ✅ | ✅ | 34/50 | 68% |
| sim | ✅ auto | ✅ | ✅ | 157/157 | 100% |
| events | ⬜ | ⬜ | ⬜ | — | — |
| chat | ⬜ | ⬜ | ⬜ | — | — |
| rooms | ⬜ | ⬜ | ⬜ | — | — |
| courses | ⬜ | ⬜ | ⬜ | — | — |
| kpis | ⬜ | ⬜ | ⬜ | — | — |
| bots | ⬜ | ⬜ | ⬜ | — | — |
| bitacora | ⬜ | ⬜ | ⬜ | — | — |
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

## Comandos Útiles para Desarrollo

    # Generar mapa de cualquier app
    bash scripts/m360_map.sh app ./kpis        # → KPIS_CONTEXT.md
    bash scripts/m360_map.sh app ./events      # → EVENTS_CONTEXT.md

    # Auditoría de URLs sin namespace
    bash scripts/m360_map.sh app ./analyst --audit

    # Ver mapa de URLs completo
    bash scripts/m360_map.sh urls

    # Tests de sim (referencia)
    python manage.py test sim.tests.test_generators sim.tests.test_gtr_engine -v 2

    # Seed de perfiles de agente (después de migrar sim)
    python manage.py seed_agent_profiles

---

## 🔄 Handoff — Cambio de Sesión

> **Estado actual:** Sprint 7 iniciado (kpis). sim Sprint 4 (SIM-7a ACD Simulator) en curso en paralelo.

### Archivos para próxima sesión

    # Documentación de referencia
    cat docs/PROJECT_DESIGN.md
    cat docs/PROJECT_DEV_REFERENCE.md

    # Mapas de apps prioritarias
    bash scripts/m360_map.sh app ./kpis        # → KPIS_CONTEXT.md
    bash scripts/m360_map.sh app ./events      # → EVENTS_CONTEXT.md

    # Código de KPIs para análisis
    cat kpis/models.py | termux-clipboard-set
    cat kpis/views.py | termux-clipboard-set

### Tareas pendientes para próxima sesión

1. **sim Sprint 4 (SIM-7a):** Modelos ACD + motor de enrutamiento multi-agente
2. Optimizar modelo `CallRecord` (índices, consultas frecuentes)
3. Implementar caching en dashboard de KPIs
4. Integrar KPIs con analyst ETL
5. Unificar manejo de fechas entre apps
6. Crear `EVENTS_DESIGN.md` y `EVENTS_DEV_REFERENCE.md`

---

## Notas para Claude

- **Fechas en `sim`:** usar `fecha` (DateField) + `hora_inicio` (DateTimeField) — NO `started_at`
- **CSRF en JS:** siempre `csrf()` desde cookie, nunca `CSRF_TOKEN` hardcoded
- **Respuestas JSON:** siempre `{"success": true/false, ...}`
- **Cache Redis:** TTL estándar 4h para sesiones, 2h para previews
- **UUIDs:** usar en todos los modelos como PK pública, pero mantener AutoField interno para joins