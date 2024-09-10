import numpy as np

def utilisation(Intensity, agents):
    return Intensity / agents

def top_row(Intensity, agents):
    return (Intensity ** agents) / np.math.factorial(agents)

def bottom_row(Intensity, agents):
    answer = 0
    for k in range(agents):
        answer += ((Intensity ** k) / np.math.factorial(k))
    return answer

def ErlangC(Intensity, agents):
    return (top_row(Intensity, agents)) / ((top_row(Intensity, agents)) + ((1 - utilisation(Intensity, agents)) * bottom_row(Intensity, agents)))

def AgentsFTE(Calls, Reporting_Period, average_handling_time, service_level_percent, service_level_time, Shrinkage):
    Intensity = (Calls / (Reporting_Period * 60)) * average_handling_time
    minagents = int(Intensity)
    agents = minagents
    while ServiceLevel(Calls, Reporting_Period, average_handling_time, service_level_time, agents) < service_level_percent:
        agents += 1
    return agents / (1 - Shrinkage)

def ServiceLevel(Calls, Reporting_Period, average_handling_time, service_level_time, agents):
    Intensity = (Calls / (Reporting_Period * 60)) * average_handling_time
    return 1 - (ProbCallWaits(Calls, Reporting_Period, average_handling_time, agents) * np.exp(-(agents - Intensity) * service_level_time / average_handling_time))

def ProbCallWaits(Calls, Reporting_Period, average_handling_time, agents):
    Intensity = (Calls / (Reporting_Period * 60)) * average_handling_time
    Occupancy = Intensity / agents
    A_n = 1
    SumA_k = 0
    for k in range(agents, -1, -1):
        A_k = A_n * k / Intensity
        SumA_k += A_k
        A_n = A_k
    return 1 / (1 + ((1 - Occupancy) * SumA_k))
