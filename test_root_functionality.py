#!/usr/bin/env python
"""
Test script para verificar la funcionalidad del dashboard root
"""
import os
import sys

# Configurar Django ANTES de cualquier importación
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'panel.settings')
import django
django.setup()

from django.test import TestCase, Client, override_settings
from django.contrib.auth.models import User
from django.urls import reverse

from events.models import InboxItem

@override_settings(ALLOWED_HOSTS=['testserver', 'localhost', '127.0.0.1', '192.168.18.46', '192.168.18.47'])
def test_create_inbox_item_api():
    """Test para verificar que la API de creación de inbox items funciona"""
    print("=== Probando API de creación de Inbox Items ===")

    # Crear cliente de pruebas
    client = Client()

    # Crear usuario superuser si no existe
    try:
        user = User.objects.get(username='admin')
    except User.DoesNotExist:
        user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='admin123'
        )
        print(f"Usuario admin creado: {user.username}")

    # Hacer login
    client.login(username='admin', password='admin123')
    print("Login exitoso")

    # Datos de prueba
    test_data = {
        'title': 'Test Item from API',
        'description': 'This is a test item created via API',
        'gtd_category': 'pendiente',
        'priority': 'media',
        'action_type': 'hacer',
        'context': '@test'
    }

    # Hacer POST request a la API
    url = reverse('create_inbox_item_api')
    print(f"Haciendo POST a: {url}")
    print(f"Datos a enviar: {test_data}")

    response = client.post(url, test_data)

    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.content.decode()}")

    if response.status_code == 200:
        try:
            import json
            data = json.loads(response.content.decode())
            if data.get('success'):
                print(f"[OK] Item creado exitosamente: {data.get('item_id')}")
                return True
            else:
                print(f"[ERROR] Error en respuesta: {data.get('error')}")
                return False
        except json.JSONDecodeError:
            print("[ERROR] Respuesta no es JSON válido")
            return False
    else:
        print(f"[ERROR] Error HTTP: {response.status_code}")
        return False

def test_inbox_item_model():
    """Test básico del modelo InboxItem"""
    print("\n=== Probando modelo InboxItem ===")

    try:
        user = User.objects.get(username='admin')

        # Crear item de prueba
        item = InboxItem.objects.create(
            title='Test Model Item',
            description='Created via model test',
            created_by=user,
            gtd_category='accionable',
            priority='alta'
        )

        print(f"[OK] Item creado: ID={item.id}, Title='{item.title}'")
        print(f"   Categoría: {item.gtd_category}, Prioridad: {item.priority}")

        # Verificar que se guardó correctamente
        saved_item = InboxItem.objects.get(id=item.id)
        assert saved_item.title == 'Test Model Item'
        assert saved_item.gtd_category == 'accionable'

        print("[OK] Item guardado correctamente en BD")
        return True

    except Exception as e:
        print(f"[ERROR] Error en modelo: {e}")
        return False

if __name__ == '__main__':
    print("Iniciando pruebas de funcionalidad del dashboard root...\n")

    # Test 1: Modelo
    model_ok = test_inbox_item_model()

    # Test 2: API
    api_ok = test_create_inbox_item_api()

    print("\n=== RESULTADOS ===")
    print(f"Modelo InboxItem: {'[OK]' if model_ok else '[FAIL]'}")
    print(f"API crear item: {'[OK]' if api_ok else '[FAIL]'}")

    if model_ok and api_ok:
        print("\n[SUCCESS] Todas las pruebas pasaron exitosamente!")
        sys.exit(0)
    else:
        print("\n[FAILED] Algunas pruebas fallaron")
        sys.exit(1)