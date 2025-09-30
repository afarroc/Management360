#!/usr/bin/env python
"""
Test HTTP para verificar que la vista inbox_item_detail_admin funciona correctamente
usando requests para hacer petición al servidor corriendo.
"""

import requests
import json

def test_inbox_detail_http():
    """Test HTTP para verificar la vista inbox_item_detail_admin"""
    print("=== Test HTTP de Vista inbox_item_detail_admin ===")

    base_url = "http://192.168.18.47:5000"
    url = f"{base_url}/events/inbox/admin/110/"

    print(f"URL: {url}")

    try:
        # Hacer petición GET (sin autenticación primero para ver si redirige)
        response = requests.get(url, timeout=10)

        print(f"Código de respuesta: {response.status_code}")

        if response.status_code == 200:
            content = response.text

            # Verificar que contiene información del item
            if "110" in content:
                print("[OK] ID del item encontrado en la respuesta")
            else:
                print("[ERROR] ID del item NO encontrado en la respuesta")

            if "Captura rapida - prueba" in content:
                print("[OK] Titulo del item encontrado en la respuesta")
            else:
                print("[ERROR] Titulo del item NO encontrado en la respuesta")

            # Verificar que contiene usuarios disponibles
            if 'form-select' in content and 'option value=' in content:
                print("[OK] Select de usuarios encontrado")

                # Contar opciones
                import re
                options = re.findall(r'<option value="\d+">', content)
                print(f"Numero de opciones de usuario: {len(options)}")

                # Mostrar algunas opciones
                if options:
                    print("Primeras opciones encontradas:")
                    for i, option in enumerate(options[:3]):
                        print(f"  {i+1}. {option}")

            else:
                print("[ERROR] Select de usuarios NO encontrado")

            # Verificar modal de delegación
            if 'delegateModal' in content:
                print("[OK] Modal de delegacion encontrado")
            else:
                print("[ERROR] Modal de delegacion NO encontrado")

        elif response.status_code == 302:
            print(f"Redirect a: {response.headers.get('Location', 'N/A')}")
            print("Esto indica que se requiere autenticación")

        else:
            print(f"Error HTTP: {response.status_code}")
            print(f"Contenido: {response.text[:500]}")

    except requests.exceptions.RequestException as e:
        print(f"Error de conexión: {e}")

    print("\n=== Fin del Test HTTP ===")

if __name__ == '__main__':
    test_inbox_detail_http()