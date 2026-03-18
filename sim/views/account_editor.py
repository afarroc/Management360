# sim/views/account_editor.py
"""
SIM-3 — Editor de cuentas personalizables.
Dos endpoints:
  GET  /sim/accounts/<uuid>/edit/    → renderiza el editor
  POST /sim/accounts/<uuid>/config/  → guarda config JSON
"""

import json
import logging

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.views.decorators.http import require_POST

from sim.models import SimAccount

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Defaults por canal — usados cuando el campo config está vacío
# ---------------------------------------------------------------------------

INBOUND_DEFAULT = {
    'weekday_vol':    1490,
    'weekend_vol':    883,
    'tmo_s':          313,
    'acw_s':          18,
    'agents':         22,
    'abandon_rate':   0.039,
    'sl_s':           20,
    'schedule_start': 9,
    'schedule_end':   18,
    'intraday': {
        '9': 0.123, '10': 0.135, '11': 0.136, '12': 0.116,
        '13': 0.102, '14': 0.096, '15': 0.096, '16': 0.109, '17': 0.087,
    },
    'skills': {
        'PLD': {
            'weight': 0.657,
            'tipificaciones': {
                'CUOTA MENSUAL': 0.473, 'INFORMATIVA': 0.207,
                'OFERTA PRESTAMO LIBRE DISP.': 0.135,
                'LIQUIDACION TOTAL': 0.113, 'INGRESO DE REGULAR': 0.072,
            },
        },
        'CONVENIOS': {
            'weight': 0.098,
            'tipificaciones': {
                'CUOTA MENSUAL': 0.583, 'SE BRINDA TELEFONOS': 0.171,
                'TASAS/COMISIONES/PORTES': 0.152,
                'INGRESO DE REGULAR': 0.047, 'SOLICITA HOJA RESUMEN': 0.047,
            },
        },
        'HIPOTECARIO MI VIVIENDA': {
            'weight': 0.085,
            'tipificaciones': {
                'CUOTA MENSUAL': 0.469, 'SOLICITA HOJA RESUMEN': 0.204,
                'INGRESO DE REGULAR': 0.198, 'TASAS/COMISIONES/PORTES': 0.069,
                'INFORMACIÓN SOBRE EL RECLAMO': 0.059,
            },
        },
        'HIPOTECARIO BANCO': {
            'weight': 0.054,
            'tipificaciones': {
                'CUOTA MENSUAL': 0.499, 'INGRESO DE REGULAR': 0.142,
                'SOLICITA HOJA RESUMEN': 0.138,
                'TASAS/COMISIONES/PORTES': 0.110, 'OPC 3 - ASESOR RECLAMO': 0.110,
            },
        },
        'CREDICARSA': {'weight': 0.045, 'tipificaciones': {'CONSULTA GENERAL': 1.0}},
        'COMPRA DE CARTERA': {'weight': 0.044, 'tipificaciones': {'CONSULTA CARTERA': 1.0}},
        'MICROFINANZAS': {'weight': 0.017, 'tipificaciones': {'CONSULTA': 1.0}},
        'VEHICULAR': {'weight': 0.001, 'tipificaciones': {'CONSULTA VEHÍCULO': 1.0}},
    },
}

OUTBOUND_DEFAULT = {
    'daily_marcaciones': 131400,
    'contact_rate':      0.276,
    'conv_rate':         0.0084,
    'agenda_rate':       0.128,
    'agents':            322,
    'absence_rate':      0.050,
    'sph_base':          0.128,
    'arpu':              37.95,
    'turnos':            ['MANANA', 'TARDE'],
    'no_contact': {
        'no_contesta': 0.524,
        'buzon':       0.328,
        'desconectada':0.034,
        'timeout':     0.053,
        'otros':       0.061,
    },
    'tipificaciones_contacto': {
        'Venta':               0.0084,
        'Agenda (Usuario)':    0.076,
        'Agenda (Sistema)':    0.052,
        'Rechazo':             0.216,
        'Cliente corta':       0.415,
        'Línea ocupada':       0.229,
    },
    'producto': {'PORTABILIDAD': 0.92, 'LINEA NUEVA': 0.08},
}

DIGITAL_DEFAULT = {
    'daily_vol':  203,
    'duration_s': 240,
    'channels': {'bxi': 0.849, 'app': 0.151},
    'tipificaciones': {
        'BXI_ACTIVACION USUARIO NUEVO': 0.634,
        'BXI_DESEA INFO GRAL':          0.046,
        'BXI_COMO INGRESAR (LOGUEO)':   0.044,
        'BXI_INCIDENCIA LOGUEO':        0.026,
        'BXI_TRANSACCIONAR':            0.026,
        'BXI_OTROS':                    0.073,
        'APP_ACTIVACION USUARIO':       0.045,
        'APP_DESEA INFO GRAL':          0.030,
        'APP_COMO INGRESAR':            0.028,
        'APP_OTROS':                    0.048,
    },
}

CANAL_DEFAULTS = {
    'inbound':  {'inbound':  INBOUND_DEFAULT},
    'outbound': {'outbound': OUTBOUND_DEFAULT},
    'digital':  {'digital':  DIGITAL_DEFAULT},
    'mixed':    {'inbound':  INBOUND_DEFAULT,
                 'outbound': OUTBOUND_DEFAULT,
                 'digital':  DIGITAL_DEFAULT},
}


def _merge_config(canal: str, saved: dict) -> dict:
    """
    Combina el config guardado con los defaults del canal.
    Garantiza que todos los campos existan aunque el config esté incompleto.
    """
    base = CANAL_DEFAULTS.get(canal, {})
    merged = {}
    for ckey, cdefault in base.items():
        csaved = saved.get(ckey, {})
        section = dict(cdefault)
        section.update(csaved)
        # Sub-dicts: intraday, skills, no_contact, tipificaciones
        for sub in ('intraday', 'skills', 'no_contact', 'tipificaciones_contacto',
                    'tipificaciones', 'channels', 'producto'):
            if sub in cdefault and isinstance(cdefault[sub], dict):
                section[sub] = {**cdefault[sub], **csaved.get(sub, {})}
        merged[ckey] = section
    return merged


# ---------------------------------------------------------------------------
# Views
# ---------------------------------------------------------------------------

@login_required
def account_edit(request, account_id):
    """
    Renderiza el editor de configuración de la cuenta.
    Pasa el config actual (merged con defaults) al template como JSON.
    """
    acc = get_object_or_404(SimAccount, id=account_id, created_by=request.user)
    config_merged = _merge_config(acc.canal, acc.config or {})

    return render(request, 'sim/account_editor.html', {
        'account':     acc,
        'canal':       acc.canal,
        'config_json': json.dumps(config_merged),
        'defaults_json': json.dumps(CANAL_DEFAULTS.get(acc.canal, {})),
    })


@login_required
@require_POST
def account_config_save(request, account_id):
    """
    Guarda el config editado en SimAccount.config.
    Body: { config: { inbound: {...}, outbound: {...}, digital: {...} } }
    """
    acc = get_object_or_404(SimAccount, id=account_id, created_by=request.user)
    try:
        body   = json.loads(request.body)
        config = body.get('config', {})

        # Validaciones mínimas
        errors = _validate_config(acc.canal, config)
        if errors:
            return JsonResponse({'success': False, 'errors': errors}, status=400)

        acc.config = config
        acc.preset = ''   # al editar manualmente, preset deja de ser estándar
        acc.save(update_fields=['config', 'preset', 'updated_at'])

        return JsonResponse({'success': True, 'message': 'Configuración guardada.'})
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'errors': ['JSON inválido.']}, status=400)
    except Exception as e:
        logger.error("account_config_save %s: %s", account_id, e, exc_info=True)
        return JsonResponse({'success': False, 'errors': [str(e)]}, status=500)


def _validate_config(canal: str, config: dict) -> list:
    """Validaciones básicas de coherencia. Retorna lista de errores (vacía = OK)."""
    errors = []
    canales_esperados = {
        'inbound':  ['inbound'],
        'outbound': ['outbound'],
        'digital':  ['digital'],
        'mixed':    ['inbound', 'outbound', 'digital'],
    }
    for ckey in canales_esperados.get(canal, []):
        sec = config.get(ckey, {})
        if not sec:
            continue
        # Volumen positivo
        for vol_field in ('weekday_vol', 'daily_vol', 'daily_marcaciones'):
            if vol_field in sec and int(sec[vol_field]) <= 0:
                errors.append(f"{ckey}.{vol_field} debe ser > 0")
        # Tasas en [0, 1]
        for rate_field in ('abandon_rate', 'contact_rate', 'conv_rate', 'agenda_rate', 'absence_rate'):
            if rate_field in sec:
                v = float(sec[rate_field])
                if not (0 <= v <= 1):
                    errors.append(f"{ckey}.{rate_field} debe estar entre 0 y 1")
        # Horario inbound
        if ckey == 'inbound':
            s = int(sec.get('schedule_start', 9))
            e = int(sec.get('schedule_end',   18))
            if s >= e:
                errors.append("inbound.schedule_start debe ser menor que schedule_end")
    return errors
