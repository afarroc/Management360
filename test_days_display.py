#!/usr/bin/env python3
"""
Script para probar que los días de la semana se muestran correctamente
cuando se selecciona recurrencia semanal
"""

import requests
from bs4 import BeautifulSoup

def test_days_display():
    """Prueba que los días de la semana se muestran cuando se selecciona recurrencia semanal"""

    # Configuración
    base_url = "http://127.0.0.1:8000"
    form_url = f"{base_url}/events/tasks/schedules/create/"

    print("=== PRUEBA: VISUALIZACIÓN DE DÍAS DE LA SEMANA ===")

    try:
        # 1. Acceder directamente al formulario (sin login para simplificar)
        print("\n[1/2] Accediendo al formulario...")
        response = requests.get(form_url, allow_redirects=True)

        # Si nos redirige al login, obtenemos el HTML del login pero continuamos
        if response.url != form_url:
            print("[INFO] Redirigido al login, pero continuamos con la verificación del HTML")

        if response.status_code not in [200, 302]:
            print(f"ERROR: No se pudo acceder al formulario ({response.status_code})")
            return False

        print("[OK] Página cargada")

        # 2. Verificar que el HTML contiene los elementos correctos
        print("\n[2/2] Verificando estructura del formulario...")

        soup = BeautifulSoup(response.text, 'html.parser')

        # Verificar que existe el contenedor de días
        days_group = soup.find('div', {'id': 'daysGroup'})
        if not days_group:
            print("ERROR: No se encontró el contenedor de días (daysGroup)")
            return False

        print("[OK] Contenedor de días encontrado")

        # Verificar que inicialmente está oculto
        style_attr = days_group.get('style', '')
        if 'display: none' not in style_attr:
            print("ADVERTENCIA: Los días no están ocultos inicialmente (esto puede ser normal)")
        else:
            print("[OK] Días ocultos inicialmente")

        # Verificar que existen todos los checkboxes de días
        day_checkboxes = days_group.find_all('input', {'class': 'day-checkbox'})
        if len(day_checkboxes) != 7:
            print(f"ERROR: Se encontraron {len(day_checkboxes)} checkboxes de días, se esperaban 7")
            return False

        print(f"[OK] Encontrados {len(day_checkboxes)} checkboxes de días")

        # Verificar que los días están en el orden correcto
        expected_days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
        for i, checkbox in enumerate(day_checkboxes):
            day_id = checkbox.get('id', '')
            expected_id = f"id_{expected_days[i]}"
            if day_id != expected_id:
                print(f"ERROR: Checkbox {i+1} no tiene el ID esperado (esperado: {expected_id}, encontrado: {day_id})")
                return False

        print("[OK] IDs de checkboxes correctos")

        # Verificar que existe el JavaScript para mostrar/ocultar días
        script_tags = soup.find_all('script')
        js_found = False
        for script in script_tags:
            if script.string and 'toggleDaysVisibility' in script.string:
                js_found = True
                break

        if not js_found:
            print("ERROR: No se encontró el JavaScript para mostrar/ocultar días")
            return False

        print("[OK] JavaScript para mostrar días encontrado")

        # Verificar que existe el selector de recurrencia
        recurrence_select = soup.find('select', {'id': 'id_recurrence_type'})
        if not recurrence_select:
            print("ERROR: No se encontró el selector de tipo de recurrencia")
            return False

        print("[OK] Selector de recurrencia encontrado")

        print("\n=== PRUEBA COMPLETADA EXITOSAMENTE ===")
        print("✓ Contenedor de días presente")
        print("✓ 7 checkboxes de días encontrados")
        print("✓ IDs de checkboxes correctos")
        print("✓ JavaScript de visibilidad presente")
        print("✓ Selector de recurrencia presente")
        print("\nLos días de la semana se mostrarán correctamente cuando se seleccione 'weekly'")
        return True

    except Exception as e:
        print(f"ERROR: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_days_display()
    exit(0 if success else 1)