#!/usr/bin/env python3
"""
Script para probar validación de formulario TaskScheduleForm
Captura logs de errores de cada campo del formulario
"""

import requests
import json
from datetime import datetime, timedelta

# Configuración
BASE_URL = "http://192.168.18.47:5000"
CREATE_URL = f"{BASE_URL}/events/tasks/schedules/create/"
LOGIN_URL = f"{BASE_URL}/accounts/login/"

# Credenciales (ajusta según tu configuración)
USERNAME = "admin"
PASSWORD = "admin123"  # Ajusta según tu configuración

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

    # Verificar si el login fue exitoso (debería redirigir a dashboard o home)
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

def test_field_validation():
    """Prueba validación de cada campo del formulario"""

    session = login_and_get_session()
    if not session:
        return

    csrf_token = get_csrf_token(session, CREATE_URL)
    if not csrf_token:
        print("ERROR: No se pudo obtener CSRF token del formulario")
        return

    # Datos base válidos
    base_data = {
        'csrfmiddlewaretoken': csrf_token,
        'task': '1',  # Asumiendo que existe una tarea con ID 1
        'recurrence_type': 'weekly',
        'monday': 'on',
        'start_time': '09:00',
        'start_date': '2025-01-01',
        'end_date': '2025-12-31',
        'is_active': 'on',
        'duration_hours': '1.0'
    }

    # Pruebas de validación por campo
    test_cases = [
        # Campo: task
        {
            'name': 'task',
            'description': 'Campo requerido - valor vacío',
            'data': {**base_data, 'task': ''},
            'expected_error': 'Este campo es obligatorio'
        },
        {
            'name': 'task',
            'description': 'Campo requerido - valor inválido',
            'data': {**base_data, 'task': '99999'},
            'expected_error': 'Selecciona una opción válida'
        },

        # Campo: recurrence_type
        {
            'name': 'recurrence_type',
            'description': 'Valor inválido',
            'data': {**base_data, 'recurrence_type': 'invalid'},
            'expected_error': 'Selecciona una opción válida'
        },

        # Campo: start_time
        {
            'name': 'start_time',
            'description': 'Formato inválido',
            'data': {**base_data, 'start_time': '25:00'},
            'expected_error': 'Introduzca una hora válida'
        },
        {
            'name': 'start_time',
            'description': 'Valor vacío',
            'data': {**base_data, 'start_time': ''},
            'expected_error': 'Este campo es obligatorio'
        },

        # Campo: start_date
        {
            'name': 'start_date',
            'description': 'Fecha en el pasado',
            'data': {**base_data, 'start_date': '2020-01-01'},
            'expected_error': 'La fecha de inicio debe ser futura o actual'
        },
        {
            'name': 'start_date',
            'description': 'Formato inválido',
            'data': {**base_data, 'start_date': 'invalid-date'},
            'expected_error': 'Introduzca una fecha válida'
        },
        {
            'name': 'start_date',
            'description': 'Valor vacío',
            'data': {**base_data, 'start_date': ''},
            'expected_error': 'Este campo es obligatorio'
        },

        # Campo: end_date
        {
            'name': 'end_date',
            'description': 'Fecha anterior a start_date',
            'data': {**base_data, 'start_date': '2025-12-31', 'end_date': '2025-01-01'},
            'expected_error': 'La fecha de fin debe ser posterior a la fecha de inicio'
        },

        # Campo: duration_hours
        {
            'name': 'duration_hours',
            'description': 'Valor negativo',
            'data': {**base_data, 'duration_hours': '-1'},
            'expected_error': 'Asegúrese de que este valor sea mayor o igual a 0.25'
        },
        {
            'name': 'duration_hours',
            'description': 'Valor mayor a 24',
            'data': {**base_data, 'duration_hours': '25'},
            'expected_error': 'Asegúrese de que este valor sea menor o igual a 24'
        },
        {
            'name': 'duration_hours',
            'description': 'Valor no numérico',
            'data': {**base_data, 'duration_hours': 'abc'},
            'expected_error': 'Introduzca un número'
        },
        {
            'name': 'duration_hours',
            'description': 'Valor vacío',
            'data': {**base_data, 'duration_hours': ''},
            'expected_error': 'Este campo es obligatorio'
        },

        # Validación específica: recurrencia semanal sin días seleccionados
        {
            'name': 'recurrence_weekly_validation',
            'description': 'Recurrencia semanal sin días seleccionados',
            'data': {
                **base_data,
                'recurrence_type': 'weekly',
                'monday': '',
                'tuesday': '',
                'wednesday': '',
                'thursday': '',
                'friday': '',
                'saturday': '',
                'sunday': ''
            },
            'expected_error': 'Debes seleccionar al menos un día de la semana'
        }
    ]

    print("\n" + "="*80)
    print("INICIANDO PRUEBAS DE VALIDACIÓN DEL FORMULARIO TaskScheduleForm")
    print("="*80)

    results = []

    for i, test_case in enumerate(test_cases, 1):
        print(f"\n[{i}/{len(test_cases)}] Probando: {test_case['name']} - {test_case['description']}")

        try:
            response = session.post(CREATE_URL, data=test_case['data'], headers={
                'Referer': CREATE_URL
            })

            # Verificar si hay errores en el formulario
            if response.status_code == 200:
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(response.text, 'html.parser')

                # Buscar errores de formulario
                error_divs = soup.find_all('div', class_='invalid-feedback')
                error_lists = soup.find_all('ul', class_='errorlist')

                errors_found = []

                # Errores en divs invalid-feedback
                for error_div in error_divs:
                    if error_div.text.strip():
                        errors_found.append(error_div.text.strip())

                # Errores en ul.errorlist
                for error_list in error_lists:
                    for li in error_list.find_all('li'):
                        if li.text.strip():
                            errors_found.append(li.text.strip())

                # Errores en alertas de Django (alert alert-danger)
                alerts = soup.find_all('div', class_='alert-danger')
                for alert in alerts:
                    alert_text = alert.get_text().strip()
                    if alert_text:
                        # Remover el texto del icono si existe
                        if alert_text.startswith(''):
                            alert_text = alert_text[1:].strip()
                        errors_found.append(alert_text)

                if errors_found:
                    print(f"[PASS] Errores encontrados: {len(errors_found)}")
                    for error in errors_found:
                        print(f"  - {error}")

                    results.append({
                        'test': f"{test_case['name']} - {test_case['description']}",
                        'status': 'PASS',
                        'errors': errors_found
                    })
                else:
                    print("[FAIL] No se encontraron errores esperados")
                    results.append({
                        'test': f"{test_case['name']} - {test_case['description']}",
                        'status': 'FAIL',
                        'errors': []
                    })

            else:
                print(f"[ERROR] Error HTTP: {response.status_code}")
                results.append({
                    'test': f"{test_case['name']} - {test_case['description']}",
                    'status': 'ERROR',
                    'errors': [f'HTTP {response.status_code}']
                })

        except Exception as e:
            print(f"[ERROR] Error en la prueba: {str(e)}")
            results.append({
                'test': f"{test_case['name']} - {test_case['description']}",
                'status': 'ERROR',
                'errors': [str(e)]
            })

    # Resumen final
    print("\n" + "="*80)
    print("RESUMEN DE PRUEBAS")
    print("="*80)

    passed = sum(1 for r in results if r['status'] == 'PASS')
    failed = sum(1 for r in results if r['status'] == 'FAIL')
    errors = sum(1 for r in results if r['status'] == 'ERROR')

    print(f"Total de pruebas: {len(results)}")
    print(f"Pasaron: {passed}")
    print(f"Fallaron: {failed}")
    print(f"Errores: {errors}")

    # Mostrar detalles de cada prueba
    print("\nDETALLE DE RESULTADOS:")
    for result in results:
        status_icon = "[PASS]" if result['status'] == 'PASS' else "[FAIL]" if result['status'] == 'FAIL' else "[ERROR]"
        print(f"{status_icon} {result['test']}")
        if result['errors']:
            for error in result['errors']:
                print(f"    - {error}")

    # Guardar resultados en archivo JSON
    with open('form_validation_results.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print("\nResultados guardados en 'form_validation_results.json'")
if __name__ == "__main__":
    test_field_validation()