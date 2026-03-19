# analyst/services/planning.py
import math
import numpy as np
from typing import Union

def utilisation(Intensity: float, agents: Union[int, float]) -> float:
    """Calcula la utilización de agentes"""
    return Intensity / agents

def top_row(Intensity: float, agents: int) -> float:
    """Calcula el numerador de Erlang C"""
    return (Intensity ** agents) / math.factorial(agents)

def bottom_row(Intensity: float, agents: int) -> float:
    """Calcula el denominador de Erlang C"""
    answer = 0
    for k in range(agents):
        answer += ((Intensity ** k) / math.factorial(k))
    return answer

def ErlangC(Intensity: float, agents: int) -> float:
    """Calcula la probabilidad de espera usando Erlang C"""
    return (top_row(Intensity, agents)) / ((top_row(Intensity, agents)) + ((1 - utilisation(Intensity, agents)) * bottom_row(Intensity, agents)))

def ServiceLevel(Calls: int, Reporting_Period: int, average_handling_time: float, 
                 service_level_time: float, agents: int) -> float:
    """Calcula el nivel de servicio"""
    Intensity = (Calls / (Reporting_Period * 60)) * average_handling_time
    return 1 - (ProbCallWaits(Calls, Reporting_Period, average_handling_time, agents) * 
                np.exp(-(agents - Intensity) * service_level_time / average_handling_time))

def ProbCallWaits(Calls: int, Reporting_Period: int, average_handling_time: float, agents: int) -> float:
    """Calcula la probabilidad de que una llamada espere"""
    Intensity = (Calls / (Reporting_Period * 60)) * average_handling_time
    Occupancy = Intensity / agents
    A_n = 1
    SumA_k = 0
    for k in range(agents, -1, -1):
        A_k = A_n * k / Intensity
        SumA_k += A_k
        A_n = A_k
    return 1 / (1 + ((1 - Occupancy) * SumA_k))

def AgentsFTE(Calls: int, Reporting_Period: int, average_handling_time: float,
              service_level_percent: float, service_level_time: float, Shrinkage: float) -> float:
    """Calcula los agentes FTE necesarios"""
    Intensity = (Calls / (Reporting_Period * 60)) * average_handling_time
    minagents = int(Intensity)
    agents = minagents
    while ServiceLevel(Calls, Reporting_Period, average_handling_time, service_level_time, agents) < service_level_percent:
        agents += 1
    return agents / (1 - Shrinkage)