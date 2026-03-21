# analyst/models.py
"""
Persistent models for the Dataset Manager + Report Builder.
"""
import uuid
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class StoredDataset(models.Model):
    id          = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name        = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    cache_key   = models.CharField(max_length=120, unique=True)
    rows        = models.PositiveIntegerField(default=0)
    col_count   = models.PositiveIntegerField(default=0)
    columns     = models.JSONField(default=list)
    dtype_map   = models.JSONField(default=dict)
    source_file = models.CharField(max_length=500, blank=True)
    # Serialized DataFrame (pickle+base64) stored in DB so data survives
    # Redis outages and Django restarts.  Populated on save, read on cache miss.
    data_blob   = models.TextField(blank=True, default="")
    created_by  = models.ForeignKey(User, on_delete=models.CASCADE, related_name="stored_datasets")
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name        = "Dataset Guardado"
        verbose_name_plural = "Datasets Guardados"

    def __str__(self):
        return f"{self.name} ({self.rows}x{self.col_count})"

    @staticmethod
    def make_cache_key(dataset_id):
        return f"stored_dataset_{dataset_id}"


REPORT_STATUS = [
    ("pending", "Pendiente"),
    ("running", "Generando"),
    ("done",    "Listo"),
    ("error",   "Error"),
]


class Report(models.Model):
    id           = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name         = models.CharField(max_length=200)
    description  = models.TextField(blank=True)
    function_key = models.CharField(max_length=100)
    sources      = models.JSONField(default=list)
    params       = models.JSONField(default=dict)
    status       = models.CharField(max_length=20, choices=REPORT_STATUS, default="pending")
    error_msg    = models.TextField(blank=True)
    result_data  = models.JSONField(default=list)
    result_meta  = models.JSONField(default=dict)
    created_by   = models.ForeignKey(User, on_delete=models.CASCADE, related_name="reports")
    created_at   = models.DateTimeField(auto_now_add=True)
    updated_at   = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name        = "Reporte"
        verbose_name_plural = "Reportes"

    def __str__(self):
        return f"{self.name} [{self.get_status_display()}]"

    @property
    def row_count(self):
        return self.result_meta.get("rows", len(self.result_data))

    @property
    def col_list(self):
        return self.result_meta.get("columns", [])


# ─────────────────────────────────────────────────────────────────────────────
# ETL: Extract-Transform-Load
# Allows users to extract data from any registered Django model, apply basic
# transforms (filters, aggregations, column selection) and save the result
# as a StoredDataset that the analyst panel can work with.
# ─────────────────────────────────────────────────────────────────────────────

ETL_STATUS = [
    ("idle",    "Inactivo"),
    ("running", "Ejecutando"),
    ("done",    "Completado"),
    ("error",   "Error"),
]

ETL_FREQUENCY = [
    ("manual",  "Manual"),
    ("daily",   "Diario"),
    ("weekly",  "Semanal"),
    ("monthly", "Mensual"),
]


class ETLSource(models.Model):
    """
    Reusable extraction definition.
    Describes WHERE to pull data from (model + fields + filters + aggregations).
    A single ETLSource can be run multiple times producing new StoredDatasets.
    """
    id          = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name        = models.CharField(max_length=200)
    description = models.TextField(blank=True)

    # ── Source ────────────────────────────────────────────────────────────────
    # "app_label.ModelName"  e.g. "crm.Contact"
    model_path  = models.CharField(max_length=200, blank=True)

    # FK opcional a una AnalystBase — se usa como fuente en lugar de model_path/sql
    analyst_base = models.ForeignKey(
        'AnalystBase',
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='etl_sources',
        verbose_name='Base de datos analista',
    )

    # FK opcional a una SimAccount — fuente sim nativa (SIM-4)
    sim_account = models.ForeignKey(
        'sim.SimAccount',
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='etl_sources',
        verbose_name='Cuenta Sim',
    )

    # EVENTS-AI-3: modelo events a extraer (sin FK — no hay un objeto "cuenta")
    # Valores: 'inbox' | 'tasks' | 'projects' | 'events' | '' (no events)
    events_model = models.CharField(
        max_length=20,
        blank=True,
        default='',
        choices=[
            ('inbox',    'GTD Inbox (InboxItem)'),
            ('tasks',    'Tareas (Task)'),
            ('projects', 'Proyectos (Project)'),
            ('events',   'Agenda (Event)'),
        ],
        verbose_name='Modelo Events',
    )

    # ── Extraction config (all JSONField for schema-free flexibility) ─────────
    # List of field names to SELECT; empty = all fields
    fields      = models.JSONField(default=list)

    # List of filter dicts: [{field, lookup, value}]
    # e.g. [{"field":"status","lookup":"exact","value":"active"}]
    filters     = models.JSONField(default=list)

    # Optional date-range filter: apply on this field
    date_field  = models.CharField(max_length=100, blank=True)

    # Aggregation config: {group_by:[fields], aggregations:[{field,func,alias}]}
    # func ∈ Count, Sum, Avg, Min, Max
    aggregations = models.JSONField(default=dict)

    # Raw SQL override (advanced — bypasses ORM, uses connection.cursor())
    sql_override = models.TextField(blank=True)

    # ── Output config ─────────────────────────────────────────────────────────
    chunk_size   = models.PositiveIntegerField(default=5000)
    max_rows     = models.PositiveIntegerField(default=0, help_text="0 = sin límite")
    frequency    = models.CharField(max_length=20, choices=ETL_FREQUENCY, default="manual")

    created_by   = models.ForeignKey(User, on_delete=models.CASCADE, related_name="etl_sources")
    created_at   = models.DateTimeField(auto_now_add=True)
    updated_at   = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name        = "Fuente ETL"
        verbose_name_plural = "Fuentes ETL"

    def __str__(self):
        return f"{self.name} ({self.model_path})"


class ETLJob(models.Model):
    """
    Single execution of an ETLSource.
    Tracks status, timing, row count and links to the resulting StoredDataset.
    """
    id             = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    source         = models.ForeignKey(ETLSource, on_delete=models.CASCADE, related_name="jobs")

    # Runtime params that override source config (e.g. specific date range)
    runtime_params = models.JSONField(default=dict)

    status         = models.CharField(max_length=20, choices=ETL_STATUS, default="idle")
    error_msg      = models.TextField(blank=True)
    rows_extracted = models.PositiveIntegerField(default=0)
    duration_s     = models.FloatField(default=0.0, help_text="Segundos de ejecución")

    # Resulting dataset (null until job completes successfully)
    result_dataset = models.ForeignKey(
        StoredDataset, null=True, blank=True,
        on_delete=models.SET_NULL, related_name="etl_jobs"
    )

    triggered_by   = models.ForeignKey(User, on_delete=models.CASCADE, related_name="etl_jobs")
    started_at     = models.DateTimeField(null=True, blank=True)
    finished_at    = models.DateTimeField(null=True, blank=True)
    created_at     = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name        = "Trabajo ETL"
        verbose_name_plural = "Trabajos ETL"

    def __str__(self):
        return f"{self.source.name} [{self.status}] {self.created_at:%Y-%m-%d %H:%M}"

# ─────────────────────────────────────────────────────────────────────────────
# AGREGAR AL FINAL DE analyst/models.py
# (después de la clase ETLJob)
# ─────────────────────────────────────────────────────────────────────────────

class AnalystBase(models.Model):
    """
    Base de datos dinámica gestionada por el analista.
    No requiere migraciones Django para definir su estructura:
    el schema se guarda en un JSONField y los datos viven en
    un StoredDataset asociado (Redis + data_blob).

    Schema — lista de columnas:
    [
      {
        "name":     "nombre_lead",          # snake_case, único por base
        "label":    "Nombre del Lead",      # texto visible al usuario
        "type":     "text",                 # ver FIELD_TYPES abajo
        "required": true,
        "unique":   false,
        "choices":  ["a", "b"],             # solo si type="choice"
        "default":  null,                   # valor por defecto
        "max_length": 200,                  # solo para type="text"
        "min_value":  0,                    # solo para type="number"/"decimal"
        "max_value":  null
      }
    ]

    FIELD_TYPES soportados:
      text | number | decimal | date | datetime | boolean | choice | email | phone
    """

    FIELD_TYPES = [
        'text', 'number', 'decimal', 'date', 'datetime',
        'boolean', 'choice', 'email', 'phone',
    ]

    CATEGORIES = [
        ('ventas',    'Ventas'),
        ('calidad',   'Calidad'),
        ('rrhh',      'RRHH'),
        ('operaciones','Operaciones'),
        ('finanzas',  'Finanzas'),
        ('marketing', 'Marketing'),
        ('otro',      'Otro'),
    ]

    id          = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name        = models.CharField(max_length=200, verbose_name='Nombre')
    description = models.TextField(blank=True, verbose_name='Descripción')
    category    = models.CharField(
        max_length=50, blank=True, choices=CATEGORIES, verbose_name='Categoría'
    )
    schema      = models.JSONField(default=list, verbose_name='Schema')

    # Dataset asociado: puede ser None si la base está vacía (sin datos aún)
    dataset     = models.OneToOneField(
        'StoredDataset',
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='analyst_base',
        verbose_name='Dataset',
    )
    row_count   = models.IntegerField(default=0, verbose_name='Registros')

    created_by  = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='analyst_bases',
        verbose_name='Creado por',
    )
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name        = 'Base de datos analista'
        verbose_name_plural = 'Bases de datos analista'
        ordering            = ['-updated_at']

    def __str__(self):
        return self.name

    @property
    def column_names(self):
        """Lista de nombres de columna en orden del schema."""
        return [col['name'] for col in self.schema]

    @property
    def required_columns(self):
        return [col['name'] for col in self.schema if col.get('required')]

    def schema_dict(self):
        """Schema indexado por nombre de columna para acceso rápido."""
        return {col['name']: col for col in self.schema}


# ─────────────────────────────────────────────────────────────────────────────
# AGREGAR AL FINAL DE analyst/models.py  (después de AnalystBase)
# ─────────────────────────────────────────────────────────────────────────────

CROSS_SOURCE_TYPES = [
    ('left_join',  'Left Join'),
    ('inner_join', 'Inner Join'),
    ('outer_join', 'Outer Join'),
    ('concat',     'Concatenar (apilar filas)'),
]


class CrossSource(models.Model):
    """
    Cruce configurable entre dos fuentes de datos.

    Soporta las mismas fuentes que el ETL y el Report Builder:
      - stored_dataset  → StoredDataset por UUID
      - analyst_base    → AnalystBase por UUID
      - etl_source      → ETLSource (se ejecuta en el momento del cruce)
      - clip            → DataFrameClipboard (por clip_key)

    El resultado se guarda como un nuevo StoredDataset y puede
    re-ejecutarse para obtener datos frescos.

    config = {
      "operation": "left_join" | "inner_join" | "outer_join" | "concat",
      "left": {
        "type":  "stored_dataset" | "analyst_base" | "etl_source" | "clip",
        "id":    "uuid o clip_key",
        "alias": "ventas",         # nombre corto usado en columnas duplicadas
        "columns": []              # [] = todas; ["col1","col2"] = subconjunto
      },
      "right": {
        "type":  "stored_dataset" | "analyst_base" | "etl_source" | "clip",
        "id":    "uuid o clip_key",
        "alias": "agentes",
        "columns": []
      },
      "on": [
        {"left": "agente_id", "right": "codigo_empleado"}
      ],
      "suffixes": ["_izq", "_der"],   # para columnas duplicadas tras el merge
      "post_filters": [               # misma estructura que ETLSource.filters
        {"field": "estado", "lookup": "exact", "value": "activo", "negate": false}
      ],
      "output_columns": []            # [] = todas; lista = selección final
    }
    """

    id          = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name        = models.CharField(max_length=200, verbose_name='Nombre')
    description = models.TextField(blank=True, verbose_name='Descripción')

    config      = models.JSONField(verbose_name='Configuración del cruce')

    last_result = models.ForeignKey(
        'StoredDataset',
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='cross_sources',
        verbose_name='Último resultado',
    )
    last_run_at   = models.DateTimeField(null=True, blank=True)
    last_row_count = models.IntegerField(default=0)

    created_by  = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='cross_sources',
        verbose_name='Creado por',
    )
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name        = 'Cruce de datos'
        verbose_name_plural = 'Cruces de datos'
        ordering            = ['-updated_at']

    def __str__(self):
        return self.name

    @property
    def operation_label(self):
        return dict(CROSS_SOURCE_TYPES).get(
            self.config.get('operation', ''), self.config.get('operation', '—')
        )

    @property
    def has_result(self):
        return self.last_result_id is not None


# ─────────────────────────────────────────────────────────────────────────────
# Fase 4 — Dashboard
# ─────────────────────────────────────────────────────────────────────────────

WIDGET_TYPES = [
    ('kpi_card',   'KPI / Indicador'),
    ('table',      'Tabla'),
    ('bar_chart',  'Gráfico de barras'),
    ('line_chart', 'Gráfico de líneas'),
    ('pie_chart',  'Gráfico de pastel'),
    ('text',       'Texto / Nota'),
]

WIDGET_SOURCE_TYPES = [
    ('report',       'Reporte'),
    ('dataset',      'Dataset guardado'),
    ('cross_source', 'Cruce de datos'),
    ('analyst_base', 'Base de datos analista'),
]


class Dashboard(models.Model):
    """
    Panel de visualización compuesto de widgets configurables.

    layout = [
      {
        "widget_id": "<uuid>",
        "col": 0,        # columna de inicio (0–11, grid de 12)
        "width": 6,      # ancho en columnas (1–12)
        "row_order": 0   # orden vertical
      }, ...
    ]
    """
    id          = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name        = models.CharField(max_length=200, verbose_name='Nombre')
    description = models.TextField(blank=True, verbose_name='Descripción')
    is_public   = models.BooleanField(default=False, verbose_name='Público')
    layout      = models.JSONField(default=list, verbose_name='Layout')

    created_by  = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='dashboards'
    )
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name        = 'Dashboard'
        verbose_name_plural = 'Dashboards'
        ordering            = ['-updated_at']

    def __str__(self):
        return self.name


class DashboardWidget(models.Model):
    """
    Widget individual de un dashboard.

    config por tipo:
      kpi_card:   { "value_col": "col", "label": "texto", "format": "number|percent|currency" }
      table:      { "columns": ["c1","c2"], "page_size": 10 }
      bar_chart:  { "x_col": "col", "y_cols": ["col1","col2"], "stacked": false }
      line_chart: { "x_col": "col", "y_cols": ["col1","col2"], "fill": false }
      pie_chart:  { "label_col": "col", "value_col": "col" }
      text:       { "content": "markdown/html texto libre" }

    source:
      { "type": "report|dataset|cross_source|analyst_base", "id": "uuid" }
    """
    id          = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    dashboard   = models.ForeignKey(
        Dashboard, on_delete=models.CASCADE, related_name='widgets'
    )
    widget_type = models.CharField(max_length=20, choices=WIDGET_TYPES)
    title       = models.CharField(max_length=200, blank=True)
    source      = models.JSONField(default=dict, blank=True)  # {type, id}
    config      = models.JSONField(default=dict, blank=True)
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name        = 'Widget'
        verbose_name_plural = 'Widgets'
        ordering            = ['created_at']

    def __str__(self):
        return f"{self.get_widget_type_display()} — {self.title or self.id}"

# ─────────────────────────────────────────────────────────────────────────────
# Fase 5 — Pipeline
# Secuencia grabada de operaciones re-ejecutables sobre un StoredDataset.
# ─────────────────────────────────────────────────────────────────────────────

PIPELINE_STEP_TYPES = [
    ('delete_columns',   'Eliminar columnas'),
    ('rename_column',    'Renombrar columna'),
    ('replace_values',   'Reemplazar valores'),
    ('fill_na',          'Rellenar nulos'),
    ('convert_date',     'Convertir a fecha'),
    ('convert_dtype',    'Convertir tipo de dato'),
    ('normalize_text',   'Normalizar texto'),
    ('drop_duplicates',  'Eliminar duplicados'),
    ('sort_data',        'Ordenar datos'),
    ('filter_delete',    'Filtrar y eliminar filas'),
    ('filter_replace',   'Filtrar y reemplazar filas'),
]

PIPELINE_STATUS = [
    ('idle',    'Inactivo'),
    ('running', 'Ejecutando'),
    ('done',    'Completado'),
    ('error',   'Error'),
]


class Pipeline(models.Model):
    """
    Secuencia grabada de pasos de transformacion re-ejecutable.

    Puede aplicarse a cualquier StoredDataset compatible.
    El resultado se guarda como un nuevo StoredDataset o sobreescribe el original
    segun el modo de ejecucion.

    steps = [
        {
            "order":      0,
            "type":       "delete_columns",      # uno de PIPELINE_STEP_TYPES
            "label":      "Quitar col nula",      # descripcion libre
            "params":     { ... }                 # parametros especificos del tipo
        },
        ...
    ]

    Parametros por tipo:
        delete_columns:   { "columns": ["col1", "col2"] }
        rename_column:    { "old_name": "col", "new_name": "nueva" }
        replace_values:   { "column": "col", "old_value": "x", "new_value": "y" }
        fill_na:          { "column": "col", "strategy": "value|mean|median|mode|ffill|bfill",
                            "value": "..." }
        convert_date:     { "column": "col", "format": "%d/%m/%Y" }
        convert_dtype:    { "column": "col", "target_type": "int|float|str|bool",
                            "coerce": true }
        normalize_text:   { "column": "col", "ops": ["lower","strip","remove_accents"] }
        drop_duplicates:  { "columns": [] }       # [] = todas
        sort_data:        { "column": "col", "ascending": true }
        filter_delete:    { "column": "col", "lookup": "exact|contains|gt|lt|isnull",
                            "value": "...", "negate": false }
        filter_replace:   { "column": "col", "lookup": "...", "value": "...",
                            "replace_col": "col", "replace_value": "..." }
    """
    id          = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name        = models.CharField(max_length=200, verbose_name='Nombre')
    description = models.TextField(blank=True, verbose_name='Descripcion')
    steps       = models.JSONField(default=list, verbose_name='Pasos')

    # Optional source dataset this pipeline was originally designed for
    source_dataset = models.ForeignKey(
        'StoredDataset',
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='pipelines',
        verbose_name='Dataset origen',
    )

    created_by  = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='pipelines'
    )
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name        = 'Pipeline'
        verbose_name_plural = 'Pipelines'
        ordering            = ['-updated_at']

    def __str__(self):
        return f"{self.name} ({len(self.steps)} pasos)"

    @property
    def step_count(self):
        return len(self.steps)


class PipelineRun(models.Model):
    """
    Ejecucion de un Pipeline sobre un dataset especifico.
    Registra estado, errores, tiempo y resultado.
    """
    id              = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    pipeline        = models.ForeignKey(
        Pipeline, on_delete=models.CASCADE, related_name='runs'
    )
    input_dataset   = models.ForeignKey(
        'StoredDataset',
        on_delete=models.CASCADE,
        related_name='pipeline_runs_as_input',
        verbose_name='Dataset entrada',
    )
    result_dataset  = models.ForeignKey(
        'StoredDataset',
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='pipeline_runs_as_result',
        verbose_name='Dataset resultado',
    )
    status          = models.CharField(
        max_length=20, choices=PIPELINE_STATUS, default='idle'
    )
    error_msg       = models.TextField(blank=True)
    steps_completed = models.PositiveIntegerField(default=0)
    duration_s      = models.FloatField(default=0.0)

    # Runtime params that can override step params (e.g. column overrides)
    runtime_params  = models.JSONField(default=dict, blank=True)

    triggered_by    = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='pipeline_runs'
    )
    started_at      = models.DateTimeField(null=True, blank=True)
    finished_at     = models.DateTimeField(null=True, blank=True)
    created_at      = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name        = 'Ejecucion de pipeline'
        verbose_name_plural = 'Ejecuciones de pipeline'
        ordering            = ['-created_at']

    def __str__(self):
        return f"{self.pipeline.name} [{self.status}] {self.created_at:%Y-%m-%d %H:%M}"
