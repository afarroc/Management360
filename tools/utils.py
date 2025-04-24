def calcular_trafico_intensidad(calls, average_handling_time):
    # Calculate total call minutes
    call_minutes = calls * average_handling_time
    
    # Convert minutes to hours
    call_hours = call_minutes / 60
    
    # Traffic intensity in Erlangs
    traffic_intensity = call_hours
    
    return traffic_intensity

# Example usage
calls = 200
average_handling_time = 3  # In minutes

traffic_intensity = calcular_trafico_intensidad(calls, average_handling_time)
print(f"The traffic intensity is {traffic_intensity} Erlangs.")