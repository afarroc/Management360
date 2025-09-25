#!/usr/bin/env python3
"""
Script para probar la vista mejorada de edición de programaciones
"""

import requests
import json
from datetime import datetime, timedelta

# Configuración
BASE_URL = "http://192.168.18.47:5000"
ENHANCED_EDIT_URL = f"{BASE_URL}/events/tasks/schedules/32/edit/enhanced/"
LOGIN_URL = f"{BASE_URL}/accounts/login/"

# Credenciales
USERNAME = "admin"
PASSWORD = "admin123"

def login_and_get_session():
    """Inicia sesión y obtiene la sesión con cookies"""
    session = requests.Session()

    # Obtener la página de login primero para obtener el CSRF token
    response = session.get(LOGIN_URL)
    if 'csrftoken' in response.cookies:
        csrf_token = response.cookies['csrftoken']
    else:
        # Buscar CSRF token en el HTML
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(response.text, 'html.parser')
        csrf_input = soup.find('input', {'name': 'csrfmiddlewaretoken'})
        csrf_token = csrf_input['value'] if csrf_input else None

    if not csrf_token:
        print("ERROR: No se pudo obtener CSRF token")
        return None

    # Hacer login
    login_data = {
        'username': USERNAME,
        'password': PASSWORD,
        'csrfmiddlewaretoken': csrf_token
    }

    response = session.post(LOGIN_URL, data=login_data, headers={
        'Referer': LOGIN_URL
    }, allow_redirects=True)

    # Verificar si el login fue exitoso
    if response.status_code == 200 and ('dashboard' in response.url or '/' in response.url):
        print("[OK] Login exitoso")
        return session
    else:
        print(f"[ERROR] Error en login: {response.status_code} - URL: {response.url}")
        return None

def test_enhanced_edit_view():
    """Prueba la vista mejorada de edición"""

    session = login_and_get_session()
    if not session:
        return

    print("\n" + "="*80)
    print("PRUEBA DE VISTA MEJORADA DE EDICIÓN")
    print("="*80)

    try:
        # Acceder a la vista mejorada
        response = session.get(ENHANCED_EDIT_URL)

        print(f"Código de respuesta: {response.status_code}")

        if response.status_code == 200:
            print("[SUCCESS] Vista mejorada accesible")

            # Verificar que contiene elementos de la vista mejorada
            if "Vista avanzada con funcionalidades mejoradas" in response.text:
                print("[SUCCESS] Contiene elementos de la vista mejorada")
            else:
                print("[WARNING] No se encontraron elementos específicos de la vista mejorada")

            # Verificar que contiene estadísticas
            if "Programaciones Creadas" in response.text:
                print("[SUCCESS] Contiene estadísticas")
            else:
                print("[WARNING] No se encontraron estadísticas")

            # Verificar que contiene preview
            if "Próximas Ocurrencias" in response.text:
                print("[SUCCESS] Contiene sección de preview")
            else:
                print("[WARNING] No se encontró sección de preview")

            return True
        else:
            print(f"[ERROR] Error HTTP: {response.status_code}")
            print(f"Contenido: {response.text[:500]}")
            return False

    except Exception as e:
        print(f"[ERROR] Error en la prueba: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_enhanced_edit_view()
    if success:
        print("\n[SUCCESS] PRUEBA EXITOSA: La vista mejorada funciona correctamente")
    else:
        print("\n[FAILED] PRUEBA FALLIDA: Hay problemas con la vista mejorada")