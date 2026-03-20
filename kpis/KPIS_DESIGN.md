# Diseño y Roadmap — App `kpis`

> **Actualizado:** 2026-03-20 (Sesión Analista Doc — documentación completa)
> **Estado:** KPI-1 a KPI-6 completados en Sprint 7. App estable.
> **Fase del proyecto:** Fase 7 — Métricas de Contacto ✅
> **Migraciones:** `0001_initial` · `0002_refactor_callrecord` — ambas aplicadas

---

## Visión General

La app `kpis` centraliza las **métricas operativas de contact center** de Management360. Resuelve dos necesidades:

1. **Análisis histórico de rendimiento** — AHT, satisfacción y volumen por agente/supervisor/servicio/canal con visualización en dashboard y exportación CSV.
2. **Datos para integración BI** — API JSON que alimenta el ETL y el Report Builder de `analyst`, cerrando el ciclo WFM: `sim` genera datos sintéticos → `kpis` almacena métricas reales → `analyst` las procesa.

```
          ┌──────────────────────────────────────┐
          │           App kpis                    │
          │                                      │
   CSV/  ─►  generate_fake_data    CallRecord   ─►  export CSV
   Form       (faker + numpy)          │         
                                       │         
   Analyst ◄── kpi_api (JSON) ─────────┤         
   ETL/Report                          │         
                                       ▼         
                              aht_dashboard      
                         (Redis cache 5min)      
                                       │         
                              Chart.js (5 charts)
          └──────────────────────────────────────┘
```

---

## Estado de Implementación

| Módulo | Componente | Estado | Notas |
|--------|-----------|--------|-------|
| **Modelos** | `CallRecord` | ✅ Completo | UUID PK · 5 índices · `aht_min` property · semana auto-calculada |
| **Modelos** | `ExchangeRate` | ✅ Completo | UUID PK · `period` property · único por mes |
| **Dashboard** | `aht_dashboard` | ✅ Completo | 5 agrupaciones · Redis cache · colores fijos |
| **API** | `kpi_api` | ✅ Completo | `summary` + `records` paginado · integrado con analyst |
| **Export** | `export_data` | ✅ Completo | `StreamingHttpResponse` · `chunk_size=500` · utf-8-sig |
| **Data gen** | `generate_fake_data` | ✅ Completo | faker + numpy · distribuciones por servicio/canal |
| **Formularios** | `DataGenerationForm` | ✅ Completo | Pesos, semillas, batch_size configurables |
| **Formularios** | `UploadCSVForm` | ❌ Sin vista | Form definido, vista de upload nunca implementada |
| **Caché** | Redis TTL 5min | ✅ Completo | Key por usuario + rango · invalidación post-generación |
| **Seguridad** | `@login_required` | ✅ Completo | Todas las vistas protegidas · namespace correcto |
| **Tests** | `tests.py` | ❌ Stub | 3 líneas — sin tests reales |
| **Admin** | `admin.py` | ✅ Registrado | 48 líneas — modelos en admin |

---

## Arquitectura de Datos

### Jerarquía de modelos

```
CallRecord  (modelo principal)
  ├── dimensiones: fecha, semana, agente, supervisor, servicio, canal
  ├── métricas:    eventos, aht, evaluaciones, satisfaccion
  └── auditoría:   created_by → accounts.User (null=True, SET_NULL)

ExchangeRate  (tabla de referencia)
  └── date (unique) → rate PEN/USD
```

### Dependencias con otras apps

| Dependencia | Dirección | Punto de integración | Estado |
|-------------|-----------|---------------------|--------|
| `accounts.User` | kpis → accounts | `CallRecord.created_by` (null=True, SET_NULL) | ✅ Estable |
| `analyst` (ETL) | analyst → kpis | `kpi_api?format=records` como fuente ETL | ✅ KPI-3 |
| `analyst` (Report Builder) | analyst → kpis | 3 funciones WFM registradas | ✅ KPI-3 |

### Convención de fechas (CRÍTICO)

```
CallRecord.fecha   → DateField  — SIEMPRE usar para filtros temporales
CallRecord.semana  → IntegerField ISO — solo para compatibilidad, no filtrar por semana sin año
```

---

## Roadmap completado — Sprint 7

| ID | Tarea | Estado |
|----|-------|--------|
| KPI-1 | UUID PK + `fecha` DateField + 5 índices + `created_by` (migración IF NOT EXISTS) | ✅ |
| KPI-2 | Cache Redis 5min `kpis:dashboard:{user}:{desde}:{hasta}` · colores fijos | ✅ |
| KPI-3 | `/kpis/api/` JSON + 3 funciones WFM en Report Builder analyst | ✅ |
| KPI-4 | Dashboard sat promedio + top/bottom servicio + total eventos | ✅ |
| KPI-5 | `kpis_aht_report` — agrupa por agente/supervisor/canal/servicio/semana | ✅ |
| KPI-6 | `StreamingHttpResponse` + filtros fecha + `chunk_size=500` | ✅ |
| —     | Namespace `kpis:` + `login_required` + nav template corregido | ✅ |

---

## Roadmap pendiente — Sprint 9

| ID | Tarea | Prioridad | Notas |
|----|-------|-----------|-------|
| KPI-7 | Unificar `SERVICE_CHOICES` en `forms.py` con `SERVICIO_CHOICES` de `models.py` | 🔴 | Bug #69 — datos generados inconsistentes |
| KPI-8 | Implementar vista de upload CSV (`UploadCSVForm` existente sin conectar) | 🟠 | Permite ingresar datos reales sin generación sintética |
| KPI-9 | Fix `aht_por_semana` — ordenar por `fecha` para evitar ambigüedad cross-year | 🟠 | Bug #71 |
| KPI-10 | Agregar tests — `tests.py` es stub | 🟠 | Mínimo: test de API, filtros de fecha, `_build_chart()` |
| KPI-11 | Limpiar `forms.py` — doble import, estructura legacy | 🟡 | Bug #70 |
| KPI-12 | Agregar `updated_at` a `CallRecord` | 🟡 | Consistencia con resto del proyecto |

---

## Incidentes registrados

### INC-002 — 2026-03-18: `Duplicate column name created_at` en kpis.0002

**Síntoma:** Error al aplicar migración 0002.
**Causa:** La columna ya existía en la tabla desde migración previa.
**Resolución:** `RunSQL` con `IF NOT EXISTS` + `SeparateDatabaseAndState`.
**Lección:** Siempre usar `IF NOT EXISTS` en migraciones que agregan columnas a tablas preexistentes.

---

## Notas para Claude

- **`semana` es derivado de `fecha`** — se auto-calcula en `save()`. Si se crea un `CallRecord` sin `semana`, se calcula. Si se provee `semana`, se respeta. No recalcular manualmente.
- **`created_by` es `null=True`** en `CallRecord` — es intencional. No cambiar a CASCADE. Acceder siempre con `record.created_by` (puede ser `None`).
- **Cache key incluye `fecha_desde:fecha_hasta`** — si se cambia el formato de las fechas, las keys viejas quedan huérfanas hasta TTL.
- **`cache.delete_pattern()` puede no existir** — siempre verificar con `hasattr` antes de llamar.
- **`SERVICIO_CHOICES` y `CANAL_CHOICES` son module-level** — importar directamente: `from kpis.models import SERVICIO_CHOICES`.
- **`kpi_api` serializa UUID a string** — `str(r['id'])` y `str(r['fecha'])` antes de `JsonResponse`. Pandas/analyst los reciben como strings.
- **`ExchangeRate` no tiene `created_by`** — tabla de referencia global, no por usuario.
- **`aht_por_agente` está limitado a top 20** (`.order_by('avg_aht')[:20]`) — muestra los 20 agentes con menor AHT, no todos.
- **`generate_fake_data` requiere `faker` y `numpy`** — imports lazy dentro de la función POST. Si no están instalados, el error se captura y se muestra al usuario.
- **Namespace `kpis`** declarado en `urls.py` — usar siempre `kpis:dashboard`, `kpis:api`, etc.
