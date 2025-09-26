#!/usr/bin/env python
"""
Test script simple para verificar el formulario de edición de habitaciones
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

def test_room_form():
    """Prueba basica del formulario"""
    print("=== Test del Formulario de Edicion ===")

    # Crear usuario
    user, created = User.objects.get_or_create(
        username='testuser',
        defaults={'email': 'test@example.com'}
    )
    if created:
        user.set_password('testpass123')
        user.save()
        print("Usuario creado")

    # Obtener habitacion
    room, created = Room.objects.get_or_create(
        name='Habitacion Test',
        defaults={'owner': user, 'room_type': 'OFFICE'}
    )
    if created:
        print("Habitacion creada")

    print(f"Habitacion: {room.name} (ID: {room.id})")

    # Crear formulario
    form = RoomForm(instance=room, user=user)
    print(f"Formulario creado con {len(form.fields)} campos")

    # Verificar campos nuevos
    new_fields = ['color_primary', 'material_type', 'mass', 'temperature']
    for field in new_fields:
        if field in form.fields:
            print(f"Campo {field}: OK")
        else:
            print(f"Campo {field}: FALTANTE")

    # Probar guardar con todos los campos requeridos
    test_data = {
        'name': 'Habitacion Editada',
        'description': 'Descripcion de prueba',
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
        'special_properties': '{}'
    }

    form = RoomForm(data=test_data, instance=room, user=user)
    if form.is_valid():
        saved_room = form.save()
        print("Formulario guardado correctamente")
        print(f"Nombre: {saved_room.name}")
        print(f"Color: {saved_room.color_primary}")
        print(f"Material: {saved_room.material_type}")
        print("TEST PASSED")
        return True
    else:
        print("Errores en formulario:")
        for field, errors in form.errors.items():
            print(f"  {field}: {errors}")
        print("TEST FAILED")
        return False

if __name__ == '__main__':
    success = test_room_form()
    sys.exit(0 if success else 1)