#!/usr/bin/env python3
"""
Script para crear una tarea de prueba que no tenga programaciones activas
"""

import requests
import json
from datetime import datetime, timedelta

# Configuración
BASE_URL = "http://127.0.0.1:8000"
LOGIN_URL = f"{BASE_URL}/accounts/login/"
CREATE_TASK_URL = f"{BASE_URL}/events/tasks/create/"

# Credenciales
USERNAME = "admin"
PASSWORD = "admin123"

def login_and_create_task():
    """Inicia sesión y crea una tarea de prueba"""
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

    if 'dashboard' not in response.url and '/' not in response.url:
        print(f"[ERROR] Error en login: {response.status_code} - URL: {response.url}")
        return None

    print("[OK] Login exitoso")

    # Obtener la página de creación de tarea para conseguir el CSRF token
    response = session.get(CREATE_TASK_URL)
    if response.status_code != 200:
        print(f"Error al acceder a la página de creación de tarea: {response.status_code}")
        return None

    from bs4 import BeautifulSoup
    soup = BeautifulSoup(response.text, 'html.parser')
    csrf_input = soup.find('input', {'name': 'csrfmiddlewaretoken'})
    csrf_token = csrf_input['value'] if csrf_input else None

    if not csrf_token:
        print("ERROR: No se pudo obtener CSRF token del formulario de tarea")
        return None

    # Crear datos válidos para la tarea
    import time
    timestamp = str(int(time.time()))

    task_data = {
        'csrfmiddlewaretoken': csrf_token,
        'title': f'Tarea de prueba para edición {timestamp}',
        'description': 'Tarea creada automáticamente para probar la edición de programaciones',
        'important': '',  # No importante
        'project': '',  # Sin proyecto
        'task_status': '1',  # Asumiendo que existe un estado con ID 1
        'event': '',  # Sin evento
        'assigned_to': '',  # Sin asignar
        'ticket_price': '0.07'
    }

    print("[INFO] Creando tarea de prueba...")

    response = session.post(CREATE_TASK_URL, data=task_data, headers={
        'Referer': CREATE_TASK_URL
    }, allow_redirects=True)

    if response.status_code == 200:
        # Verificar si hay errores
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(response.text, 'html.parser')
        errors = soup.find_all('div', class_='invalid-feedback')
        if errors:
            print("[ERROR] Errores en la creación de tarea:")
            for error in errors:
                print(f"  - {error.text.strip()}")
            return None
        else:
            print("[OK] Tarea creada exitosamente")
            return "created"
    else:
        print(f"[ERROR] Error HTTP: {response.status_code}")
        return None

if __name__ == "__main__":
    result = login_and_create_task()
    if result:
        print(f"\n[SUCCESS] Tarea de prueba creada")
    else:
        print("\n[FAILED] No se pudo crear la tarea de prueba")