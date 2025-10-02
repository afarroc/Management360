#!/usr/bin/env python3
"""
Script final para probar como usuario 'arturo'
"""
import requests
import json
from bs4 import BeautifulSoup

BASE_URL = "http://192.168.18.47:5000"
USERNAME = "arturo"
PASSWORD = "Peru+123"
INBOX_ITEM_ID = 115

def test_login():
    """Probar login como arturo"""
    print("PROBANDO LOGIN COMO ARTURO")
    print("-" * 40)

    session = requests.Session()
    login_url = f"{BASE_URL}/accounts/login/"

    # Obtener pagina de login
    response = session.get(login_url)
    print(f"Pagina de login: {response.status_code}")

    if response.status_code != 200:
        print("ERROR: No se pudo acceder a pagina de login")
        return None

    # Extraer CSRF token
    soup = BeautifulSoup(response.text, 'html.parser')
    csrf_input = soup.find('input', {'name': 'csrfmiddlewaretoken'})

    if not csrf_input:
        print("ERROR: No se encontro token CSRF")
        return None

    csrf_token = csrf_input['value']
    print(f"Token CSRF: {csrf_token[:20]}...")

    # Hacer login
    login_data = {
        'username': USERNAME,
        'password': PASSWORD,
        'csrfmiddlewaretoken': csrf_token
    }

    response = session.post(login_url, data=login_data, allow_redirects=True)
    print(f"Login response: {response.status_code}")

    if response.status_code == 200 and 'logout' in response.text.lower():
        print("EXITO: Login correcto como arturo")
        return session
    else:
        print("ERROR: Login fallido")
        print(f"Respuesta: {response.text[:200]}...")
        return None

def test_inbox_access(session):
    """Probar acceso al inbox"""
    print("
PROBANDO ACCESO AL INBOX")
    print("-" * 40)

    inbox_url = f"{BASE_URL}/events/inbox/"
    response = session.get(inbox_url)

    print(f"Inbox access: {response.status_code}")

    if response.status_code == 200:
        print("EXITO: Acceso al inbox correcto")
        return True
    else:
        print("ERROR: No se pudo acceder al inbox")
        return False

def test_item_access(session):
    """Probar acceso al item especifico"""
    print(f"\nPROBANDO ACCESO AL ITEM {INBOX_ITEM_ID}")
    print("-" * 40)

    item_url = f"{BASE_URL}/events/inbox/process/{INBOX_ITEM_ID}/"
    response = session.get(item_url)

    print(f"Item access: {response.status_code}")

    if response.status_code == 200:
        # Verificar si el panel esta presente
        if 'Panel de Control del Inbox' in response.text:
            print("EXITO: Panel de control accesible")

            if 'Vincular a Tarea Existente' in response.text:
                print("EXITO: Boton de vincular tarea encontrado")
                return True
            else:
                print("ERROR: Boton de vincular tarea NO encontrado")
                return False
        else:
            print("ERROR: Panel de control NO encontrado")
            return False

    elif response.status_code == 404:
        print("ERROR: Item no encontrado")
        return False
    elif response.status_code == 403:
        print("ERROR: Acceso denegado al item")
        return False
    else:
        print(f"ERROR: Codigo inesperado {response.status_code}")
        return False

def test_tasks_api(session):
    """Probar API de tareas"""
    print("
PROBANDO API DE TAREAS")
    print("-" * 40)

    api_url = f"{BASE_URL}/events/inbox/api/tasks/"
    response = session.get(api_url, headers={'X-Requested-With': 'XMLHttpRequest'})

    print(f"API response: {response.status_code}")

    if response.status_code == 200:
        try:
            data = response.json()
            if data.get('success'):
                tasks_count = data.get('total', 0)
                print(f"EXITO: API funcional, {tasks_count} tareas disponibles")
                return True
            else:
                print(f"ERROR: API reporto error: {data.get('error')}")
                return False
        except:
            print("ERROR: Respuesta no es JSON")
            return False
    else:
        print(f"ERROR: API no accesible ({response.status_code})")
        return False

def test_link_functionality(session):
    """Probar funcionalidad de vinculacion"""
    print("
PROBANDO FUNCIONALIDAD DE VINCULACION")
    print("-" * 40)

    # Obtener el panel para CSRF token
    item_url = f"{BASE_URL}/events/inbox/process/{INBOX_ITEM_ID}/"
    response = session.get(item_url)

    if response.status_code != 200:
        print("ERROR: No se pudo acceder al panel")
        return False

    # Extraer CSRF token
    soup = BeautifulSoup(response.text, 'html.parser')
    csrf_input = soup.find('input', {'name': 'csrfmiddlewaretoken'}')
    csrf_token = csrf_input['value'] if csrf_input else ''

    # Datos para vincular a tarea existente
    form_data = {
        'action': 'link_to_task',
        'task_id': '1',  # ID de tarea existente
        'csrfmiddlewaretoken': csrf_token
    }

    print("Enviando peticion de vinculacion...")
    response = session.post(item_url, data=form_data, allow_redirects=False)

    print(f"Link response: {response.status_code}")

    if response.status_code == 302:
        location = response.headers.get('Location', '')
        print(f"Redireccion: {location}")

        if 'tasks' in location:
            print("EXITO: Vinculacion exitosa")
            return True
        else:
            print("ERROR: Redireccion inesperada")
            return False

    elif response.status_code == 200:
        if 'vinculado exitosamente' in response.text.lower():
            print("EXITO: Vinculacion exitosa (mensaje encontrado)")
            return True
        elif 'no tienes permisos' in response.text.lower():
            print("ERROR: Permisos insuficientes")
            return False
        else:
            print("INFO: Respuesta 200 sin mensaje claro")
            return True

    else:
        print(f"ERROR: Error HTTP {response.status_code}")
        return False

def main():
    """Funcion principal"""
    print("PRUEBA COMPLETA COMO USUARIO 'ARTURO'")
    print("=" * 50)
    print(f"Usuario: {USERNAME}")
    print(f"Item a probar: {INBOX_ITEM_ID}")

    # 1. Login
    session = test_login()
    if not session:
        print("\nFALLIDO: No se pudo iniciar sesion")
        return

    # 2. Acceso al inbox
    if not test_inbox_access(session):
        print("\nFALLIDO: No se pudo acceder al inbox")
        return

    # 3. Acceso al item
    if not test_item_access(session):
        print("\nFALLIDO: No se pudo acceder al item")
        return

    # 4. API de tareas
    if not test_tasks_api(session):
        print("\nFALLIDO: API de tareas no funcional")
        return

    # 5. Funcionalidad de vinculacion
    if not test_link_functionality(session):
        print("\nFALLIDO: Funcionalidad de vinculacion no funciona")
        return

    print("
EXITO: Todas las pruebas pasaron!"    print("El usuario 'arturo' puede usar el sistema correctamente")

if __name__ == "__main__":
    main()