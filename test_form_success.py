#!/usr/bin/env python3
"""
Script para probar creación exitosa de una programación de tarea
Verifica que el formulario funcione correctamente con datos válidos
"""

import requests
import json
from datetime import datetime, timedelta

# Configuración
BASE_URL = "http://192.168.18.47:5000"
CREATE_URL = f"{BASE_URL}/events/tasks/schedules/create/"
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

def get_available_task(session):
    """Obtiene la tarea específica creada para pruebas (ID 97)"""
    # Usar la tarea específica que creamos para pruebas
    test_task_id = '97'

    # Verificar que la tarea existe en el formulario
    response = session.get(CREATE_URL)
    if response.status_code != 200:
        print(f"[ERROR] No se pudo acceder al formulario: {response.status_code}")
        return None

    from bs4 import BeautifulSoup
    soup = BeautifulSoup(response.text, 'html.parser')
    task_select = soup.find('select', {'id': 'id_task'})

    if task_select:
        options = task_select.find_all('option')
        for option in options:
            if option.get('value') == test_task_id:
                task_name = option.get_text().strip()
                print(f"[OK] Tarea de prueba encontrada: ID {test_task_id} - {task_name}")
                return test_task_id

    print(f"[WARNING] Tarea de prueba ID {test_task_id} no encontrada en el formulario")
    print("[INFO] Buscando cualquier tarea disponible...")

    # Fallback: buscar cualquier tarea disponible
    if task_select:
        options = task_select.find_all('option')
        for option in options:
            if option.get('value') and option.get('value') != '':
                task_name = option.get_text().strip()
                print(f"[INFO] Usando tarea alternativa: ID {option.get('value')} - {task_name}")
                return option.get('value')

    print("[ERROR] No se encontraron tareas disponibles")
    return None

def test_successful_creation():
    """Prueba creación exitosa de una programación"""

    session = login_and_get_session()
    if not session:
        return

    # Obtener una tarea válida
    task_id = get_available_task(session)
    if not task_id:
        print("[ERROR] No hay tareas disponibles para crear programaciones")
        return

    print(f"[OK] Usando tarea ID: {task_id}")

    # Obtener CSRF token del formulario
    response = session.get(CREATE_URL)
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(response.text, 'html.parser')
    csrf_input = soup.find('input', {'name': 'csrfmiddlewaretoken'})
    csrf_token = csrf_input['value'] if csrf_input else None

    if not csrf_token:
        print("[ERROR] No se pudo obtener CSRF token del formulario")
        return

    # Datos válidos para crear una programación
    tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
    next_week = (datetime.now() + timedelta(days=8)).strftime('%Y-%m-%d')

    valid_data = {
        'csrfmiddlewaretoken': csrf_token,
        'task': task_id,
        'recurrence_type': 'weekly',
        'monday': 'on',
        'tuesday': 'on',
        'start_time': '09:00',
        'start_date': tomorrow,
        'end_date': next_week,
        'is_active': 'on',
        'duration_hours': '1.5'
    }

    print("\n" + "="*80)
    print("PRUEBA DE CREACIÓN EXITOSA DE PROGRAMACIÓN")
    print("="*80)
    print(f"Datos a enviar: {json.dumps(valid_data, indent=2)}")

    try:
        response = session.post(CREATE_URL, data=valid_data, headers={
            'Referer': CREATE_URL
        }, allow_redirects=True)

        print(f"\nCódigo de respuesta: {response.status_code}")
        print(f"URL final: {response.url}")

        if response.status_code == 200:
            # Verificar si hay errores en el formulario
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(response.text, 'html.parser')

            # Buscar errores
            error_divs = soup.find_all('div', class_='invalid-feedback')
            error_alerts = soup.find_all('div', class_='alert-danger')

            if error_divs or error_alerts:
                print("[FAIL] Se encontraron errores en el formulario:")
                for error in error_divs + error_alerts:
                    print(f"  - {error.get_text().strip()}")
                return False
            else:
                # Verificar si se redirigió a la página de detalle
                if 'task_schedule_detail' in response.url or 'schedules' in response.url:
                    print("[SUCCESS] Programación creada exitosamente")
                    print(f"Redirigido a: {response.url}")

                    # Extraer ID de la programación si está en la URL
                    if 'schedule_id' in response.url:
                        schedule_id = response.url.split('schedule_id=')[1].split('&')[0]
                        print(f"ID de programación creada: {schedule_id}")

                    return True
                else:
                    print("[WARNING] No se detectó redirección a página de detalle")
                    print("Contenido de la página:")
                    print(response.text[:500] + "..." if len(response.text) > 500 else response.text)
                    return False
        else:
            print(f"[ERROR] Error HTTP: {response.status_code}")
            return False

    except Exception as e:
        print(f"[ERROR] Error en la prueba: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_successful_creation()
    if success:
        print("\n[SUCCESS] PRUEBA EXITOSA: El formulario funciona correctamente")
    else:
        print("\n[FAILED] PRUEBA FALLIDA: Hay problemas con el formulario")