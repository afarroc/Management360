# Referencia de Desarrollo — App `kpis`

> **Actualizado:** 2026-03-20 (Sesión Analista Doc — Sprint 7.5 completado)
> **Audiencia:** Desarrolladores del proyecto y asistentes de IA (Claude)
> **Sprint:** S7 — KPI-1 a KPI-6 completados. Documentación completa generada S7.5.
> **Stats:** 11 archivos · models.py 148 L · views.py 338 L · forms.py 170 L · urls.py 13 L
> **Namespace:** `kpis` ✅

---

## Índice

| # | Sección | Contenido |
|---|---------|-----------|
| 1 | Resumen | Qué hace la app, sus pilares |
| 2 | Modelos | `CallRecord`, `ExchangeRate` — campo por campo |
| 3 | Formularios | `UploadCSVForm`, `DataGenerationForm` |
| 4 | Vistas | 5 vistas organizadas por función |
| 5 | URLs | Mapa completo de endpoints |
| 6 | Sistema de caché | Redis keys, TTL, invalidación |
| 7 | Integración con analyst | API, ETL, Report Builder |
| 8 | Convenciones críticas | Gotchas, fechas, choices |
| 9 | Bugs conocidos | Tabla con estado |
| 10 | Deuda técnica | Clasificada por prioridad |

---

## 1. Resumen

La app `kpis` implementa el módulo de **métricas de contact center** de Management360. Provee tres capacidades:

**Pilar 1 — Almacenamiento y dashboard de KPIs operativos**
`CallRecord` almacena registros semanales de AHT, satisfacción y volumen por agente/servicio/canal. El dashboard `aht_dashboard` agrega estos datos en 5 dimensiones con cache Redis por usuario y rango de fechas.

**Pilar 2 — Exportación y API JSON**
`export_data` genera CSV con `StreamingHttpResponse` para volúmenes grandes. `kpi_api` expone los datos como JSON en dos formatos (`summary` y `records` paginado) para consumo por `analyst` y otros clientes.

**Pilar 3 — Generación de datos sintéticos**
`generate_fake_data` + `DataGenerationForm` permiten poblar la BD con datos realistas (distribuciones numpy gaussianas) para testing y demos, con configuración total de agentes, servicios, canales y pesos.

---

## 2. Modelos

### 2.1 `CallRecord`

Registro de métricas semanales por agente / servicio / canal. Es el modelo principal de la app.

| Campo | Tipo | Notas |
|-------|------|-------|
| `id` | `UUIDField(primary_key=True)` | ✅ Convención del proyecto |
| `fecha` | `DateField(db_index=True)` | Primer día de la semana. **Usar para filtros de rango temporal** |
| `semana` | `IntegerField(db_index=True)` | Semana ISO — calculado automáticamente desde `fecha` en `save()`. Conservado por compatibilidad |
| `agente` | `CharField(100, db_index=True)` | Nombre del agente (string libre) |
| `supervisor` | `CharField(100, db_index=True)` | Nombre del supervisor |
| `servicio` | `CharField(50, choices=SERVICIO_CHOICES, db_index=True)` | Ver choices abajo |
| `canal` | `CharField(50, choices=CANAL_CHOICES, db_index=True)` | Ver choices abajo |
| `eventos` | `IntegerField(min=0)` | Volumen de eventos de la semana |
| `aht` | `FloatField(min=0)` | AHT en segundos |
| `evaluaciones` | `IntegerField(default=0, min=0)` | Evaluaciones de calidad |
| `satisfaccion` | `FloatField(default=0.0, min=0)` | Escala 1–10 |
| `created_by` | `FK(AUTH_USER_MODEL, null=True, SET_NULL)` | ⚠️ `null=True` — excepción intencional (no perder registros si se borra el usuario) |
| `created_at` | `DateTimeField(auto_now_add=True)` | ✅ |

**Choices a nivel de módulo:**

```python
SERVICIO_CHOICES = ['Reclamos', 'Consultas', 'Ventas', 'Soporte', 'Cobranzas']
CANAL_CHOICES    = ['Phone', 'Mail', 'Chat', 'WhatsApp', 'Social Media']
```

**Índices compuestos (5):**

| Nombre | Campos | Uso |
|--------|--------|-----|
| `kpis_cr_fecha_serv` | `fecha, servicio` | Query principal dashboard |
| `kpis_cr_fecha_canal` | `fecha, canal` | Dashboard por canal |
| `kpis_cr_fecha_agente` | `fecha, agente` | Dashboard por agente |
| `kpis_cr_fecha_sup` | `fecha, supervisor` | Dashboard por supervisor |
| `kpis_cr_sem_serv` | `semana, servicio` | Compatibilidad legacy |

**Métodos:**

- `save()` — auto-calcula `semana` desde `fecha` si `semana` no está seteado: `self.fecha.isocalendar()[1]`
- `aht_min` (property) — AHT en minutos con 2 decimales: `round(self.aht / 60, 2)`

**Ordering:** `['-fecha', 'agente']`

---

### 2.2 `ExchangeRate`

Tasas de cambio PEN/USD por mes. Usada para conversión de métricas financieras.

| Campo | Tipo | Notas |
|-------|------|-------|
| `id` | `UUIDField(primary_key=True)` | ✅ Convención del proyecto |
| `date` | `DateField(unique=True, db_index=True)` | Primer día del mes de referencia |
| `rate` | `DecimalField(max_digits=10, decimal_places=6, min=0)` | Tasa promedio PEN/USD — compra interbancaria |
| `created_at` | `DateTimeField(auto_now_add=True)` | ✅ |
| `updated_at` | `DateTimeField(auto_now=True)` | ✅ |

**Métodos:**

- `period` (property) — formato `MmmYY`: `self.date.strftime('%b%y').lower()` — ej: `"mar26"`
- `__str__` — ej: `"mar26: 3.850000 PEN/USD"`

**Ordering:** `['-date']`

⚠️ **Sin `created_by`** — modelo de configuración global, no por usuario.

---

## 3. Formularios

### 3.1 `UploadCSVForm`

Formulario para subir archivos CSV con detección de delimitador.

| Campo | Tipo | Notas |
|-------|------|-------|
| `csv_file` | `FileField` | Valida extensión `.csv` |
| `delimiter` | `ChoiceField` | Opciones: `,`, `;`, `\t`, `\|`, `auto` |

⚠️ **Bug #68** — Este formulario está importado en `views.py` pero **ninguna vista lo usa**. El endpoint de upload CSV nunca fue implementado. Import muerto.

---

### 3.2 `DataGenerationForm`

Formulario complejo para generación de datos sintéticos. Todos los campos tienen widgets Bootstrap (`form-control`, `form-select`).

| Campo | Tipo | Default | Notas |
|-------|------|---------|-------|
| `weeks` | `IntegerField(1–52)` | 12 | Semanas a generar hacia atrás desde hoy |
| `records_per_week` | `IntegerField(10–1000)` | 50 | Registros por semana |
| `services` | `MultipleChoiceField` | Todos | Checkboxes — servicios a incluir |
| `service_weights` | `CharField` | `"3,2,2,1,1"` | Pesos relativos por servicio (CSV de floats) |
| `channels` | `MultipleChoiceField` | Todos | Checkboxes — canales a incluir |
| `channel_weights` | `CharField` | `"4,2,3,1,2"` | Pesos relativos por canal |
| `num_agents` | `IntegerField(5–100)` | 20 | Agentes a simular |
| `num_supervisors` | `IntegerField(2–20)` | 5 | Supervisores |
| `min_evaluations` | `IntegerField(0–50)` | 1 | Evaluaciones mínimas |
| `max_evaluations` | `IntegerField(1–100)` | 20 | Evaluaciones máximas |
| `batch_size` | `IntegerField(100–5000)` | 1000 | Tamaño de lote para `bulk_create` |
| `random_seed` | `IntegerField(opcional)` | None | Semilla numpy para reproducibilidad |
| `clear_existing` | `BooleanField` | True | Si elimina datos antes de generar |

**Validaciones custom:**
- `clean_service_weights()` — verifica que el número de pesos coincida con servicios seleccionados y que sean todos positivos
- `clean_channel_weights()` — ídem para canales
- `clean()` — verifica que `min_evaluations <= max_evaluations`

⚠️ **Bug #69** — Los `SERVICE_CHOICES` en `forms.py` son `['Reclamos','Consultas','Soporte Técnico','Ventas','Información']` — **difieren** de `SERVICIO_CHOICES` en `models.py` (`['Reclamos','Consultas','Ventas','Soporte','Cobranzas']`). Los datos generados con "Soporte Técnico" o "Información" no tendrán match con las choices del modelo.

⚠️ **Bug #70 (forms.py)** — El archivo tiene **doble bloque de imports** (`from django import forms` aparece dos veces) y la clase `UploadCSVForm` está definida antes del segundo bloque. Es código legacy no limpiado.

---

## 4. Vistas

Todas las vistas tienen `@login_required`. No hay `@csrf_exempt`.

### 4.1 `kpi_home`

**URL:** `GET /kpis/`  
**Template:** `kpis/home.html`

Vista de entrada. Muestra conteo total de `CallRecord`. Contexto: `{'total_records': int}`.

---

### 4.2 `aht_dashboard`

**URL:** `GET /kpis/dashboard/?desde=YYYY-MM-DD&hasta=YYYY-MM-DD`  
**Template:** `kpis/dashboard.html`  
**Cache:** Redis — TTL 5 min, key por usuario + rango de fechas

Dashboard principal. Si no se proveen fechas, usa las últimas 12 semanas.

**Aggregaciones calculadas:**

| Variable | Tipo | Agrupación |
|----------|------|------------|
| `aht_por_servicio` | QuerySet anotado | `avg_aht`, `total_eventos`, `total_registros` — order `-avg_aht` |
| `aht_por_canal` | QuerySet anotado | `avg_aht`, `total_eventos` — order `-avg_aht` |
| `aht_por_semana` | QuerySet anotado | `avg_aht`, `total_eventos` — order `semana` ⚠️ ver bug #71 |
| `aht_por_supervisor` | QuerySet anotado | `avg_aht`, `total_eventos`, `avg_sat` — order `-avg_aht` |
| `aht_por_agente` | QuerySet anotado | `avg_aht`, `total_eventos`, `avg_sat` — order `avg_aht` — **top 20 con menor AHT** |

**Totales (`qs.aggregate()`):** `total_llamadas`, `aht_promedio`, `sat_promedio`, `total_eventos`, `total_evals`.

**Chart data (Chart.js):** 4 JSONs serializados con `_build_chart()`: `chart_data_json`, `aht_por_canal_json`, `aht_por_semana_json`, `aht_por_agente_json`. Colores fijos (no random).

**Contexto adicional:** `servicio_mas_alto`, `servicio_mas_bajo` (por AHT), `aht_promedio_min` (AHT en minutos), `cached_at` (timestamp del cache), `fecha_desde`, `fecha_hasta`.

⚠️ `fecha_desde`/`fecha_hasta` se añaden con `ctx.update()` **fuera del cache** — no se cachean, se recalculan en cada request.

---

### 4.3 `kpi_api`

**URL:** `GET /kpis/api/?desde=&hasta=&format=summary|records&page=&per_page=`  
**Auth:** `@login_required`  
**Respuesta:** `{"success": true, ...}`

Dos modos:

**`format=summary` (default):**
```json
{
  "success": true,
  "desde": "YYYY-MM-DD",
  "hasta": "YYYY-MM-DD",
  "summary": {"total": int, "avg_aht": float, "avg_sat": float, "max_aht": float, "min_aht": float, "total_ev": int},
  "by_servicio": [{"servicio": str, "total": int, "avg_aht": float}, ...],
  "by_canal": [{"canal": str, "total": int, "avg_aht": float}, ...]
}
```

**`format=records` (paginado):**
```json
{
  "success": true,
  "total": int,
  "page": int,
  "per_page": int,
  "records": [{"id": "uuid-str", "fecha": "YYYY-MM-DD", ...}, ...]
}
```

Parámetros: `page` (default 1), `per_page` (default 100, máx 500). UUID e `id` se serializan a string.

---

### 4.4 `export_data`

**URL:** `GET /kpis/export/?desde=&hasta=`  
**Respuesta:** CSV con `StreamingHttpResponse`, `Content-Disposition: attachment`

Exporta `CallRecord` filtrado por rango de fechas. Usa `qs.iterator(chunk_size=500)` — no carga todos los registros en memoria. Encoding: `utf-8-sig` (BOM para compatibilidad con Excel).

Columnas: `fecha`, `semana`, `agente`, `supervisor`, `servicio`, `canal`, `eventos`, `aht`, `evaluaciones`, `satisfaccion`.

Nombre de archivo: `call_records_{fecha_desde}_{fecha_hasta}.csv`.

---

### 4.5 `generate_fake_data`

**URL:** `GET|POST /kpis/generate-data/`  
**Template:** `kpis/generate_data.html`  
**Dependencias:** `faker`, `numpy`

`GET` — muestra `DataGenerationForm`.  
`POST` — valida el form, genera datos con distribuciones gaussianas por servicio:

| Servicio | Eventos (µ, σ) | AHT (µ, σ) | SAT (µ, σ) |
|---------|----------------|-------------|------------|
| Reclamos | N(85, 10) | N(1350, 100) | N(7.0, 0.8) |
| Consultas | N(45, 10) | N(400, 50) / N(1100, 50) si Mail | N(6.5, 0.7) |
| Otros | N(55, 12) | N(900, 200) | N(7.5, 0.5) |

**Ajuste de canal:** Chat, WhatsApp, Social Media → `aht = max(200, aht * 0.35)`.

**Límites de clipping:** eventos [5–150], aht [100–2000], satisfaccion [1.0–10.0].

Inserta con `bulk_create(batch_size)`. Invalida cache del usuario tras la inserción.

---

## 5. URLs

| Pattern | Name | Vista | Método |
|---------|------|-------|--------|
| `/kpis/` | `kpis:home` | `kpi_home` | GET |
| `/kpis/dashboard/` | `kpis:dashboard` | `aht_dashboard` | GET |
| `/kpis/api/` | `kpis:api` | `kpi_api` | GET |
| `/kpis/export/` | `kpis:export_data` | `export_data` | GET |
| `/kpis/generate-data/` | `kpis:generate_data` | `generate_fake_data` | GET, POST |

**Namespace:** `app_name = 'kpis'` ✅ declarado en `urls.py`.

---

## 6. Sistema de Caché

### Cache key

```python
_CACHE_PREFIX = 'kpis:dashboard'
_CACHE_TTL    = 300  # 5 minutos

# key = "kpis:dashboard:{user_id}:{fecha_desde}:{fecha_hasta}"
cache_key = f"kpis:dashboard:{request.user.id}:{fecha_desde}:{fecha_hasta}"
```

### Contenido cacheado

Todo el contexto del dashboard **excepto** `fecha_desde` y `fecha_hasta` (se añaden post-cache). Incluye los 4 JSONs de Chart.js, las 5 tablas de agrupación, los totales y `cached_at`.

### Invalidación

```python
# Tras generate_fake_data — solo si el backend soporta delete_pattern (django-redis)
cache.delete_pattern(f"kpis:dashboard:{request.user.id}:*") \
    if hasattr(cache, 'delete_pattern') else None
```

⚠️ La invalidación es **silenciosa** si el backend no soporta `delete_pattern`. Con Redis estándar funciona; con otros backends (locmem, memcache) el cache queda stale hasta TTL.

---

## 7. Integración con Analyst

### ETL source (analyst)

`kpi_api` con `format=records` es el endpoint que consume el ETL de `analyst`:

```
ETL source type: 'model'
app: kpis
model: CallRecord
Orden sugerido: fecha ASC, agente ASC
```

### Report Builder (KPI-3)

Se registraron 3 funciones WFM en el Report Builder de `analyst`:
- Cálculo de AHT promedio
- Service Level estimado
- Volumen de llamadas por período

### Notas de integración

`kpi_api` serializa UUIDs a string (`str(r['id'])`) y dates a `str(r['fecha'])` — compatible con pandas y el pipeline ETL de `analyst`.

---

## 8. Convenciones Críticas

### Fechas — CRÍTICO

| Campo | Tipo | Cuándo usar |
|-------|------|-------------|
| `fecha` | `DateField` | **Siempre para filtros de rango temporal** — `fecha__gte`, `fecha__lte` |
| `semana` | `IntegerField` | Solo para compatibilidad — ⚠️ ambigüedad cross-year (semana 1 de 2025 ≠ semana 1 de 2026) |

```python
# CORRECTO
CallRecord.objects.filter(fecha__gte=fecha_desde, fecha__lte=fecha_hasta)

# INCORRECTO — semana sin año es ambigua
CallRecord.objects.filter(semana=1)
```

### `created_by` con `null=True`

`CallRecord.created_by` usa `SET_NULL` con `null=True, blank=True`. Es una **excepción intencional** — el objetivo es no perder registros históricos de métricas si se elimina el usuario que los importó. No cambiar a CASCADE.

### Import de User

```python
# models.py — CORRECTO
from django.conf import settings
created_by = models.ForeignKey(settings.AUTH_USER_MODEL, ...)
```

### Choices a nivel de módulo

```python
# CORRECTO — importar desde el módulo
from kpis.models import SERVICIO_CHOICES, CANAL_CHOICES

# INCORRECTO
CallRecord.SERVICIO_CHOICES  # AttributeError — no están en la clase
```

---

## 9. Bugs Conocidos

| # | Estado | Descripción | Impacto | Fix |
|---|--------|-------------|---------|-----|
| #68 | ⬜ | `UploadCSVForm` importada en `views.py` sin uso — endpoint de upload CSV nunca implementado | Bajo — solo code smell | Eliminar import o implementar vista |
| #69 | ⬜ | `SERVICE_CHOICES` en `forms.py` difiere de `SERVICIO_CHOICES` en `models.py` ("Soporte Técnico" e "Información" vs "Soporte" y "Cobranzas") | Medio — datos generados no matchean choices del modelo | Unificar: importar `SERVICIO_CHOICES` desde `models.py` en el form |
| #70 | ⬜ | `forms.py` con doble bloque de `from django import forms` y estructura legacy | Bajo — funciona pero es confuso | Limpiar archivo — un solo bloque, un solo import |
| #71 | ⬜ | `aht_por_semana` ordena por `semana` (int ISO) sin considerar el año — datos de semana 1 de diferentes años se mezclan | Medio — el gráfico semanal no es correcto en datasets que cruzan enero | Ordenar por `fecha` y agrupar por `fecha` truncada a semana |
| #72 | ⬜ | `cache.delete_pattern()` silencioso si el backend no lo soporta — el cache queda stale tras `generate_fake_data` en entornos sin `django-redis` | Bajo (dev/test) | Documentar dependencia en settings; alternativa: TTL corto |

---

## 10. Deuda Técnica

### Alta prioridad

- **Bug #69 — Unificar choices** entre `forms.py` y `models.py`: importar `SERVICIO_CHOICES`/`CANAL_CHOICES` desde `models.py` en el form. Bloquea consistencia de datos generados.
- **Implementar `UploadCSVForm`** o eliminarla — actualmente es un import muerto. La funcionalidad de importar registros reales vía CSV no existe y es necesaria.

### Media prioridad

- **Fix bug #71 — ordenar por fecha** en `aht_por_semana` para datasets que cruzan año
- **Limpiar `forms.py`** — un solo bloque, unificar imports
- **Agregar `updated_at` a `CallRecord`** — solo tiene `created_at` (inconsistencia con `ExchangeRate`)
- **Tests** — `tests.py` es stub (3 líneas). Prioridad: test de `_build_chart()`, filtros de fecha y la API

### Baja prioridad

- Agregar `created_by` a `ExchangeRate` (actualmente sin propietario)
- Implementar invalidación de cache robusta sin `delete_pattern`
- Soporte de encodings en CSV export (actualmente solo `utf-8-sig`)
- Registrar modelos en `admin.py` — actualmente con contenido (48 L según CONTEXT) pero no documentado
