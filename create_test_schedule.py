#!/usr/bin/env python3
"""
Script para crear una programación de prueba usando el formulario
"""

import requests
import json
from datetime import datetime, timedelta

# Configuración
BASE_URL = "http://127.0.0.1:8000"
LOGIN_URL = f"{BASE_URL}/accounts/login/"
CREATE_URL = f"{BASE_URL}/events/tasks/schedules/create/"

# Credenciales
USERNAME = "admin"
PASSWORD = "admin123"

def login_and_create_schedule():
    """Inicia sesión y crea una programación de prueba"""
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

    # Obtener la página de creación para conseguir el CSRF token y las tareas disponibles
    response = session.get(CREATE_URL)
    if response.status_code != 200:
        print(f"Error al acceder a la página de creación: {response.status_code}")
        return None

    from bs4 import BeautifulSoup
    soup = BeautifulSoup(response.text, 'html.parser')
    csrf_input = soup.find('input', {'name': 'csrfmiddlewaretoken'})
    csrf_token = csrf_input['value'] if csrf_input else None

    if not csrf_token:
        print("ERROR: No se pudo obtener CSRF token del formulario")
        return None

    # Obtener todas las tareas disponibles del select
    task_select = soup.find('select', {'id': 'id_task'})
    if not task_select:
        print("ERROR: No se encontró el select de tareas")
        return None

    task_options = task_select.find_all('option')
    task_options = [opt for opt in task_options if opt.get('value') and opt.get('value') != '']

    if not task_options:
        print("ERROR: No hay tareas disponibles para el usuario")
        return None

    # Mostrar todas las tareas disponibles
    print("Tareas disponibles:")
    for i, opt in enumerate(task_options[:10]):  # Mostrar primeras 10
        print(f"  {i+1}. ID: {opt['value']} - {opt.text.strip()}")

    # Intentar usar la última tarea (probablemente la más nueva)
    if len(task_options) > 1:
        task_option = task_options[-1]  # Usar la última
    else:
        task_option = task_options[0]

    task_id = task_option['value']
    task_name = task_option.text.strip()
    print(f"[INFO] Usando tarea ID: {task_id} - {task_name}")

    # Crear datos válidos para la programación
    schedule_data = {
        'csrfmiddlewaretoken': csrf_token,
        'task': task_id,
        'recurrence_type': 'weekly',
        'monday': 'on',
        'tuesday': 'on',
        'start_time': '09:00',
        'start_date': '2025-10-01',
        'end_date': '2025-12-31',
        'is_active': 'on',
        'duration_hours': '1.0'
    }

    print("[INFO] Creando programación de prueba...")

    response = session.post(CREATE_URL, data=schedule_data, headers={
        'Referer': CREATE_URL
    }, allow_redirects=True)

    if response.status_code == 200:
        # Verificar si hay errores
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(response.text, 'html.parser')
        errors = soup.find_all('div', class_='invalid-feedback')
        if errors:
            print("[ERROR] Errores en la creación:")
            for error in errors:
                print(f"  - {error.text.strip()}")
            return None
        else:
            print("[OK] Programación creada exitosamente")
            # Extraer ID de la URL de redirección si existe
            if 'schedule_id' in response.url:
                schedule_id = response.url.split('/')[-2]
                print(f"[OK] ID de la programación creada: {schedule_id}")
                return schedule_id
            else:
                print("[INFO] Programación creada pero no se pudo extraer el ID")
                return "created"
    else:
        print(f"[ERROR] Error HTTP: {response.status_code}")
        return None

if __name__ == "__main__":
    result = login_and_create_schedule()
    if result:
        print(f"\n[SUCCESS] Programación creada con ID: {result}")
    else:
        print("\n[FAILED] No se pudo crear la programación")