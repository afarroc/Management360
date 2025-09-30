#!/usr/bin/env python
"""
Script para probar la vista inbox_item_detail_admin y revisar los logs
"""
import os
import sys
import django
from django.test import Client
from django.contrib.auth.models import User

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'panel.settings')
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
django.setup()

from events.models import InboxItem

def test_inbox_detail_view():
    """Probar la vista inbox_item_detail_admin con logs"""

    # Crear cliente de prueba
    client = Client()

    # Obtener usuario admin
    try:
        admin_user = User.objects.filter(is_superuser=True).first()
        if not admin_user:
            admin_user = User.objects.filter(is_staff=True).first()
        if not admin_user:
            admin_user = User.objects.first()

        if not admin_user:
            print("ERROR: No hay usuarios en la base de datos")
            return

        print(f"Usando usuario: {admin_user.username}")

        # Hacer login
        client.force_login(admin_user)

        # Obtener un item del inbox
        inbox_item = InboxItem.objects.first()
        if not inbox_item:
            print("ERROR: No hay items en el inbox")
            return

        print(f"Probando con item ID: {inbox_item.id}")

        # Hacer petición GET
        url = f'/events/inbox/admin/{inbox_item.id}/'
        print(f"Haciendo petición a: {url}")

        response = client.get(url)

        print(f"Status code: {response.status_code}")

        if response.status_code == 200:
            print("SUCCESS: Vista cargada correctamente")

            # Verificar que el contenido tenga datos del item
            content = response.content.decode('utf-8')

            # Verificar que el título esté presente
            if inbox_item.title in content:
                print(f"SUCCESS: Título '{inbox_item.title}' encontrado en la respuesta")
            else:
                print(f"ERROR: Título '{inbox_item.title}' NO encontrado en la respuesta")

            # Verificar que la descripción esté presente
            if inbox_item.description and inbox_item.description in content:
                print(f"SUCCESS: Descripción encontrada en la respuesta")
            else:
                print("WARNING: Descripción no encontrada o vacía")

            # Verificar que el usuario creador esté presente
            if inbox_item.created_by.username in content:
                print(f"SUCCESS: Usuario creador '{inbox_item.created_by.username}' encontrado")
            else:
                print(f"ERROR: Usuario creador '{inbox_item.created_by.username}' NO encontrado")

            # Verificar que los usuarios disponibles estén presentes
            from django.contrib.auth.models import User
            available_users = User.objects.filter(is_active=True)
            if str(available_users.count()) in content:
                print(f"SUCCESS: Usuarios disponibles ({available_users.count()}) encontrados")
            else:
                print("WARNING: Conteo de usuarios disponibles no encontrado")

        else:
            print(f"ERROR: Status code {response.status_code}")
            print("Contenido de error:")
            print(response.content.decode('utf-8')[:500])

    except Exception as e:
        print(f"ERROR: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    print("=== Probando vista inbox_item_detail_admin con logs ===")
    test_inbox_detail_view()
    print("=== Fin de la prueba ===")