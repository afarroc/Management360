#!/usr/bin/env python
"""
Test script para verificar la funcionalidad de la vista root
"""
import os
import sys
import django
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'panel.settings')
django.setup()

from events.models import InboxItem

def test_root_view():
    """Test básico de la vista root"""
    print("=== TEST DE LA VISTA ROOT ===")

    # Crear cliente de prueba
    client = Client()

    # Crear usuario superuser de prueba
    try:
        superuser = User.objects.create_superuser(
            username='test_superuser',
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='Superuser'
        )
        print("✓ Usuario superuser creado")
    except:
        superuser = User.objects.get(username='test_superuser')
        print("✓ Usuario superuser ya existe")

    # Hacer login
    login_success = client.login(username='test_superuser', password='testpass123')
    if login_success:
        print("✓ Login exitoso")
    else:
        print("✗ Error en login")
        return False

    # Probar acceso a la vista root
    try:
        response = client.get('/events/root/')
        if response.status_code == 200:
            print("✓ Vista root accesible (status 200)")
        else:
            print(f"✗ Error en vista root (status {response.status_code})")
            return False
    except Exception as e:
        print(f"✗ Error al acceder a la vista root: {e}")
        return False

    # Verificar que el contenido contiene elementos esperados
    content = response.content.decode('utf-8')

    # Verificar elementos clave
    checks = [
        ('Título de la página', 'Root Dashboard' in content),
        ('Información del usuario', 'test_superuser' in content),
        ('Badge de superuser', 'Super Usuario' in content),
        ('Tabla de inbox', 'Gestión Completa del Inbox GTD' in content),
        ('Modal de creación', 'createInboxItemModal' in content),
        ('JavaScript functions', 'viewInboxItem' in content),
        ('API endpoint URL', '/events/inbox/create/' in content),
    ]

    all_passed = True
    for check_name, check_result in checks:
        if check_result:
            print(f"✓ {check_name}")
        else:
            print(f"✗ {check_name}")
            all_passed = False

    # Probar crear un item del inbox
    print("\n=== TEST DE CREACIÓN DE ITEM DEL INBOX ===")

    # Datos del formulario
    form_data = {
        'title': 'Test Item from API',
        'description': 'Item creado desde el test de API',
        'gtd_category': 'accionable',
        'priority': 'alta',
        'action_type': 'hacer',
        'context': '@test'
    }

    try:
        response = client.post('/events/inbox/create/', form_data, follow=True)
        if response.status_code == 200:
            print("✓ API de creación de inbox item accesible")

            # Verificar respuesta JSON
            import json
            try:
                json_response = json.loads(response.content.decode('utf-8'))
                if json_response.get('success'):
                    print("✓ Item del inbox creado exitosamente")
                    item_id = json_response.get('item_id')
                    print(f"✓ ID del item creado: {item_id}")

                    # Verificar que el item existe en la base de datos
                    try:
                        item = InboxItem.objects.get(id=item_id)
                        print(f"✓ Item verificado en BD: {item.title}")
                    except InboxItem.DoesNotExist:
                        print("✗ Item no encontrado en BD")
                        all_passed = False

                else:
                    print(f"✗ Error en creación: {json_response.get('error')}")
                    all_passed = False
            except json.JSONDecodeError:
                print("✗ Respuesta no es JSON válido")
                all_passed = False
        else:
            print(f"✗ Error en API (status {response.status_code})")
            all_passed = False
    except Exception as e:
        print(f"✗ Error al probar API: {e}")
        all_passed = False

    # Limpiar datos de prueba
    try:
        superuser.delete()
        print("✓ Datos de prueba limpiados")
    except:
        pass

    return all_passed

if __name__ == '__main__':
    success = test_root_view()
    if success:
        print("\n🎉 TODOS LOS TESTS PASARON")
        sys.exit(0)
    else:
        print("\n❌ ALGUNOS TESTS FALLARON")
        sys.exit(1)