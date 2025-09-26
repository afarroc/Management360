#!/usr/bin/env python
"""
Test script para verificar el funcionamiento del formulario de edición de habitaciones
"""
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'panel.settings')
django.setup()

from django.test import TestCase, Client
from django.contrib.auth.models import User
from rooms.models import Room
from rooms.forms import RoomForm

def test_room_edit_form():
    """Prueba el formulario de edición de habitación"""
    print("=== Prueba del Formulario de Edición de Habitación ===")

    # Crear usuario de prueba si no existe
    user, created = User.objects.get_or_create(
        username='testuser',
        defaults={'email': 'test@example.com'}
    )
    if created:
        user.set_password('testpass123')
        user.save()
        print("[OK] Usuario de prueba creado")

    # Obtener o crear habitación de prueba
    room, created = Room.objects.get_or_create(
        name='Habitación de Prueba',
        defaults={
            'owner': user,
            'room_type': 'OFFICE',
            'length': 30,
            'width': 30,
            'height': 10
        }
    )
    if created:
        print("[OK] Habitacion de prueba creada")

    print(f"Habitación: {room.name} (ID: {room.id})")
    print(f"Tipo: {room.room_type}")
    print(f"Dimensiones: {room.length}×{room.width}×{room.height}")

    # Probar formulario con datos existentes
    form = RoomForm(instance=room, user=user)
    print(f"✅ Formulario creado con {len(form.fields)} campos")

    # Verificar que los campos nuevos están presentes
    required_fields = [
        'color_primary', 'color_secondary', 'material_type', 'opacity',
        'mass', 'density', 'friction', 'restitution',
        'is_active', 'health', 'temperature', 'lighting_intensity'
    ]

    missing_fields = []
    for field_name in required_fields:
        if field_name not in form.fields:
            missing_fields.append(field_name)

    if missing_fields:
        print(f"❌ Campos faltantes: {missing_fields}")
        return False
    else:
        print("✅ Todos los campos nuevos están presentes")

    # Probar guardar formulario con datos modificados
    test_data = {
        'name': 'Habitación Editada',
        'description': 'Descripción de prueba editada',
        'room_type': 'MEETING',
        'capacity': 15,
        'permissions': 'public',
        'length': 25,
        'width': 20,
        'height': 12,
        'color_primary': '#ff5722',
        'color_secondary': '#4caf50',
        'material_type': 'WOOD',
        'opacity': 0.9,
        'mass': 1500.0,
        'density': 0.8,
        'friction': 0.7,
        'restitution': 0.4,
        'is_active': True,
        'health': 95,
        'temperature': 24.5,
        'lighting_intensity': 75,
        'sound_ambient': 'Ambiente oficina',
        'special_properties': '{"has_windows": true, "floor_type": "carpet"}'
    }

    form = RoomForm(data=test_data, instance=room, user=user)
    if form.is_valid():
        try:
            saved_room = form.save()
            print("✅ Formulario guardado exitosamente")
            print(f"Nombre actualizado: {saved_room.name}")
            print(f"Tipo actualizado: {saved_room.room_type}")
            print(f"Color primario: {saved_room.color_primary}")
            print(f"Material: {saved_room.material_type}")
            print(f"Temperatura: {saved_room.temperature}°C")
            return True
        except Exception as e:
            print(f"❌ Error al guardar: {e}")
            return False
    else:
        print(f"❌ Formulario inválido: {form.errors}")
        return False

def test_view_access():
    """Prueba el acceso a la vista de edición"""
    print("\n=== Prueba de Acceso a Vista ===")

    client = Client()

    # Crear usuario y habitación
    user, _ = User.objects.get_or_create(
        username='testuser',
        defaults={'email': 'test@example.com'}
    )
    user.set_password('testpass123')
    user.save()

    room, _ = Room.objects.get_or_create(
        name='Habitación de Prueba',
        defaults={'owner': user}
    )

    # Login
    login_success = client.login(username='testuser', password='testpass123')
    if not login_success:
        print("❌ Error en login")
        return False

    print("✅ Login exitoso")

    # Acceder a la vista de edición
    url = f'/rooms/rooms/{room.id}/edit/'
    response = client.get(url)

    if response.status_code == 200:
        print(f"✅ Vista accesible en {url}")
        if 'room_form.html' in str(response.content):
            print("✅ Template correcto cargado")
            return True
        else:
            print("❌ Template incorrecto")
            return False
    else:
        print(f"❌ Error HTTP {response.status_code}")
        return False

def main():
    try:
        success1 = test_room_edit_form()
        success2 = test_view_access()

        if success1 and success2:
            print("\n🎉 TODAS LAS PRUEBAS PASARON EXITOSAMENTE!")
            return True
        else:
            print("\n❌ Algunas pruebas fallaron")
            return False

    except Exception as e:
        print(f"❌ Error en las pruebas: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    main()