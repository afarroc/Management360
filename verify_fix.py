#!/usr/bin/env python
"""
Verificación final del fix para la vista inbox_item_detail_admin
"""

import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'panel.settings')
django.setup()

from django.contrib.auth.models import User
from events.models import InboxItem
from django.test import Client

def verify_fix():
    """Verificar que el fix funciona"""
    print("=== Verificación del Fix ===")

    # Verificar que hay usuarios activos
    users = User.objects.filter(is_active=True)
    print(f"Usuarios activos encontrados: {users.count()}")

    if users.count() == 0:
        print("ERROR: No hay usuarios activos en el sistema")
        return False

    # Verificar que el item 110 existe
    try:
        item = InboxItem.objects.get(id=110)
        print(f"Item 110 encontrado: {item.title}")
    except InboxItem.DoesNotExist:
        print("ERROR: Item 110 no encontrado")
        return False

    # Crear cliente de test
    client = Client()

    # Usar el primer usuario activo encontrado
    test_user = users.first()
    print(f"Usando usuario de test: {test_user.username}")

    # Simular login
    from django.contrib.auth import authenticate, login
    user = authenticate(username=test_user.username, password='admin123')
    if user:
        client.login(username=test_user.username, password='admin123')
        print("Login exitoso")
    else:
        print("ERROR: No se pudo autenticar el usuario")
        return False

    # Hacer petición a la vista
    url = f'/events/inbox/admin/{item.id}/'
    response = client.get(url)

    print(f"Código de respuesta: {response.status_code}")

    if response.status_code == 200:
        content = response.content.decode('utf-8')

        # Verificar contenido
        checks = [
            ('ID del item', str(item.id) in content),
            ('Título del item', item.title in content),
            ('Select de usuarios', 'form-select' in content),
            ('Opciones de usuario', 'option value=' in content),
            ('Modal de delegación', 'delegateModal' in content),
        ]

        all_passed = True
        for check_name, passed in checks:
            status = "[OK]" if passed else "[ERROR]"
            print(f"{status} {check_name}")
            if not passed:
                all_passed = False

        # Contar usuarios en el select
        if 'option value=' in content:
            import re
            options = re.findall(r'<option value="\d+">', content)
            print(f"Usuarios disponibles en el select: {len(options)}")

        return all_passed
    else:
        print(f"ERROR: Respuesta HTTP {response.status_code}")
        return False

if __name__ == '__main__':
    success = verify_fix()
    print(f"\nResultado: {'EXITO' if success else 'FALLIDO'}")