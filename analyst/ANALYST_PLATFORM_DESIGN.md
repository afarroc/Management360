# Plataforma de Datos `analyst` — Diseño y Estado de Implementación

> **Última actualización:** 2026-03-20 (Sprint 9 — EVENTS-AI-1)
> **Contexto:** Expansión del módulo ETL hacia una plataforma completa de gestión de datos,
> reportes y dashboards para analistas de negocio.
> **Metodología:** Scrum — sprints sincronizados con `sim` y `events`.

---

## Estado por fase

| Fase | Descripción | Sprint | Estado |
|------|-------------|--------|--------|
| **Fase 1** | `AnalystBase` — bases de datos propias sin migraciones Django | S1 | ✅ Completada |
| **Fase 2** | `CrossSource` — joins entre fuentes | S1 | ✅ Completada |
| **Fase 3** | `Report` extendido — funciones de reporte calculadas | S1 | ✅ Completada |
| **Fase 4** | `Dashboard` — composición visual con widgets | S1 | ✅ Completada |
| **Fase 5** | `Pipeline` — transformaciones encadenadas y programables | S1 | ✅ Completada |
| **SIM-4 ETL** | `ETLSource.sim_account` FK — fuente sim nativa | S2 | ✅ Completada |
| **SIM-4b Dashboard** | `source.type = "sim"` en widgets | S2 | ✅ Completada |
| **Sprint 7 WFM** | 3 funciones kpis en Report Builder | S7 | ✅ Completada |
| **EVENTS-AI-1** | 5 funciones Events/GTD en Report Builder | S9 | ✅ Completada |

---

## Fase 1 — AnalystBase (Completada)

### Archivos entregados e integrados

| Archivo destino | Descripción | Estado |
|-----------------|-------------|--------|
| `analyst/models.py` | Modelo `AnalystBase` + campo `analyst_base` en `ETLSource` + `model_path` blank=True | Migrado |
| `analyst/migrations/0006_add_analyst_base.py` | CreateModel + AddField | Aplicado |
| `analyst/migrations/0007_*` | Limpieza Django | Aplicado |
| `analyst/migrations/0008_*` | AddField + AlterField | Aplicado |
| `analyst/services/base_validator.py` | Validación y persistencia | Listo |
| `analyst/views/analyst_base.py` | 18 endpoints REST + HTML | Listo |
| `analyst/views/etl_manager.py` | Soporte AnalystBase como fuente ETL | Listo |
| `analyst/templates/analyst/analyst_base.html` | Panel SPA | Listo |
| `analyst/urls.py` | 16 rutas bajo `bases/` | Listo |

### Modelo `AnalystBase`

```python
class AnalystBase(models.Model):
    FIELD_TYPES = ['text','number','decimal','date','datetime','boolean','choice','email','phone']
    CATEGORIES  = [('ventas','Ventas'),('calidad','Calidad'),('rrhh','RRHH'),
                   ('operaciones','Operaciones'),('finanzas','Finanzas'),
                   ('marketing','Marketing'),('otro','Otro')]

    id          = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name        = models.CharField(max_length=200)
    category    = models.CharField(max_length=50, blank=True, choices=CATEGORIES)
    schema      = models.JSONField(default=list)
    dataset     = models.OneToOneField('StoredDataset', null=True, blank=True,
                                       on_delete=models.SET_NULL, related_name='analyst_base')
    row_count   = models.IntegerField(default=0)
    created_by  = models.ForeignKey(User, on_delete=models.CASCADE, related_name='analyst_bases')
```

**Estructura de columna en `schema`:**
```json
{
  "name": "nombre_lead", "label": "Nombre del Lead", "type": "text",
  "required": true, "unique": false, "choices": [],
  "default": null, "max_length": 200, "min_value": null, "max_value": null
}
```

### Servicio `BaseValidator`

| Método | Descripción |
|--------|-------------|
| `validate_row(row, schema)` | Valida un dict. Devuelve `(cleaned, [errores])` |
| `validate_dataframe(df, schema)` | Valida todas las filas |
| `load_dataframe(analyst_base)` | Redis hit → fallback a `data_blob` |
| `save_dataframe(analyst_base, df, user)` | Redis + StoredDataset.data_blob |

### Endpoints AnalystBase

| URL | Descripción |
|-----|-------------|
| `bases/` | Panel HTML |
| `bases/create/` | Crear base |
| `bases/api/` | Lista JSON |
| `bases/sources/` | StoredDatasets + Clips del usuario |
| `bases/sources/columns-from-clip/` | Columnas de un clip |
| `bases/<id>/schema/` | Actualizar schema |
| `bases/<id>/delete/` | Eliminar |
| `bases/<id>/data/` | Datos paginados + búsqueda |
| `bases/<id>/rows/add/` | Agregar fila |
| `bases/<id>/rows/edit/` | Editar fila |
| `bases/<id>/rows/delete/` | Eliminar fila(s) |
| `bases/<id>/bulk-import/` | Importar CSV/Excel |
| `bases/<id>/bulk-import-raw/` | Importar desde texto/clip/dataset |
| `bases/<id>/export/` | CSV utf-8-sig |
| `bases/<id>/columns/` | Schema para ETL/CrossSource |

---

## Fase 2 — CrossSource (Completada)

### Archivos entregados

| Archivo | Descripción |
|---------|-------------|
| `analyst/models.py` | Modelo `CrossSource` agregado |
| `analyst/migrations/0009_add_cross_source.py` | CreateModel |
| `analyst/migrations/0010_alter_crosssource_id.py` | AlterField id |
| `analyst/services/cross_engine.py` | Motor de cruce |
| `analyst/views/cross_source.py` | 10 endpoints + HTML |
| `analyst/templates/analyst/cross_source.html` | Panel SPA con toolbar |
| `analyst/urls.py` | 8 rutas bajo `cross/` |

### Modelo `CrossSource`

```python
class CrossSource(models.Model):
    id           = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name         = models.CharField(max_length=200)
    config       = models.JSONField()
    last_result  = models.ForeignKey('StoredDataset', null=True, blank=True, on_delete=models.SET_NULL)
    last_run_at  = models.DateTimeField(null=True, blank=True)
    last_row_count = models.IntegerField(default=0)
    created_by   = models.ForeignKey(User, on_delete=models.CASCADE, related_name='cross_sources')
```

**Config:**
```json
{
  "operation": "left_join | inner_join | outer_join | concat",
  "left":  {"type": "stored_dataset|analyst_base|etl_source|clip",
            "id": "uuid_o_clip_key", "alias": "ventas", "columns": []},
  "right": {"type": "...", "id": "...", "alias": "agentes", "columns": []},
  "on": [{"left": "agente_id", "right": "codigo_empleado"}],
  "suffixes": ["_izq", "_der"],
  "post_filters": [{"field": "estado", "lookup": "exact", "value": "activo", "negate": false}],
  "output_columns": []
}
```

### Bugs corregidos durante implementación

- `df.dtypes[i]` → KeyError (indexación por nombre, no posición)
- UUID Python en JS → SyntaxError (corregido con `_safe_json_str()`)
- `KeyError: NaN` en columnas float (corregido con `.astype(object).where(pd.notnull, None)`)
- Tabla sin scroll horizontal en móvil (corregido con `min-width:max-content` + `touch-action`)

---

## Fase 3 — Report Builder (Completada + extensiones)

### Archivos entregados

| Archivo | Descripción |
|---------|-------------|
| `analyst/report_functions.py` | 13 funciones registradas (7 originales + 3 WFM/sim + 3 WFM/kpis) |
| `analyst/report_functions_events.py` | **NUEVO Sprint 9** — 5 funciones Events/GTD |
| `analyst/views/report_builder.py` | 7 endpoints |
| `analyst/templates/analyst/report_builder.html` | Panel SPA con toolbar |
| `analyst/urls.py` | 7 rutas bajo `reports/` |

### Funciones registradas — 18 total

| key | Descripción | Fuentes | Params clave |
|-----|-------------|---------|-------------|
| `quality_avg` | Promedio de notas por agente | base + notes | join_col, note_cols, group_by |
| `planilla_summary` | Estadísticas de planilla | planilla | numeric_cols, group_by |
| `period_comparison` | Variación entre dos períodos | periodo_a + periodo_b | key_col, value_cols |
| `ranking` | Clasificación por métrica | data | label_col, metric_col, top_n |
| `attendance_report` | Asistencia/ausencias/tardanzas | attendance | agent_col, status_col |
| `performance_report` | Desempeño vs meta | performance | agent_col, metric_cols, target_value |
| `funnel_report` | Embudo de conversión | data | stage_col, count_col |
| `sim_agent_performance` | Performance por Agente (WFM) | sim interactions | agente, duracion_s, status |
| `sim_inbound_daily` | KPIs Inbound Diarios (WFM) | sim interactions | fecha, status, duracion_s |
| `sim_contact_funnel` | Embudo de Contactabilidad Outbound (WFM) | sim interactions | status |
| `kpis_aht_report` | Reporte AHT por Dimensión | kpis.CallRecord | agente/canal/servicio/supervisor, aht, eventos |
| `kpis_satisfaction_report` | Reporte de Satisfacción por Agente | kpis.CallRecord | satisfaccion, evaluaciones |
| `kpis_weekly_trend` | Tendencia Semanal de KPIs | kpis.CallRecord | semana/fecha, métrica elegida |
| `events_inbox_summary` | GTD Inbox — Resumen por Estado | events.InboxItem | period_days, include_processed |
| `events_task_backlog` | Tasks — Backlog y Vencimiento | events.Task | group_by, period_days |
| `events_project_status` | Projects — Estado y Progreso | events.Project | group_by, period_days |
| `events_agenda` | Agenda — Eventos Próximos | events.Event | window_days, include_past, cols |
| `events_gtd_health` | GTD Health Score — Diagnóstico Combinado | inbox + tasks + projects | — |

### Patrón de extensión

Para añadir más categorías crear un módulo `report_functions_<app>.py` e importarlo al final de `report_functions.py`:

```python
# report_functions.py — al final
from analyst import report_functions_events  # noqa: F401  ← aplicado Sprint 9
# from analyst import report_functions_bots  # cuando se necesite
```

### Endpoint `report_rerun`

Re-ejecuta un reporte existente reconstruyendo `sources_desc` desde `report.sources` y la
metadata de la función. Actualiza `result_data`, `result_meta` y `status` en-lugar.

### Fuentes soportadas

`dataset` · `analyst_base` · `cross_source` · `clip` · `model` (Django ORM)

Todos con fallback a `data_blob` si Redis no disponible.

---

## Fase 4 — Dashboard (Completada)

### Archivos entregados

| Archivo | Descripción |
|---------|-------------|
| `analyst/models.py` | Modelos `Dashboard` + `DashboardWidget` |
| `analyst/migrations/0011_add_dashboard.py` | CreateModel ambos |
| `analyst/views/dashboard.py` | 10 endpoints |
| `analyst/templates/analyst/dashboard.html` | SPA con toolbar, modales y Chart.js |
| `analyst/urls.py` | 10 rutas bajo `dashboards/` |

### Modelo Dashboard

```python
class Dashboard(models.Model):
    id          = models.UUIDField(primary_key=True)
    name        = models.CharField(max_length=200)
    is_public   = models.BooleanField(default=False)
    layout      = models.JSONField(default=list)
    # [{"widget_id": "uuid", "col": 0, "width": 6, "row_order": 0}, ...]

class DashboardWidget(models.Model):
    WIDGET_TYPES = ['kpi_card','table','bar_chart','line_chart','pie_chart','text']
    dashboard   = models.ForeignKey(Dashboard, related_name='widgets')
    widget_type = models.CharField(max_length=20)
    title       = models.CharField(max_length=200, blank=True)
    source      = models.JSONField()  # {type, id}
    config      = models.JSONField()  # por tipo de widget
```

### Grid de 12 columnas

Los widgets se posicionan con `grid-column: {col+1} / span {width}`.
En móvil (≤768px) todos colapsan a `grid-column: 1 / -1`.

### Fuentes de widgets

| `source.type` | Cómo se carga |
|---------------|---------------|
| `report` | `Report.result_data` |
| `dataset` | Redis → `data_blob` |
| `cross_source` | `last_result` StoredDataset |
| `analyst_base` | `BaseValidator.load_dataframe()` |
| `sim` | `Interaction.objects.filter(account=account).order_by('fecha','hora_inicio')` ✅ SIM-4b |

### Renderizado (Chart.js 4.4.1)

- `bar_chart` / `line_chart` → tipo `bar` / `line`
- `pie_chart` → tipo `doughnut`
- Paleta de 6 colores reutilizable
- Instancias destruidas antes de re-renderizar para evitar memory leak

---

## Fase 5 — Pipeline (Completada)

### Archivos entregados

| Archivo | Descripción |
|---------|-------------|
| `analyst/models.py` | Modelos `Pipeline` + `PipelineRun` agregados |
| `analyst/migrations/0012_add_pipeline.py` | CreateModel ambos |
| `analyst/services/pipeline_engine.py` | Motor — 11 executors + `PipelineEngine.run()` |
| `analyst/views/pipeline.py` | 10 endpoints REST |
| `analyst/templates/analyst/pipeline.html` | Panel SPA con toolbar |
| `analyst/urls.py` | Rutas bajo `pipelines/` |

### Motor (`pipeline_engine.py`)

Carga `StoredDataset` de entrada (Redis → `data_blob`), ejecuta los pasos en orden,
persiste como nuevo `StoredDataset`, registra `PipelineRun` con estado, tiempo y errores.

Cada paso es función pura `(df, params) → (df, error|None)` que replica la lógica
de `data_upload_async/edit.py`.

**Operaciones soportadas (11):**
`filter_delete` · `rename_column` · `convert_dtype` · `fill_na` · `drop_duplicates`
· `sort` · `replace_values` · `convert_date` · `normalize_text` · `filter_replace` · `sort_data`

### Endpoints (bajo `analyst/pipelines/`)

| URL | Descripción |
|-----|-------------|
| `pipelines/` | Lista + panel HTML |
| `pipelines/api/` | Lista JSON |
| `pipelines/create/` | Crear pipeline |
| `pipelines/<id>/update/` | Actualizar nombre/desc/steps |
| `pipelines/<id>/delete/` | Eliminar |
| `pipelines/<id>/steps/add/` | Agregar paso |
| `pipelines/<id>/steps/<idx>/delete/` | Eliminar paso por índice |
| `pipelines/<id>/steps/reorder/` | Reordenar pasos |
| `pipelines/<id>/run/` | Ejecutar contra un dataset |
| `pipelines/<id>/runs/` | Historial de ejecuciones |

---

## SIM-4 — ETL Source type `sim` (Completada, Sprint 2)

### Archivos entregados

| Archivo | Descripción |
|---------|-------------|
| `analyst/migrations/0013_etlsource_sim_account.py` | AddField sim_account FK |
| `analyst/models.py` | `ETLSource.sim_account` FK → `sim.SimAccount` |
| `analyst/views/etl_manager.py` | `_extract_sim_account()`, `_sim_interaction_fields()`, `_get_sim_accounts()`, tab "Simulador" |
| `analyst/templates/analyst/etl_manager.html` | 3er tab "Simulador" en modal de fuente |

### ETL Manager — fuentes soportadas

| Tipo | Campo en ETLSource | Prioridad en `_run_extraction` |
|------|--------------------|-------------------------------|
| **Simulador** | `sim_account` FK → `sim.SimAccount` | 1 (primero) |
| Base analista | `analyst_base` FK → `AnalystBase` | 2 |
| SQL raw | `sql_override` (superusers) | 3 |
| Modelo ORM | `model_path` | 4 |

**Extracción:**
```python
# _extract_sim_account en etl_manager.py
qs = Interaction.objects.filter(account=account)
if date_from: qs = qs.filter(fecha__gte=date_from)   # campo real: fecha
if date_to:   qs = qs.filter(fecha__lte=date_to)
qs = qs.order_by('fecha', 'hora_inicio')
```

**Flujo completo:**
```
ETL Manager → tab "Simulador" → elegir SimAccount
→ campos de Interaction auto-populados (_sim_interaction_fields())
→ filtro de fecha (sobre campo `fecha`)
→ Ejecutar → StoredDataset
→ Report Builder / Dashboard / CrossSource
```

---

## SIM-4b — Dashboard widgets fuente `sim` (Completada, Sprint 2)

`_load_df` en `dashboard.py` branch `sim`:
```python
if src_type == 'sim':
    account = SimAccount.objects.get(id=src_id, created_by=user)
    qs = Interaction.objects.filter(account=account).order_by('fecha', 'hora_inicio')
    return pd.DataFrame(list(qs.values()))
```

Selector `🎮 Cuenta Simulador` disponible en modal de widget.
Columnas de `Interaction` auto-populadas al seleccionar la cuenta.

---

## Migraciones aplicadas

| Migración | Descripción | Estado |
|-----------|-------------|--------|
| `0001`–`0005` | Modelos base + ETL | ✅ |
| `0006_add_analyst_base` | AnalystBase + ETLSource.analyst_base | ✅ |
| `0007`, `0008` | Limpieza + AlterField | ✅ |
| `0009_add_cross_source` | CrossSource | ✅ |
| `0010_alter_crosssource_id` | AlterField id | ✅ |
| `0011_add_dashboard` | Dashboard + DashboardWidget | ✅ |
| `0012_add_pipeline` | Pipeline + PipelineRun | ✅ |
| `0013_etlsource_sim_account` | ETLSource.sim_account FK → sim.SimAccount | ✅ |

---

## Invariantes del sistema (no modificar)

- `StoredDataset` — formato universal de persistencia
- `data_upload_async/` — motor de edición del panel principal
- `DataFrameClipboard` — portapapeles temporal
- `_save_as_stored_dataset()` — función canónica de guardado en `etl_manager.py`
- Flujo CSV/Excel → Preview → Import del panel principal

---

## Visión completa — estado actual

```
FUENTES                   TRANSFORMACIÓN          SALIDA
-----------------         ---------------         --------
Modelos Django    ──┐                             StoredDataset  ✅
SQL raw           ──┤  ETL Engine        ✅       AnalystBase    ✅
CSV/Excel         ──┤                             Export CSV     ✅
AnalystBase       ──┤
DataFrameClip     ──┘──> bulk-import-raw ✅

sim.SimAccount    ──────> ETL sim  (SIM-4)  ✅    StoredDataset  ✅
sim.SimAccount    ──────> Dashboard widget  ✅    Vista HTML     ✅
  incl. GTR BD            (SIM-4b + SIM-6a) ✅

events.InboxItem  ──────> ETL + Report GTD  ✅    result_data    ✅  ← Sprint 9
events.Task       ──────> ETL + Report GTD  ✅    result_data    ✅  ← Sprint 9
events.Project    ──────> ETL + Report GTD  ✅    result_data    ✅  ← Sprint 9
events.Event      ──────> ETL + Report GTD  ✅    result_data    ✅  ← Sprint 9

CrossSource       ──────> join/merge/concat ──>  StoredDataset  ✅
Report            ──────> cálculo funciones ──>  result_data    ✅
Dashboard         ──────> widgets visuales  ──>  Vista HTML     ✅
Pipeline          ──────> transformaciones  ──>  StoredDataset  ✅
```

---

## Integraciones completadas

| Integración | Sprint | Estado | Descripción |
|-------------|--------|--------|-------------|
| Interacciones GTR persistidas en ETL/Dashboard | S3 | ✅ | `SimRun(canales=['gtr'])` identifica sesiones GTR |
| `kpis.CallRecord` en ETL Manager | S7 | ✅ | ORM path + `/kpis/api/` — campo `fecha` DateField |
| 3 funciones WFM kpis en Report Builder | S7 | ✅ | `kpis_aht_report`, `kpis_satisfaction_report`, `kpis_weekly_trend` |
| 5 funciones Events/GTD en Report Builder | S9 | ✅ | `events_inbox_summary`, `events_task_backlog`, `events_project_status`, `events_agenda`, `events_gtd_health` |

---

## Bugs conocidos pendientes

| Archivo | Descripción |
|---------|-------------|
| `forms.py` | `clean_file` duplicado — solo actúa la segunda definición |
| `services/file_processor_service.py` | `process_excel` referencia `ExcelProcessor._read_with_range` fuera de scope |

## Bugs corregidos en sesiones

| Bug | Archivo | Descripción |
|-----|---------|-------------|
| `started_at` inexistente | `dashboard.py`, `etl_manager.py` | Corregido a `order_by('fecha','hora_inicio')` y `fecha__gte/lte` |

---

## Próximas integraciones (roadmap)

| Integración | Sprint | Descripción |
|-------------|--------|-------------|
| ETL Sources + Dashboard "GTD Overview" | S9 | EVENTS-AI-3 — crear configuraciones en UI |
| `SimAgentProfile` en Report Builder | S5 | Nueva función `sim_agent_profile_report` |
| Dashboard ACD en tiempo real | S5 | Widget polling `ACDSession` → métricas live |
| Funciones `bots` en Report Builder | S10 | leads, distribución, performance |

---

> **Notas para Claude:**
> - Fases 1–5 completadas. SIM-4/4b + Sprint 7 kpis + Sprint 9 Events/GTD integrados.
> - No modificar: `StoredDataset`, `data_upload_async/`, `_save_as_stored_dataset()`.
> - `sim.Interaction` → fecha: `fecha` (DateField). Nunca `started_at`.
> - `kpis.CallRecord` → fecha: `fecha` (DateField). Nunca `start_time`.
> - Las interacciones GTR persisten en BD con `SimRun.canales` conteniendo `'gtr'`.
> - `report_functions.py` tiene 13 funciones base — no añadir imports pandas/numpy dentro de funciones.
> - `report_functions_events.py` tiene 5 funciones GTD — importado al final de `report_functions.py`.
> - Las funciones GTD reciben DataFrames via ETL, no consultan la DB directamente.
> - `events.InboxItem` usa `created_by_id` como filtro ETL; `events.Task`/`Project` usan `host_id`.

---

## Handoff

> Estado: Fases 1–5 + SIM-4/4b + Sprint 7 kpis + Sprint 9 EVENTS-AI-1.
> Próximo: EVENTS-AI-3 (ETL Sources + Dashboard GTD) + Dashboard ACD widget.

### Archivos para próxima sesión

```bash
cat analyst/views/etl_manager.py | termux-clipboard-set
cat analyst/views/dashboard.py | termux-clipboard-set
# Adjuntar ANALYST_PLATFORM_DESIGN.md + ANALYST_DEV_REFERENCE.md
```
