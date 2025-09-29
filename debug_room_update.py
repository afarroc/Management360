#!/usr/bin/env python
import os
import sys

# Configurar Django ANTES de cualquier import
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'panel.settings')
sys.path.append('.')

import django
django.setup()

from django.test import Client
from django.contrib.auth.models import User
from rooms.models import Room
import json

def debug_room_update():
    """Debug detallado del error 400 en actualización de habitación"""

    print("=" * 80)
    print("DEBUG: ERROR 400 EN ACTUALIZACIÓN DE HABITACIÓN")
    print("=" * 80)
    print()

    # Crear cliente y login
    client = Client()
    login_success = client.login(username='su', password='su')
    print(f"LOGIN: {'EXITOSO' if login_success else 'FALLIDO'}")
    print()

    if not login_success:
        return

    # PASO 1: Obtener habitación actual
    print("PASO 1: OBTENER HABITACIÓN ACTUAL")
    print("-" * 40)

    response = client.get('/rooms/api/crud/rooms/2/')
    print(f"URL: /rooms/api/crud/rooms/2/")
    print(f"Respuesta HTTP: {response.status_code}")

    if response.status_code == 200:
        current_room = response.json()
        print("Habitación actual:")
        for key, value in current_room.items():
            print(f"  {key}: {value}")
    else:
        print(f"ERROR obteniendo habitación: {response.status_code}")
        print(f"Respuesta: {response.content.decode('utf-8')}")
        return

    print()

    # PASO 2: Intentar actualización mínima
    print("PASO 2: INTENTAR ACTUALIZACIÓN MÍNIMA")
    print("-" * 40)

    # Obtener token CSRF
    response = client.get('/rooms/rooms/crud/')
    import re
    csrf_match = re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', response.content.decode('utf-8'))
    csrf_token = csrf_match.group(1) if csrf_match else 'dummy_token'

    # Datos mínimos para actualizar
    update_data = {
        'name': 'Habitación Debug Actualizada'
    }

    print("Datos de actualización mínima:")
    print(f"  name: {update_data['name']}")

    response = client.put('/rooms/api/crud/rooms/2/', json.dumps(update_data), content_type='application/json', HTTP_X_CSRFTOKEN=csrf_token)

    print(f"Respuesta HTTP: {response.status_code}")

    if response.status_code == 200:
        print("✅ ACTUALIZACIÓN EXITOSA")
        updated_room = response.json()
        print(f"Nombre actualizado: {updated_room.get('name')}")
    else:
        print("❌ ERROR EN ACTUALIZACIÓN")
        print(f"Código: {response.status_code}")
        try:
            error_data = response.json()
            print("Errores de validación:")
            for field, errors in error_data.items():
                print(f"  {field}: {errors}")
        except:
            print("Respuesta de error:")
            print(response.content.decode('utf-8'))

    print()

    # PASO 3: Verificar permisos
    print("PASO 3: VERIFICAR PERMISOS")
    print("-" * 40)

    try:
        room = Room.objects.get(id=2)
        user = User.objects.get(username='su')

        print(f"Habitación ID: {room.id}")
        print(f"Propietario: {room.owner.username}")
        print(f"Usuario actual: {user.username}")
        print(f"Es propietario: {room.owner == user}")
        print(f"Puede gestionar: {room.can_user_manage(user)}")

        # Verificar administradores
        admins = list(room.administrators.all())
        print(f"Administradores: {[admin.username for admin in admins]}")
        print(f"Es administrador: {user in admins}")

    except Exception as e:
        print(f"ERROR verificando permisos: {e}")

    print()

    # PASO 4: Probar con datos completos
    print("PASO 4: PROBAR CON DATOS COMPLETOS")
    print("-" * 40)

    complete_data = {
        'name': 'Habitación Debug Completa',
        'room_type': 'OFFICE',
        'description': 'Descripción de debug',
        'capacity': 10,
        'permissions': 'public',
        'is_active': True,
        'length': 30,
        'width': 30,
        'height': 10,
        'color_primary': '#2196f3',
        'color_secondary': '#1976d2',
        'material_type': 'CONCRETE',
        'opacity': 1.0
    }

    print("Datos completos:")
    for key, value in complete_data.items():
        print(f"  {key}: {value}")

    response = client.put('/rooms/api/crud/rooms/2/', json.dumps(complete_data), content_type='application/json', HTTP_X_CSRFTOKEN=csrf_token)

    print(f"Respuesta HTTP: {response.status_code}")

    if response.status_code == 200:
        print("✅ ACTUALIZACIÓN COMPLETA EXITOSA")
    else:
        print("❌ ERROR EN ACTUALIZACIÓN COMPLETA")
        try:
            error_data = response.json()
            print("Errores detallados:")
            for field, errors in error_data.items():
                print(f"  {field}: {errors}")
        except:
            print("Respuesta de error:")
            print(response.content.decode('utf-8'))

    print()
    print("=" * 80)
    print("ANÁLISIS DEL ERROR 400")
    print("=" * 80)

    print("POSIBLES CAUSAS:")
    print("1. Permisos insuficientes")
    print("2. Validación de campos requeridos")
    print("3. Formato de datos incorrecto")
    print("4. Campos read-only siendo enviados")
    print("5. Validación personalizada en serializer")

    print("\nSOLUCIONES PROPUESTAS:")
    print("1. Verificar que el usuario tenga permisos")
    print("2. Revisar campos requeridos en serializer")
    print("3. Verificar formato de datos enviados")
    print("4. Revisar validaciones personalizadas")

if __name__ == '__main__':
    debug_room_update()