#!/usr/bin/env python3
import requests
import json
from bs4 import BeautifulSoup

BASE_URL = "http://192.168.18.47:5000"
USERNAME = "arturo"
PASSWORD = "Peru+123"
INBOX_ITEM_ID = 115

def main():
    print("PRUEBA COMO USUARIO ARTURO")
    print("=========================")

    # Crear sesion
    session = requests.Session()

    # 1. Obtener pagina de login
    print("1. Obteniendo pagina de login...")
    login_url = f"{BASE_URL}/accounts/login/"
    response = session.get(login_url)
    print(f"   Status: {response.status_code}")

    if response.status_code != 200:
        print("ERROR: No se pudo acceder al login")
        return

    # 2. Extraer CSRF token
    print("2. Extrayendo token CSRF...")
    soup = BeautifulSoup(response.text, 'html.parser')
    csrf_input = soup.find('input', {'name': 'csrfmiddlewaretoken'})

    if not csrf_input:
        print("ERROR: No se encontro token CSRF")
        return

    csrf_token = csrf_input['value']
    print(f"   Token: {csrf_token[:20]}...")

    # 3. Hacer login
    print("3. Intentando login...")
    login_data = {
        'username': USERNAME,
        'password': PASSWORD,
        'csrfmiddlewaretoken': csrf_token
    }

    response = session.post(login_url, data=login_data, allow_redirects=True)
    print(f"   Login status: {response.status_code}")

    if not (response.status_code == 200 and 'logout' in response.text.lower()):
        print("ERROR: Login fallido")
        return

    print("   EXITO: Login correcto")

    # 4. Probar acceso al inbox
    print("4. Probando acceso al inbox...")
    inbox_url = f"{BASE_URL}/events/inbox/"
    response = session.get(inbox_url)
    print(f"   Inbox status: {response.status_code}")

    # 5. Probar acceso al item
    print(f"5. Probando acceso al item {INBOX_ITEM_ID}...")
    item_url = f"{BASE_URL}/events/inbox/process/{INBOX_ITEM_ID}/"
    response = session.get(item_url)
    print(f"   Item status: {response.status_code}")

    if response.status_code == 200:
        print("   EXITO: Item accesible")

        # Verificar si contiene elementos clave
        if 'Panel de Control del Inbox' in response.text:
            print("   Panel de control encontrado")
        else:
            print("   Panel de control NO encontrado")

        if 'Vincular a Tarea Existente' in response.text:
            print("   Boton de vincular tarea encontrado")
        else:
            print("   Boton de vincular tarea NO encontrado")

    elif response.status_code == 404:
        print("   ERROR: Item no encontrado")
    elif response.status_code == 403:
        print("   ERROR: Acceso denegado")
    else:
        print(f"   ERROR: Status inesperado {response.status_code}")

    # 6. Probar API de tareas
    print("6. Probando API de tareas...")
    api_url = f"{BASE_URL}/events/inbox/api/tasks/"
    response = session.get(api_url, headers={'X-Requested-With': 'XMLHttpRequest'})
    print(f"   API status: {response.status_code}")

    if response.status_code == 200:
        try:
            data = response.json()
            if data.get('success'):
                print(f"   EXITO: {data.get('total', 0)} tareas disponibles")
            else:
                print(f"   ERROR: {data.get('error')}")
        except:
            print("   ERROR: Respuesta no es JSON")
    else:
        print("   ERROR: API no accesible")

    print("\nRESUMEN:")
    print("========")
    print("Si el item es accesible y contiene el panel de control,")
    print("entonces la solucion implementada esta funcionando.")
    print("El usuario 'arturo' deberia poder usar el boton 'Vincular a Tarea Existente'")

if __name__ == "__main__":
    main()