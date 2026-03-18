# sim/generators/inbound.py
"""
Generador de interacciones inbound voz.
Calibrado con Banca Telefónica (Pichincha) — Julio 2020.
"""
import random
from datetime import datetime, timedelta
from .base import (
    weighted_choice, gaussian_duration, intraday_slot,
    daily_volume, synthetic_lead_id
)

# ── Preset Banca Telefónica ───────────────────────────────────────────────────
DEFAULT_CONFIG = {
    'weekday_vol':    1490,
    'weekend_vol':    883,
    'weekend_factor': 0.59,
    'tmo_s':          313,
    'acw_s':          18,
    'agents':         22,
    'abandon_rate':   0.039,
    'sl_s':           20,
    'schedule_start': 9,
    'schedule_end':   18,
    'intraday': {
        9: 0.1228, 10: 0.1354, 11: 0.1356,
        12: 0.1160, 13: 0.1017, 14: 0.0963,
        15: 0.0962, 16: 0.1085, 17: 0.0874,
    },
    'skills': {
        'PLD': {
            'weight': 0.657,
            'tipificaciones': {
                'CUOTA MENSUAL':                      0.473,
                'INFORMATIVA':                        0.207,
                'OFERTA PRESTAMO LIBRE DISPONIBILIDAD':0.135,
                'LIQUIDACION TOTAL':                  0.113,
                'INGRESO DE REGULAR':                 0.072,
            }
        },
        'CONVENIOS': {
            'weight': 0.098,
            'tipificaciones': {
                'CUOTA MENSUAL':             0.583,
                'SE BRINDA TELEFONOS BANCO': 0.171,
                'TASAS/COMISIONES/PORTES':   0.152,
                'INGRESO DE REGULAR':        0.047,
                'SOLICITA HOJA RESUMEN':     0.047,
            }
        },
        'HIPOTECARIO MI VIVIENDA': {
            'weight': 0.085,
            'tipificaciones': {
                'CUOTA MENSUAL':             0.469,
                'SOLICITA HOJA RESUMEN':     0.204,
                'INGRESO DE REGULAR':        0.198,
                'TASAS/COMISIONES/PORTES':   0.069,
                'INFORMACION SOBRE RECLAMO': 0.059,
            }
        },
        'HIPOTECARIO BANCO': {
            'weight': 0.054,
            'tipificaciones': {
                'CUOTA MENSUAL':             0.499,
                'INGRESO DE REGULAR':        0.142,
                'SOLICITA HOJA RESUMEN':     0.138,
                'TASAS/COMISIONES/PORTES':   0.110,
                'RECLAMO / ASESOR':          0.110,
            }
        },
        'CREDICARSA':       {'weight': 0.045, 'tipificaciones': {'CONSULTA GENERAL': 1.0}},
        'COMPRA DE CARTERA':{'weight': 0.044, 'tipificaciones': {'CONSULTA GENERAL': 1.0}},
        'MICROFINANZAS':    {'weight': 0.017, 'tipificaciones': {'CONSULTA GENERAL': 1.0}},
        'VEHICULAR':        {'weight': 0.001, 'tipificaciones': {'CONSULTA GENERAL': 1.0}},
    },
    # AHT por tipificación (segundos) — calibrado
    'tmo_by_tipif': {
        'CUOTA MENSUAL':                       {'mean': 270, 'sigma': 0.18},
        'INFORMATIVA':                         {'mean': 155, 'sigma': 0.20},
        'OFERTA PRESTAMO LIBRE DISPONIBILIDAD':{'mean': 350, 'sigma': 0.20},
        'LIQUIDACION TOTAL':                   {'mean': 360, 'sigma': 0.20},
        'INGRESO DE REGULAR':                  {'mean': 240, 'sigma': 0.18},
        'SOLICITA HOJA RESUMEN':               {'mean': 200, 'sigma': 0.18},
        'TASAS/COMISIONES/PORTES':             {'mean': 220, 'sigma': 0.18},
        'RECLAMO / ASESOR':                    {'mean': 480, 'sigma': 0.22},
        'INFORMACION SOBRE RECLAMO':           {'mean': 420, 'sigma': 0.20},
        'SE BRINDA TELEFONOS BANCO':           {'mean': 120, 'sigma': 0.15},
        'CONSULTA GENERAL':                    {'mean': 300, 'sigma': 0.20},
    },
    # Abandono varía por hora (pico a las 15:00)
    'abandon_by_hour': {
        9:  0.020, 10: 0.030, 11: 0.035,
        12: 0.040, 13: 0.038, 14: 0.040,
        15: 0.055, 16: 0.035, 17: 0.025,
    },
}


def _get_config(account_config: dict) -> dict:
    """Merge account config over default."""
    cfg = dict(DEFAULT_CONFIG)
    cfg.update(account_config)
    return cfg


def generate_day(date: datetime, agent_pool: list,
                  account_config: dict, lead_offset: int = 0) -> list:
    """
    Genera todas las interacciones inbound de un día.

    Returns: lista de dicts listos para bulk_create de Interaction.
    """
    cfg     = _get_config(account_config)
    weekday = date.weekday()
    vol     = daily_volume(
        cfg['weekday_vol'], weekday,
        cfg.get('weekend_factor', 0.59)
    )

    if vol == 0:
        return []

    # Agentes activos para el día (adherencia)
    active_agents = [
        a for a in agent_pool
        if random.random() < a.get('adherencia_base', 0.931)
    ]

    interactions = []
    skill_weights = {k: v['weight'] for k, v in cfg['skills'].items()}

    for i in range(vol):
        hora        = intraday_slot(cfg['intraday'], date)
        hora_hour   = hora.hour
        abandon_p   = cfg['abandon_by_hour'].get(hora_hour, cfg['abandon_rate'])

        # Skill y tipificación
        skill    = weighted_choice(skill_weights)
        skill_cfg = cfg['skills'][skill]
        tipif    = weighted_choice(skill_cfg['tipificaciones'])

        # Duración
        tmo_cfg  = cfg.get('tmo_by_tipif', {}).get(tipif, {'mean': cfg['tmo_s'], 'sigma': 0.15})
        tmo_s    = gaussian_duration(tmo_cfg['mean'], tmo_cfg['sigma'], min_s=30, max_s=900)

        # Abandono
        is_abandoned = random.random() < abandon_p
        if is_abandoned:
            # Abandona antes de ser atendida — duración corta
            abandon_s = random.randint(5, int(cfg['sl_s'] * 3))
            hora_fin  = hora + timedelta(seconds=abandon_s)
            status    = 'abandonada'
            agent     = None
            acw       = 0
            tmo_s     = abandon_s
        else:
            acw      = gaussian_duration(cfg['acw_s'], 0.30, min_s=5, max_s=180)
            hora_fin = hora + timedelta(seconds=tmo_s + acw)
            status   = 'atendida'
            agent    = random.choice(active_agents) if active_agents else None

        interactions.append({
            'canal':       'inbound',
            'skill':       skill,
            'sub_canal':   '',
            'fecha':       date.date(),
            'hora_inicio': hora,
            'hora_fin':    hora_fin,
            'duracion_s':  tmo_s,
            'acw_s':       0 if is_abandoned else acw,
            'tipificacion':tipif,
            'status':      status,
            'lead_id':     synthetic_lead_id('inbound', lead_offset + i),
            'agent_codigo':agent['codigo'] if agent else None,
            'intento_num': 1,
            'is_simulated':True,
        })

    return interactions
