# sim/generators/digital.py
"""
Generador de interacciones digitales (Chat / Mail / App).
Calibrado con Banca Digital (Pichincha) — Julio 2020.
"""
import random
from datetime import datetime, timedelta
from .base import weighted_choice, gaussian_duration, synthetic_lead_id, daily_volume

DEFAULT_CONFIG = {
    'daily_vol':     203,
    'schedule_start': 8,
    'schedule_end':   22,
    'channels': {
        'bxi': 0.849,
        'app': 0.151,
    },
    'duration_s':    240,
    'intraday': {
        8:  0.04, 9: 0.10, 10: 0.13, 11: 0.13,
        12: 0.11, 13: 0.10, 14: 0.09, 15: 0.09,
        16: 0.09, 17: 0.07, 18: 0.03, 19: 0.02,
    },
    'tipificaciones_bxi': {
        'BXI_ACTIVACION USUARIO NUEVO':           0.634,
        'BXI_DESEA INFORMACION GENERAL':          0.046,
        'BXI_COMO INGRESAR (LOGUEO)':             0.044,
        'BXI_INCIDENCIA CON EL LOGUEO':           0.026,
        'BXI_TRANSACCIONAR (OPERAR)':             0.026,
        'BXI_DESBLOQUEO DE USUARIO':              0.019,
        'BXI_CLAVE DE 6 DIGITOS':                 0.019,
        'BXI_INCIDENCIA SIN SOLUCION':            0.011,
        'BXI_INCIDENCIA PARA TRANSACCIONAR':      0.014,
        'BXI_INCIDENCIA RESUELTA':                0.004,
        'BXI_BLOQUEO DE USUARIO':                 0.003,
        'BXI_OTROS':                              0.154,
    },
    'tipificaciones_app': {
        'APP_ACTIVACION USUARIO NUEVO':           0.295,
        'APP_DESEA INFORMACION GENERAL':          0.201,
        'APP_COMO INGRESAR (LOGUEO)':             0.183,
        'APP_CLAVE DE INGRESO':                   0.062,
        'APP_INCIDENCIA CON EL LOGUEO':           0.076,
        'APP_DESBLOQUEO DE USUARIO':              0.033,
        'APP_INCIDENCIA PARA TRANSACCIONAR':      0.034,
        'APP_INCIDENCIA SIN SOLUCION':            0.036,
        'APP_TRANSACCIONAR (OPERAR)':             0.033,
        'APP_OTROS':                              0.047,
    },
    # AHT por tipificación
    'tmo_by_tipif': {
        'ACTIVACION USUARIO NUEVO': {'mean': 240, 'sigma': 0.20},
        'INCIDENCIA':               {'mean': 320, 'sigma': 0.22},
        'COMO INGRESAR':            {'mean': 180, 'sigma': 0.18},
        'INFORMACION GENERAL':      {'mean': 150, 'sigma': 0.18},
        'DEFAULT':                  {'mean': 240, 'sigma': 0.20},
    },
}


def _match_tmo(tipif: str, tmo_map: dict) -> dict:
    for key, cfg in tmo_map.items():
        if key.upper() in tipif.upper():
            return cfg
    return tmo_map['DEFAULT']


def generate_day(date: datetime, agent_pool: list,
                  account_config: dict, lead_offset: int = 0) -> list:
    cfg     = {**DEFAULT_CONFIG, **account_config}
    weekday = date.weekday()
    vol     = daily_volume(cfg['daily_vol'], weekday, weekend_factor=0.75)

    if vol == 0:
        return []

    interactions = []
    from .base import intraday_slot

    for i in range(vol):
        hora    = intraday_slot(cfg['intraday'], date)
        channel = weighted_choice(cfg['channels'])

        if channel == 'bxi':
            tipif = weighted_choice(cfg['tipificaciones_bxi'])
        else:
            tipif = weighted_choice(cfg['tipificaciones_app'])

        tmo_cfg = _match_tmo(tipif, cfg['tmo_by_tipif'])
        tmo_s   = gaussian_duration(tmo_cfg['mean'], tmo_cfg['sigma'], min_s=30, max_s=900)
        acw_s   = gaussian_duration(20, 0.30, 5, 90)
        agent   = random.choice(agent_pool) if agent_pool else None

        interactions.append({
            'canal':       'digital',
            'skill':       'CANALES DIGITALES',
            'sub_canal':   channel,
            'fecha':       date.date(),
            'hora_inicio': hora,
            'hora_fin':    hora + timedelta(seconds=tmo_s + acw_s),
            'duracion_s':  tmo_s,
            'acw_s':       acw_s,
            'tipificacion':tipif,
            'status':      'atendida',
            'lead_id':     synthetic_lead_id('digital', lead_offset + i),
            'agent_codigo':agent['codigo'] if agent else None,
            'intento_num': 1,
            'is_simulated':True,
        })

    return interactions
