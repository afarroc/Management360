#!/usr/bin/env python
"""
Script para renderizar la vista inbox_item_detail_admin y guardar la respuesta HTML
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

def test_render_response():
    """Renderizar la vista y guardar la respuesta HTML"""

    # Crear cliente de prueba
    client = Client()

    # Obtener usuario admin
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

    # Obtener item específico (ID 99)
    try:
        inbox_item = InboxItem.objects.get(id=99)
        print(f"Item encontrado: ID={inbox_item.id}, Title='{inbox_item.title}'")
    except InboxItem.DoesNotExist:
        print("ERROR: Item con ID 99 no encontrado")
        return

    # Hacer petición GET
    url = f'/events/inbox/admin/{inbox_item.id}/'
    print(f"Haciendo petición GET a: {url}")

    response = client.get(url)

    print(f"Status code: {response.status_code}")
    print(f"Content-Type: {response.get('Content-Type', 'N/A')}")

    if response.status_code == 200:
        # Guardar la respuesta HTML en un archivo
        with open('response_debug.html', 'w', encoding='utf-8') as f:
            f.write(response.content.decode('utf-8'))

        print("SUCCESS: Respuesta HTML guardada en 'response_debug.html'")

        # Verificar elementos clave en la respuesta
        content = response.content.decode('utf-8')

        # Verificar que el título del item esté presente
        if inbox_item.title in content:
            print(f"SUCCESS: Título del item encontrado en respuesta")
        else:
            print(f"ERROR: Título del item NO encontrado en respuesta")

        # Verificar que el ID esté presente
        if str(inbox_item.id) in content:
            print(f"SUCCESS: ID del item encontrado en respuesta")
        else:
            print(f"ERROR: ID del item NO encontrado en respuesta")

        # Verificar que el nombre del creador esté presente
        if inbox_item.created_by.username in content:
            print(f"SUCCESS: Usuario creador encontrado en respuesta")
        else:
            print(f"ERROR: Usuario creador NO encontrado en respuesta")

        # Verificar que haya opciones de usuario para delegar
        if 'option value=' in content and 'Elegir usuario' in content:
            print("SUCCESS: Opciones de delegación encontradas")
        else:
            print("WARNING: Opciones de delegación no encontradas")

        # Mostrar las primeras 1000 líneas para debug
        lines = content.split('\n')
        print(f"\n--- Primeras 50 líneas de la respuesta ({len(lines)} líneas totales) ---")
        for i, line in enumerate(lines[:50]):
            if line.strip():  # Solo líneas no vacías
                print("2")
        print("--- Fin del extracto ---")

    else:
        print(f"ERROR: Status code {response.status_code}")
        print("Contenido del error:")
        print(response.content.decode('utf-8')[:500])

if __name__ == '__main__':
    print("=== Renderizando vista inbox_item_detail_admin ===")
    test_render_response()
    print("=== Fin del renderizado ===")