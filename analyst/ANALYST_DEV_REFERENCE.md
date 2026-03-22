# Referencia de Desarrollo — App `analyst`

> **Audiencia:** Desarrolladores del proyecto y asistentes de IA (Claude, Copilot, etc.)
> **Actualizado:** 2026-03-22 (Sprint 9 — ANALYST-BUG + EVENTS-AI-3 + ANALYST-GTD + ANALYST-ACD)
> **Archivos cubiertos:** 38 / 52
> **Proyecto:** Management360 · Django app

---

## Índice rápido

| Sección | Contenido |
|---------|-----------|
| 1. Visión general | Qué hace la app, stack |
| 2. Estructura de directorios | Árbol completo comentado |
| 3. Modelos | StoredDataset · Report · ETLSource · ETLJob · AnalystBase · CrossSource · Dashboard · DashboardWidget |
| 4. Flujo de carga de archivos | Pipeline completo |
| 5. Subpaquete data_upload_async | SPA endpoints |
| 6. Servicios | Capa de negocio, procesamiento |
| 7. Utilidades | Clipboard, validadores, cálculos |
| 8. ETL Manager | Extracción, seguridad, ejecución |
| 9. Dataset Manager | Persistencia de datasets |
| 10. Clipboard | Portapapeles por sesión |
| 11. Report Builder | Reportes calculados con funciones registradas |
| 11b. Integración WFM | sim.Interaction + kpis.CallRecord como fuentes |
| 12. CrossSource | Cruces entre fuentes |
| 13. Dashboard | Paneles de visualización con widgets |
| 14. Formularios y validaciones | DataUploadForm |
| 15. Endpoints | Todos los endpoints |
| 16. Seguridad | CSRF, modelos prohibidos, ETL |
| 17. Estado JS (STATE) | Variables del cliente |
| 18. Convenciones CSS / UI | Patrones de interfaz |
| 19. Constantes y settings | Valores configurables |
| 20. Convenciones del proyecto | Patrones, nomenclatura |
| 21. Bugs conocidos | Issues activos y corregidos |
| 22. Pendientes de documentar | Archivos no revisados |

---

## 1. Visión general

`analyst` es una app Django de **gestión y análisis de datos** que permite a usuarios autenticados:

- Cargar archivos **CSV / XLS / XLSX** y mapearlos a cualquier modelo Django para importación masiva via `bulk_create`
- Editar DataFrames en memoria (filtros, tipo de dato, valores nulos, duplicados, normalización) antes de importar
- Persistir DataFrames como **`StoredDataset`** (BD + Redis) para reutilización entre sesiones
- Copiar DataFrames temporalmente al **portapapeles** de la sesión activa
- Extraer datos desde modelos ORM o SQL raw via el gestor **ETL** — incluyendo `events` (GTD/InboxItems)
- Cruzar fuentes de datos con **`CrossSource`** (join / concat entre StoredDataset, AnalystBase, ETLSource, Clipboard)
- Construir **reportes** calculados sobre datasets almacenados con funciones registradas
- Componer **dashboards** de visualización con widgets configurables (KPI, tabla, gráficos) — incluyendo preset GTD Overview

### Stack técnico relevante

| Componente | Detalle |
|------------|---------|
| Framework | Django (`login_required` en todas las vistas) |
| Cache | Redis (recomendado) |
| DataFrame | pandas + numpy |
| Excel | openpyxl (análisis de rangos), pandas ExcelFile (lectura) |
| Encoding | chardet para detección automática de CSV |
| Seguridad | `django.core.signing.Signer` en portapapeles; whitelist de modelos en ETL |
| Charts | Chart.js 4.4.1 (cdnjs) — dashboards |
| Frontend | SPA en templates HTML con `#analyst-root` como scope CSS |

---

## 2. Estructura de directorios

```
analyst/
├── models.py                       # StoredDataset · Report · ETLSource · ETLJob
│                                   # AnalystBase · CrossSource · Dashboard · DashboardWidget
├── forms.py                        # DataUploadForm
├── urls.py                         # ~80 endpoints + dashboards/gtd-overview/
├── constants.py                    # MAX_FILE_SIZE · FORBIDDEN_MODELS · DEFAULT_CHUNK_SIZE
├── signals.py                      # Hooks post-save
├── report_functions.py             # Registro de funciones (13 funciones — 7 generales + 3 WFM/sim + 3 WFM/kpis)
├── apps.py
├── admin.py
│
├── views/
│   ├── __init__.py
│   ├── data_upload.py              # Vista GET/POST del panel principal
│   ├── clipboard.py
│   ├── dataset_manager.py
│   ├── etl_manager.py              # Incluye _extract_events_items() — fuente events/GTD
│   ├── analyst_base.py             # AnalystBase (18 endpoints)
│   ├── cross_source.py             # CrossSource (10 endpoints)
│   ├── report_builder.py           # Report Builder (7 endpoints)
│   ├── dashboard.py                # Dashboard + widgets (11 endpoints) + gtd_overview_preset
│   ├── excel_analyze.py
│   ├── file_views.py
│   ├── other_tools.py
│   └── data_upload_async/
│       ├── __init__.py
│       ├── _core.py
│       ├── upload.py
│       ├── edit.py
│       ├── filters.py
│       ├── defaults.py
│       ├── dataset.py
│       └── clipboard.py
│
├── services/
│   ├── file_processor_service.py   # Servicio central — process_file() entrada programática
│   ├── base_validator.py           # Validacion AnalystBase
│   ├── cross_engine.py             # Motor de cruce
│   ├── excel_processor.py          # process_excel() — usado directo por _handle_preview()
│   ├── excel_analyzer.py
│   ├── model_mapper.py             # Fuzzy matching columna->campo
│   ├── data_importer.py            # bulk_create
│   ├── data_processor.py
│   └── planning.py                 # Erlang C
│
├── utils/
│   ├── clipboard.py                # DataFrameClipboard
│   ├── validators.py
│   ├── calculations.py
│   └── json_encoder.py
│
└── templates/analyst/
    ├── upload_data_csv.html         # Panel principal SPA (~5540 lineas)
    ├── dataset_manager.html
    ├── etl_manager.html             # Incluye tab Events/GTD con hints y labels
    ├── analyst_base.html            # SPA
    ├── cross_source.html            # SPA
    ├── report_builder.html          # SPA
    ├── dashboard.html               # SPA (~960 lineas) + modal GTD Overview + ACD widget UI
    ├── load_clipboard_form.html
    └── partials/
        └── clipboard_details.html
```

### Migraciones aplicadas

| Migracion | Contenido |
|-----------|-----------|
| `0006_add_analyst_base` | CreateModel AnalystBase + AddField ETLSource.analyst_base |
| `0007_*` | Limpieza generada por Django |
| `0008_*` | AddField ETLSource.analyst_base + AlterField model_path blank |
| `0009_add_cross_source` | CreateModel CrossSource |
| `0010_alter_crosssource_id` | AlterField id |
| `0011_add_dashboard` | CreateModel Dashboard + CreateModel DashboardWidget |
| `0012_add_pipeline` | CreateModel Pipeline + CreateModel PipelineRun |

---

## 3. Modelos

### `StoredDataset`

Dataset persistente con doble almacenamiento: Redis + `data_blob` en BD como respaldo.

```python
class StoredDataset(models.Model):
    id           = models.UUIDField(primary_key=True, default=uuid.uuid4)
    name         = models.CharField(max_length=200)
    cache_key    = models.CharField(max_length=120, unique=True)
    rows         = models.PositiveIntegerField()
    col_count    = models.PositiveIntegerField()
    columns      = models.JSONField()        # Lista de nombres de columna
    dtype_map    = models.JSONField()        # {"col": "dtype_str"}
    source_file  = models.CharField(max_length=500)
    data_blob    = models.TextField()        # pickle + base64 del DataFrame completo
    created_by   = models.ForeignKey(User, ...)
```

**Clave Redis:** `"stored_dataset_{uuid}"` — `timeout=None` (sin expiracion).

---

### `Report`

Reporte calculado ejecutado por una funcion registrada en `report_functions.py`.

```python
class Report(models.Model):
    id           = models.UUIDField(primary_key=True, default=uuid.uuid4)
    name         = models.CharField(max_length=200)
    function_key = models.CharField(max_length=100)   # clave en _REGISTRY
    sources      = models.JSONField(default=list)      # [{type, ref, name}, ...]
    params       = models.JSONField(default=dict)
    status       = models.CharField(choices=REPORT_STATUS)  # pending/running/done/error
    error_msg    = models.TextField(blank=True)
    result_data  = models.JSONField(default=list)      # list-of-dicts
    result_meta  = models.JSONField(default=dict)      # {rows, columns, dtype_map, generated_at}
    created_by   = models.ForeignKey(User, ...)
```

---

### `ETLSource` / `ETLJob`

Ver seccion 8 (ETL Manager).

---

### `AnalystBase`

Base de datos dinamica del analista. Schema en JSONField, datos en `StoredDataset` asociado.

```python
class AnalystBase(models.Model):
    FIELD_TYPES = ['text','number','decimal','date','datetime','boolean','choice','email','phone']
    id          = models.UUIDField(primary_key=True, default=uuid.uuid4)
    name        = models.CharField(max_length=200)
    category    = models.CharField(max_length=50, blank=True, choices=CATEGORIES)
    schema      = models.JSONField(default=list)
    dataset     = models.OneToOneField('StoredDataset', null=True, blank=True,
                                       on_delete=models.SET_NULL, related_name='analyst_base')
    row_count   = models.IntegerField(default=0)
    created_by  = models.ForeignKey(User, ...)
```

---

### `CrossSource`

Cruce configurable entre dos fuentes. Resultado guardado como `StoredDataset`.

```python
class CrossSource(models.Model):
    id          = models.UUIDField(primary_key=True, default=uuid.uuid4)
    name        = models.CharField(max_length=200)
    config      = models.JSONField()
    # {
    #   "operation": "left_join|inner_join|outer_join|concat",
    #   "left":  {"type": "stored_dataset|analyst_base|etl_source|clip",
    #             "id": "uuid_o_clip_key", "alias": "...", "columns": []},
    #   "right": {...},
    #   "on":    [{"left": "col_a", "right": "col_b"}],
    #   "suffixes": ["_izq","_der"],
    #   "post_filters": [{"field","lookup","value","negate"}],
    #   "output_columns": []
    # }
    last_result    = models.ForeignKey('StoredDataset', null=True, blank=True, on_delete=models.SET_NULL)
    last_run_at    = models.DateTimeField(null=True, blank=True)
    last_row_count = models.IntegerField(default=0)
    created_by     = models.ForeignKey(User, ...)
```

---

### `Pipeline` / `PipelineRun`

Secuencia grabada de pasos de transformacion re-ejecutable sobre cualquier `StoredDataset`.

```python
class Pipeline(models.Model):
    id             = models.UUIDField(primary_key=True, default=uuid.uuid4)
    name           = models.CharField(max_length=200)
    steps          = models.JSONField(default=list)
    # steps = [{"order":0,"type":"delete_columns","label":"...","params":{...}}, ...]
    source_dataset = models.ForeignKey('StoredDataset', null=True, blank=True, ...)
    created_by     = models.ForeignKey(User, ...)

class PipelineRun(models.Model):
    pipeline        = models.ForeignKey(Pipeline, related_name='runs')
    input_dataset   = models.ForeignKey('StoredDataset', related_name='pipeline_runs_as_input')
    result_dataset  = models.ForeignKey('StoredDataset', null=True, ...)
    status          = # idle/running/done/error
    steps_completed = models.PositiveIntegerField()
    duration_s      = models.FloatField()
    runtime_params  = models.JSONField()  # overrides para params de pasos especificos
```

**Tipos de paso (11):** `delete_columns` · `rename_column` · `replace_values` · `fill_na` · `convert_date` · `convert_dtype` · `normalize_text` · `drop_duplicates` · `sort_data` · `filter_delete` · `filter_replace`

### `Dashboard` / `DashboardWidget`

Panel de visualizacion con widgets en grid de 12 columnas.

```python
class Dashboard(models.Model):
    id          = models.UUIDField(primary_key=True, default=uuid.uuid4)
    name        = models.CharField(max_length=200)
    is_public   = models.BooleanField(default=False)
    layout      = models.JSONField(default=list)
    # [{"widget_id": "uuid", "col": 0, "width": 6, "row_order": 0}, ...]
    created_by  = models.ForeignKey(User, ...)

class DashboardWidget(models.Model):
    WIDGET_TYPES = ['kpi_card','table','bar_chart','line_chart','pie_chart','text']
    id          = models.UUIDField(primary_key=True, default=uuid.uuid4)
    dashboard   = models.ForeignKey(Dashboard, on_delete=models.CASCADE, related_name='widgets')
    widget_type = models.CharField(max_length=20)
    title       = models.CharField(max_length=200, blank=True)
    source      = models.JSONField(default=dict)
    # {"type": "report|dataset|cross_source|analyst_base|sim|events", "id": "uuid"}
    config      = models.JSONField(default=dict)
    # kpi_card:   {value_col, aggregation: sum|avg|count|max|min|last, format: number|percent|currency}
    # table:      {columns: [], page_size: 10}
    # bar_chart:  {x_col, y_cols: [], stacked: false, limit: 50}
    # line_chart: {x_col, y_cols: [], fill: false, limit: 50}
    # pie_chart:  {label_col, value_col, limit: 12}
    # text:       {content: "texto libre"}
```

---

## 4. Flujo de carga de archivos

```
1. Usuario sube archivo (POST multipart)  ->  data_upload.py
2. FileProcessorService detecta encoding / extension
3. ExcelProcessor (XLSX) o pandas (CSV)  ->  DataFrame crudo
4. ModelMapper fuzzy-matching columnas -> campos del modelo
5. JSON de preview -> Redis "df_preview_{uuid}" (TTL 2h)
6. renderPreview() en browser construye la UI
7. Operaciones de edicion -> endpoints async -> modifican DF en Redis -> re-render
8. doConfirmUpload() -> DataImporter.bulk_create() -> registros en BD
```

---

## 5. Subpaquete data_upload_async

Todos los endpoints devuelven `{"success": bool, ...}` y operan sobre el DF en Redis.

| Modulo | Endpoints clave |
|--------|----------------|
| `upload.py` | `preview_async`, `preview_page_async`, `confirm_upload_async`, `reanalyze_async` |
| `edit.py` | `delete_columns_async`, `rename_column_async`, `convert_dtype_async`, `normalize_text_async`, `sort_data_async`, `drop_duplicates_async` |
| `filters.py` | `replace_values_async`, `fill_na_async`, `filter_rows_*`, `filter_unique_values_async` |
| `defaults.py` | `apply_field_defaults_async` (11 estrategias de relleno) |
| `dataset.py` | `save_as_dataset` |
| `clipboard.py` | `save_clipboard_async`, `load_clip_as_preview` |

**Patron obligatorio `_edit`:**
```python
def mi_operacion_async(request):
    def _op(df, body):
        df["col"] = df["col"].str.upper()
        return df, None   # (df_transformado, error_msg|None)
    return _edit(request, _op)
```

---

## 6. Servicios

| Servicio | Responsabilidad |
|----------|----------------|
| `FileProcessorService` | Orquesta pipeline de carga. `normalize_name()` es la funcion canonica. `process_file()` es la entrada programática (bulk import). |
| `BaseValidator` | Valida filas contra schema AnalystBase. Persiste DF en Redis + `data_blob`. |
| `CrossEngine` | Ejecuta cruces. Resuelve fuentes, merge/concat, post-filtros, guarda StoredDataset. |
| `ModelMapper` | Fuzzy matching columna->campo con `difflib`. |
| `DataImporter` | `bulk_create` en chunks. Estadisticas de exito/error por fila. |
| `ExcelProcessor` | Lectura con hoja, rango y sin-cabecera. `process_excel()` usado directamente por `_handle_preview()`. |
| `ExcelAnalyzer` | Detecta regiones de datos automaticamente en XLSX. |

### ⚠️ Arquitectura crítica — dos rutas de procesamiento Excel (post Bug #2/#3)

| Ruta | Usada por | Retorna |
|------|-----------|---------|
| `ExcelProcessor.process_excel()` | `_handle_preview()` en `data_upload.py` | `(df, metadata)` |
| `FileProcessorService.process_excel()` | `process_file()` — entrada programática | `(records, preview, columns)` |

Ambas rutas tienen `no_header` propagado correctamente tras Bug #3. **NUNCA** llamar a `FileProcessorService` desde `_handle_preview()` ni viceversa — son rutas independientes.

---

## 7. Utilidades

### `DataFrameClipboard`

| Metodo | Descripcion |
|--------|-------------|
| `save(request, df, key, meta)` | Guarda en sesion firmado |
| `retrieve_df(request, key)` | Devuelve `(df, meta)` o `(None, None)` |
| `list_clips(request)` | Lista con metadatos — valores sanitizados a primitivos Python |
| `delete(request, key)` | Elimina un clip |

---

## 8. ETL Manager

### Seguridad (doble capa)

1. Al guardar `ETLSource`: modelo validado contra `ANALYST_ETL_ALLOWED_APPS`
2. Al ejecutar job: re-validado en `_run_extraction()`

### Orden de ramas en `_run_extraction()`

```python
if getattr(source, 'sim_account_id', None):    # sim.Interaction — prioridad 0
    return _extract_sim_account(...)
if getattr(source, 'analyst_base_id', None):   # AnalystBase — prioridad 1
    return _extract_analyst_base(...)
if source.events_model:                         # events GTD — prioridad 2 ✨
    return _extract_events_items(...)
if source.sql_override.strip():                 # SQL raw
    ...
# ORM path — kpis.CallRecord y cualquier modelo Django permitido
```

### Fuentes ETL disponibles (post Sprint 9)

| Tipo | Modelo fuente | Filtros soportados | Orden |
|------|--------------|-------------------|-------|
| `sim` | `sim.Interaction` | `date_from`, `date_to`, `run_id`, `canal` | `fecha ASC, hora_inicio ASC` |
| `kpis` | `kpis.CallRecord` | `fecha__gte`, `fecha__lte` | `fecha ASC, agente ASC` |
| `events` ✨ | `events.InboxItem` / GTD items | `created_by`, `status`, `date_range` | `created_at ASC` |
| `analyst_base` | `AnalystBase` dataset | — | por `StoredDataset` |
| `model` (ORM) | Cualquier modelo en `ANALYST_ETL_ALLOWED_APPS` | JSONField filters | definido en source |
| `sql` | Query raw SELECT | — | definido en SQL |

> **CRÍTICO:** En `kpis.CallRecord` el campo de fecha es `fecha` (DateField). Nunca usar `start_time`.
> En `sim.Interaction` el campo de fecha es `fecha` (DateField) + `hora_inicio` (DateTimeField). Nunca usar `started_at`.

### Fuente `events` — integración GTD (EVENTS-AI-3) ✨

```python
# etl_manager.py — funciones nuevas
_extract_events_items(source, filters)
    # Extrae InboxItems del usuario con los campos definidos en _events_item_fields()
    # Retorna DataFrame con columnas: id, title, status, priority, due_date,
    #                                  project, tags, created_at, updated_at

_events_item_fields()
    # Retorna lista de campos disponibles para la fuente events

# etl_source_save() — acepta events_model como campo de ETLSource
# etl_source_run()  — delega a _extract_events_items() si source.events_model
# etl_models_api()  — incluye events models en la respuesta
# _source_row()     — serializa events_model en la lista de fuentes del template
```

**Template ETL (`etl_manager.html`):** incluye tab "Events/GTD" con hints contextuales y labels descriptivos por campo.

---

## 9. Dataset Manager

Endpoints bajo `analyst/datasets/`:

| Endpoint | Descripcion |
|----------|-------------|
| `dataset_list` | Lista + HTML |
| `dataset_save` | Guarda preview activo como StoredDataset |
| `dataset_columns_api` | Columnas de datasets o modelos Django |
| `dataset_preview` | Preview paginado (usado por `loadDatasetAsPreview`) |
| `dataset_export` | CSV con BOM UTF-8 |
| `dataset_delete` | Elimina BD + Redis |

---

## 10. Clipboard

Portapapeles temporal (sesion). Seccion visible en `upload_data_csv.html` al final de la pagina con botones cargar, ver y eliminar.

---

## 11. Report Builder

### Registro de funciones (`report_functions.py`)

```python
@register(
    key="my_fn",
    label="Mi Funcion",
    category="Categoria",
    sources=[{"id":"src","label":"Fuente","required":True}],
    params=[{"id":"col","label":"Columna","type":"column_select","source":"src","required":True}],
)
def my_fn(sources: dict, params: dict) -> pd.DataFrame:
    return result_df
```

**Tipos de param:** `column_select` · `multi_column` · `number` · `boolean` · `text` · `choice`

> `choice` — selector cerrado de opciones. Requiere `choices: [...]` en la definición del param.

### Funciones registradas (13)

| key | label | category | Fuentes |
|-----|-------|----------|---------|
| `quality_avg` | Promedio de Notas de Calidad | Calidad | base + notes |
| `planilla_summary` | Resumen de Planilla | RRHH | planilla |
| `period_comparison` | Comparativa entre Periodos | Análisis | periodo_a + periodo_b |
| `ranking` | Ranking por Métrica | Análisis | data |
| `attendance_report` | Reporte de Asistencia | RRHH | attendance |
| `performance_report` | Reporte de Desempeño vs Meta | Análisis | performance |
| `funnel_report` | Embudo de Conversión | Análisis | data |
| `sim_agent_performance` | Performance por Agente (WFM) | WFM | interactions (sim) |
| `sim_inbound_daily` | KPIs Inbound Diarios (WFM) | WFM | interactions (sim) |
| `sim_contact_funnel` | Embudo de Contactabilidad (Outbound) | WFM | interactions (sim) |
| `kpis_aht_report` | Reporte AHT por Dimensión | WFM | callrecords (kpis) |
| `kpis_satisfaction_report` | Reporte de Satisfacción por Agente | WFM | callrecords (kpis) |
| `kpis_weekly_trend` | Tendencia Semanal de KPIs | WFM | callrecords (kpis) |

### Fuentes soportadas en `_load_source()`

`dataset` · `analyst_base` · `cross_source` · `clip` · `model` · **`sim`** · **`kpis`**

Todos con fallback a `data_blob` si Redis no está disponible.

> `sim` → carga `sim.Interaction` filtrado por `sim_account_id` vía ETL.
> `kpis` → carga `kpis.CallRecord` vía `/kpis/api/?format=records` o ETL ORM.

### Endpoints

| URL | Descripcion |
|-----|-------------|
| `reports/` | Panel HTML |
| `reports/build/` | Ejecuta funcion, persiste Report |
| `reports/api/functions/` | Registro en JSON |
| `reports/<id>/detail/` | Datos paginados |
| `reports/<id>/delete/` | Elimina |
| `reports/<id>/export/` | CSV con BOM |
| `reports/<id>/rerun/` | Re-ejecuta con datos frescos |

---

## 11b. Integración WFM — sim + kpis

### Flujo recomendado

```
ETL Manager → kpis.CallRecord (o sim.Interaction)
    → StoredDataset (guardado con nombre "callrecords_semXX")
    → Report Builder → función kpis_aht_report / sim_agent_performance
    → Report guardado → Dashboard widget (kpi_card o bar_chart)
```

### Columnas esperadas por las funciones WFM

**`sim.Interaction` (para sim_*):**

| Columna | Tipo | Notas |
|---------|------|-------|
| `agente` | str | código del agente |
| `fecha` | date | campo de fecha — NO `started_at` |
| `hora_inicio` | datetime | hora de inicio |
| `duracion_s` | int | duración en segundos |
| `acw_s` | int | post-llamada |
| `status` | str | atendida / abandonada / venta / agenda / no_contacto |
| `canal` | str | inbound / outbound / digital |
| `skill` | str | PLD / CONVENIOS / PORTABILIDAD... |

**`kpis.CallRecord` (para kpis_*):**

| Columna | Tipo | Notas |
|---------|------|-------|
| `fecha` | date | campo principal de filtro temporal |
| `semana` | int | calculado automáticamente en save() |
| `agente` | str | |
| `supervisor` | str | |
| `servicio` | str | Reclamos / Consultas / Ventas... |
| `canal` | str | Phone / Mail / Chat / WhatsApp... |
| `aht` | float | segundos |
| `eventos` | int | cantidad de interacciones |
| `satisfaccion` | float | escala 1–10 |
| `evaluaciones` | int | cantidad de evaluaciones |

### ETL directo kpis

```python
# analyst/views/etl_manager.py — fuente kpis
GET /kpis/api/?desde=YYYY-MM-DD&hasta=YYYY-MM-DD&format=records&per_page=500
# Paginado, max 500 por request
# Retorna: {success, total, page, records: [{fecha, semana, agente, ...}]}
```

---

## 12. CrossSource

### Motor (`cross_engine.py`)

Resuelve fuentes, seleccion de columnas, merge/concat, post-filtros, guarda resultado como StoredDataset.

**Operaciones:** `left_join` · `inner_join` · `outer_join` · `concat`

**Post-filtros:** `[{field, lookup, value, negate}]` — mismo formato que `ETLSource.filters`

### Endpoints (bajo `analyst/cross/`)

| URL | Descripcion |
|-----|-------------|
| `cross/` | Lista + HTML |
| `cross/create/` | Crear |
| `cross/api/` | Lista JSON |
| `cross/api/columns/` | Columnas de una fuente |
| `cross/<id>/update/` | Editar config |
| `cross/<id>/run/` | Ejecutar -> guarda StoredDataset |
| `cross/<id>/delete/` | Eliminar |
| `cross/<id>/preview/` | Preview paginado del ultimo resultado |

---

## 13. Dashboard

### Renderizado de widgets (`dashboard.py -> _compute_widget_data`)

| widget_type | Salida |
|-------------|--------|
| `kpi_card` | `{value, label, format, rows}` — agrega con sum/avg/count/max/min/last |
| `table` | `{columns, rows, total, page, pages}` — paginado |
| `bar_chart` / `line_chart` | `{labels, datasets[]}` — formato Chart.js |
| `pie_chart` | `{labels, values, backgroundColors}` — Chart.js doughnut |
| `text` | `{content}` — texto libre |

### Tipos de fuente en `DashboardWidget.source`

```python
source = {
    "type": "report|dataset|cross_source|analyst_base|sim|events",
    "id":   "uuid_del_recurso"
}
```

| type | Recurso | Carga vía |
|------|---------|-----------|
| `report` | `Report` | `result_data` JSONField |
| `dataset` | `StoredDataset` | Redis → fallback data_blob |
| `cross_source` | `CrossSource.last_result` | StoredDataset |
| `analyst_base` | `AnalystBase.dataset` | StoredDataset |
| `sim` | `sim.SimAccount` interacciones | ORM → `Interaction.objects.filter(account=id)` |
| `events` ✨ | `events.InboxItem` / GTD items | `_extract_events_items()` → ETL |

### Modal selector de fuente (dashboard.html)

El modal de creación/edición de widget incluye selector de tipo de fuente con la opción `events` habilitada. Al seleccionar `events`, muestra los campos de `InboxItem` disponibles con hints contextuales.

### Widget ACD — UI enriquecida (ANALYST-ACD) ✨

Los widgets que renderizan datos ACD muestran:
- **Labels ricos** con formato `[canal · status]` — ej. `[inbound · atendida]`
- **Hints contextuales** que explican cada KPI al hacer hover
- Presentación diferenciada por canal e estado de interacción

### GTD Overview — preset 6 widgets (ANALYST-GTD) ✨

```
POST /analyst/dashboards/gtd-overview/
Body JSON: {name?, description?}  — fallback a valores por defecto
```

Crea un `Dashboard` + 6 `DashboardWidget` con layout predefinido y retorna el dashboard creado:

| Fila | Widgets | Tipo |
|------|---------|------|
| 0 | 3 KPI cards | `kpi_card` |
| 1 | 2 tablas | `table` |
| 2 | 1 tabla | `table` |

El modal de GTD Overview es accesible desde el toolbar del dashboard (`bi-kanban`, `tip-teal`) y crea el preset en un click usando `submitGtdOverview()` — mismo patrón de re-render que `submitDashboard()`.

### Endpoints (bajo `analyst/dashboards/`)

| URL | Descripcion |
|-----|-------------|
| `dashboards/` | Lista + SPA HTML |
| `dashboards/create/` | Crear |
| `dashboards/<id>/view/` | JSON completo con todos los widgets y datos |
| `dashboards/<id>/update/` | Nombre / descripcion / is_public |
| `dashboards/<id>/delete/` | Eliminar |
| `dashboards/<id>/layout/save/` | Guardar posiciones del grid |
| `dashboards/<id>/widgets/add/` | Agregar widget |
| `dashboards/<id>/widgets/<wid>/update/` | Editar widget |
| `dashboards/<id>/widgets/<wid>/delete/` | Eliminar widget |
| `dashboards/<id>/widgets/<wid>/data/` | Datos frescos de un widget |
| `dashboards/gtd-overview/` ✨ | Genera preset GTD Overview (6 widgets) |

---

## 14. Formularios y validaciones

### `DataUploadForm`

Campo principal: `model` — selector de modelo destino. Validado contra `FORBIDDEN_MODELS` + whitelist de apps.

✅ **Bug #1 resuelto** — `clean_file()` duplicado eliminado. El archivo tenía comentarios huérfanos de una definición anterior; eliminados en commit `ef3678e7`.

---

## 15. Endpoints completos

**Carga / edicion:** preview · page · confirm · reanalyze · delete-columns · replace-values · fill-na · convert-date · rename-column · drop-duplicates · sort-data · convert-dtype · normalize-text · filter-count · filter-delete · filter-replace · unique-values · apply-defaults

**Clipboard:** save · load · details · export · list · load-form · load-form-data · delete · clear-all

**Datasets:** list · save · columns-api · preview · export · delete

**Reports:** list · build · functions-api · detail · delete · export · **rerun**

**CrossSource:** list · create · api · columns-api · update · run · delete · preview

**AnalystBase:** list · create · api · sources · columns-from-clip · schema · delete · data · rows/add · rows/edit · rows/delete · bulk-import · bulk-import-raw · export · columns-api

**Dashboard:** list · create · view · update · delete · layout/save · widgets/add · widgets/update · widgets/delete · widgets/data · **gtd-overview** ✨

**ETL:** list · sources/save · sources/delete · sources/run · jobs/status · models-api · model-fields-api

**Otras:** file-tree · calculate-agents · traffic-intensity · analyze-excel

---

## 16. Seguridad

### CSRF

```javascript
// CORRECTO
fetch(url, { headers: { 'X-CSRFToken': csrf() } })

// INCORRECTO — CSRF_TOKEN no existe como variable global
fetch(url, { headers: { 'X-CSRFToken': CSRF_TOKEN } })  // ReferenceError
```

### Modelos prohibidos

`FORBIDDEN_MODELS` en `constants.py`. Case-insensitive. Apps `auth/admin/contenttypes/sessions` excluidas a nivel de query.

### ETL — Doble validacion

Al guardar `ETLSource` Y al ejecutar el job.

---

## 17. Estado JS (STATE)

```javascript
const STATE = {
    cacheKey:        null,   // "df_preview_{uuid}" — clave Redis del DF activo
    model:           null,   // "app.ModelName"
    stats:           null,   // {total_rows, total_cols, mapped_count, required_count}
    filename:        null,
    activeTab:       null,   // tab de herramientas activo
    currentPage:     1,
    currentPageSize: 50
};
```

### Funciones JS principales (`upload_data_csv.html`)

| Funcion | Descripcion |
|---------|-------------|
| `renderPreview(data)` | Reconstruye el panel completo desde JSON |
| `previewGoToPage(page, pageSize?)` | Solicita pagina — usa `csrf()` |
| `postJSON(url, data)` | Wrapper fetch con CSRF header |
| `showNotification(type, msg)` | Toast: success / error / info / warning |
| `csrf()` | Lee el token del DOM |
| `loadDatasetAsPreview(id)` | Carga StoredDataset como preview activo |
| `doReanalyze()` | Cambia modelo y llama `reanalyze_async` |
| `tbSyncState()` | Actualiza barra de subtitulo bajo el toolbar |
| `switchEditTab(tab, el)` | Cambia pestana y persiste en STATE + sessionStorage |

---

## 18. Convenciones CSS / UI

### Scope

Todos los templates usan `<div id="analyst-root">` como raiz. Todas las reglas CSS prefijadas con `#analyst-root`.

Variables CSS: `#analyst-root { --ar-primary: ...; --primary: var(--ar-primary); }`.

### Toolbar

```html
<div class="analyst-toolbar" id="analystToolbar">
  <div class="tb-section">
    <span class="tb-label">Seccion</span>
    <button type="button" class="tb-btn" onclick="accion()">
      <div class="tb-icon-pill tip-blue"><i class="bi bi-plus-lg"></i></div>
      <span>Label</span>
    </button>
  </div>
</div>
```

- **`tip-*` disponibles:** `tip-blue` · `tip-green` · `tip-teal` · `tip-amber` · `tip-purple` · `tip-orange` · `tip-red` · `tip-indigo`
- En <=768px: labels y textos se ocultan, solo iconos.
- **Subtitulo:** `<div id="tbState" class="tb-subtitle-bar">` bajo el toolbar, visible solo con datos cargados. Texto completo sin truncar.

### Regla de scroll en secciones de edicion

El scroll va en los **elementos internos**, nunca en `.edit-group` ni `.edit-section`:

| Elemento | max-height | Overflow |
|----------|-----------|---------|
| `.col-check-list` | 180px | overflow-y: auto |
| Tabla de tipos (tab-tipos) | 160px | overflow-y: auto |
| `#dtypeCol`, `#filterCol` | 120px | scroll nativo select |
| Mapeo de columnas (card-body) | 280px | overflow-y: auto |
| Columnas no mapeadas | 60px | overflow-y: auto |
| `.edit-group` | sin limite | overflow: visible |
| `.edit-section` | sin limite | overflow: visible |

### Serializacion JSON segura para `<script>`

```python
def _safe_json_str(obj) -> str:
    import re, math, json
    cleaned = _json_safe(obj)   # elimina NaN, Infinity, UUID, datetime
    result  = json.dumps(cleaned, ensure_ascii=True, allow_nan=True)
    result  = re.sub(r'\bNaN\b',       'null', result)
    result  = re.sub(r'\bInfinity\b',  'null', result)
    result  = re.sub(r'\b-Infinity\b', 'null', result)
    return result.replace('</', r'<\/')
```

Usar en todas las vistas que inyectan datos en templates: `{{ datasets_json|safe }}`.

### Contexto de vistas — fuentes adicionales en `data_upload.py`

Los tres bloques de contexto (upload_csv, _prepare_preview_context, fallback) deben incluir:

```python
'analyst_bases':   AnalystBase.objects.filter(
                       created_by=request.user).select_related('dataset'),
'cross_sources':   CrossSource.objects.filter(
                       created_by=request.user).select_related('last_result'),
```

---

## 19. Constantes y settings

| Constante | Uso |
|-----------|-----|
| `MAX_FILE_SIZE` | `DataUploadForm.clean_file()` |
| `DEFAULT_CHUNK_SIZE` | `DataImporter` batch size |
| `MAX_RECORDS_FOR_IMPORT` | Techo de registros |
| `FORBIDDEN_MODELS` | `{"label": "app.Model"}` |

```python
# settings.py
ANALYST_ETL_ALLOWED_APPS = ['myapp', 'otherapp']
ANALYST_ETL_MAX_ROWS     = 100_000
```

---

## 20. Convenciones del proyecto

1. **Normalizacion:** solo `FileProcessorService.normalize_name()` — no duplicar.
2. **Respuesta JSON:** siempre `{"success": true/false, ...}`.
3. **Edicion async:** usar patron `_edit(request, _op)`.
4. **CSRF:** siempre `csrf()`, nunca `CSRF_TOKEN`.
5. **Modelo en vistas async:** `model_class, err = _resolve_model(body.get("model"))`.
6. **Paginacion:** propagar `page` y `page_size` en todas las operaciones de edicion.
7. **dtype_map:** indexar por nombre de columna, nunca por posición: `{str(col): str(df.dtypes[col]) for col in df.columns}`.
8. **Funciones WFM en Report Builder:** nunca duplicar imports de `pandas`/`numpy` dentro de las funciones — ya están en el top del módulo.
9. **Campo fecha en fuentes WFM:** `sim.Interaction` → `fecha` (DateField). `kpis.CallRecord` → `fecha` (DateField). Nunca `started_at` ni `start_time`.
10. **process_excel en FileProcessorService:** `@classmethod` — firma `(cls, file, model, column_mapping, no_header, ...)` → retorna `(records, preview, columns)`. No es `@staticmethod`. No llamar desde `_handle_preview()` — es la ruta programática.

---

## 21. Bugs conocidos

| # | Estado | Archivo | Descripcion |
|---|--------|---------|-------------|
| 1 | ✅ Corregido | `forms.py` | `clean_file()` duplicado — comentarios huérfanos de definición anterior eliminados. Commit `ef3678e7`. |
| 2 | ✅ Corregido | `services/file_processor_service.py` | `process_excel()` tenía tres sub-bugs: (2a) era `@staticmethod` en lugar de `@classmethod`; (2b) firma `(file, sheet_name, cell_range)` — `model` se asignaba a `sheet_name` en runtime; (2c) retornaba `(df, metadata)` en vez de `(records, preview, columns)`. Todo upload Excel fallaba silenciosamente. Commit `ef3678e7` / `4b7a0219`. |
| 3 | ✅ Corregido | `services/file_processor_service.py` | `no_header` nunca se propagaba a `ExcelProcessor` dentro de `FileProcessorService`. `ExcelProcessor` ya lo soportaba — faltaba pasarlo. Commit `4b7a0219`. |
| 4 | Corregido | `upload_data_csv.html` | `CSRF_TOKEN` inexistente al paginar. Corregido a `csrf()`. |
| 5 | Corregido | `upload_data_csv.html` | `showToast()` inexistente. Corregido a `showNotification()`. |
| 6 | Corregido | `upload_data_csv.html` | Toolbar crecia al cargar dataset. tbState movido como barra de subtitulo fija. |
| 7 | Corregido | `upload_data_csv.html` | Boton Reanalizar desbordaba en movil. Corregido con flex-wrap y model-switcher flexible. |
| 8 | Corregido | `cross_engine.py` | `df.dtypes[i]` por posicion -> KeyError. Corregido a `df.dtypes[col]`. |
| 9 | Corregido | `cross_source.py` | UUID Python en JS -> SyntaxError. Corregido con `_safe_json_str()`. |
| 10 | Corregido | `cross_source.py` | KeyError: NaN por columnas float. Corregido con `.astype(object).where(pd.notnull, None)`. |
| B-1 | ✅ Corregido | `views/dashboard.py` | `_load_df._EVENTS_MAP`: `Project.start_date` y `Event.start_time` no existen → `FieldError` al renderizar cualquier widget `events:projects` o `events:events`. Corregido a `created_at`. |
| B-2 | ✅ Corregido | `views/etl_manager.py` | `_source_row()` no incluía `events_model` → JS no podía identificar fuentes events ni activar el tab correcto al editar. Añadido `"events_model": getattr(src,'events_model','') or ''`. |
| B-NEW | ✅ Corregido | `views/dashboard.py` | `_EVENTS_MAP['tasks']` usaba `due_date` como `order_field` → `Task` no tiene `due_date`. `FieldError` en todo widget `events:tasks`. Corregido a `created_at`. |
| T-1 | ✅ Corregido | `templates/analyst/etl_manager.html` | `_EVENTS_DATE_HINTS` apuntaba a campos incorrectos. Corregidos a: `inbox→due_date`, `tasks/projects/events→created_at`. |
| T-2 | ✅ Corregido | `templates/analyst/etl_manager.html` | `get_events_model_display` llamado sobre CharField sin `choices` → probable `AttributeError`. Reemplazado por lookup inline con if/elif. |
| T-3 | ✅ Corregido | `templates/analyst/etl_manager.html` | Sección sim mostraba "started_at" en labels y texto de ayuda. Corregido a `fecha` (campo real de `sim.Interaction`). |
| T-4 | ✅ Corregido | `templates/analyst/dashboard.html` | Fuente `events` completamente ausente del modal de widgets: faltaban `<option value="events">`, `events_sources` en `SOURCES`, y branch `events` en `onSrcTypeChange()` / `onSrcRefChange()`. |

**Bugs abiertos: NINGUNO.**

---

## 22. Pendientes de documentar

| Prioridad | Archivo | Notas |
|-----------|---------|-------|
| Alta | `constants.py` | Valores exactos de límites y FORBIDDEN_MODELS |
| Alta | `signals.py` | Qué eventos dispara |
| Alta | `views/etl_manager.py` | Documentar `_extract_events_items()`, `_events_item_fields()`, `_extract_sim_account()`, `_extract_kpis_callrecord()` |
| Media | `views/clipboard.py` | Vistas de portapapeles no-async |
| Media | `views/data_upload.py` | Vista principal legacy |
| Media | `views/report_builder.py` | Flujo completo de ejecución y persistencia |
| Baja | `views/other_tools.py` | Calculadoras Erlang C y tráfico |
| Baja | `views/file_views.py` | Árbol de archivos |
| Baja | `views/excel_analyze.py` | AJAX análisis rangos Excel |
| Info | `templates/etl_manager.html` | Tab Events/GTD — documentar hints y campos |
| Info | `templates/dashboard.html` | Modal GTD Overview + ACD widget UI |
| Info | `templates/load_clipboard_form.html` | Formulario de carga clip |
| Info | `templates/report_builder.html` | SPA Report Builder |

### Cambios aplicados en código (✅ cerrados)

| Archivo | Cambio |
|---------|--------|
| `forms.py` | ✅ Comentarios huérfanos de `clean_file()` eliminados (Bug #1) |
| `services/file_processor_service.py` | ✅ `process_excel()` corregido: `@classmethod`, firma completa con `model`/`column_mapping`/`no_header`, retorno `(records, preview, columns)` (Bugs #2 y #3) |
| `views/etl_manager.py` | ✅ `_extract_events_items()` / `_events_item_fields()` implementados; `_source_row()` incluye `events_model` (EVENTS-AI-3 + fix B-2) |
| `views/dashboard.py` | ✅ `dashboard_gtd_overview()` endpoint POST; fuente `events` en `_compute_widget_data`; fix B-1 (`Project/Event created_at`); fix B-NEW (`Task order_field created_at`) |
| `templates/etl_manager.html` | ✅ Tab Events/GTD con hints; fix T-1 (`_EVENTS_DATE_HINTS`), T-2 (`get_events_model_display`), T-3 (sim `started_at`→`fecha`) |
| `templates/dashboard.html` | ✅ Modal GTD Overview + ACD widget UI (labels ricos + hints `_SRC_TYPE_HINTS`); fix T-4 (fuente events ausente del modal) |
| `urls.py` | ✅ Ruta `dashboards/gtd-overview/` añadida |
| `report_functions.py` | ✅ Integrado Sprint 7 — 13 funciones |
