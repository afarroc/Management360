# analyst/report_functions.py
"""
Registry of pre-defined report functions.

Register a new function:

    @register(
        key="my_fn", label="My Label", category="Category",
        sources=[{"id":"src", "label":"Source", "required":True}],
        params=[{"id":"col","label":"Column","type":"column_select","source":"src","required":True}],
    )
    def my_fn(sources: dict[str, pd.DataFrame], params: dict) -> pd.DataFrame:
        return result_df

Param types: column_select | multi_column | number | boolean | text
"""

import logging
import pandas as pd
import numpy as np
from typing import Callable, Dict, List

logger = logging.getLogger(__name__)

_REGISTRY: Dict[str, dict] = {}


def register(key, label, category="General", sources=None, params=None, description=""):
    def decorator(fn: Callable) -> Callable:
        _REGISTRY[key] = {
            "key": key, "label": label, "category": category,
            "description": description or (fn.__doc__ or "").strip(),
            "sources": sources or [], "params": params or [], "fn": fn,
        }
        return fn
    return decorator


def get_registry() -> Dict[str, dict]:
    return {k: {kk: vv for kk, vv in v.items() if kk != "fn"} for k, v in _REGISTRY.items()}


def get_function(key: str) -> Callable | None:
    e = _REGISTRY.get(key)
    return e["fn"] if e else None


def get_meta(key: str) -> dict | None:
    e = _REGISTRY.get(key)
    return {kk: vv for kk, vv in e.items() if kk != "fn"} if e else None


# ═══════════════════════════════════════════════════════════════════════════════
# Built-in functions
# ═══════════════════════════════════════════════════════════════════════════════

@register(
    key="quality_avg",
    label="Promedio de Notas de Calidad",
    category="Calidad",
    description=(
        "Cruza un modelo base (agentes, planilla) con un DataFrame de notas. "
        "Calcula promedio por agente y opcionalmente agrupa por dimensión."
    ),
    sources=[
        {"id": "base",  "label": "Fuente base (agentes, usuarios, planilla)", "required": True},
        {"id": "notes", "label": "Dataset de notas de calidad",               "required": True},
    ],
    params=[
        {"id": "join_col_base",  "label": "Columna de cruce (base)",   "type": "column_select", "source": "base",  "required": True},
        {"id": "join_col_notes", "label": "Columna de cruce (notas)",  "type": "column_select", "source": "notes", "required": True},
        {"id": "note_cols",      "label": "Columnas de notas",         "type": "multi_column",  "source": "notes", "required": True},
        {"id": "group_by",       "label": "Agrupar por (opcional)",    "type": "column_select", "source": "base",  "required": False},
        {"id": "min_score",      "label": "Nota mínima aprobatoria",   "type": "number",        "default": 70,     "required": False},
    ],
)
def quality_avg(sources: dict, params: dict) -> pd.DataFrame:
    """Average quality notes per agent, optionally grouped."""
    base  = sources["base"].copy()
    notes = sources["notes"].copy()

    join_base  = params.get("join_col_base")
    join_notes = params.get("join_col_notes")
    note_cols  = params.get("note_cols") or []
    group_by   = params.get("group_by") or None
    min_score  = float(params.get("min_score") or 70)

    if not join_base or not join_notes:
        raise ValueError("Debes especificar las columnas de cruce.")
    if not note_cols:
        raise ValueError("Selecciona al menos una columna de notas.")

    for col in note_cols:
        if col in notes.columns:
            notes[col] = pd.to_numeric(notes[col], errors="coerce")

    notes["__avg__"] = notes[[c for c in note_cols if c in notes.columns]].mean(axis=1)

    merged = base.merge(
        notes[[join_notes, "__avg__"] + [c for c in note_cols if c in notes.columns]],
        left_on=join_base, right_on=join_notes, how="left",
    )
    merged["promedio_notas"] = merged["__avg__"].round(2)
    merged["estado"] = merged["promedio_notas"].apply(
        lambda x: "Aprobado" if pd.notna(x) and x >= min_score
                  else ("Sin notas" if pd.isna(x) else "Reprobado")
    )
    merged.drop(columns=["__avg__"], errors="ignore", inplace=True)

    if group_by and group_by in merged.columns:
        merged = (
            merged.groupby(group_by)
            .agg(
                total          = (join_base,         "count"),
                promedio_grupo = ("promedio_notas",   "mean"),
                aprobados      = ("estado", lambda s: (s == "Aprobado").sum()),
                reprobados     = ("estado", lambda s: (s == "Reprobado").sum()),
                sin_notas      = ("estado", lambda s: (s == "Sin notas").sum()),
            )
            .reset_index()
        )
        merged["promedio_grupo"]  = merged["promedio_grupo"].round(2)
        merged["pct_aprobados"]   = (merged["aprobados"] / merged["total"] * 100).round(1)

    return merged


@register(
    key="planilla_summary",
    label="Resumen de Planilla",
    category="RRHH",
    description="Estadísticas de planilla agrupadas por una dimensión (cargo, sede, etc.).",
    sources=[
        {"id": "planilla", "label": "Dataset de planilla", "required": True},
    ],
    params=[
        {"id": "numeric_cols", "label": "Columnas numéricas (salario, horas…)", "type": "multi_column",  "source": "planilla", "required": True},
        {"id": "group_by",     "label": "Agrupar por",                          "type": "column_select", "source": "planilla", "required": False},
    ],
)
def planilla_summary(sources: dict, params: dict) -> pd.DataFrame:
    """Aggregate payroll DataFrame."""
    df       = sources["planilla"].copy()
    num_cols = params.get("numeric_cols") or []
    group_by = params.get("group_by") or None

    for col in num_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    valid = [c for c in num_cols if c in df.columns]
    if not valid:
        raise ValueError("Ninguna columna numérica válida seleccionada.")

    if group_by and group_by in df.columns:
        agg   = {c: ["sum", "mean", "min", "max"] for c in valid}
        result = df.groupby(group_by).agg(agg)
        result.columns = ["_".join(c) for c in result.columns]
        result = result.reset_index()
    else:
        result = df[valid].describe().T.reset_index().rename(columns={"index": "columna"})

    return result


@register(
    key="period_comparison",
    label="Comparativa entre Períodos",
    category="Análisis",
    description="Compara dos datasets del mismo tipo y calcula variación absoluta y porcentual.",
    sources=[
        {"id": "periodo_a", "label": "Período A – referencia / anterior", "required": True},
        {"id": "periodo_b", "label": "Período B – actual",                "required": True},
    ],
    params=[
        {"id": "key_col",   "label": "Columna identificadora",        "type": "column_select", "source": "periodo_a", "required": True},
        {"id": "value_cols","label": "Columnas de valores a comparar","type": "multi_column",  "source": "periodo_a", "required": True},
    ],
)
def period_comparison(sources: dict, params: dict) -> pd.DataFrame:
    """Side-by-side comparison with absolute and % variation."""
    df_a     = sources["periodo_a"].copy()
    df_b     = sources["periodo_b"].copy()
    key_col  = params.get("key_col")
    val_cols = params.get("value_cols") or []

    if not key_col or not val_cols:
        raise ValueError("Especifica columna clave y columnas de valores.")

    for col in val_cols:
        for df in (df_a, df_b):
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")

    keep_a = [key_col] + [c for c in val_cols if c in df_a.columns]
    keep_b = [key_col] + [c for c in val_cols if c in df_b.columns]
    merged = df_a[keep_a].merge(df_b[keep_b], on=key_col, how="outer", suffixes=("_A", "_B"))

    for col in val_cols:
        ca, cb = f"{col}_A", f"{col}_B"
        if ca in merged.columns and cb in merged.columns:
            merged[f"{col}_var"]     = (merged[cb] - merged[ca]).round(2)
            merged[f"{col}_var_pct"] = ((merged[cb] - merged[ca]) / merged[ca].replace(0, np.nan) * 100).round(1)

    return merged


@register(
    key="ranking",
    label="Ranking por Métrica",
    category="Análisis",
    description="Ordena y clasifica un dataset según una métrica numérica.",
    sources=[
        {"id": "data", "label": "Dataset a rankear", "required": True},
    ],
    params=[
        {"id": "label_col",  "label": "Columna de etiqueta",         "type": "column_select", "source": "data", "required": True},
        {"id": "metric_col", "label": "Columna métrica (numérica)",  "type": "column_select", "source": "data", "required": True},
        {"id": "ascending",  "label": "Orden ascendente",            "type": "boolean",       "default": False, "required": False},
        {"id": "top_n",      "label": "Top N (0 = todos)",           "type": "number",        "default": 0,     "required": False},
    ],
)
def ranking(sources: dict, params: dict) -> pd.DataFrame:
    """Rank rows by a numeric metric."""
    df         = sources["data"].copy()
    label_col  = params.get("label_col")
    metric_col = params.get("metric_col")
    ascending  = bool(params.get("ascending", False))
    top_n      = int(params.get("top_n") or 0)

    if not label_col or not metric_col:
        raise ValueError("Especifica columna de etiqueta y métrica.")

    df[metric_col] = pd.to_numeric(df[metric_col], errors="coerce")
    df = df.dropna(subset=[metric_col]).sort_values(metric_col, ascending=ascending).reset_index(drop=True)
    df.insert(0, "posicion", range(1, len(df) + 1))

    return df.head(top_n) if top_n > 0 else df


# ═══════════════════════════════════════════════════════════════════════════════
# Fase 3 — Nuevas funciones
# ═══════════════════════════════════════════════════════════════════════════════

@register(
    key="attendance_report",
    label="Reporte de Asistencia",
    category="RRHH",
    description=(
        "Calcula asistencia, ausencias y tardanzas por agente. "
        "Acepta cualquier columna de estado con valores como 'presente/ausente/tardanza'."
    ),
    sources=[
        {"id": "attendance", "label": "Dataset de asistencia", "required": True},
    ],
    params=[
        {"id": "agent_col",  "label": "Columna de agente / empleado", "type": "column_select", "source": "attendance", "required": True},
        {"id": "status_col", "label": "Columna de estado",            "type": "column_select", "source": "attendance", "required": True},
        {"id": "date_col",   "label": "Columna de fecha (opcional)",  "type": "column_select", "source": "attendance", "required": False},
        {"id": "group_by",   "label": "Agrupar por (área, equipo…)",  "type": "column_select", "source": "attendance", "required": False},
    ],
)
def attendance_report(sources: dict, params: dict) -> pd.DataFrame:
    """Attendance summary: present / absent / late counts and percentages per agent."""
    df         = sources["attendance"].copy()
    agent_col  = params.get("agent_col")
    status_col = params.get("status_col")
    group_by   = params.get("group_by") or None

    if not agent_col or not status_col:
        raise ValueError("Debes especificar columna de agente y columna de estado.")

    PRESENT = {"presente", "p", "1", "yes", "si", "sí", "asistio", "asistió", "true"}
    LATE    = {"tardanza", "t", "tarde", "retardo", "tardy", "late"}
    ABSENT  = {"ausente", "a", "0", "no", "false", "faltó", "falto", "absent"}

    def _classify(v):
        if v is None or (isinstance(v, float) and pd.isna(v)):
            return "ausente"
        s = str(v).lower().strip()
        if s in PRESENT: return "presente"
        if s in LATE:    return "tardanza"
        if s in ABSENT:  return "ausente"
        return s  # keep as-is if unknown

    df["__st__"] = df[status_col].apply(_classify)

    pivot = (
        df.groupby(agent_col)["__st__"]
        .value_counts()
        .unstack(fill_value=0)
        .reset_index()
    )
    for col in ["presente", "tardanza", "ausente"]:
        if col not in pivot.columns:
            pivot[col] = 0

    pivot["total"]           = pivot[["presente", "tardanza", "ausente"]].sum(axis=1)
    pivot["pct_asistencia"]  = ((pivot["presente"] + pivot["tardanza"]) / pivot["total"] * 100).round(1)
    pivot["pct_presente"]    = (pivot["presente"]  / pivot["total"] * 100).round(1)
    pivot["pct_tardanza"]    = (pivot["tardanza"]  / pivot["total"] * 100).round(1)
    pivot["pct_ausente"]     = (pivot["ausente"]   / pivot["total"] * 100).round(1)

    if group_by and group_by in df.columns and group_by != agent_col:
        gmap = df.groupby(agent_col)[group_by].agg(lambda x: x.mode()[0] if len(x) > 0 else None)
        pivot = pivot.merge(gmap.rename(group_by), on=agent_col, how="left")

    return pivot.sort_values("pct_asistencia", ascending=False).reset_index(drop=True)


@register(
    key="performance_report",
    label="Reporte de Desempeño vs Meta",
    category="Análisis",
    description=(
        "Compara métricas reales contra una meta fija o columna de objetivos. "
        "Clasifica cada agente como 'Sobre meta' o 'Bajo meta'."
    ),
    sources=[
        {"id": "performance", "label": "Dataset de métricas/desempeño", "required": True},
    ],
    params=[
        {"id": "agent_col",    "label": "Columna de agente / empleado",       "type": "column_select", "source": "performance", "required": True},
        {"id": "metric_cols",  "label": "Métricas a evaluar",                 "type": "multi_column",  "source": "performance", "required": True},
        {"id": "target_value", "label": "Meta fija (número)",                 "type": "number",        "default": 80,           "required": False},
        {"id": "target_col",   "label": "Columna de meta individual (opc.)",  "type": "column_select", "source": "performance", "required": False},
        {"id": "group_by",     "label": "Agrupar por",                        "type": "column_select", "source": "performance", "required": False},
    ],
)
def performance_report(sources: dict, params: dict) -> pd.DataFrame:
    """Performance vs target by agent with achievement % and status."""
    df          = sources["performance"].copy()
    agent_col   = params.get("agent_col")
    metric_cols = params.get("metric_cols") or []
    target_val  = float(params.get("target_value") or 0)
    target_col  = params.get("target_col") or None
    group_by    = params.get("group_by")   or None

    if not agent_col:
        raise ValueError("Debes especificar la columna de agente.")
    if not metric_cols:
        raise ValueError("Selecciona al menos una métrica.")

    valid = [c for c in metric_cols if c in df.columns]
    if not valid:
        raise ValueError("Ninguna columna de métrica válida.")

    for col in valid:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    agg = df.groupby(agent_col)[valid].mean().round(2).reset_index()

    # Per-agent target from column (if provided)
    if target_col and target_col in df.columns:
        df[target_col] = pd.to_numeric(df[target_col], errors="coerce")
        tgt_agg = df.groupby(agent_col)[target_col].mean().round(2)
        agg = agg.merge(tgt_agg.rename("meta"), on=agent_col, how="left")
        target_series = agg["meta"]
    else:
        agg["meta"]    = round(target_val, 2)
        target_series  = target_val

    for col in valid:
        ref = target_series if isinstance(target_series, pd.Series) else target_val
        if (isinstance(ref, (int, float)) and ref > 0) or isinstance(ref, pd.Series):
            agg[f"{col}_cumplimiento_%"] = (agg[col] / ref * 100).round(1)
            agg[f"{col}_estado"] = agg[col].apply(
                lambda x, t=ref if isinstance(ref, (int,float)) else None:
                    ("✓ Sobre meta" if pd.notna(x) and x >= (t if t else 0) else "✗ Bajo meta")
                    if t is not None else "—"
            )
        if isinstance(ref, pd.Series):
            agg[f"{col}_cumplimiento_%"] = (agg[col] / ref * 100).round(1)
            agg[f"{col}_estado"] = [
                "✓ Sobre meta" if pd.notna(actual) and pd.notna(target) and actual >= target
                else "✗ Bajo meta"
                for actual, target in zip(agg[col], ref)
            ]

    if group_by and group_by in df.columns and group_by != agent_col:
        gmap = df.groupby(agent_col)[group_by].agg(lambda x: x.mode()[0] if len(x) > 0 else None)
        agg = agg.merge(gmap.rename(group_by), on=agent_col, how="left")

    return agg.sort_values(valid[0], ascending=False).reset_index(drop=True)


@register(
    key="funnel_report",
    label="Embudo de Conversión",
    category="Análisis",
    description=(
        "Muestra la conversión entre etapas de un funnel. "
        "Calcula tasas de conversión vs primera etapa y entre etapas consecutivas."
    ),
    sources=[
        {"id": "data", "label": "Dataset con etapas del funnel", "required": True},
    ],
    params=[
        {"id": "stage_col", "label": "Columna de etapas",                    "type": "column_select", "source": "data", "required": True},
        {"id": "count_col", "label": "Columna de cantidad (vacío = contar)",  "type": "column_select", "source": "data", "required": False},
        {"id": "order_col", "label": "Columna de orden (vacío = auto)",       "type": "column_select", "source": "data", "required": False},
    ],
)
def funnel_report(sources: dict, params: dict) -> pd.DataFrame:
    """Conversion funnel with step-by-step and cumulative rates."""
    df        = sources["data"].copy()
    stage_col = params.get("stage_col")
    count_col = params.get("count_col") or None
    order_col = params.get("order_col") or None

    if not stage_col:
        raise ValueError("Debes especificar la columna de etapas.")

    if count_col and count_col in df.columns:
        df[count_col] = pd.to_numeric(df[count_col], errors="coerce")
        funnel = df.groupby(stage_col)[count_col].sum().reset_index()
        funnel.columns = ["etapa", "total"]
    else:
        funnel = df[stage_col].value_counts().reset_index()
        funnel.columns = ["etapa", "total"]

    if order_col and order_col in df.columns:
        omap = df.drop_duplicates(subset=[stage_col]).set_index(stage_col)[order_col]
        funnel["_ord"] = funnel["etapa"].map(omap)
        funnel = funnel.sort_values("_ord").drop(columns=["_ord"])
    else:
        funnel = funnel.sort_values("total", ascending=False)

    funnel = funnel.reset_index(drop=True)
    first  = funnel["total"].iloc[0] if len(funnel) > 0 else 1

    funnel["conv_vs_inicio_%"] = (funnel["total"] / first * 100).round(1)
    conv_prev = [None]
    for i in range(1, len(funnel)):
        prev = funnel.at[i-1, "total"]
        curr = funnel.at[i, "total"]
        conv_prev.append(round(curr / prev * 100, 1) if prev > 0 else None)
    funnel["conv_vs_anterior_%"] = conv_prev

    funnel["perdida"]    = (funnel["total"] - funnel["total"].shift(-1)).clip(lower=0).fillna(0).astype(int)
    funnel["perdida_%"]  = (funnel["perdida"] / funnel["total"] * 100).round(1)

    return funnel


# ═══════════════════════════════════════════════════════════════════════════════
# WFM / Sim functions
# ═══════════════════════════════════════════════════════════════════════════════

@register(
    key="sim_agent_performance",
    label="Performance por Agente (WFM)",
    category="WFM",
    description="AHT, contactos, SL y abandono individual por agente. Diseñado para datos de sim.Interaction.",
    sources=[
        {"id": "interactions", "label": "Interacciones", "required": True,
         "hint": "Dataset desde sim.Interaction vía ETL"},
    ],
    params=[
        {"id": "agente_col",    "label": "Columna agente",     "type": "column_select", "source": "interactions", "required": True},
        {"id": "duracion_col",  "label": "Columna duración (s)","type": "column_select", "source": "interactions", "required": True},
        {"id": "status_col",    "label": "Columna status",      "type": "column_select", "source": "interactions", "required": True},
        {"id": "acw_col",       "label": "Columna ACW (s)",     "type": "column_select", "source": "interactions", "required": False},
        {"id": "fecha_col",     "label": "Columna fecha",       "type": "column_select", "source": "interactions", "required": False},
        {"id": "sl_threshold",  "label": "Umbral SL (segundos)","type": "number",        "required": False, "default": 20},
        {"id": "min_contacts",  "label": "Mínimo contactos",   "type": "number",        "required": False, "default": 5},
    ],
)
def sim_agent_performance(sources: dict, params: dict) -> pd.DataFrame:
    """
    Performance individual por agente:
    contactos, AHT (talk+ACW), tasa de atención, abandono y SL estimado.

    Status considerados atendidos: atendida, venta, agenda.
    """
    df = sources["interactions"].copy()

    agente_col   = params.get("agente_col",   "agente")
    dur_col      = params.get("duracion_col", "duracion_s")
    status_col   = params.get("status_col",   "status")
    acw_col      = params.get("acw_col")
    sl_threshold = int(params.get("sl_threshold", 20))
    min_contacts = int(params.get("min_contacts", 5))

    # Normalizar columnas
    for col in [agente_col, dur_col, status_col]:
        if col not in df.columns:
            raise ValueError(f"Columna '{col}' no encontrada. Columnas: {list(df.columns)}")

    df[dur_col] = pd.to_numeric(df[dur_col], errors="coerce").fillna(0)
    if acw_col and acw_col in df.columns:
        df[acw_col] = pd.to_numeric(df[acw_col], errors="coerce").fillna(0)
        df["_tmo_total"] = df[dur_col] + df[acw_col]
    else:
        df["_tmo_total"] = df[dur_col]

    ATENDIDAS  = {"atendida", "venta", "agenda"}
    ABANDONADAS = {"abandonada"}

    df["_atendida"]  = df[status_col].str.lower().isin(ATENDIDAS)
    df["_abandono"]  = df[status_col].str.lower().isin(ABANDONADAS)
    df["_venta"]     = df[status_col].str.lower() == "venta"
    df["_sl_ok"]     = df["_atendida"] & (df[dur_col] <= sl_threshold)

    grp = df.groupby(agente_col)

    # Aggregate — group must be reset_index to get column back
    agg = grp.agg(
        total_contactos=(agente_col, "count"),
        atendidas=("_atendida", "sum"),
        abandonadas=("_abandono", "sum"),
        ventas=("_venta", "sum"),
        sl_count=("_sl_ok", "sum"),
    ).reset_index()  # agente_col becomes a regular column here

    # AHT only on answered rows
    df_ans   = df[df["_atendida"]].copy()
    aht_map  = df_ans.groupby(agente_col)["_tmo_total"].mean().round(0)
    talk_map = df_ans.groupby(agente_col)[dur_col].mean().round(0)
    agg["aht_s"]  = agg[agente_col].map(aht_map).fillna(0)
    agg["talk_s"] = agg[agente_col].map(talk_map).fillna(0)
    result = agg

    # Derived
    result["atencion_%"]  = (result["atendidas"] / result["total_contactos"] * 100).round(1)
    result["abandono_%"]  = (result["abandonadas"] / result["total_contactos"] * 100).round(1)
    result["sl_%"]        = (result["sl_count"] / result["atendidas"].replace(0, np.nan) * 100).round(1)
    result["conv_%"]      = (result["ventas"] / result["atendidas"].replace(0, np.nan) * 100).round(2)
    result["aht_min"]     = (result["aht_s"] / 60).round(2)

    # Filter min contacts
    result = result[result["total_contactos"] >= min_contacts].copy()

    # Ranking
    result = result.sort_values("atendidas", ascending=False).reset_index(drop=True)
    result.insert(0, "rank", range(1, len(result) + 1))

    # Rename agente_col to 'agente' for consistent output
    if agente_col != "agente":
        result = result.rename(columns={agente_col: "agente"})
    result = result.fillna(0)
    result["aht_s"]  = result["aht_s"].astype(int)
    result["talk_s"] = result["talk_s"].astype(int)

    return result[[
        "rank", "agente", "total_contactos", "atendidas", "abandonadas", "ventas",
        "atencion_%", "abandono_%", "sl_%", "conv_%", "aht_min", "aht_s", "talk_s",
    ]]


@register(
    key="sim_inbound_daily",
    label="KPIs Inbound Diarios (WFM)",
    category="WFM",
    description="Volumen, SL, TMO y abandono por día. Vista del supervisor de turno.",
    sources=[
        {"id": "interactions", "label": "Interacciones", "required": True},
    ],
    params=[
        {"id": "fecha_col",    "label": "Columna fecha",        "type": "column_select", "source": "interactions", "required": True},
        {"id": "status_col",   "label": "Columna status",       "type": "column_select", "source": "interactions", "required": True},
        {"id": "duracion_col", "label": "Columna duración (s)", "type": "column_select", "source": "interactions", "required": True},
        {"id": "canal_col",    "label": "Columna canal",        "type": "column_select", "source": "interactions", "required": False},
        {"id": "canal_filter", "label": "Filtrar por canal",    "type": "text",          "required": False, "default": "inbound"},
        {"id": "sl_threshold", "label": "Umbral SL (segundos)", "type": "number",        "required": False, "default": 20},
    ],
)
def sim_inbound_daily(sources: dict, params: dict) -> pd.DataFrame:
    """
    KPIs diarios: entrantes, atendidas, abandonadas, SL%, TMO, AHT.
    Equivalente al informe diario que se entrega al cliente.
    """
    df = sources["interactions"].copy()

    fecha_col    = params.get("fecha_col",    "fecha")
    status_col   = params.get("status_col",   "status")
    dur_col      = params.get("duracion_col", "duracion_s")
    canal_col    = params.get("canal_col")
    canal_filter = params.get("canal_filter", "inbound")
    sl_threshold = int(params.get("sl_threshold", 20))

    for col in [fecha_col, status_col, dur_col]:
        if col not in df.columns:
            raise ValueError(f"Columna '{col}' no encontrada.")

    # Canal filter
    if canal_col and canal_col in df.columns and canal_filter:
        df = df[df[canal_col].str.lower() == canal_filter.lower()]

    df[dur_col] = pd.to_numeric(df[dur_col], errors="coerce").fillna(0)
    df["_fecha"] = pd.to_datetime(df[fecha_col], errors="coerce").dt.date

    ATENDIDAS = {"atendida", "venta", "agenda"}
    df["_atendida"] = df[status_col].str.lower().isin(ATENDIDAS)
    df["_abandono"] = df[status_col].str.lower() == "abandonada"
    df["_sl_ok"]    = df["_atendida"] & (df[dur_col] <= sl_threshold)

    grp = df.groupby("_fecha")

    result = pd.DataFrame({
        "fecha":       grp["_fecha"].first(),
        "entrantes":   grp[status_col].count(),
        "atendidas":   grp["_atendida"].sum(),
        "abandonadas": grp["_abandono"].sum(),
        "sl_count":    grp["_sl_ok"].sum(),
        "tmo_s":       df[df["_atendida"]].groupby("_fecha")[dur_col].mean().round(0),
    }).reset_index(drop=True)

    result["na_%"]     = (result["atendidas"] / result["entrantes"] * 100).round(1)
    result["sl_%"]     = (result["sl_count"] / result["atendidas"].replace(0, np.nan) * 100).round(1)
    result["aban_%"]   = (result["abandonadas"] / result["entrantes"] * 100).round(1)
    result["tmo_min"]  = (result["tmo_s"] / 60).round(2)

    # Day of week
    result["dia"]      = pd.to_datetime(result["fecha"]).dt.day_name()
    result["tmo_s"]    = result["tmo_s"].fillna(0).astype(int)

    return result[["fecha", "dia", "entrantes", "atendidas", "abandonadas",
                   "na_%", "sl_%", "aban_%", "tmo_min", "tmo_s"]].sort_values("fecha")


@register(
    key="sim_contact_funnel",
    label="Embudo de Contactabilidad (Outbound)",
    category="WFM",
    description="Funnel real outbound: marcaciones → contacto → venta. Calibrado con datos reales (27.6% contactabilidad).",
    sources=[
        {"id": "interactions", "label": "Interacciones outbound", "required": True},
    ],
    params=[
        {"id": "status_col",   "label": "Columna status",       "type": "column_select", "source": "interactions", "required": True},
        {"id": "tipif_col",    "label": "Columna tipificación",  "type": "column_select", "source": "interactions", "required": False},
        {"id": "fecha_col",    "label": "Columna fecha",         "type": "column_select", "source": "interactions", "required": False},
        {"id": "agrupar_por",  "label": "Agrupar por",          "type": "text",          "required": False,
         "default": "", "hint": "Vacío = total. O nombre de columna: skill, agente, fecha"},
    ],
)
def sim_contact_funnel(sources: dict, params: dict) -> pd.DataFrame:
    """
    Embudo de contactabilidad outbound.
    Muestra las tasas reales de cada etapa del funnel discador.
    """
    df = sources["interactions"].copy()

    status_col  = params.get("status_col",  "status")
    tipif_col   = params.get("tipif_col")
    agrupar_por = str(params.get("agrupar_por", "")).strip()

    if status_col not in df.columns:
        raise ValueError(f"Columna '{status_col}' no encontrada.")

    s = df[status_col].str.lower()
    df["_marcacion"]  = True
    df["_contacto"]   = s.isin({"atendida", "venta", "agenda", "rechazo"})
    df["_venta"]      = s == "venta"
    df["_agenda"]     = s == "agenda"
    df["_rechazo"]    = s == "rechazo"
    df["_no_contacto"]= s == "no_contacto"

    def _funnel(sub: pd.DataFrame, label: str = "Total") -> list:
        total = len(sub)
        cont  = sub["_contacto"].sum()
        venta = sub["_venta"].sum()
        agend = sub["_agenda"].sum()
        rech  = sub["_rechazo"].sum()
        nocon = sub["_no_contacto"].sum()

        def pct(n, d): return round(n / d * 100, 2) if d > 0 else 0.0

        return [
            {"grupo": label, "etapa": "Marcaciones",     "cantidad": total,  "pct_total": 100.0,             "pct_anterior": None},
            {"grupo": label, "etapa": "Contacto efectivo","cantidad": cont,  "pct_total": pct(cont, total),  "pct_anterior": pct(cont, total)},
            {"grupo": label, "etapa": "└─ Venta",         "cantidad": venta, "pct_total": pct(venta, total), "pct_anterior": pct(venta, cont)},
            {"grupo": label, "etapa": "└─ Agenda/Callback","cantidad": agend, "pct_total": pct(agend, total), "pct_anterior": pct(agend, cont)},
            {"grupo": label, "etapa": "└─ Rechazo",       "cantidad": rech,  "pct_total": pct(rech, total),  "pct_anterior": pct(rech, cont)},
            {"grupo": label, "etapa": "No contacto",      "cantidad": nocon, "pct_total": pct(nocon, total), "pct_anterior": pct(nocon, total)},
        ]

    if agrupar_por and agrupar_por in df.columns:
        rows = []
        for grp_val, sub in df.groupby(agrupar_por):
            rows.extend(_funnel(sub, str(grp_val)))
        result = pd.DataFrame(rows)
    else:
        result = pd.DataFrame(_funnel(df))
        result = result.drop(columns=["grupo"])

    result["cantidad"]      = result["cantidad"].astype(int)
    result["pct_total"]     = result["pct_total"].round(2)
    result["pct_anterior"]  = result["pct_anterior"].round(2)

    return result


# ═══════════════════════════════════════════════════════════════════════════════
# KPIs / CallRecord functions (Sprint 7)
# ═══════════════════════════════════════════════════════════════════════════════

@register(
    key='kpis_aht_report',
    label='Reporte AHT por Dimensión',
    category='WFM',
    description='AHT promedio agrupado por servicio, canal, agente o supervisor. '
                'Requiere dataset de CallRecord con columnas: fecha, agente, supervisor, servicio, canal, aht, eventos.',
    sources=[
        {'id': 'callrecords', 'label': 'CallRecords', 'required': True},
    ],
    params=[
        {'id': 'group_by',     'label': 'Agrupar por',   'type': 'choice',
         'choices': ['servicio', 'canal', 'agente', 'supervisor', 'semana'], 'required': True},
        {'id': 'top_n',        'label': 'Top N',          'type': 'number',  'default': 20},
        {'id': 'fecha_col',    'label': 'Columna fecha',  'type': 'column_select', 'source': 'callrecords', 'required': False},
        {'id': 'aht_col',      'label': 'Columna AHT',    'type': 'column_select', 'source': 'callrecords', 'required': False},
        {'id': 'eventos_col',  'label': 'Columna eventos','type': 'column_select', 'source': 'callrecords', 'required': False},
    ],
)
def kpis_aht_report(sources: dict, params: dict):
    """
    AHT promedio por dimensión elegida.

    Output columns:
      {group_by}, total_registros, avg_aht_s, avg_aht_min, total_eventos, pct_total
    """
    df        = sources['callrecords']
    group_by  = params.get('group_by', 'servicio')
    top_n     = int(params.get('top_n', 20))
    aht_col   = params.get('aht_col') or 'aht'
    ev_col    = params.get('eventos_col') or 'eventos'

    if group_by not in df.columns:
        raise ValueError(f"Columna '{group_by}' no encontrada en el dataset.")
    if aht_col not in df.columns:
        raise ValueError(f"Columna AHT '{aht_col}' no encontrada.")

    df[aht_col] = pd.to_numeric(df[aht_col], errors='coerce')
    if ev_col in df.columns:
        df[ev_col] = pd.to_numeric(df[ev_col], errors='coerce').fillna(0)

    grouped = df.groupby(group_by).agg(
        total_registros = (aht_col, 'count'),
        avg_aht_s       = (aht_col, 'mean'),
        total_eventos   = (ev_col, 'sum') if ev_col in df.columns else (aht_col, 'count'),
    ).reset_index()

    grouped['avg_aht_min'] = (grouped['avg_aht_s'] / 60).round(2)
    grouped['avg_aht_s']   = grouped['avg_aht_s'].round(2)
    total_ev = grouped['total_eventos'].sum()
    grouped['pct_total']   = ((grouped['total_eventos'] / total_ev * 100).round(1)
                               if total_ev > 0 else 0)

    grouped = grouped.sort_values('avg_aht_s', ascending=False).head(top_n)
    grouped = grouped.reset_index(drop=True)
    grouped.insert(0, 'rank', range(1, len(grouped) + 1))

    return grouped


@register(
    key='kpis_satisfaction_report',
    label='Reporte de Satisfacción por Agente',
    category='WFM',
    description='Satisfacción promedio y ranking por agente/supervisor. '
                'Dataset: CallRecord con columnas satisfaccion, agente, supervisor.',
    sources=[
        {'id': 'callrecords', 'label': 'CallRecords', 'required': True},
    ],
    params=[
        {'id': 'group_by',    'label': 'Agrupar por',   'type': 'choice',
         'choices': ['agente', 'supervisor', 'servicio', 'canal'], 'required': True},
        {'id': 'sat_col',     'label': 'Columna CSAT',  'type': 'column_select',
         'source': 'callrecords', 'required': False},
        {'id': 'min_evals',   'label': 'Mín. evaluaciones', 'type': 'number', 'default': 5},
        {'id': 'top_n',       'label': 'Top N',          'type': 'number',  'default': 20},
    ],
)
def kpis_satisfaction_report(sources: dict, params: dict):
    """
    Ranking de satisfacción por dimensión elegida.

    Output: rank, {group_by}, total_evals, avg_sat, min_sat, max_sat, sat_band
    """
    df       = sources['callrecords']
    group_by = params.get('group_by', 'agente')
    sat_col  = params.get('sat_col') or 'satisfaccion'
    eval_col = 'evaluaciones'
    min_evals = int(params.get('min_evals', 5))
    top_n     = int(params.get('top_n', 20))

    if sat_col not in df.columns:
        raise ValueError(f"Columna satisfacción '{sat_col}' no encontrada.")

    df[sat_col] = pd.to_numeric(df[sat_col], errors='coerce')
    has_evals = eval_col in df.columns

    agg = {
        'avg_sat': (sat_col, 'mean'),
        'min_sat': (sat_col, 'min'),
        'max_sat': (sat_col, 'max'),
    }
    if has_evals:
        df[eval_col] = pd.to_numeric(df[eval_col], errors='coerce').fillna(0)
        agg['total_evals'] = (eval_col, 'sum')
    else:
        agg['total_evals'] = (sat_col, 'count')

    grouped = df.groupby(group_by).agg(**agg).reset_index()

    if has_evals and min_evals > 0:
        grouped = grouped[grouped['total_evals'] >= min_evals]

    grouped['avg_sat']   = grouped['avg_sat'].round(2)
    grouped['min_sat']   = grouped['min_sat'].round(2)
    grouped['max_sat']   = grouped['max_sat'].round(2)
    grouped['sat_band']  = grouped['avg_sat'].apply(
        lambda s: 'Alto (≥8)' if s >= 8 else ('Medio (6-8)' if s >= 6 else 'Bajo (<6)')
    )

    grouped = grouped.sort_values('avg_sat', ascending=False).head(top_n).reset_index(drop=True)
    grouped.insert(0, 'rank', range(1, len(grouped) + 1))
    return grouped


@register(
    key='kpis_weekly_trend',
    label='Tendencia Semanal de KPIs',
    category='WFM',
    description='Evolución semanal de AHT, eventos y satisfacción. '
                'Ideal para gráficos de línea en Dashboard.',
    sources=[
        {'id': 'callrecords', 'label': 'CallRecords', 'required': True},
    ],
    params=[
        {'id': 'metric',      'label': 'Métrica',         'type': 'choice',
         'choices': ['aht', 'satisfaccion', 'eventos', 'evaluaciones'], 'required': True},
        {'id': 'group_by',    'label': 'Segmentar por',   'type': 'choice',
         'choices': ['ninguno', 'servicio', 'canal'], 'default': 'ninguno'},
        {'id': 'fecha_col',   'label': 'Columna fecha',   'type': 'column_select',
         'source': 'callrecords', 'required': False},
    ],
)
def kpis_weekly_trend(sources: dict, params: dict):
    """
    Tendencia semanal de una métrica KPI.

    Output: semana, {group_by si aplica}, valor_promedio, total_registros
    """
    df       = sources['callrecords']
    metric   = params.get('metric', 'aht')
    group_by = params.get('group_by', 'ninguno')
    fecha_col= params.get('fecha_col') or ('fecha' if 'fecha' in df.columns else None)

    if metric not in df.columns:
        raise ValueError(f"Columna '{metric}' no encontrada.")

    df[metric] = pd.to_numeric(df[metric], errors='coerce')

    # Usar 'semana' si existe, sino intentar calcular desde fecha
    if 'semana' not in df.columns and fecha_col and fecha_col in df.columns:
        df['semana'] = pd.to_datetime(df[fecha_col]).dt.isocalendar().week.astype(int)
    elif 'semana' not in df.columns:
        raise ValueError("Se necesita columna 'semana' o 'fecha' en el dataset.")

    group_cols = ['semana']
    if group_by != 'ninguno' and group_by in df.columns:
        group_cols.append(group_by)

    grouped = df.groupby(group_cols).agg(
        valor_promedio  = (metric, 'mean'),
        total_registros = (metric, 'count'),
    ).reset_index()

    grouped['valor_promedio']  = grouped['valor_promedio'].round(3)
    grouped = grouped.sort_values('semana')
    return grouped
