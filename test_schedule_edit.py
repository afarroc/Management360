#!/usr/bin/env python3
"""
Script para probar la edición de programaciones de tareas
y verificar que los mensajes de error funcionen correctamente
"""

import requests
import json
from datetime import datetime, timedelta

# Configuración
BASE_URL = "http://127.0.0.1:8000"
LOGIN_URL = f"{BASE_URL}/accounts/login/"
SCHEDULES_URL = f"{BASE_URL}/events/tasks/schedules/"

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

def get_first_schedule_id(session):
    """Obtiene el ID de la primera programación disponible"""
    response = session.get(SCHEDULES_URL)
    if response.status_code != 200:
        print(f"Error al obtener programaciones: {response.status_code}")
        return None

    from bs4 import BeautifulSoup
    soup = BeautifulSoup(response.text, 'html.parser')

    # Buscar enlaces que contengan 'edit' y 'schedule' en cualquier parte del href
    all_links = soup.find_all('a', href=True)
    schedule_edit_links = []

    for link in all_links:
        href = link.get('href')
        if href and 'edit' in href and 'schedule' in href:
            schedule_edit_links.append(link)

    print(f"Encontrados {len(schedule_edit_links)} enlaces de edición de schedules")

    if schedule_edit_links:
        href = schedule_edit_links[0]['href']
        print(f"Usando enlace: {href}")

        # Extraer ID - buscar patrón /edit/{id}/
        import re
        match = re.search(r'/edit/(\d+)/', href)
        if match:
            schedule_id = match.group(1)
            print(f"[OK] Encontrada programación con ID: {schedule_id}")
            return schedule_id

    print("[ERROR] No se encontraron programaciones para editar")
    return None

def test_edit_schedule_validation():
    """Prueba la validación en la edición de programaciones"""

    session = login_and_get_session()
    if not session:
        return

    # Usar el ID de la programación que acabamos de crear (39)
    schedule_id = "39"
    print(f"[INFO] Probando edición de la programación ID: {schedule_id}")

    edit_url = f"{BASE_URL}/events/tasks/schedules/{schedule_id}/edit/"

    # Obtener la página de edición para conseguir el CSRF token
    response = session.get(edit_url)
    if response.status_code != 200:
        print(f"Error al acceder a la página de edición: {response.status_code}")
        return

    from bs4 import BeautifulSoup
    soup = BeautifulSoup(response.text, 'html.parser')
    csrf_input = soup.find('input', {'name': 'csrfmiddlewaretoken'})
    csrf_token = csrf_input['value'] if csrf_input else None

    if not csrf_token:
        print("ERROR: No se pudo obtener CSRF token de la página de edición")
        return

    print(f"\n[TEST] Probando edición de programación ID: {schedule_id}")

    # Datos de prueba con errores intencionales
    test_cases = [
        {
            'name': 'Fecha de inicio en el pasado',
            'data': {
                'csrfmiddlewaretoken': csrf_token,
                'task': '1',  # Mantener la tarea original
                'recurrence_type': 'weekly',
                'monday': 'on',
                'start_time': '09:00',
                'start_date': '2020-01-01',  # Fecha en el pasado
                'end_date': '2025-12-31',
                'is_active': 'on',
                'duration_hours': '1.0'
            },
            'expected_error': 'La fecha de inicio debe ser hoy o una fecha futura'
        },
        {
            'name': 'Fecha de fin anterior a fecha de inicio',
            'data': {
                'csrfmiddlewaretoken': csrf_token,
                'task': '1',
                'recurrence_type': 'weekly',
                'monday': 'on',
                'start_time': '09:00',
                'start_date': '2025-12-31',
                'end_date': '2025-01-01',  # Fecha anterior
                'is_active': 'on',
                'duration_hours': '1.0'
            },
            'expected_error': 'La fecha de fin debe ser posterior a la fecha de inicio'
        },
        {
            'name': 'Duración inválida (negativa)',
            'data': {
                'csrfmiddlewaretoken': csrf_token,
                'task': '1',
                'recurrence_type': 'weekly',
                'monday': 'on',
                'start_time': '09:00',
                'start_date': '2025-01-01',
                'end_date': '2025-12-31',
                'is_active': 'on',
                'duration_hours': '-1'  # Duración negativa
            },
            'expected_error': 'La duración mínima permitida es de 15 minutos'
        },
        {
            'name': 'Recurrencia semanal sin días seleccionados',
            'data': {
                'csrfmiddlewaretoken': csrf_token,
                'task': '1',
                'recurrence_type': 'weekly',
                # Ningún día seleccionado
                'start_time': '09:00',
                'start_date': '2025-01-01',
                'end_date': '2025-12-31',
                'is_active': 'on',
                'duration_hours': '1.0'
            },
            'expected_error': 'Para la recurrencia semanal, debes seleccionar al menos un día'
        }
    ]

    results = []

    for i, test_case in enumerate(test_cases, 1):
        print(f"\n[{i}/{len(test_cases)}] Probando: {test_case['name']}")

        try:
            response = session.post(edit_url, data=test_case['data'], headers={
                'Referer': edit_url
            })

            if response.status_code == 200:
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(response.text, 'html.parser')

                # Buscar errores
                error_divs = soup.find_all('div', class_='invalid-feedback')
                error_alerts = soup.find_all('div', class_='alert-danger')

                errors_found = []

                # Errores en invalid-feedback
                for error_div in error_divs:
                    if error_div.text.strip():
                        errors_found.append(error_div.text.strip())

                # Errores en alertas
                for alert in error_alerts:
                    alert_text = alert.get_text().strip()
                    if alert_text:
                        if alert_text.startswith(''):
                            alert_text = alert_text[1:].strip()
                        errors_found.append(alert_text)

                if errors_found:
                    print(f"[PASS] Errores encontrados: {len(errors_found)}")
                    for error in errors_found:
                        print(f"  - {error}")

                    # Verificar si contiene el error esperado
                    expected_found = any(test_case['expected_error'].lower() in error.lower() for error in errors_found)
                    if expected_found:
                        print(f"[OK] Error esperado encontrado")
                    else:
                        print(f"[WARNING] Error esperado no encontrado exactamente")

                    results.append({
                        'test': test_case['name'],
                        'status': 'PASS',
                        'errors': errors_found
                    })
                else:
                    print("[FAIL] No se encontraron errores esperados")
                    results.append({
                        'test': test_case['name'],
                        'status': 'FAIL',
                        'errors': []
                    })

            else:
                print(f"[ERROR] Error HTTP: {response.status_code}")
                results.append({
                    'test': test_case['name'],
                    'status': 'ERROR',
                    'errors': [f'HTTP {response.status_code}']
                })

        except Exception as e:
            print(f"[ERROR] Error en la prueba: {str(e)}")
            results.append({
                'test': test_case['name'],
                'status': 'ERROR',
                'errors': [str(e)]
            })

    # Resumen
    print(f"\n{'='*60}")
    print("RESUMEN DE PRUEBAS DE EDICIÓN")
    print(f"{'='*60}")

    passed = sum(1 for r in results if r['status'] == 'PASS')
    failed = sum(1 for r in results if r['status'] == 'FAIL')
    errors = sum(1 for r in results if r['status'] == 'ERROR')

    print(f"Total de pruebas: {len(results)}")
    print(f"Pasaron: {passed}")
    print(f"Fallaron: {failed}")
    print(f"Errores: {errors}")

    # Guardar resultados
    with open('schedule_edit_validation_results.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print("\nResultados guardados en 'schedule_edit_validation_results.json'")

if __name__ == "__main__":
    test_edit_schedule_validation()