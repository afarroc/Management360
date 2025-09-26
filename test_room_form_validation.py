#!/usr/bin/env python
"""
Test script para verificar la validación del formulario de habitaciones
"""
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'panel.settings')
django.setup()

from django.contrib.auth.models import User
from rooms.models import Room
from rooms.forms import RoomForm

def test_form_validation():
    """Prueba la validación del formulario con campos faltantes"""
    print("=== Test de Validación del Formulario ===")

    # Crear usuario
    user, created = User.objects.get_or_create(
        username='testuser',
        defaults={'email': 'test@example.com'}
    )
    if created:
        user.set_password('testpass123')
        user.save()
        print("Usuario creado")

    # Obtener habitación existente
    room, created = Room.objects.get_or_create(
        name='Habitacion Test',
        defaults={'owner': user, 'room_type': 'OFFICE'}
    )
    if created:
        print("Habitación creada")

    print(f"Habitación: {room.name} (ID: {room.id})")

    # Probar formulario con datos incompletos (faltan campos requeridos)
    incomplete_data = {
        'name': '',  # Campo requerido vacío
        'room_type': '',  # Campo requerido vacío
        'description': 'Descripción de prueba',
        # Faltan otros campos requeridos como capacity, permissions, etc.
    }

    form = RoomForm(data=incomplete_data, instance=room, user=user)
    print(f"Formulario válido: {form.is_valid()}")

    if not form.is_valid():
        print("Errores encontrados:")
        for field_name, errors in form.errors.items():
            print(f"  - {field_name}: {errors}")

        # Verificar que los campos requeridos están marcados como errores
        required_fields = ['name', 'room_type']
        missing_required_errors = []

        for field_name in required_fields:
            if field_name in form.errors:
                missing_required_errors.append(field_name)

        if missing_required_errors:
            print(f"Campos requeridos con errores correctamente detectados: {missing_required_errors}")
            return True
        else:
            print("ERROR: Campos requeridos no están siendo validados")
            return False
    else:
        print("ERROR: El formulario debería ser inválido con datos incompletos")
        return False

def test_form_with_valid_data():
    """Prueba el formulario con datos válidos"""
    print("\n=== Test con Datos Válidos ===")

    user = User.objects.get(username='testuser')
    room = Room.objects.get(name='Habitacion Test')

    # Datos válidos completos
    valid_data = {
        'name': 'Habitación Editada Validada',
        'description': 'Descripción completa',
        'room_type': 'MEETING',
        'capacity': 10,
        'permissions': 'public',
        'x': 0,
        'y': 0,
        'z': 0,
        'length': 25,
        'width': 25,
        'height': 10,
        'pitch': 0,
        'yaw': 0,
        'roll': 0,
        'color_primary': '#ff5722',
        'color_secondary': '#4caf50',
        'material_type': 'WOOD',
        'opacity': 1.0,
        'mass': 1200.0,
        'density': 0.8,
        'friction': 0.5,
        'restitution': 0.3,
        'is_active': True,
        'health': 100,
        'temperature': 23.0,
        'lighting_intensity': 70,
        'special_properties': '{"test": "value"}'
    }

    form = RoomForm(data=valid_data, instance=room, user=user)
    print(f"Formulario válido: {form.is_valid()}")

    if form.is_valid():
        saved_room = form.save()
        print("Habitación guardada exitosamente")
        print(f"Nombre: {saved_room.name}")
        print(f"Tipo: {saved_room.room_type}")
        print(f"Color primario: {saved_room.color_primary}")
        return True
    else:
        print("Errores inesperados:")
        for field_name, errors in form.errors.items():
            print(f"  - {field_name}: {errors}")
        return False

if __name__ == '__main__':
    try:
        success1 = test_form_validation()
        success2 = test_form_with_valid_data()

        if success1 and success2:
            print("\n[SUCCESS] Todos los tests de validación pasaron!")
            print("El formulario correctamente:")
            print("- Detecta campos requeridos faltantes")
            print("- Acepta datos válidos completos")
            print("- Muestra errores específicos por campo")
            sys.exit(0)
        else:
            print("\n[ERROR] Algunos tests fallaron")
            sys.exit(1)

    except Exception as e:
        print(f"[ERROR] Error en los tests: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)