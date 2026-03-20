# analyst/report_functions_events.py
"""
Report functions — app events / GTD.

Registradas automáticamente al importar este módulo.
Añadir al final de analyst/report_functions.py:

    from analyst import report_functions_events  # noqa: F401

Fuente ETL recomendada para cada función:
  events_inbox_summary    → model_path="events.InboxItem"
  events_task_backlog     → model_path="events.Task"
  events_project_status   → model_path="events.Project"
  events_agenda           → model_path="events.Event"
  events_gtd_health       → no requiere fuente (usa 4 anteriores juntas)

Para filtrar por usuario en el ETL Source, usar:
  filters = [{"field": "created_by_id", "lookup": "exact", "value": "<user_id>"}]
  (Task/Project/Event usan "host_id" en vez de "created_by_id")
"""

import logging
import pandas as pd
from datetime import datetime, timezone as dt_tz

logger = logging.getLogger(__name__)

# Importación lazy para evitar circular import si apps.py importa esto muy
# temprano. La función register está disponible cuando report_functions ya cargó.
from analyst.report_functions import register  # noqa: E402


# ─── helpers internos ─────────────────────────────────────────────────────────

def _to_utc(series: pd.Series) -> pd.Series:
    """Convierte una serie de fechas a UTC-aware sin errores."""
    parsed = pd.to_datetime(series, errors="coerce", utc=True)
    return parsed


def _days_ago(n: int) -> pd.Timestamp:
    return pd.Timestamp.now(tz="UTC") - pd.Timedelta(days=n)


def _filter_period(df: pd.DataFrame, date_col: str, days: int) -> pd.DataFrame:
    if days <= 0 or date_col not in df.columns:
        return df
    df = df.copy()
    df[date_col] = _to_utc(df[date_col])
    return df[df[date_col] >= _days_ago(days)]


# ═══════════════════════════════════════════════════════════════════════════════
# 1. GTD Inbox — Resumen por Estado
# ═══════════════════════════════════════════════════════════════════════════════

@register(
    key="events_inbox_summary",
    label="GTD Inbox — Resumen por Estado",
    category="Events / GTD",
    description=(
        "Distribución de InboxItems por categoría GTD (pendiente / accionable / "
        "no_accionable) y tipo de acción (hacer, delegar, posponer…). "
        "Fuente ETL: events.InboxItem"
    ),
    sources=[
        {"id": "inbox", "label": "InboxItems (events.InboxItem via ETL)", "required": True},
    ],
    params=[
        {
            "id": "period_days",
            "label": "Últimos N días (0 = todos)",
            "type": "number",
            "default": 30,
        },
        {
            "id": "include_processed",
            "label": "Incluir procesados",
            "type": "boolean",
            "default": False,
        },
    ],
)
def events_inbox_summary(sources: dict, params: dict) -> pd.DataFrame:
    """
    Resumen GTD del Inbox: totales por categoría y tipo de acción.

    Columnas de salida:
      dimension, valor, total, pct_del_total
    """
    df = sources["inbox"].copy()
    period_days = int(params.get("period_days") or 0)
    include_processed = bool(params.get("include_processed", False))

    df = _filter_period(df, "created_at", period_days)

    if not include_processed and "is_processed" in df.columns:
        df = df[df["is_processed"] != True]  # noqa: E712

    if df.empty:
        return pd.DataFrame(columns=["dimension", "valor", "total", "pct_del_total"])

    rows = []
    total_items = len(df)

    # — por gtd_category —
    if "gtd_category" in df.columns:
        for cat, grp in df.groupby("gtd_category", dropna=False):
            rows.append({
                "dimension": "gtd_category",
                "valor": str(cat) if pd.notna(cat) else "sin_categoría",
                "total": len(grp),
            })

    # — por action_type —
    if "action_type" in df.columns:
        action_df = df[df["action_type"].notna() & (df["action_type"] != "")]
        for atype, grp in action_df.groupby("action_type", dropna=False):
            rows.append({
                "dimension": "action_type",
                "valor": str(atype),
                "total": len(grp),
            })

    # — procesados vs pendientes —
    if "is_processed" in df.columns:
        n_proc = int(df["is_processed"].sum())
        rows.append({"dimension": "estado", "valor": "procesado", "total": n_proc})
        rows.append({"dimension": "estado", "valor": "sin_procesar", "total": total_items - n_proc})

    result = pd.DataFrame(rows)
    result["pct_del_total"] = (result["total"] / total_items * 100).round(1)
    result = result.sort_values(["dimension", "total"], ascending=[True, False])
    return result.reset_index(drop=True)


# ═══════════════════════════════════════════════════════════════════════════════
# 2. Task Backlog — Tareas por Estado y Vencimiento
# ═══════════════════════════════════════════════════════════════════════════════

@register(
    key="events_task_backlog",
    label="Tasks — Backlog y Vencimiento",
    category="Events / GTD",
    description=(
        "Distribución de tareas por estado (task_status_id) con detección de "
        "vencidas (due_date < hoy) y tareas importantes. "
        "Fuente ETL: events.Task"
    ),
    sources=[
        {"id": "tasks", "label": "Tasks (events.Task via ETL)", "required": True},
    ],
    params=[
        {
            "id": "group_by",
            "label": "Agrupar por",
            "type": "choice",
            "choices": ["task_status_id", "priority", "action_type", "assigned_to_id"],
            "default": "task_status_id",
        },
        {
            "id": "period_days",
            "label": "Últimos N días creación (0 = todos)",
            "type": "number",
            "default": 0,
        },
    ],
)
def events_task_backlog(sources: dict, params: dict) -> pd.DataFrame:
    """
    Backlog de tareas agrupado por estado/prioridad/asignado.

    Columnas de salida:
      {group_by}, total, vencidas, importantes, pct_vencidas
    """
    df = sources["tasks"].copy()
    group_by = params.get("group_by", "task_status_id")
    period_days = int(params.get("period_days") or 0)

    df = _filter_period(df, "created_at", period_days)

    if df.empty:
        return pd.DataFrame(columns=[group_by, "total", "vencidas", "importantes", "pct_vencidas"])

    now = pd.Timestamp.now(tz="UTC")

    # Detectar vencidas
    if "due_date" in df.columns:
        df["_due"] = _to_utc(df["due_date"])
        df["_vencida"] = df["_due"].notna() & (df["_due"] < now)
    else:
        df["_vencida"] = False

    # Importantes
    if "important" in df.columns:
        df["_imp"] = df["important"].astype(bool)
    else:
        df["_imp"] = False

    if group_by not in df.columns:
        # Fallback: usar columna disponible
        for fallback in ["task_status_id", "priority", "assigned_to_id"]:
            if fallback in df.columns:
                group_by = fallback
                break

    grouped = df.groupby(group_by, dropna=False).agg(
        total=("_vencida", "count"),
        vencidas=("_vencida", "sum"),
        importantes=("_imp", "sum"),
    ).reset_index()

    grouped["pct_vencidas"] = (grouped["vencidas"] / grouped["total"].replace(0, 1) * 100).round(1)
    grouped["vencidas"] = grouped["vencidas"].astype(int)
    grouped["importantes"] = grouped["importantes"].astype(int)
    grouped = grouped.sort_values("total", ascending=False).reset_index(drop=True)
    grouped.insert(0, "rank", range(1, len(grouped) + 1))

    return grouped


# ═══════════════════════════════════════════════════════════════════════════════
# 3. Projects — Estado y Progreso
# ═══════════════════════════════════════════════════════════════════════════════

@register(
    key="events_project_status",
    label="Projects — Estado y Progreso",
    category="Events / GTD",
    description=(
        "Distribución de proyectos por estado (project_status_id). "
        "Si hay columna de progreso, calcula promedio por grupo. "
        "Fuente ETL: events.Project"
    ),
    sources=[
        {"id": "projects", "label": "Projects (events.Project via ETL)", "required": True},
    ],
    params=[
        {
            "id": "group_by",
            "label": "Agrupar por",
            "type": "choice",
            "choices": ["project_status_id", "host_id", "assigned_to_id"],
            "default": "project_status_id",
        },
        {
            "id": "period_days",
            "label": "Últimos N días (0 = todos)",
            "type": "number",
            "default": 0,
        },
    ],
)
def events_project_status(sources: dict, params: dict) -> pd.DataFrame:
    """
    Estado de proyectos con conteo y progreso promedio por grupo.

    Columnas de salida:
      {group_by}, total, con_progreso, progreso_promedio
    """
    df = sources["projects"].copy()
    group_by = params.get("group_by", "project_status_id")
    period_days = int(params.get("period_days") or 0)

    df = _filter_period(df, "created_at", period_days)

    if df.empty:
        return pd.DataFrame(columns=[group_by, "total", "progreso_promedio"])

    if group_by not in df.columns:
        for fallback in ["project_status_id", "host_id"]:
            if fallback in df.columns:
                group_by = fallback
                break

    # Detectar columna de progreso
    progress_col = None
    for candidate in ["progress", "progreso", "completion_pct", "percent_complete"]:
        if candidate in df.columns:
            progress_col = candidate
            df[progress_col] = pd.to_numeric(df[progress_col], errors="coerce")
            break

    agg_dict = {"total": (group_by, "count")}
    if progress_col:
        agg_dict["progreso_promedio"] = (progress_col, "mean")
        agg_dict["con_progreso"] = (progress_col, lambda x: x.notna().sum())

    grouped = df.groupby(group_by, dropna=False).agg(**agg_dict).reset_index()

    if "progreso_promedio" in grouped.columns:
        grouped["progreso_promedio"] = grouped["progreso_promedio"].round(1)
    else:
        grouped["progreso_promedio"] = None

    if "con_progreso" not in grouped.columns:
        grouped["con_progreso"] = 0

    grouped = grouped.sort_values("total", ascending=False).reset_index(drop=True)
    grouped.insert(0, "rank", range(1, len(grouped) + 1))

    return grouped


# ═══════════════════════════════════════════════════════════════════════════════
# 4. Agenda — Eventos próximos
# ═══════════════════════════════════════════════════════════════════════════════

@register(
    key="events_agenda",
    label="Agenda — Eventos Próximos",
    category="Events / GTD",
    description=(
        "Lista de eventos ordenados por fecha de inicio. "
        "Permite filtrar por ventana de días hacia adelante. "
        "Fuente ETL: events.Event"
    ),
    sources=[
        {"id": "events", "label": "Events (events.Event via ETL)", "required": True},
    ],
    params=[
        {
            "id": "window_days",
            "label": "Próximos N días (0 = todos)",
            "type": "number",
            "default": 30,
        },
        {
            "id": "include_past",
            "label": "Incluir pasados",
            "type": "boolean",
            "default": False,
        },
        {
            "id": "cols",
            "label": "Columnas a mostrar",
            "type": "multi_column",
            "source": "events",
            "required": False,
        },
    ],
)
def events_agenda(sources: dict, params: dict) -> pd.DataFrame:
    """
    Agenda de eventos con fechas, estado y asistentes.

    Columnas de salida: id, title, start_date, event_status_id, host_id,
                        max_attendees (las disponibles en la fuente)
    """
    df = sources["events"].copy()
    window_days = int(params.get("window_days") or 0)
    include_past = bool(params.get("include_past", False))
    cols = params.get("cols") or []

    now = pd.Timestamp.now(tz="UTC")

    # Detectar columna de fecha de inicio
    start_col = None
    for candidate in ["start_date", "start_datetime", "date", "fecha", "event_date"]:
        if candidate in df.columns:
            start_col = candidate
            break

    if start_col:
        df[start_col] = _to_utc(df[start_col])
        if not include_past:
            df = df[df[start_col] >= now]
        if window_days > 0:
            df = df[df[start_col] <= now + pd.Timedelta(days=window_days)]
        df = df.sort_values(start_col)

    if df.empty:
        return pd.DataFrame(columns=["id", "title", start_col or "start_date"])

    # Selección de columnas
    default_cols = ["id", "title", start_col, "event_status_id", "host_id", "max_attendees"]
    if cols:
        select = [c for c in cols if c in df.columns]
    else:
        select = [c for c in default_cols if c and c in df.columns]

    return df[select].reset_index(drop=True) if select else df.reset_index(drop=True)


# ═══════════════════════════════════════════════════════════════════════════════
# 5. GTD Health Score — Combinado
# ═══════════════════════════════════════════════════════════════════════════════

@register(
    key="events_gtd_health",
    label="GTD Health Score — Diagnóstico Combinado",
    category="Events / GTD",
    description=(
        "Score de salud GTD combinando Inbox (backlog), Tasks (vencidas) y "
        "Projects (sin progreso). Produce una tabla de métricas clave + score 0-100 "
        "lista para KPI card en Dashboard. "
        "Fuentes: inbox (events.InboxItem) + tasks (events.Task) + projects (events.Project)"
    ),
    sources=[
        {"id": "inbox",    "label": "InboxItems   (events.InboxItem)",  "required": True},
        {"id": "tasks",    "label": "Tasks        (events.Task)",       "required": True},
        {"id": "projects", "label": "Projects     (events.Project)",    "required": True},
    ],
    params=[],
)
def events_gtd_health(sources: dict, params: dict) -> pd.DataFrame:
    """
    Score de salud GTD 0–100.

    Columnas de salida:
      metrica, valor, benchmark, estado, peso, aporte_score
    """
    inbox_df    = sources["inbox"].copy()
    tasks_df    = sources["tasks"].copy()
    projects_df = sources["projects"].copy()

    now = pd.Timestamp.now(tz="UTC")

    # ── Inbox metrics ──────────────────────────────────────────────────────────
    inbox_total = len(inbox_df)
    inbox_proc  = int(inbox_df["is_processed"].sum()) if "is_processed" in inbox_df.columns else 0
    inbox_pend  = inbox_total - inbox_proc
    inbox_rate  = round(inbox_proc / inbox_total * 100, 1) if inbox_total > 0 else 100.0

    # ── Tasks metrics ──────────────────────────────────────────────────────────
    tasks_total = len(tasks_df)
    if "due_date" in tasks_df.columns:
        tasks_df["_due"] = _to_utc(tasks_df["due_date"])
        overdue = int((tasks_df["_due"].notna() & (tasks_df["_due"] < now)).sum())
    else:
        overdue = 0
    overdue_pct = round(overdue / tasks_total * 100, 1) if tasks_total > 0 else 0.0

    # ── Projects metrics ───────────────────────────────────────────────────────
    proj_total = len(projects_df)
    progress_col = next(
        (c for c in ["progress", "progreso", "completion_pct"] if c in projects_df.columns),
        None,
    )
    if progress_col:
        projects_df[progress_col] = pd.to_numeric(projects_df[progress_col], errors="coerce")
        stalled = int((projects_df[progress_col].fillna(0) == 0).sum())
    else:
        stalled = 0
    stalled_pct = round(stalled / proj_total * 100, 1) if proj_total > 0 else 0.0

    # ── Score calculation (ponderado) ─────────────────────────────────────────
    # Inbox rate → 40 pts (objetivo: ≥ 80 % procesados)
    # Overdue pct → 35 pts (objetivo: 0 % vencidas)
    # Stalled pct → 25 pts (objetivo: 0 % proyectos sin avance)
    score_inbox   = min(40, round(inbox_rate / 100 * 40, 1))
    score_tasks   = min(35, round((1 - overdue_pct / 100) * 35, 1))
    score_proj    = min(25, round((1 - stalled_pct / 100) * 25, 1))
    total_score   = round(score_inbox + score_tasks + score_proj, 1)

    def _estado(val, benchmark, higher_is_better=True):
        ok = val >= benchmark if higher_is_better else val <= benchmark
        if ok:
            return "✅ Bueno"
        elif (val >= benchmark * 0.7 if higher_is_better else val <= benchmark * 1.5):
            return "⚠️ Regular"
        return "🔴 Crítico"

    rows = [
        {
            "metrica": "Inbox procesado (%)",
            "valor": inbox_rate,
            "benchmark": 80.0,
            "estado": _estado(inbox_rate, 80.0, True),
            "peso": "40 pts",
            "aporte_score": score_inbox,
        },
        {
            "metrica": "Tareas vencidas (%)",
            "valor": overdue_pct,
            "benchmark": 5.0,
            "estado": _estado(overdue_pct, 5.0, False),
            "peso": "35 pts",
            "aporte_score": score_tasks,
        },
        {
            "metrica": "Proyectos sin avance (%)",
            "valor": stalled_pct,
            "benchmark": 20.0,
            "estado": _estado(stalled_pct, 20.0, False),
            "peso": "25 pts",
            "aporte_score": score_proj,
        },
        {
            "metrica": "GTD Health Score",
            "valor": total_score,
            "benchmark": 75.0,
            "estado": _estado(total_score, 75.0, True),
            "peso": "100 pts",
            "aporte_score": total_score,
        },
        # Detalle complementario
        {
            "metrica": "Inbox pendientes (absoluto)",
            "valor": float(inbox_pend),
            "benchmark": 0.0,
            "estado": _estado(inbox_pend, 10, False),
            "peso": "—",
            "aporte_score": None,
        },
        {
            "metrica": "Tareas vencidas (absoluto)",
            "valor": float(overdue),
            "benchmark": 0.0,
            "estado": _estado(overdue, 3, False),
            "peso": "—",
            "aporte_score": None,
        },
        {
            "metrica": "Proyectos sin avance (absoluto)",
            "valor": float(stalled),
            "benchmark": 0.0,
            "estado": _estado(stalled, 5, False),
            "peso": "—",
            "aporte_score": None,
        },
    ]

    return pd.DataFrame(rows)
