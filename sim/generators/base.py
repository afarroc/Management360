# sim/generators/base.py
"""
Utilidades compartidas por todos los generadores.
Sin dependencias de Django — solo stdlib + random.
"""
import random
import math
from datetime import datetime, timedelta


def weighted_choice(weights: dict) -> str:
    """Elige una clave según pesos. weights = {'A': 0.6, 'B': 0.3, 'C': 0.1}"""
    keys    = list(weights.keys())
    values  = list(weights.values())
    total   = sum(values)
    r       = random.uniform(0, total)
    cumul   = 0.0
    for k, v in zip(keys, values):
        cumul += v
        if r <= cumul:
            return k
    return keys[-1]


def gaussian_duration(mean_s: float, sigma_factor: float = 0.15,
                       min_s: int = 30, max_s: int = 1800) -> int:
    """Duración en segundos con distribución gaussiana. sigma = mean × factor."""
    sigma = mean_s * sigma_factor
    val   = random.gauss(mean_s, sigma)
    return max(min_s, min(max_s, int(val)))


def intraday_slot(intraday: dict, date: datetime) -> datetime:
    """
    Genera una hora dentro del día según pesos intradía.
    intraday = {9: 0.123, 10: 0.135, ...}  (hora entera → peso)
    Devuelve datetime con hora aleatoria dentro del intervalo de 1h elegido.
    """
    hour      = int(weighted_choice({str(k): v for k, v in intraday.items()}))
    minute    = random.randint(0, 59)
    second    = random.randint(0, 59)
    return date.replace(hour=hour, minute=minute, second=second, microsecond=0)


def daily_volume(base_vol: int, weekday: int,
                  weekend_factor: float = 0.59,
                  variance: float = 0.08) -> int:
    """
    Volumen diario con varianza gaussiana.
    weekday: 0=lunes ... 6=domingo
    """
    factor = weekend_factor if weekday >= 5 else 1.0
    vol    = base_vol * factor * random.gauss(1.0, variance)
    return max(0, int(vol))


def synthetic_lead_id(canal: str, index: int) -> str:
    """Genera un ID de lead sintético."""
    prefix = {'inbound': 'CLI', 'outbound': 'LID', 'digital': 'DIG'}.get(canal, 'GEN')
    return f"{prefix}-{index:08d}"


def agent_tmo_factor(antiguedad: str) -> float:
    """Factor de TMO según antigüedad. Senior más rápido."""
    return {'senior': 1.0, 'junior': 1.15}.get(antiguedad, 1.0)


def agent_sph_factor(antiguedad: str) -> float:
    """Factor SPH según antigüedad. Senior = 100%, junior = 71% (calibrado)."""
    return {'senior': 1.0, 'junior': 0.71}.get(antiguedad, 1.0)


def is_working_day(date: datetime, include_saturday: bool = False) -> bool:
    """Lunes-Viernes siempre laborable. Sábado opcional."""
    wd = date.weekday()
    if wd == 6:
        return False
    if wd == 5:
        return include_saturday
    return True


def generate_agent_pool(n_agents: int, turnos: list,
                         sph_base: float, adherencia_base: float,
                         senior_ratio: float = 0.82) -> list:
    """
    Genera un pool de perfiles de agente con varianza gaussiana.
    Retorna lista de dicts — no instancias Django.
    """
    agents = []
    for i in range(1, n_agents + 1):
        ant    = 'senior' if random.random() < senior_ratio else 'junior'
        turno  = turnos[i % len(turnos)]
        sph    = max(0.01, random.gauss(sph_base * agent_sph_factor(ant), sph_base * 0.15))
        adh    = min(0.999, max(0.696, random.gauss(adherencia_base, 0.04)))
        tmo_f  = random.gauss(agent_tmo_factor(ant), 0.05)
        agents.append({
            'codigo':          f"AGT-{i:03d}",
            'turno':           turno,
            'antiguedad':      ant,
            'sph_base':        round(sph, 4),
            'adherencia_base': round(adh, 4),
            'tmo_factor':      round(tmo_f, 3),
        })
    return agents
