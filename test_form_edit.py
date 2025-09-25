#!/usr/bin/env python3
"""
Script para probar edición exitosa de una programación de tarea
Verifica que el formulario de edición funcione correctamente con datos válidos
"""

import requests
import json
from datetime import datetime, timedelta

# Configuración
BASE_URL = "http://127.0.0.1:5000"
EDIT_URL = f"{BASE_URL}/events/tasks/schedules/42/edit/"
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

def get_current_form_data(session):
    """Obtiene los datos actuales del formulario de edición"""
    response = session.get(EDIT_URL)
    if response.status_code != 200:
        print(f"[ERROR] No se pudo acceder al formulario de edición: {response.status_code}")
        return None

    from bs4 import BeautifulSoup
    soup = BeautifulSoup(response.text, 'html.parser')

    # Extraer CSRF token
    csrf_input = soup.find('input', {'name': 'csrfmiddlewaretoken'})
    csrf_token = csrf_input['value'] if csrf_input else None

    if not csrf_token:
        print("[ERROR] No se pudo obtener CSRF token del formulario de edición")
        return None

    # Extraer valores actuales de los campos
    form_data = {
        'csrfmiddlewaretoken': csrf_token
    }

    # Task
    task_select = soup.find('select', {'id': 'id_task'})
    if task_select:
        selected_option = task_select.find('option', selected=True)
        if selected_option:
            form_data['task'] = selected_option.get('value')

    # Recurrence type
    recurrence_select = soup.find('select', {'id': 'id_recurrence_type'})
    if recurrence_select:
        selected_option = recurrence_select.find('option', selected=True)
        if selected_option:
            form_data['recurrence_type'] = selected_option.get('value')

    # Start time
    start_time_input = soup.find('input', {'id': 'id_start_time'})
    if start_time_input:
        form_data['start_time'] = start_time_input.get('value', '')

    # Duration
    duration_input = soup.find('input', {'id': 'id_duration_hours'})
    if duration_input:
        form_data['duration_hours'] = duration_input.get('value', '1.0')

    # Start date
    start_date_input = soup.find('input', {'id': 'id_start_date'})
    if start_date_input:
        form_data['start_date'] = start_date_input.get('value', '')

    # End date
    end_date_input = soup.find('input', {'id': 'id_end_date'})
    if end_date_input:
        form_data['end_date'] = end_date_input.get('value', '')

    # Is active
    is_active_input = soup.find('input', {'id': 'id_is_active'})
    if is_active_input:
        form_data['is_active'] = 'on' if is_active_input.get('checked') else ''

    # Days (for weekly)
    days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
    for day in days:
        day_input = soup.find('input', {'id': f'id_{day}'})
        if day_input and day_input.get('checked'):
            form_data[day] = 'on'

    print(f"[OK] Datos actuales del formulario obtenidos: {json.dumps(form_data, indent=2)}")
    return form_data

def test_successful_edit():
    """Prueba edición exitosa de una programación"""

    session = login_and_get_session()
    if not session:
        return

    # Obtener datos actuales del formulario
    current_data = get_current_form_data(session)
    if not current_data:
        print("[ERROR] No se pudieron obtener los datos actuales del formulario")
        return

    print("\n" + "="*80)
    print("PRUEBA DE EDICIÓN EXITOSA DE PROGRAMACIÓN")
    print("="*80)

    # Modificar algunos valores para la edición
    updated_data = current_data.copy()

    # Cambiar la hora de inicio (ejemplo: sumar 1 hora)
    if 'start_time' in updated_data and updated_data['start_time']:
        # Handle different time formats
        time_str = updated_data['start_time']
        if 'a.m.' in time_str or 'p.m.' in time_str:
            # Convert from "9 a.m." format to 24-hour format
            if 'a.m.' in time_str:
                hour = int(time_str.split(' ')[0])
                if hour == 12:
                    hour = 0
            else:  # p.m.
                hour = int(time_str.split(' ')[0])
                if hour != 12:
                    hour += 12
            updated_data['start_time'] = f"{hour:02d}:00"
        else:
            # Assume it's already in HH:MM format
            current_time = datetime.strptime(time_str, '%H:%M').time()
            new_time = datetime.combine(datetime.today(), current_time) + timedelta(hours=1)
            updated_data['start_time'] = new_time.strftime('%H:%M')
        print(f"[INFO] Cambiando hora de inicio de {current_data['start_time']} a {updated_data['start_time']}")

    # Cambiar duración (ejemplo: aumentar en 0.5 horas)
    if 'duration_hours' in updated_data:
        current_duration = float(updated_data['duration_hours'])
        updated_data['duration_hours'] = str(current_duration + 0.5)
        print(f"[INFO] Cambiando duración de {current_data['duration_hours']} a {updated_data['duration_hours']} horas")

    # Cambiar días si es semanal (ejemplo: agregar o quitar un día)
    if updated_data.get('recurrence_type') == 'weekly':
        if 'wednesday' not in updated_data:  # Si no está marcado miércoles, marcarlo
            updated_data['wednesday'] = 'on'
            print("[INFO] Agregando miércoles a los días seleccionados")
        elif 'monday' in updated_data:  # Si está monday, quitarlo
            del updated_data['monday']
            print("[INFO] Removiendo lunes de los días seleccionados")

    # Cambiar fecha de fin (ejemplo: extender una semana)
    if 'end_date' in updated_data and updated_data['end_date']:
        # Handle localized date formats
        date_str = updated_data['end_date']
        try:
            # Try standard format first
            current_end = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            # Try localized format like "Oct. 3, 2025" - handle abbreviated month names
            # Remove the dot after abbreviated month names
            date_str = date_str.replace('Sept.', 'Sep.').replace('Oct.', 'Oct.').replace('Nov.', 'Nov.').replace('Dec.', 'Dec.')
            current_end = datetime.strptime(date_str, '%b. %d, %Y').date()
        new_end = current_end + timedelta(days=7)
        updated_data['end_date'] = new_end.strftime('%Y-%m-%d')
        print(f"[INFO] Extendiendo fecha de fin de {current_data['end_date']} a {updated_data['end_date']}")

    # Also handle start_date if needed
    if 'start_date' in updated_data and updated_data['start_date']:
        date_str = updated_data['start_date']
        try:
            # Try standard format first
            current_start = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            # Try localized format like "Sept. 26, 2025" - handle abbreviated month names
            # Remove the dot after abbreviated month names
            date_str = date_str.replace('Sept.', 'Sep.').replace('Oct.', 'Oct.').replace('Nov.', 'Nov.').replace('Dec.', 'Dec.')
            current_start = datetime.strptime(date_str, '%b. %d, %Y').date()
        updated_data['start_date'] = current_start.strftime('%Y-%m-%d')

    print(f"Datos a enviar para edición: {json.dumps(updated_data, indent=2)}")

    try:
        response = session.post(EDIT_URL, data=updated_data, headers={
            'Referer': EDIT_URL
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
                    print("[SUCCESS] Programación editada exitosamente")
                    print(f"Redirigido a: {response.url}")

                    # Extraer ID de la programación si está en la URL
                    if 'schedule_id' in response.url:
                        schedule_id = response.url.split('schedule_id=')[1].split('&')[0]
                        print(f"ID de programación editada: {schedule_id}")

                    return True
                else:
                    print("[WARNING] No se detectó redirección a página de detalle")
                    print("Contenido de la página:")
                    print(response.text[:500] + "..." if len(response.text) > 500 else response.text)
                    return False
        else:
            print(f"[ERROR] Error HTTP: {response.status_code}")
            print("Respuesta del servidor:")
            print(response.text[:1000] + "..." if len(response.text) > 1000 else response.text)
            return False

    except Exception as e:
        print(f"[ERROR] Error en la prueba: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_successful_edit()
    if success:
        print("\n[SUCCESS] PRUEBA EXITOSA: El formulario de edición funciona correctamente")
    else:
        print("\n[FAILED] PRUEBA FALLIDA: Hay problemas con el formulario de edición")