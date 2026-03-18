# sim/generators/outbound.py
"""
Generador de interacciones outbound (discador predictivo).
Calibrado con Conduent — ENTEL/Telefónica Agosto 2018.
"""
import random
from datetime import datetime, timedelta
from .base import weighted_choice, gaussian_duration, synthetic_lead_id, daily_volume

DEFAULT_CONFIG = {
    'daily_marcaciones': 131400,
    'contact_rate':      0.276,
    'conv_rate':         0.0084,
    'agenda_rate':       0.128,
    'agents':            322,
    'absence_rate':      0.050,
    'sph_base':          0.128,
    'arpu':              37.95,
    'schedule_start':    8,
    'schedule_end':      20,
    'turnos':            ['MANANA', 'TARDE'],
    'tmo_contacto_s':    180,   # contacto válido — duración media
    'tmo_no_contesta_s': 25,    # no contesta — corto
    'tmo_buzon_s':       40,    # buzón
    'producto': {
        'PORTABILIDAD': 0.92,
        'LINEA NUEVA':  0.08,
    },
    'sub_producto': {
        'CHIP': 0.87,
        'PACK': 0.13,
    },
    # Tipificaciones contacto válido (proporciones reales)
    'tipif_contacto': {
        'Cliente corta llamada':                0.415,
        'Cliente ocupado':                      0.229,
        'No venta - No interesado':             0.188,
        'Agenda (Usuario)':                     0.090,
        'Agenda (Titular)':                     0.032,
        'No venta - No asume penalidad':        0.017,
        'Venta':                                0.008,
        'Cliente critico - No volver a llamar': 0.007,
        'Agenda (Promesa de Venta)':            0.006,
        'No venta - No volver a llamar':        0.005,
        'No venta - Linea suspendida':          0.001,
        'No venta - Fuera de zona':             0.001,
        'No venta - Otro':                      0.001,
    },
    # No contacto — automáticas del discador
    'tipif_no_contacto': {
        'No contesta':           0.524,
        'Buzon de voz':          0.328,
        'Timeout conclusion':    0.053,
        'Desconectada':          0.034,
        'Tono llamable':         0.022,
        'Ocupado':               0.017,
        'Error conectar agente': 0.010,
        'Tono no llamable':      0.007,
        'Otros':                 0.005,
    },
    # Intradía outbound (uniforme con pico mañana)
    'intraday': {
        8:  0.06, 9: 0.10, 10: 0.13, 11: 0.13,
        12: 0.11, 13: 0.10, 14: 0.10, 15: 0.10,
        16: 0.09, 17: 0.07, 18: 0.01,
    },
}


def generate_day(date: datetime, agent_pool: list,
                  account_config: dict, lead_offset: int = 0) -> list:
    cfg     = {**DEFAULT_CONFIG, **account_config}
    weekday = date.weekday()
    if weekday == 6:
        return []

    # Outbound tiene volumen alto — escalar según día
    factor  = 0.70 if weekday == 5 else 1.0
    vol     = int(cfg['daily_marcaciones'] * factor * random.gauss(1.0, 0.05))

    interactions = []
    from .base import intraday_slot

    for i in range(vol):
        hora = intraday_slot(cfg['intraday'], date)
        is_contact = random.random() < cfg['contact_rate']

        if is_contact:
            tipif  = weighted_choice(cfg['tipif_contacto'])
            is_sale   = tipif == 'Venta'
            is_agenda = 'Agenda' in tipif

            if is_sale:
                status = 'venta'
                tmo_s  = gaussian_duration(300, 0.20, 120, 720)
            elif is_agenda:
                status = 'agenda'
                tmo_s  = gaussian_duration(240, 0.20, 60, 600)
            elif 'corta' in tipif.lower():
                status = 'atendida'
                tmo_s  = gaussian_duration(45, 0.30, 10, 120)
            else:
                status = 'rechazo'
                tmo_s  = gaussian_duration(cfg['tmo_contacto_s'], 0.20, 60, 600)

            acw_s  = gaussian_duration(30, 0.30, 10, 120)
            agent  = random.choice(agent_pool) if agent_pool else None
        else:
            tipif  = weighted_choice(cfg['tipif_no_contacto'])
            status = 'no_contacto'
            tmo_s  = gaussian_duration(cfg['tmo_no_contesta_s'], 0.25, 5, 90)
            acw_s  = 0
            agent  = None

        producto   = weighted_choice(cfg['producto'])
        sub_prod   = weighted_choice(cfg['sub_producto'])

        interactions.append({
            'canal':       'outbound',
            'skill':       producto,
            'sub_canal':   sub_prod,
            'fecha':       date.date(),
            'hora_inicio': hora,
            'hora_fin':    hora + timedelta(seconds=tmo_s + acw_s),
            'duracion_s':  tmo_s,
            'acw_s':       acw_s,
            'tipificacion':tipif,
            'status':      status,
            'lead_id':     synthetic_lead_id('outbound', lead_offset + i),
            'agent_codigo':agent['codigo'] if agent else None,
            'intento_num': random.randint(1, 5),
            'is_simulated':True,
        })

    return interactions
