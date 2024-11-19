def calcular_trafico_intensidad(llamadas, tiempo_manejo_promedio):
    # Cálculo de minutos de llamada
    minutos_llamada = llamadas * tiempo_manejo_promedio
    
    # Cálculo de horas de llamada
    horas_llamada = minutos_llamada / 60
    
    # La intensidad del tráfico en Erlangs
    trafico_intensidad = horas_llamada
    
    return trafico_intensidad

# Ejemplo de uso
llamadas = 200
tiempo_manejo_promedio = 3  # En minutos

trafico_intensidad = calcular_trafico_intensidad(llamadas, tiempo_manejo_promedio)
print(f"La intensidad del tráfico es {trafico_intensidad} Erlangs.")