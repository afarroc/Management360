"""
sim/views/dashboard.py
Dashboard KPI — consulta sim.Interaction y sirve widgets al frontend.
"""

from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Avg, Q
from datetime import timedelta, date

from ..models import SimAccount, Interaction, SimRun


# ---------------------------------------------------------------------------
# Vista principal
# ---------------------------------------------------------------------------

@login_required
def sim_dashboard(request):
    """Renderiza el dashboard KPI con selector de cuenta."""
    accounts = SimAccount.objects.filter(
        created_by=request.user, is_active=True
    ).order_by('name')
    return render(request, 'sim/dashboard.html', {'accounts': accounts})


# ---------------------------------------------------------------------------
# API de datos
# ---------------------------------------------------------------------------

@login_required
@require_GET
def dashboard_api(request):
    """
    Devuelve KPIs agregados para los widgets del dashboard.

    GET /sim/dashboard/api/?account_id=<uuid>&days=<int>
        account_id  — UUID de SimAccount (requerido)
        days        — ventana lookback en días (default 30; 0 = todos)
    """
    account_id = request.GET.get('account_id')
    days = int(request.GET.get('days', 30))

    if not account_id:
        return JsonResponse({'error': 'account_id required'}, status=400)

    try:
        account = SimAccount.objects.get(pk=account_id, created_by=request.user)
    except SimAccount.DoesNotExist:
        return JsonResponse({'error': 'cuenta no encontrada'}, status=404)

    qs = Interaction.objects.filter(account=account)
    if days > 0:
        since = date.today() - timedelta(days=days)
        qs = qs.filter(fecha__gte=since)

    total = qs.count()
    if total == 0:
        return JsonResponse({
            'account': account.name,
            'canal': account.canal,
            'total': 0,
            'canales': {},
            'inbound': None,
            'outbound': None,
            'digital': None,
            'daily_trend': [],
            'recent_runs': [],
        })

    # ------------------------------------------------------------------
    # Distribución por canal
    # ------------------------------------------------------------------
    canal_counts = dict(
        qs.values_list('canal').annotate(n=Count('id')).values_list('canal', 'n')
    )

    # ------------------------------------------------------------------
    # KPIs Inbound
    # ------------------------------------------------------------------
    inbound_qs = qs.filter(canal='inbound')
    inbound_total = inbound_qs.count()
    inbound = None
    if inbound_total:
        atendidas  = inbound_qs.filter(status='atendida').count()
        abandonadas = inbound_qs.filter(status='abandonada').count()
        aht_avg    = (
            inbound_qs.filter(status='atendida')
            .aggregate(a=Avg('duracion_s'))['a'] or 0
        )
        inbound = {
            'total':      inbound_total,
            'atendidas':  atendidas,
            'abandonadas': abandonadas,
            'na_pct':     round(atendidas  / inbound_total * 100, 1),
            'aban_pct':   round(abandonadas / inbound_total * 100, 1),
            'aht_s':      round(aht_avg),
            'aht_min':    round(aht_avg / 60, 2),
        }

    # ------------------------------------------------------------------
    # KPIs Outbound
    # ------------------------------------------------------------------
    outbound_qs = qs.filter(canal='outbound')
    outbound_total = outbound_qs.count()
    outbound = None
    if outbound_total:
        contactados = outbound_qs.exclude(status='no_contacto').count()
        ventas   = outbound_qs.filter(status='venta').count()
        agendas  = outbound_qs.filter(status='agenda').count()
        aht_out  = (
            outbound_qs.filter(status__in=['venta', 'agenda', 'rechazo'])
            .aggregate(a=Avg('duracion_s'))['a'] or 0
        )
        outbound = {
            'total':         outbound_total,
            'contactados':   contactados,
            'ventas':        ventas,
            'agendas':       agendas,
            'contact_pct':   round(contactados / outbound_total * 100, 1),
            'conv_pct':      round(ventas / contactados * 100, 2) if contactados else 0,
            'agenda_pct':    round(agendas / contactados * 100, 1) if contactados else 0,
            'aht_s':         round(aht_out),
        }

    # ------------------------------------------------------------------
    # KPIs Digital
    # ------------------------------------------------------------------
    digital_qs = qs.filter(canal__in=['chat', 'digital', 'mail'])
    digital_total = digital_qs.count()
    digital = None
    if digital_total:
        aht_dig = digital_qs.aggregate(a=Avg('duracion_s'))['a'] or 0
        digital = {
            'total':   digital_total,
            'aht_s':   round(aht_dig),
            'aht_min': round(aht_dig / 60, 2),
        }

    # ------------------------------------------------------------------
    # Tendencia diaria (para bar chart)
    # ------------------------------------------------------------------
    trend_qs = (
        qs.values('fecha')
        .annotate(
            total=Count('id'),
            atendidas=Count('id', filter=Q(status='atendida')),
            ventas=Count('id', filter=Q(status='venta')),
        )
        .order_by('fecha')
    )
    daily_trend = [
        {
            'fecha':     str(r['fecha']),
            'total':     r['total'],
            'atendidas': r['atendidas'],
            'ventas':    r['ventas'],
        }
        for r in trend_qs
    ]

    # ------------------------------------------------------------------
    # Runs recientes
    # ------------------------------------------------------------------
    recent_runs = list(
        SimRun.objects.filter(account=account)
        .order_by('-created_at')[:6]
        .values('id', 'canal', 'dias', 'total_interactions', 'created_at', 'duration_s')
    )
    for r in recent_runs:
        r['created_at'] = str(r['created_at'])[:16]

    return JsonResponse({
        'account':     account.name,
        'canal':       account.canal,
        'total':       total,
        'canales':     canal_counts,
        'inbound':     inbound,
        'outbound':    outbound,
        'digital':     digital,
        'daily_trend': daily_trend,
        'recent_runs': recent_runs,
    })
