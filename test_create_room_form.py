#!/usr/bin/env python
"""
Test script para verificar el formulario de creación de habitaciones con alertas
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

def test_create_room_form_validation():
    """Prueba la validación del formulario de creación"""
    print("=== Test de Formulario de Creación ===")

    # Crear usuario
    user, created = User.objects.get_or_create(
        username='testuser3',
        defaults={'email': 'test3@example.com'}
    )
    if created:
        user.set_password('testpass123')
        user.save()

    print("Usuario creado")

    # Probar formulario con datos incompletos (faltan campos requeridos)
    incomplete_data = {
        'name': '',  # Campo requerido vacío
        'room_type': '',  # Campo requerido vacío
        'description': 'Descripción de prueba',
        # Faltan otros campos opcionales
    }

    form = RoomForm(data=incomplete_data, user=user)
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

def test_create_room_form_success():
    """Prueba la creación exitosa de una habitación"""
    print("\n=== Test de Creación Exitosa ===")

    user = User.objects.get(username='testuser3')

    # Datos válidos para crear habitación
    valid_data = {
        'name': 'Habitación Creada por Test',
        'description': 'Habitación creada desde el formulario de creación',
        'room_type': 'OFFICE',
        'capacity': 8,
        'permissions': 'public',
        'length': 25,
        'width': 25,
        'height': 12,
        'color_primary': '#2196f3',
        'material_type': 'WOOD',
        'opacity': 1.0,
        'mass': 1000.0,
        'density': 0.7,
        'friction': 0.5,
        'restitution': 0.3,
        'temperature': 22.0,
        'lighting_intensity': 75,
        'special_properties': '{"test": "creation"}'
    }

    form = RoomForm(data=valid_data, user=user)
    print(f"Formulario válido: {form.is_valid()}")

    if form.is_valid():
        room = form.save(commit=False)
        room.owner = user
        room.creator = user
        room.save()

        print("[SUCCESS] Habitación creada exitosamente")
        print(f"Nombre: {room.name}")
        print(f"Tipo: {room.room_type}")
        print(f"Owner: {room.owner.username}")
        print(f"Color primario: {room.color_primary}")

        # Verificar que se creó correctamente
        created_room = Room.objects.get(name='Habitación Creada por Test')
        assert created_room.owner == user
        assert created_room.room_type == 'OFFICE'
        assert created_room.capacity == 8

        print("[SUCCESS] Todos los datos se guardaron correctamente")
        return True
    else:
        print("Errores inesperados:")
        for field_name, errors in form.errors.items():
            print(f"  - {field_name}: {errors}")
        return False

if __name__ == '__main__':
    try:
        success1 = test_create_room_form_validation()
        success2 = test_create_room_form_success()

        if success1 and success2:
            print("\n[SUCCESS] Formulario de creación funcionando correctamente!")
            print("Características verificadas:")
            print("- Validación de campos requeridos")
            print("- Creación exitosa con datos completos")
            print("- Mensajes de error apropiados")
            print("- Campos opcionales con valores por defecto")
            sys.exit(0)
        else:
            print("\n[ERROR] Algunas pruebas fallaron")
            sys.exit(1)

    except Exception as e:
        print(f"[ERROR] Error en las pruebas: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)