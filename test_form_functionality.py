#!/usr/bin/env python3
"""
Script para verificar la funcionalidad completa del formulario TaskScheduleForm
Prueba casos válidos e inválidos, y verifica la creación exitosa
"""

import requests
import json
from datetime import datetime, timedelta

# Configuración
BASE_URL = "http://127.0.0.1:8000"
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

    if response.status_code == 200 and ('dashboard' in response.url or '/' in response.url):
        print("[OK] Login exitoso")
        return session
    else:
        print(f"[ERROR] Error en login: {response.status_code} - URL: {response.url}")
        return None

def get_csrf_token(session, url):
    """Obtiene CSRF token de una página"""
    response = session.get(url)
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(response.text, 'html.parser')
    csrf_input = soup.find('input', {'name': 'csrfmiddlewaretoken'})
    return csrf_input['value'] if csrf_input else None

def get_available_task_id(session):
    """Obtiene el ID de una tarea disponible para el usuario"""
    response = session.get(CREATE_URL)
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(response.text, 'html.parser')

    task_select = soup.find('select', {'name': 'task'})
    if task_select:
        first_option = task_select.find('option')
        if first_option and first_option.get('value'):
            return first_option['value']
    return None

def test_form_functionality():
    """Prueba la funcionalidad completa del formulario"""

    session = login_and_get_session()
    if not session:
        return

    csrf_token = get_csrf_token(session, CREATE_URL)
    if not csrf_token:
        print("ERROR: No se pudo obtener CSRF token del formulario")
        return

    # Obtener una tarea disponible
    available_task_id = get_available_task_id(session)
    if not available_task_id:
        print("ERROR: No se pudo encontrar una tarea disponible")
        return

    print(f"Tarea disponible encontrada: ID {available_task_id}")
    print("\n" + "="*80)
    print("VERIFICANDO FUNCIONALIDAD COMPLETA DEL FORMULARIO TaskScheduleForm")
    print("="*80)

    # Prueba 1: Formulario válido - debería crear la programación
    print("\n[1/3] Probando: Creación exitosa de programación")
    valid_data = {
        'csrfmiddlewaretoken': csrf_token,
        'task': available_task_id,  # Usar tarea disponible
        'recurrence_type': 'weekly',
        'monday': 'on',
        'tuesday': 'on',
        'start_time': '09:00',
        'start_date': '2025-12-01',
        'end_date': '2025-12-31',
        'is_active': 'on',
        'duration_hours': '1.5'
    }

    try:
        response = session.post(CREATE_URL, data=valid_data, headers={
            'Referer': CREATE_URL
        }, allow_redirects=False)

        if response.status_code == 302:  # Redirección exitosa
            print("[PASS] Programación creada exitosamente (redirección)")
            # Verificar que se creó en la base de datos
            schedules_url = f"{BASE_URL}/events/tasks/schedules/"
            schedules_response = session.get(schedules_url)
            if "Programación Recurrente" in schedules_response.text:
                print("[PASS] Programación visible en la lista")
            else:
                print("[WARN] Programación no visible en la lista")
        else:
            print(f"[FAIL] Error al crear programación: {response.status_code}")
            print(f"Respuesta: {response.text[:500]}...")

    except Exception as e:
        print(f"[ERROR] Error en la prueba: {str(e)}")

    # Prueba 2: Formulario con errores - debería mostrar errores
    print("\n[2/3] Probando: Validación de errores")
    invalid_data = {
        'csrfmiddlewaretoken': csrf_token,
        'task': '',  # Campo vacío
        'recurrence_type': 'weekly',
        'start_time': '25:00',  # Hora inválida
        'start_date': '2020-01-01',  # Fecha en el pasado
        'end_date': '2020-01-01',  # Fecha anterior
        'duration_hours': '-1',  # Valor negativo
        # Sin días seleccionados para weekly
    }

    try:
        response = session.post(CREATE_URL, data=invalid_data, headers={
            'Referer': CREATE_URL
        })

        if response.status_code == 200:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(response.text, 'html.parser')

            # Buscar errores
            error_alerts = soup.find_all('div', class_='alert-danger')
            error_count = len(error_alerts)

            if error_count > 0:
                print(f"[PASS] Se encontraron {error_count} errores de validación")
                for i, alert in enumerate(error_alerts[:3], 1):  # Mostrar primeros 3
                    alert_text = alert.get_text().strip()
                    if alert_text.startswith(''):
                        alert_text = alert_text[1:].strip()
                    print(f"  Error {i}: {alert_text}")
            else:
                print("[FAIL] No se encontraron errores de validación esperados")
        else:
            print(f"[FAIL] Respuesta inesperada: {response.status_code}")

    except Exception as e:
        print(f"[ERROR] Error en la prueba: {str(e)}")

    # Prueba 3: Verificar que el formulario se carga correctamente
    print("\n[3/3] Probando: Carga del formulario")
    try:
        response = session.get(CREATE_URL)

        if response.status_code == 200:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(response.text, 'html.parser')

            # Verificar elementos del formulario
            form = soup.find('form', {'id': 'scheduleForm'})
            if form:
                print("[PASS] Formulario encontrado")

                # Verificar campos requeridos
                required_fields = ['task', 'start_time', 'start_date', 'duration_hours']
                missing_fields = []

                for field_name in required_fields:
                    field = soup.find('select', {'name': field_name}) or soup.find('input', {'name': field_name})
                    if not field:
                        missing_fields.append(field_name)

                if not missing_fields:
                    print("[PASS] Todos los campos requeridos están presentes")
                else:
                    print(f"[FAIL] Campos faltantes: {missing_fields}")

                # Verificar opciones de recurrencia
                recurrence_select = soup.find('select', {'name': 'recurrence_type'})
                if recurrence_select:
                    options = recurrence_select.find_all('option')
                    if len(options) >= 3:  # weekly, daily, custom
                        print("[PASS] Opciones de recurrencia disponibles")
                    else:
                        print(f"[WARN] Pocas opciones de recurrencia: {len(options)}")
                else:
                    print("[FAIL] Select de recurrencia no encontrado")

            else:
                print("[FAIL] Formulario no encontrado")
        else:
            print(f"[FAIL] Error al cargar formulario: {response.status_code}")

    except Exception as e:
        print(f"[ERROR] Error en la prueba: {str(e)}")

    print("\n" + "="*80)
    print("VERIFICACIÓN COMPLETA FINALIZADA")
    print("="*80)

if __name__ == "__main__":
    test_form_functionality()