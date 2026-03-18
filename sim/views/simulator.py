# sim/views/simulator.py
import json
import logging
import math
import uuid as _uuid

from datetime import date, timedelta
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.views.decorators.http import require_GET, require_POST

from sim.models import SimAccount, SimAgent, Interaction, SimRun
from sim.engine import HistoricalEngine, get_account_kpis

logger = logging.getLogger(__name__)

# ── Presets ──────────────────────────────────────────────────────────────────
PRESETS = {
    'banking_inbound': {
        'name':        'Banca Inbound',
        'canal':       'inbound',
        'account_type':'banking',
        'config': {
            'inbound': {
                'weekday_vol': 1490, 'weekend_vol': 883,
                'tmo_s': 313, 'acw_s': 18, 'agents': 22,
                'abandon_rate': 0.039, 'sl_s': 20,
                'schedule_start': 9, 'schedule_end': 18,
            }
        }
    },
    'telco_outbound': {
        'name':        'Telco Outbound',
        'canal':       'outbound',
        'account_type':'telco',
        'config': {
            'outbound': {
                'daily_marcaciones': 131400,
                'contact_rate': 0.276, 'conv_rate': 0.0084,
                'agenda_rate': 0.128, 'agents': 322,
                'absence_rate': 0.050, 'sph_base': 0.128,
                'arpu': 37.95, 'turnos': ['MANANA', 'TARDE'],
            }
        }
    },
    'banking_digital': {
        'name':        'Banca Digital',
        'canal':       'digital',
        'account_type':'banking',
        'config': {
            'digital': {
                'daily_vol': 203, 'duration_s': 240,
                'channels': {'bxi': 0.849, 'app': 0.151},
            }
        }
    },
    'mixed_full': {
        'name':        'Operación Mixta',
        'canal':       'mixed',
        'account_type':'banking',
        'config': {
            'inbound':  {'weekday_vol': 1490, 'tmo_s': 313, 'acw_s': 18, 'agents': 22, 'abandon_rate': 0.039, 'sl_s': 20, 'schedule_start': 9, 'schedule_end': 18},
            'outbound': {'daily_marcaciones': 5000,  'contact_rate': 0.276, 'conv_rate': 0.0084, 'agents': 30, 'sph_base': 0.128, 'turnos': ['MANANA', 'TARDE']},
            'digital':  {'daily_vol': 203, 'duration_s': 240},
        }
    },
}


def _json_safe(obj):
    if obj is None: return None
    if isinstance(obj, bool): return obj
    if isinstance(obj, int): return obj
    if isinstance(obj, float): return None if (math.isnan(obj) or math.isinf(obj)) else obj
    if isinstance(obj, str): return obj
    if isinstance(obj, _uuid.UUID): return str(obj)
    if hasattr(obj, 'isoformat'): return obj.isoformat()
    if isinstance(obj, dict): return {str(k): _json_safe(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)): return [_json_safe(i) for i in obj]
    return str(obj)


def _account_row(acc: SimAccount) -> dict:
    kpis = get_account_kpis(acc)
    return {
        'id':           str(acc.id),
        'name':         acc.name,
        'canal':        acc.canal,
        'canal_label':  acc.get_canal_display(),
        'account_type': acc.account_type,
        'preset':       acc.preset,
        'is_active':    acc.is_active,
        'interactions': kpis.get('total', 0),
        'kpis':         kpis,
        'created_at':   acc.created_at.isoformat(),
    }


def _run_row(r: SimRun) -> dict:
    return {
        'id':           str(r.id),
        'account':      str(r.account_id),
        'date_from':    str(r.date_from),
        'date_to':      str(r.date_to),
        'canales':      r.canales,
        'status':       r.status,
        'status_label': r.get_status_display(),
        'interactions': r.interactions_generated,
        'agents':       r.agents_generated,
        'duration_s':   round(r.duration_s, 1),
        'error_msg':    r.error_msg,
        'started_at':   r.started_at.isoformat(),
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Views
# ═══════════════════════════════════════════════════════════════════════════════

@login_required
def simulator_list(request):
    accounts = SimAccount.objects.filter(created_by=request.user).order_by('-updated_at')
    return render(request, 'sim/simulator.html', {
        'accounts':      accounts,
        'account_count': accounts.count(),
        'presets_json':  json.dumps(_json_safe(list(PRESETS.keys()))),
        'preset_labels': {k: v['name'] for k, v in PRESETS.items()},
    })


@login_required
@require_GET
def simulator_api(request):
    accounts = SimAccount.objects.filter(created_by=request.user).order_by('-updated_at')
    return JsonResponse({'success': True, 'accounts': [_account_row(a) for a in accounts]})


@login_required
@require_POST
def account_create(request):
    try:
        body   = json.loads(request.body)
        preset_key = body.get('preset', '')
        name   = str(body.get('name', '')).strip()

        if preset_key and preset_key in PRESETS:
            preset = PRESETS[preset_key]
            canal  = preset['canal']
            atype  = preset['account_type']
            config = preset['config']
            name   = name or preset['name']
        else:
            canal  = body.get('canal', 'inbound')
            atype  = body.get('account_type', 'generic')
            config = body.get('config', {})

        if not name:
            return JsonResponse({'success': False, 'error': 'Nombre requerido.'}, status=400)

        acc = SimAccount.objects.create(
            name         = name,
            canal        = canal,
            account_type = atype,
            preset       = preset_key,
            config       = config,
            created_by   = request.user,
        )
        return JsonResponse({'success': True, 'account': _account_row(acc)})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@require_POST
def account_delete(request, account_id):
    acc = get_object_or_404(SimAccount, id=account_id, created_by=request.user)
    acc.delete()
    return JsonResponse({'success': True})


@login_required
@require_POST
def account_generate(request, account_id):
    """
    POST { date_from, date_to, canales?: [...] }
    Genera interacciones históricas para la cuenta.
    """
    acc = get_object_or_404(SimAccount, id=account_id, created_by=request.user)
    try:
        body      = json.loads(request.body)
        date_from = date.fromisoformat(body.get('date_from', str(date.today() - timedelta(days=30))))
        date_to   = date.fromisoformat(body.get('date_to',   str(date.today() - timedelta(days=1))))
        canales   = body.get('canales') or None

        if date_from > date_to:
            return JsonResponse({'success': False, 'error': 'date_from > date_to'}, status=400)
        if (date_to - date_from).days > 365:
            return JsonResponse({'success': False, 'error': 'Rango máximo 365 días.'}, status=400)

        engine = HistoricalEngine(acc, request.user)
        run    = engine.generate(date_from, date_to, canales)

        return JsonResponse({
            'success': True,
            'run':     _run_row(run),
            'account': _account_row(acc),
        })
    except Exception as e:
        logger.error("account_generate %s: %s", account_id, e, exc_info=True)
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@require_POST
def account_clear(request, account_id):
    """Elimina todas las interacciones de la cuenta sin borrar la cuenta."""
    acc = get_object_or_404(SimAccount, id=account_id, created_by=request.user)
    deleted, _ = Interaction.objects.filter(account=acc).delete()
    SimAgent.objects.filter(account=acc).delete()
    return JsonResponse({'success': True, 'deleted': deleted})


@login_required
@require_GET
def account_runs(request, account_id):
    acc  = get_object_or_404(SimAccount, id=account_id, created_by=request.user)
    runs = acc.runs.order_by('-started_at')[:20]
    return JsonResponse({'success': True, 'runs': [_run_row(r) for r in runs]})


@login_required
@require_GET
def account_kpis(request, account_id):
    acc  = get_object_or_404(SimAccount, id=account_id, created_by=request.user)
    kpis = get_account_kpis(acc)
    return JsonResponse({'success': True, 'kpis': _json_safe(kpis)})


# ── API export → analyst ETL ──────────────────────────────────────────────────
@login_required
@require_GET
def export_interactions(request, account_id):
    """
    Devuelve las interacciones como JSON paginado para consumo del ETL de analyst.
    Query params: page, page_size, date_from, date_to, canal
    """
    acc = get_object_or_404(SimAccount, id=account_id, created_by=request.user)

    qs = Interaction.objects.filter(account=acc).order_by('hora_inicio')

    # Filters
    date_from = request.GET.get('date_from')
    date_to   = request.GET.get('date_to')
    canal     = request.GET.get('canal')
    if date_from: qs = qs.filter(fecha__gte=date_from)
    if date_to:   qs = qs.filter(fecha__lte=date_to)
    if canal:     qs = qs.filter(canal=canal)

    page      = max(1, int(request.GET.get('page', 1)))
    page_size = min(5000, int(request.GET.get('page_size', 1000)))
    total     = qs.count()
    offset    = (page - 1) * page_size
    rows      = qs[offset:offset + page_size]

    data = []
    for r in rows:
        data.append({
            'id':           str(r.id),
            'cuenta':       acc.name,
            'canal':        r.canal,
            'skill':        r.skill,
            'sub_canal':    r.sub_canal,
            'agente':       r.agent.codigo if r.agent else '',
            'turno':        r.agent.turno  if r.agent else '',
            'antiguedad':   r.agent.antiguedad if r.agent else '',
            'fecha':        str(r.fecha),
            'hora_inicio':  r.hora_inicio.strftime('%Y-%m-%d %H:%M:%S'),
            'hora_fin':     r.hora_fin.strftime('%Y-%m-%d %H:%M:%S'),
            'duracion_s':   r.duracion_s,
            'acw_s':        r.acw_s,
            'tmo_total_s':  r.duracion_s + r.acw_s,
            'tipificacion': r.tipificacion,
            'status':       r.status,
            'lead_id':      r.lead_id,
            'intento_num':  r.intento_num,
        })

    return JsonResponse({
        'success':   True,
        'account':   acc.name,
        'total':     total,
        'page':      page,
        'pages':     math.ceil(total / page_size),
        'page_size': page_size,
        'data':      data,
    })
