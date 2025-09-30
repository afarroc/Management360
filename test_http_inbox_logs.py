#!/usr/bin/env python
"""
Script para probar la vista inbox_item_detail_admin vía HTTP con logs
"""
import requests
import json

def test_inbox_detail_http():
    """Probar la vista inbox_item_detail_admin vía HTTP"""

    base_url = "http://192.168.18.47:5000"
    item_id = 99  # Usar el ID que mencionó el usuario

    url = f"{base_url}/events/inbox/admin/{item_id}/"
    print(f"Haciendo petición GET a: {url}")

    try:
        # Hacer petición sin autenticación primero para ver el comportamiento
        response = requests.get(url, timeout=10)

        print(f"Status code: {response.status_code}")
        print(f"Content-Type: {response.headers.get('content-type', 'N/A')}")

        if response.status_code == 200:
            content = response.text

            # Verificar que no sea una página de login
            if "login" in content.lower() or "iniciar sesión" in content.lower():
                print("WARNING: Redirigiendo a login - usuario no autenticado")
                return

            # Verificar contenido básico
            if "Inbox Item Details" in content:
                print("SUCCESS: Página de detalles cargada")
            else:
                print("WARNING: No se encontró el título esperado")

            # Buscar datos del item
            if f"#{item_id}" in content:
                print(f"SUCCESS: ID del item ({item_id}) encontrado")
            else:
                print(f"ERROR: ID del item ({item_id}) NO encontrado")

            # Verificar si hay datos de usuarios disponibles
            if "available_users" in content or "Elegir usuario" in content:
                print("SUCCESS: Usuarios disponibles encontrados")
            else:
                print("WARNING: Usuarios disponibles no encontrados")

            # Mostrar parte del contenido para debug
            print("\n--- Primeros 500 caracteres de la respuesta ---")
            print(content[:500])
            print("--- Fin del extracto ---")

        elif response.status_code == 302:
            print("REDIRECT: Posible redirección a login")
            print(f"Location: {response.headers.get('location', 'N/A')}")

        elif response.status_code == 404:
            print("ERROR 404: Item no encontrado")

        else:
            print(f"ERROR: Status code {response.status_code}")
            print("Contenido del error:")
            print(response.text[:500])

    except requests.exceptions.RequestException as e:
        print(f"ERROR de conexión: {str(e)}")

if __name__ == '__main__':
    print("=== Probando vista inbox_item_detail_admin vía HTTP ===")
    test_inbox_detail_http()
    print("=== Fin de la prueba ===")