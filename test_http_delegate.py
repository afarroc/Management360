#!/usr/bin/env python
import requests
from bs4 import BeautifulSoup

# URL del servidor
base_url = 'http://192.168.18.47:5000'

# Crear una sesión para mantener las cookies
session = requests.Session()

print("=== TEST HTTP DE DELEGACIÓN DE ITEM INBOX ===")

# Paso 1: Obtener la página de login
print("\n1. Obteniendo página de login...")
login_url = f'{base_url}/accounts/login/'
response = session.get(login_url)
print(f"Status: {response.status_code}")

if response.status_code != 200:
    print("ERROR: No se pudo acceder a la página de login")
    exit(1)

# Extraer el token CSRF de la página de login
soup = BeautifulSoup(response.text, 'html.parser')
csrf_token = soup.find('input', {'name': 'csrfmiddlewaretoken'})
if csrf_token:
    csrf_token = csrf_token['value']
    print(f"CSRF Token obtenido: {csrf_token[:10]}...")
else:
    print("ERROR: No se pudo obtener el token CSRF")
    exit(1)

# Paso 2: Hacer login
print("\n2. Realizando login...")
login_data = {
    'username': 'su',
    'password': 'su123456',
    'csrfmiddlewaretoken': csrf_token
}

response = session.post(login_url, data=login_data, headers={
    'Referer': login_url
})

print(f"Status login: {response.status_code}")
if 'dashboard' not in response.url and 'login' in response.url:
    print("ERROR: Login fallido")
    print(f"Redirigido a: {response.url}")
    exit(1)

print("Login exitoso")

# Paso 3: Acceder a la página del item inbox
print("\n3. Accediendo a la página del item inbox...")
item_url = f'{base_url}/events/inbox/admin/99/'
response = session.get(item_url)
print(f"Status item page: {response.status_code}")

if response.status_code == 200:
    print("✅ Acceso exitoso a la página del item")
    # Verificar que contiene información del item
    if 'CX: Fw: Prueba de Solicitud plan velicidad' in response.text:
        print("✅ El título del item aparece en la página")
    else:
        print("⚠️  El título del item no aparece (posible problema de renderizado)")
else:
    print(f"❌ Error accediendo a la página del item: {response.status_code}")

# Paso 4: Verificar el estado actual del item (antes de delegar)
print("\n4. Verificando estado actual del item...")
# Para esto necesitaríamos acceder a la base de datos o usar una API
# Por ahora, asumimos que está sin asignar basado en el test anterior

# Paso 5: Realizar la delegación
print("\n5. Realizando delegación del item...")
delegate_url = f'{base_url}/events/root/bulk-actions/'

# Obtener token CSRF de la página actual
soup = BeautifulSoup(response.text, 'html.parser')
csrf_token = soup.find('input', {'name': 'csrfmiddlewaretoken'})
if csrf_token:
    csrf_token = csrf_token['value']
else:
    # Intentar obtener de un meta tag
    csrf_meta = soup.find('meta', {'name': 'csrf-token'})
    if csrf_meta:
        csrf_token = csrf_meta['content']
    else:
        print("ERROR: No se pudo obtener token CSRF para delegación")
        csrf_token = None

delegate_data = {
    'action': 'delegate',
    'selected_items[]': '99',
    'delegate_user_id': '2'  # ID del usuario arturo
}

if csrf_token:
    delegate_data['csrfmiddlewaretoken'] = csrf_token

headers = {
    'Referer': item_url,
    'X-CSRFToken': csrf_token if csrf_token else '',
    'Content-Type': 'application/x-www-form-urlencoded'
}

response = session.post(delegate_url, data=delegate_data, headers=headers)
print(f"Status delegación: {response.status_code}")

if response.status_code == 200:
    try:
        result = response.json()
        if result.get('success'):
            print("✅ Delegación exitosa!")
            print(f"Mensaje: {result.get('message')}")
            print(f"Usuario destino: {result.get('delegate_user')}")
        else:
            print(f"❌ Delegación fallida: {result.get('error')}")
    except:
        print("❌ Respuesta no es JSON válido")
        print(f"Contenido: {response.text[:200]}...")
else:
    print(f"❌ Error en la petición de delegación: {response.status_code}")
    print(f"Contenido: {response.text[:200]}...")

print("\n=== TEST COMPLETADO ===")