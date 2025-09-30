#!/usr/bin/env python
"""
Test para verificar que la vista inbox_item_detail_admin funciona correctamente
y muestra los usuarios disponibles para delegación.
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

def test_inbox_detail_view():
    """Test básico para verificar que la vista funciona"""
    print("=== Test de Vista inbox_item_detail_admin ===")

    # Crear cliente de prueba
    client = Client()

    # Crear usuario de prueba si no existe
    try:
        user = User.objects.get(username='testuser')
    except User.DoesNotExist:
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            is_active=True
        )
        print(f"Usuario de prueba creado: {user.username}")

    # Crear item de inbox de prueba si no existe
    try:
        inbox_item = InboxItem.objects.get(id=110)
        print(f"Usando item existente: {inbox_item.title}")
    except InboxItem.DoesNotExist:
        inbox_item = InboxItem.objects.create(
            title="Test Item 110",
            description="Descripción de prueba",
            created_by=user,
            gtd_category='pendiente',
            priority='media'
        )
        print(f"Item de inbox creado: {inbox_item.title} (ID: {inbox_item.id})")

    # Hacer login
    client.login(username='testuser', password='testpass123')

    # Hacer petición GET a la vista
    url = f'/events/inbox/admin/{inbox_item.id}/'
    print(f"Haciendo petición GET a: {url}")

    response = client.get(url)

    print(f"Código de respuesta: {response.status_code}")

    if response.status_code == 200:
        content = response.content.decode('utf-8')

        # Verificar que contiene información del item
        if str(inbox_item.id) in content:
            print("✓ ID del item encontrado en la respuesta")
        else:
            print("✗ ID del item NO encontrado en la respuesta")

        if inbox_item.title in content:
            print("✓ Título del item encontrado en la respuesta")
        else:
            print("✗ Título del item NO encontrado en la respuesta")

        # Verificar que contiene usuarios disponibles
        if 'available_users' in content or 'option value=' in content:
            print("✓ Usuarios disponibles encontrados en la respuesta")
        else:
            print("✗ Usuarios disponibles NO encontrados en la respuesta")

        # Verificar que contiene el modal de delegación
        if 'delegateModal' in content:
            print("✓ Modal de delegación encontrado")
        else:
            print("✗ Modal de delegación NO encontrado")

        # Mostrar un fragmento del contenido para debug
        print("\n--- Fragmento del contenido ---")
        # Buscar la sección de usuarios
        start = content.find('<select class="form-select"')
        if start != -1:
            end = content.find('</select>', start)
            if end != -1:
                print(content[start:end+9])
            else:
                print("No se encontró el cierre del select")
        else:
            print("No se encontró el select de usuarios")

    else:
        print(f"Error en la respuesta: {response.status_code}")
        print(f"Contenido del error: {response.content.decode('utf-8')[:500]}")

    print("\n=== Fin del Test ===")

if __name__ == '__main__':
    test_inbox_detail_view()