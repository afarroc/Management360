# analyst/views/dashboard.py
"""
Dashboard — vistas SPA.

GET   /analyst/dashboards/                     → lista + panel HTML
POST  /analyst/dashboards/create/              → crear dashboard
POST  /analyst/dashboards/<id>/update/         → renombrar / descripción / is_public
POST  /analyst/dashboards/<id>/delete/         → eliminar
GET   /analyst/dashboards/<id>/view/           → vista de lectura del dashboard
POST  /analyst/dashboards/<id>/layout/save/    → guardar layout (posiciones)
POST  /analyst/dashboards/<id>/widgets/add/    → agregar widget
POST  /analyst/dashboards/<id>/widgets/<wid>/update/ → editar widget
POST  /analyst/dashboards/<id>/widgets/<wid>/delete/ → eliminar widget
GET   /analyst/dashboards/<id>/widgets/<wid>/data/   → datos del widget (JSON)
GET   /analyst/dashboards/api/sources/         → fuentes disponibles para widgets
"""

import json
import logging
import math
import pickle
import base64
import uuid as _uuid_mod

import pandas as pd
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.views.decorators.http import require_GET, require_POST

from analyst.models import (
    Dashboard, DashboardWidget,
    StoredDataset, Report, CrossSource, AnalystBase,
)

logger = logging.getLogger(__name__)


# ─── JSON helpers ─────────────────────────────────────────────────────────────

def _json_safe(obj):
    if obj is None: return None
    if isinstance(obj, bool): return obj
    if isinstance(obj, int): return obj
    if isinstance(obj, float):
        return None if (math.isnan(obj) or math.isinf(obj)) else obj
    if isinstance(obj, str): return obj
    if isinstance(obj, _uuid_mod.UUID): return str(obj)
    if hasattr(obj, 'isoformat'): return obj.isoformat()
    if isinstance(obj, dict): return {str(k): _json_safe(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)): return [_json_safe(i) for i in obj]
    try:
        f = float(obj)
        if math.isnan(f) or math.isinf(f): return None
        return int(f) if float(int(f)) == f else f
    except (TypeError, ValueError): pass
    return str(obj)


def _safe_json_str(obj) -> str:
    import re as _re
    result = json.dumps(_json_safe(obj), ensure_ascii=True, allow_nan=True)
    result = _re.sub(r'\bNaN\b',       'null', result)
    result = _re.sub(r'\bInfinity\b',  'null', result)
    result = _re.sub(r'\b-Infinity\b', 'null', result)
    return result.replace('</', r'<\/')


# ─── Data loading ─────────────────────────────────────────────────────────────

def _sim_interaction_columns() -> list:
    """SIM-4/Dashboard: columnas concretas de sim.Interaction para el selector de widgets."""
    try:
        from django.apps import apps as _dapps
        Model = _dapps.get_model('sim', 'Interaction')
        cols = []
        for f in Model._meta.get_fields():
            if f.many_to_many or f.one_to_many:
                continue
            if f.is_relation:
                attname = getattr(f, 'attname', None)
                if attname:
                    cols.append(attname)
            else:
                cols.append(f.name)
        return cols
    except Exception:
        return []

def _acd_interaction_columns() -> list:
    """SIM-7 / Dashboard: columnas de sim.ACDInteraction para el selector de widgets."""
    try:
        from django.apps import apps as _dapps
        Model = _dapps.get_model('sim', 'ACDInteraction')
        cols = []
        for f in Model._meta.get_fields():
            if f.many_to_many or f.one_to_many:
                continue
            if f.is_relation:
                attname = getattr(f, 'attname', None)
                if attname:
                    cols.append(attname)
            else:
                cols.append(f.name)
        return cols
    except Exception:
        return []

def _events_item_columns(model_key: str = 'inbox') -> list:
    """
    EVENTS-AI-3: columnas de un modelo events para el selector de widgets.
    model_key: 'inbox' | 'tasks' | 'projects' | 'events'
    """
    _MAP = {
        'inbox':    ('events', 'InboxItem'),
        'tasks':    ('events', 'Task'),
        'projects': ('events', 'Project'),
        'events':   ('events', 'Event'),
    }
    app_label, model_name = _MAP.get(model_key, ('events', 'InboxItem'))
    try:
        from django.apps import apps as _dapps
        Model = _dapps.get_model(app_label, model_name)
        cols = []
        for f in Model._meta.get_fields():
            if f.many_to_many or f.one_to_many:
                continue
            if f.is_relation:
                attname = getattr(f, 'attname', None)
                if attname:
                    cols.append(attname)
            else:
                cols.append(f.name)
        return cols
    except Exception:
        return []


def _deserialize(blob: str) -> pd.DataFrame:
    return pickle.loads(base64.b64decode(blob.encode()))


def _load_df(source: dict, user) -> pd.DataFrame | None:
    """Load a DataFrame from a widget source descriptor."""
    src_type = source.get('type')
    src_id   = source.get('id', '')
    if not src_type or not src_id:
        return None

    try:
        if src_type == 'report':
            r = Report.objects.get(id=src_id, created_by=user)
            if r.status != 'done' or not r.result_data:
                return None
            return pd.DataFrame(r.result_data)

        if src_type == 'dataset':
            ds = StoredDataset.objects.get(id=src_id, created_by=user)
            raw = cache.get(ds.cache_key)
            if raw:
                try:
                    return _deserialize(raw['data'])
                except Exception:
                    pass
            if ds.data_blob:
                return _deserialize(ds.data_blob)
            return None

        if src_type == 'cross_source':
            cs = CrossSource.objects.get(id=src_id, created_by=user)
            if not cs.last_result:
                return None
            ds = cs.last_result
            raw = cache.get(ds.cache_key)
            if raw:
                try:
                    return _deserialize(raw['data'])
                except Exception:
                    pass
            if ds.data_blob:
                return _deserialize(ds.data_blob)
            return None

        if src_type == 'analyst_base':
            from analyst.services.base_validator import BaseValidator
            base = AnalystBase.objects.get(id=src_id, created_by=user)
            return BaseValidator.load_dataframe(base)

        if src_type == 'sim':
            from sim.models import SimAccount, Interaction
            account = SimAccount.objects.get(id=src_id, created_by=user)
            qs      = Interaction.objects.filter(account=account).order_by('fecha', 'hora_inicio')
            records = list(qs.values())
            if not records:
                return pd.DataFrame()
            return pd.DataFrame(records)

        if src_type == 'acd':
            from sim.models import ACDSession, ACDInteraction
            session = ACDSession.objects.get(id=src_id, created_by=user)
            qs = ACDInteraction.objects.filter(session=session).order_by('routed_at')
            records = list(qs.values())
            if not records:
                return pd.DataFrame()
            return pd.DataFrame(records)

        # EVENTS-AI-3: fuente events — InboxItem / Task / Project / Event del usuario
        if src_type == 'events':
            # src_id formato: "inbox" | "tasks" | "projects" | "events"
            # El widget apunta directamente al model_key, no a un UUID de objeto.
            _EVENTS_MAP = {
                'inbox':    ('events', 'InboxItem',  'created_by', 'created_at'),
                'tasks':    ('events', 'Task',       'host',       'created_at'),  # Task NO tiene due_date
                'projects': ('events', 'Project',    'host',       'created_at'),   # Project sin start_date confirmado
                'events':   ('events', 'Event',      'host',       'created_at'),   # Event sin start_time confirmado
            }
            entry = _EVENTS_MAP.get(src_id)
            if not entry:
                return None
            app_label, model_name, owner_field, order_field = entry
            from django.apps import apps as _dapps
            Model = _dapps.get_model(app_label, model_name)
            qs = Model.objects.filter(**{owner_field: user}).order_by(f'-{order_field}')
            records = list(qs.values())
            if not records:
                return pd.DataFrame()
            return pd.DataFrame(records)

    except Exception as e:
        logger.warning("_load_df failed: %s", e)
    return None


# ─── Widget data computation ───────────────────────────────────────────────────

def _compute_widget_data(widget: DashboardWidget, user) -> dict:
    """Compute the data payload for a single widget."""
    wtype  = widget.widget_type
    config = widget.config or {}

    if wtype == 'text':
        return {'type': 'text', 'content': config.get('content', '')}

    df = _load_df(widget.source, user)
    if df is None or df.empty:
        return {'type': wtype, 'error': 'Sin datos disponibles.'}

    # Sanitize
    df = df.astype(object).where(pd.notnull(df), None)

    try:
        if wtype == 'kpi_card':
            val_col = config.get('value_col')
            if not val_col or val_col not in df.columns:
                val_col = df.select_dtypes(include='number').columns[0] if not df.select_dtypes(include='number').empty else df.columns[0]
            series  = pd.to_numeric(df[val_col], errors='coerce').dropna()
            agg     = config.get('aggregation', 'sum')
            value   = {
                'sum':   series.sum(),
                'avg':   series.mean(),
                'count': len(series),
                'max':   series.max(),
                'min':   series.min(),
                'last':  series.iloc[-1] if len(series) else None,
            }.get(agg, series.sum())
            return {
                'type':    'kpi_card',
                'value':   _json_safe(value),
                'label':   config.get('label') or val_col,
                'format':  config.get('format', 'number'),
                'rows':    len(df),
            }

        if wtype == 'table':
            cols     = config.get('columns') or list(df.columns)
            cols     = [c for c in cols if c in df.columns] or list(df.columns)
            page     = int(config.get('page', 1))
            ps       = min(int(config.get('page_size', 10)), 200)
            start    = (page - 1) * ps
            slice_df = df[cols].iloc[start:start + ps]
            return {
                'type':    'table',
                'columns': [str(c) for c in cols],
                'rows':    _json_safe(slice_df.to_dict('records')),
                'total':   len(df),
                'page':    page,
                'pages':   max(1, -(-len(df) // ps)),
            }

        if wtype in ('bar_chart', 'line_chart'):
            x_col  = config.get('x_col')
            y_cols = config.get('y_cols') or []
            if not x_col or x_col not in df.columns:
                x_col = df.columns[0]
            if not y_cols:
                num_cols = list(df.select_dtypes(include='number').columns)
                y_cols   = [c for c in num_cols if c != x_col][:3]
            y_cols = [c for c in y_cols if c in df.columns]
            limit  = int(config.get('limit', 50))
            sub    = df[[x_col] + y_cols].head(limit)
            labels = [str(v) if v is not None else '' for v in sub[x_col]]
            datasets = []
            palette  = ['#2563eb','#059669','#d97706','#dc2626','#7c3aed','#0891b2']
            for i, col in enumerate(y_cols):
                vals = pd.to_numeric(sub[col], errors='coerce').fillna(0).tolist()
                datasets.append({
                    'label':           str(col),
                    'data':            _json_safe(vals),
                    'backgroundColor': palette[i % len(palette)] + ('80' if wtype == 'bar_chart' else ''),
                    'borderColor':     palette[i % len(palette)],
                    'borderWidth':     2,
                    'fill':            config.get('fill', False) if wtype == 'line_chart' else False,
                    'tension':         0.3,
                })
            return {
                'type':     wtype,
                'labels':   labels,
                'datasets': datasets,
                'stacked':  config.get('stacked', False),
            }

        if wtype == 'pie_chart':
            label_col = config.get('label_col')
            value_col = config.get('value_col')
            if not label_col or label_col not in df.columns:
                label_col = df.columns[0]
            if not value_col or value_col not in df.columns:
                num_cols  = list(df.select_dtypes(include='number').columns)
                value_col = num_cols[0] if num_cols else df.columns[-1]
            sub    = df[[label_col, value_col]].head(int(config.get('limit', 12)))
            labels = [str(v) if v is not None else '' for v in sub[label_col]]
            values = pd.to_numeric(sub[value_col], errors='coerce').fillna(0).tolist()
            palette = ['#2563eb','#059669','#d97706','#dc2626','#7c3aed','#0891b2',
                       '#db2777','#ea580c','#65a30d','#0284c7','#9333ea','#16a34a']
            return {
                'type':             'pie_chart',
                'labels':           labels,
                'values':           _json_safe(values),
                'backgroundColors': palette[:len(labels)],
            }

    except Exception as e:
        logger.error("_compute_widget_data %s: %s", widget.id, e, exc_info=True)
        return {'type': wtype, 'error': str(e)}

    return {'type': wtype, 'error': 'Tipo de widget desconocido.'}


# ─── Row helpers ──────────────────────────────────────────────────────────────

def _dashboard_row(d: Dashboard) -> dict:
    return {
        'id':          str(d.id),
        'name':        d.name,
        'description': d.description,
        'is_public':   d.is_public,
        'layout':      d.layout,
        'widget_count': d.widgets.count(),
        'created_at':  d.created_at.isoformat(),
        'updated_at':  d.updated_at.isoformat(),
    }


def _widget_row(w: DashboardWidget) -> dict:
    return {
        'id':          str(w.id),
        'dashboard':   str(w.dashboard_id),
        'widget_type': w.widget_type,
        'type_label':  w.get_widget_type_display(),
        'title':       w.title,
        'source':      w.source,
        'config':      w.config,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Views
# ═══════════════════════════════════════════════════════════════════════════════

@login_required
def dashboard_list(request):
    """Dashboard list + builder SPA."""
    dashboards = Dashboard.objects.filter(
        created_by=request.user
    ).prefetch_related('widgets').order_by('-updated_at')

    # Sources for widget builder
    reports = Report.objects.filter(created_by=request.user, status='done').order_by('name')
    datasets = StoredDataset.objects.filter(created_by=request.user).exclude(
        source_file__startswith='analyst_base:'
    ).order_by('name')
    cross_sources = CrossSource.objects.filter(
        created_by=request.user
    ).filter(last_result__isnull=False).order_by('name')
    analyst_bases = AnalystBase.objects.filter(
        created_by=request.user
    ).filter(row_count__gt=0).order_by('name')

    # SIM-4 / Dashboard KPI: cuentas simulador activas
    sim_accounts = []
    try:
        from sim.models import SimAccount as _SA
        sim_accounts = list(
            _SA.objects.filter(created_by=request.user, is_active=True).order_by('name')
        )
    except Exception:
        pass
    sim_cols = _sim_interaction_columns()

# SIM-7 / Dashboard ACD: sesiones con interacciones persistidas
    acd_sessions = []
    try:
        from sim.models import ACDSession as _ACDS
        acd_sessions = list(
            _ACDS.objects.filter(
                created_by=request.user
            ).exclude(status='config').order_by('-started_at')[:50]
        )
    except Exception:
        pass
    acd_cols = _acd_interaction_columns()

    return render(request, 'analyst/dashboard.html', {
        'dashboards':         dashboards,
        'dashboards_count':   dashboards.count(),
        'reports_json':       _safe_json_str([
            {'id': str(r.id), 'name': r.name,
             'columns': r.result_meta.get('columns', [])}
            for r in reports
        ]),
        'datasets_json':      _safe_json_str([
            {'id': str(d.id), 'name': d.name, 'columns': list(d.columns)}
            for d in datasets
        ]),
        'cross_sources_json': _safe_json_str([
            {'id': str(c.id), 'name': c.name,
             'columns': list(c.last_result.columns) if c.last_result else []}
            for c in cross_sources
        ]),
        'analyst_bases_json': _safe_json_str([
            {'id': str(b.id), 'name': b.name,
             'columns': b.column_names}
            for b in analyst_bases
        ]),
        'sim_accounts_json':  _safe_json_str([
            {'id': str(s.id), 'name': s.name,
             'canal': s.canal, 'account_type': s.account_type,
             'columns': sim_cols}
            for s in sim_accounts
        ]),

        'acd_sessions_json': _safe_json_str([
            {
                'id':      str(s.id),
                'name':    s.name,
                'canal':   s.canal,
                'status':  s.status,
                'columns': acd_cols,
            }
            for s in acd_sessions
        ]),

        # EVENTS-AI-3: modelos GTD/Events disponibles como fuente de widget
        'events_sources_json': _safe_json_str([
            {
                'id':      key,
                'name':    label,
                'columns': _events_item_columns(key),
            }
            for key, label in [
                ('inbox',    'GTD Inbox'),
                ('tasks',    'Tareas'),
                ('projects', 'Proyectos'),
                ('events',   'Agenda'),
            ]
        ]),


        'widget_types_json':  _safe_json_str([
            {'value': k, 'label': v} for k, v in [
                ('kpi_card',  'KPI / Indicador'),
                ('table',     'Tabla'),
                ('bar_chart', 'Gráfico de barras'),
                ('line_chart','Gráfico de líneas'),
                ('pie_chart', 'Gráfico de pastel'),
                ('text',      'Texto / Nota'),
            ]
        ]),
    })


@login_required
@require_GET
def dashboard_view(request, dashboard_id):
    """Full dashboard view with all widget data."""
    db = get_object_or_404(Dashboard, id=dashboard_id, created_by=request.user)
    widgets_data = []
    for w in db.widgets.all():
        data = _compute_widget_data(w, request.user)
        widgets_data.append({'widget': _widget_row(w), 'data': data})

    # Layout: merge widget order from db.layout or default sequential
    layout_map = {item['widget_id']: item for item in db.layout}
    widgets_with_layout = []
    for w in db.widgets.all():
        wid = str(w.id)
        pos = layout_map.get(wid, {'col': 0, 'width': 6, 'row_order': 99})
        widgets_with_layout.append({
            'widget':    _widget_row(w),
            'data':      next((d['data'] for d in widgets_data if d['widget']['id'] == wid), {}),
            'col':       pos.get('col', 0),
            'width':     pos.get('width', 6),
            'row_order': pos.get('row_order', 99),
        })
    widgets_with_layout.sort(key=lambda x: (x['row_order'], x['col']))

    return JsonResponse({
        'success':   True,
        'dashboard': _dashboard_row(db),
        'widgets':   widgets_with_layout,
    })


@login_required
@require_POST
def dashboard_create(request):
    try:
        body = json.loads(request.body)
        name = str(body.get('name', '')).strip()
        if not name:
            return JsonResponse({'success': False, 'error': 'Nombre requerido.'}, status=400)
        db = Dashboard.objects.create(
            name=name,
            description=str(body.get('description', '')).strip(),
            is_public=bool(body.get('is_public', False)),
            created_by=request.user,
        )
        logger.info("Dashboard creado: %s por %s", db.id, request.user)
        return JsonResponse({'success': True, 'dashboard': _dashboard_row(db)})
    except Exception as e:
        logger.error("dashboard_create: %s", e, exc_info=True)
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@require_POST
def dashboard_update(request, dashboard_id):
    db = get_object_or_404(Dashboard, id=dashboard_id, created_by=request.user)
    try:
        body = json.loads(request.body)
        db.name        = str(body.get('name', db.name)).strip() or db.name
        db.description = str(body.get('description', db.description)).strip()
        db.is_public   = bool(body.get('is_public', db.is_public))
        db.save(update_fields=['name', 'description', 'is_public', 'updated_at'])
        return JsonResponse({'success': True, 'dashboard': _dashboard_row(db)})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@require_POST
def dashboard_delete(request, dashboard_id):
    db = get_object_or_404(Dashboard, id=dashboard_id, created_by=request.user)
    db.delete()
    return JsonResponse({'success': True})


@login_required
@require_POST
def dashboard_layout_save(request, dashboard_id):
    """Save widget positions."""
    db = get_object_or_404(Dashboard, id=dashboard_id, created_by=request.user)
    try:
        body   = json.loads(request.body)
        layout = body.get('layout', [])
        # Validate: list of {widget_id, col, width, row_order}
        valid  = []
        for item in layout:
            if not item.get('widget_id'):
                continue
            valid.append({
                'widget_id': str(item['widget_id']),
                'col':       max(0, min(11, int(item.get('col', 0)))),
                'width':     max(1, min(12, int(item.get('width', 6)))),
                'row_order': int(item.get('row_order', 0)),
            })
        db.layout = valid
        db.save(update_fields=['layout', 'updated_at'])
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@require_POST
def widget_add(request, dashboard_id):
    db = get_object_or_404(Dashboard, id=dashboard_id, created_by=request.user)
    try:
        body = json.loads(request.body)
        wtype = body.get('widget_type', '')
        if wtype not in dict([
            ('kpi_card',''), ('table',''), ('bar_chart',''),
            ('line_chart',''), ('pie_chart',''), ('text','')
        ]):
            return JsonResponse({'success': False, 'error': f"Tipo inválido: '{wtype}'."}, status=400)

        w = DashboardWidget.objects.create(
            dashboard   = db,
            widget_type = wtype,
            title       = str(body.get('title', '')).strip(),
            source      = body.get('source', {}),
            config      = body.get('config', {}),
        )
        # Append to layout
        layout = db.layout or []
        layout.append({
            'widget_id': str(w.id),
            'col':       0,
            'width':     6 if wtype != 'kpi_card' else 3,
            'row_order': len(layout),
        })
        db.layout = layout
        db.save(update_fields=['layout', 'updated_at'])

        # Return widget + initial data
        data = _compute_widget_data(w, request.user)
        return JsonResponse({
            'success': True,
            'widget':  _widget_row(w),
            'data':    data,
            'layout_item': layout[-1],
        })
    except Exception as e:
        logger.error("widget_add %s: %s", dashboard_id, e, exc_info=True)
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@require_POST
def widget_update(request, dashboard_id, widget_id):
    db = get_object_or_404(Dashboard, id=dashboard_id, created_by=request.user)
    w  = get_object_or_404(DashboardWidget, id=widget_id, dashboard=db)
    try:
        body = json.loads(request.body)
        if 'title'       in body: w.title  = str(body['title']).strip()
        if 'source'      in body: w.source = body['source']
        if 'config'      in body: w.config = body['config']
        if 'widget_type' in body:
            wtype = body['widget_type']
            if wtype in ('kpi_card','table','bar_chart','line_chart','pie_chart','text'):
                w.widget_type = wtype
        w.save()
        data = _compute_widget_data(w, request.user)
        return JsonResponse({'success': True, 'widget': _widget_row(w), 'data': data})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@require_POST
def widget_delete(request, dashboard_id, widget_id):
    db = get_object_or_404(Dashboard, id=dashboard_id, created_by=request.user)
    w  = get_object_or_404(DashboardWidget, id=widget_id, dashboard=db)
    w.delete()
    # Remove from layout
    db.layout = [item for item in (db.layout or []) if item.get('widget_id') != widget_id]
    db.save(update_fields=['layout', 'updated_at'])
    return JsonResponse({'success': True})


@login_required
@require_GET
def widget_data(request, dashboard_id, widget_id):
    db = get_object_or_404(Dashboard, id=dashboard_id, created_by=request.user)
    w  = get_object_or_404(DashboardWidget, id=widget_id, dashboard=db)
    data = _compute_widget_data(w, request.user)
    return JsonResponse({'success': True, 'data': data})


# ─── EVENTS-AI-3 Parte 3 — GTD Overview predefinido ──────────────────────────

@login_required
@require_POST
def dashboard_gtd_overview(request):
    """
    Crea un Dashboard GTD Overview predefinido con widgets events.

    Fila 0 (KPI cards, 4 cols cada una):
      - 📥 Inbox pendiente   → conteo InboxItem del usuario
      - 📋 Tareas activas    → conteo Task del usuario
      - 📁 Proyectos         → conteo Project del usuario

    Fila 1 (tablas, 6 cols cada una):
      - Detalle Inbox        → tabla InboxItem (title / is_processed / due_date / created_at)
      - Backlog de Tareas    → tabla Task      (title / created_at / host_id)

    Fila 2 (tabla, 12 cols):
      - Proyectos activos    → tabla Project   (title / created_at / host_id)

    Cada llamada crea un dashboard nuevo (sin deduplicación por diseño).
    Los widgets fallarán sin datos si el usuario no tiene eventos registrados —
    _compute_widget_data devuelve {'error': 'Sin datos disponibles.'} en ese caso,
    sin lanzar excepciones.

    Nota sobre value_col='id' en kpi_card:
      events models usan int PK → pd.to_numeric(df['id']) funciona → count = len(series).
      Si el modelo usara UUID PK, count devolvería 0 (bug conocido de _compute_widget_data).
      Events usa int PK por excepción documentada → seguro.
    """
    try:
        body = json.loads(request.body) if request.body else {}
        from django.utils import timezone as _tz
        _default_name = f"GTD Overview {_tz.localdate().strftime('%d/%m/%Y')}"
        name = str(body.get('name', '') or _default_name).strip() or _default_name
        _default_desc = "Dashboard predefinido · Inbox · Tareas · Proyectos (GTD/Events)"
        desc = str(body.get('description', '') or _default_desc).strip() or _default_desc

        db = Dashboard.objects.create(
            name=name,
            description=desc,
            created_by=request.user,
        )

        # (title, widget_type, events_src_id, config, col, width, row_order)
        _PRESET = [
            # ── Fila 0: KPI cards ────────────────────────────────────────────
            (
                "📥 Inbox pendiente",
                "kpi_card",
                "inbox",
                {"value_col": "id", "aggregation": "count",
                 "label": "Items en inbox", "format": "number"},
                0, 4, 0,
            ),
            (
                "📋 Tareas activas",
                "kpi_card",
                "tasks",
                {"value_col": "id", "aggregation": "count",
                 "label": "Tareas", "format": "number"},
                4, 4, 0,
            ),
            (
                "📁 Proyectos",
                "kpi_card",
                "projects",
                {"value_col": "id", "aggregation": "count",
                 "label": "Proyectos activos", "format": "number"},
                8, 4, 0,
            ),
            # ── Fila 1: tablas inbox + tasks ─────────────────────────────────
            (
                "📥 Detalle Inbox",
                "table",
                "inbox",
                # InboxItem: title + is_processed + due_date (existe en InboxItem) + created_at
                # _compute_widget_data filtra cols inexistentes → no falla si alguna no está
                {"columns": ["title", "is_processed", "due_date", "created_at"],
                 "page_size": 10},
                0, 6, 1,
            ),
            (
                "📋 Backlog de Tareas",
                "table",
                "tasks",
                # Task: title + created_at + host_id (Task no tiene due_date — excepción documentada)
                {"columns": ["title", "created_at", "host_id"],
                 "page_size": 10},
                6, 6, 1,
            ),
            # ── Fila 2: tabla proyectos (ancho completo) ──────────────────────
            (
                "📁 Proyectos activos",
                "table",
                "projects",
                {"columns": ["title", "created_at", "host_id"],
                 "page_size": 10},
                0, 12, 2,
            ),
        ]

        layout = []
        for title, wtype, src_id, cfg, col, width, row in _PRESET:
            w = DashboardWidget.objects.create(
                dashboard=db,
                widget_type=wtype,
                title=title,
                source={"type": "events", "id": src_id},
                config=cfg,
            )
            layout.append({
                "widget_id": str(w.id),
                "col":       col,
                "width":     width,
                "row_order": row,
            })

        db.layout = layout
        db.save(update_fields=["layout", "updated_at"])

        logger.info("GTD Overview creado: %s por %s", db.id, request.user)
        return JsonResponse({
            "success":   True,
            "dashboard": _dashboard_row(db),
        })

    except Exception as e:
        logger.error("dashboard_gtd_overview: %s", e, exc_info=True)
        return JsonResponse({"success": False, "error": str(e)}, status=500)
