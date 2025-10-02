#!/usr/bin/env python3
"""
Script de prueba mejorado para simular la petición POST de vinculación a tarea existente
con autenticación completa
"""
import requests
import json
import re
from bs4 import BeautifulSoup
from datetime import datetime

# Configuración de la prueba
BASE_URL = "http://192.168.18.47:5000"
INBOX_ITEM_ID = 115
TASK_ID = 1  # ID de una tarea existente para probar

# Credenciales de prueba (deben existir en el sistema)
USERNAME = "testuser"  # Cambiar por usuario válido
PASSWORD = "testpass"  # Cambiar por contraseña válida

class AuthenticatedSession:
    """Clase para manejar sesiones autenticadas con Django"""

    def __init__(self, base_url):
        self.base_url = base_url
        self.session = requests.Session()
        self.csrf_token = None

    def login(self, username, password):
        """Realizar login y obtener cookies de sesión"""
        print(f"Intentando login con usuario: {username}")

        # 1. Obtener página de login para CSRF token
        login_url = f"{self.base_url}/accounts/login/"
        response = self.session.get(login_url)

        if response.status_code != 200:
            print(f"Error al acceder a pagina de login: {response.status_code}")
            return False

        # 2. Extraer CSRF token
        soup = BeautifulSoup(response.text, 'html.parser')
        csrf_input = soup.find('input', {'name': 'csrfmiddlewaretoken'})

        if not csrf_input:
            print("No se encontro token CSRF en pagina de login")
            return False

        csrf_token = csrf_input['value']
        print(f"Token CSRF obtenido: {csrf_token[:20]}...")

        # 3. Hacer POST de login
        login_data = {
            'username': username,
            'password': password,
            'csrfmiddlewaretoken': csrf_token
        }

        headers = {
            'Referer': login_url,
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

        response = self.session.post(
            login_url,
            data=login_data,
            headers=headers,
            allow_redirects=True
        )

        # 4. Verificar si login fue exitoso
        if response.status_code == 200 and 'logout' in response.text.lower():
            print("Login exitoso!")
            self.csrf_token = csrf_token
            return True
        else:
            print(f"Error en login. Codigo: {response.status_code}")
            print(f"Respuesta: {response.text[:200]}...")
            return False

    def get_csrf_token_from_page(self, url):
        """Obtener CSRF token de cualquier página"""
        response = self.session.get(url)

        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            csrf_input = soup.find('input', {'name': 'csrfmiddlewaretoken'})
            if csrf_input:
                return csrf_input['value']

        return None

def test_authenticated_request():
    """Prueba con sesión autenticada completa"""

    # Crear sesión autenticada
    auth_session = AuthenticatedSession(BASE_URL)

    # Intentar login
    if not auth_session.login(USERNAME, PASSWORD):
        print("No se pudo autenticar. Verifica credenciales.")
        return

    print("Sesion autenticada correctamente")

    # URL del endpoint
    url = f"{BASE_URL}/events/inbox/process/{INBOX_ITEM_ID}/"

    # Datos del formulario
    form_data = {
        'action': 'link_to_task',
        'task_id': str(TASK_ID),
    }

    # Headers para simular petición del navegador
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Referer': url,
        'X-Requested-With': 'XMLHttpRequest'
    }

    print(f"\nProbando vinculacion autenticada del item {INBOX_ITEM_ID} a la tarea {TASK_ID}")
    print(f"URL: {url}")
    print(f"Datos del formulario: {form_data}")
    print("-" * 60)

    try:
        # Hacer la petición POST autenticada
        response = auth_session.session.post(
            url,
            data=form_data,
            headers=headers,
            allow_redirects=False
        )

        print(f"Codigo de respuesta: {response.status_code}")
        print(f"URL final: {response.url}")
        print(f"Redirects: {len(response.history)}")

        if response.history:
            for i, resp in enumerate(response.history):
                print(f"   {i+1}. {resp.status_code} -> {resp.headers.get('Location', 'N/A')}")

        print(f"\nContenido de la respuesta (primeros 500 caracteres):")
        content = response.text[:500]
        print(f"   {content}")
        if len(response.text) > 500:
            print(f"   ... (total: {len(response.text)} caracteres)")

        # Analizar la respuesta
        if response.status_code == 302:  # Redirect
            location = response.headers.get('Location', '')
            print(f"\nRedireccion detectada: {location}")

            if 'tasks' in location and str(TASK_ID) in location:
                print("EXITO: La vinculacion fue exitosa!")
            else:
                print("INFO: Redireccion a diferente ubicacion")

        elif response.status_code == 200:
            print("\nRespuesta 200 - posiblemente mostrando formulario con errores")

            # Buscar mensajes de error en el HTML
            if 'No tienes permisos' in response.text:
                print("ERROR: Error de permisos detectado")
            elif 'Debe seleccionar una tarea' in response.text:
                print("ERROR: Error de validacion: tarea no seleccionada")
            elif 'ID de tarea invalido' in response.text:
                print("ERROR: Error de validacion: ID de tarea invalido")
            elif 'tarea objetivo no existe' in response.text:
                print("ERROR: La tarea objetivo no existe")
            elif 'Error al vincular' in response.text:
                print("ERROR: Error general al vincular")
            else:
                print("INFO: Otro tipo de respuesta 200")

        elif response.status_code == 403:
            print("\nERROR 403 - Prohibido (problema de permisos)")
        elif response.status_code == 404:
            print("\nERROR 404 - Pagina no encontrada")
        elif response.status_code == 500:
            print("\nERROR 500 - Error interno del servidor")
        else:
            print(f"\nCODIGO INESPERADO: {response.status_code}")

    except requests.exceptions.ConnectionError:
        print("\nError de conexion - Esta el servidor corriendo?")
    except requests.exceptions.Timeout:
        print("\nTimeout - El servidor tardo demasiado en responder")
    except Exception as e:
        print(f"\nError inesperado: {e}")

def test_get_tasks_api_authenticated():
    """Prueba el endpoint de la API con autenticación"""

    auth_session = AuthenticatedSession(BASE_URL)

    if not auth_session.login(USERNAME, PASSWORD):
        print("No se pudo autenticar para probar API")
        return

    url = f"{BASE_URL}/events/inbox/api/tasks/"

    headers = {
        'X-Requested-With': 'XMLHttpRequest',
        'Content-Type': 'application/json',
    }

    print(f"\nProbando API de tareas con autenticacion: {url}")

    try:
        response = auth_session.session.get(url, headers=headers)

        print(f"Codigo de respuesta: {response.status_code}")

        if response.status_code == 200:
            try:
                data = response.json()
                print("EXITO: API respondio correctamente")
                print(f"Numero de tareas: {data.get('total', 0)}")
                print(f"Estado: {data.get('success', False)}")

                if data.get('tasks'):
                    print("Primeras tareas encontradas:")
                    for i, task in enumerate(data['tasks'][:3]):
                        print(f"   {i+1}. {task.get('title', 'Sin titulo')} (ID: {task.get('id')})")
                else:
                    print("No se encontraron tareas disponibles")
            except json.JSONDecodeError:
                print("ERROR: La respuesta no es JSON valido")
                print(f"Contenido: {response.text[:200]}")
        else:
            print(f"ERROR en la API: {response.status_code}")
            print(f"Respuesta: {response.text[:200]}")

    except Exception as e:
        print(f"Error al probar la API: {e}")

def test_inbox_item_access():
    """Probar acceso al item del inbox específico"""

    auth_session = AuthenticatedSession(BASE_URL)

    if not auth_session.login(USERNAME, PASSWORD):
        print("No se pudo autenticar para probar acceso")
        return

    url = f"{BASE_URL}/events/inbox/process/{INBOX_ITEM_ID}/"

    print(f"\nProbando acceso al item {INBOX_ITEM_ID}: {url}")

    try:
        response = auth_session.session.get(url)

        print(f"Codigo de respuesta: {response.status_code}")

        if response.status_code == 200:
            print("EXITO: Acceso permitido al item del inbox")

            # Verificar si el item existe
            if f'#{INBOX_ITEM_ID}' in response.text:
                print("El item del inbox existe y es accesible")
            else:
                print("El item del inbox no existe o no es visible")

        elif response.status_code == 404:
            print("ERROR: Item del inbox no encontrado")
        elif response.status_code == 403:
            print("ERROR: Acceso denegado al item del inbox")
        else:
            print(f"ERROR inesperado: {response.status_code}")

    except Exception as e:
        print(f"Error al probar acceso: {e}")

if __name__ == "__main__":
    print("Iniciando pruebas avanzadas de vinculacion a tarea existente")
    print("=" * 70)

    # Probar acceso básico primero
    test_inbox_item_access()

    # Probar API con autenticación
    test_get_tasks_api_authenticated()

    # Probar vinculación con autenticación completa
    test_authenticated_request()

    print("\n" + "=" * 70)
    print("Pruebas completadas")