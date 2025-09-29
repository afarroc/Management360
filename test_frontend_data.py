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

def test_frontend_data_simulation():
    """Simular exactamente los datos que envía el frontend"""

    print("=" * 80)
    print("SIMULACIÓN DE DATOS DEL FRONTEND")
    print("=" * 80)
    print()

    # Crear cliente y login
    client = Client()
    login_success = client.login(username='su', password='su')
    print(f"LOGIN: {'EXITOSO' if login_success else 'FALLIDO'}")
    print()

    if not login_success:
        return

    # Obtener token CSRF
    response = client.get('/rooms/rooms/crud/')
    import re
    csrf_match = re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', response.content.decode('utf-8'))
    csrf_token = csrf_match.group(1) if csrf_match else 'dummy_token'

    print(f"Token CSRF obtenido: {csrf_token[:20]}...")
    print()

    # PASO 1: Simular datos EXACTOS del frontend
    print("PASO 1: DATOS EXACTOS DEL FRONTEND")
    print("-" * 40)

    # Estos son los datos EXACTOS que envía el JavaScript del frontend
    frontend_data = {
        'name': 'Habitación Editada por Test',
        'room_type': 'OFFICE',
        'description': None,  # null en JavaScript
        'capacity': None,     # null en JavaScript
        'permissions': 'public',
        'is_active': True,
        'length': 30,         # Valor por defecto
        'width': 30,          # Valor por defecto
        'height': 10,         # Valor por defecto
        'color_primary': '#2196f3',
        'color_secondary': '#1976d2',
        'material_type': 'CONCRETE',
        'opacity': 1.0
    }

    print("Datos simulados del frontend:")
    for key, value in frontend_data.items():
        print(f"  {key}: {repr(value)} (tipo: {type(value).__name__})")

    print()

    # PASO 2: Probar con datos JSON (como los envía fetch)
    print("PASO 2: ENVÍO COMO JSON (como hace fetch)")
    print("-" * 40)

    response = client.put('/rooms/api/crud/rooms/2/', json.dumps(frontend_data), content_type='application/json', HTTP_X_CSRFTOKEN=csrf_token)

    print(f"URL: /rooms/api/crud/rooms/2/")
    print(f"Método: PUT")
    print(f"Content-Type: application/json")
    print(f"Respuesta HTTP: {response.status_code}")

    if response.status_code == 200:
        print("✅ ACTUALIZACIÓN EXITOSA")
        result = response.json()
        print(f"Habitación actualizada: {result.get('name')}")
    else:
        print("❌ ERROR EN ACTUALIZACIÓN")
        try:
            error_data = response.json()
            print("Errores de validación detallados:")
            for field, errors in error_data.items():
                print(f"  {field}: {errors}")
        except:
            print("Respuesta de error cruda:")
            print(response.content.decode('utf-8'))

    print()

    # PASO 3: Probar con FormData (como si fuera un formulario HTML)
    print("PASO 3: ENVÍO COMO FormData (como formulario HTML)")
    print("-" * 40)

    # Simular FormData como lo haría un formulario HTML
    form_data = {
        'name': 'Habitación FormData Test',
        'room_type': 'OFFICE',
        'description': '',  # Vacío en lugar de null
        'capacity': '',     # Vacío en lugar de null
        'permissions': 'public',
        'is_active': 'on',  # Como checkbox
        'length': '30',
        'width': '30',
        'height': '10',
        'color_primary': '#2196f3',
        'color_secondary': '#1976d2',
        'material_type': 'CONCRETE',
        'opacity': '1.0'
    }

    print("Datos simulados de FormData:")
    for key, value in form_data.items():
        print(f"  {key}: {repr(value)}")

    response = client.put('/rooms/api/crud/rooms/2/', form_data, HTTP_X_CSRFTOKEN=csrf_token)

    print(f"Respuesta HTTP: {response.status_code}")

    if response.status_code == 200:
        print("✅ ACTUALIZACIÓN EXITOSA CON FormData")
    else:
        print("❌ ERROR CON FormData")
        try:
            error_data = response.json()
            print("Errores:")
            for field, errors in error_data.items():
                print(f"  {field}: {errors}")
        except:
            print("Respuesta de error:")
            print(response.content.decode('utf-8'))

    print()

    # PASO 4: Verificar el serializer directamente
    print("PASO 4: PRUEBA DIRECTA DEL SERIALIZER")
    print("-" * 40)

    from rooms.serializers import RoomCRUDSerializer

    # Obtener la habitación
    try:
        room = Room.objects.get(id=2)
        print(f"Habitación encontrada: {room.name}")

        # Probar serialización
        serializer = RoomCRUDSerializer(room)
        serialized_data = serializer.data
        print("Serialización exitosa:")
        print(f"  Campos serializados: {len(serialized_data)}")

        # Probar deserialización con datos del frontend
        update_serializer = RoomCRUDSerializer(room, data=frontend_data, partial=True)
        is_valid = update_serializer.is_valid()

        print(f"Validación del serializer: {'VÁLIDA' if is_valid else 'INVÁLIDA'}")

        if not is_valid:
            print("Errores de validación del serializer:")
            for field, errors in update_serializer.errors.items():
                print(f"  {field}: {errors}")

        if is_valid:
            print("Intentando guardar...")
            try:
                saved_room = update_serializer.save()
                print(f"✅ Guardado exitoso: {saved_room.name}")
            except Exception as save_error:
                print(f"❌ Error al guardar: {save_error}")

    except Room.DoesNotExist:
        print("❌ Habitación no encontrada")
    except Exception as e:
        print(f"❌ Error en prueba del serializer: {e}")

    print()
    print("=" * 80)
    print("DIAGNÓSTICO FINAL")
    print("=" * 80)

    print("POSIBLES CAUSAS DEL ERROR 400:")
    print("1. El frontend envía 'null' en lugar de valores apropiados")
    print("2. Campos opcionales no manejados correctamente en el serializer")
    print("3. Conversión de tipos de datos problemática")
    print("4. Validaciones personalizadas en el serializer")

    print("\nSOLUCIONES PROPUESTAS:")
    print("1. Modificar el JavaScript para enviar strings vacías en lugar de null")
    print("2. Ajustar el serializer para manejar nulls correctamente")
    print("3. Agregar validaciones más específicas en el serializer")
    print("4. Verificar que los tipos de datos sean correctos")

if __name__ == '__main__':
    test_frontend_data_simulation()