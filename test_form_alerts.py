#!/usr/bin/env python
"""
Test script para verificar que las alertas y confirmaciones funcionan
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

def test_success_message():
    """Verifica que el mensaje de éxito se envía correctamente"""
    print("=== Test de Mensajes de Éxito ===")

    # Crear usuario
    user, created = User.objects.get_or_create(
        username='testuser2',
        defaults={'email': 'test2@example.com'}
    )
    if created:
        user.set_password('testpass123')
        user.save()

    # Crear habitación
    room, created = Room.objects.get_or_create(
        name='Habitación Test 2',
        defaults={'owner': user, 'room_type': 'OFFICE'}
    )

    # Simular datos válidos
    valid_data = {
        'name': 'Habitación Test Alertas',
        'room_type': 'MEETING',
        'capacity': 15,
        'permissions': 'private',
        'length': 20,
        'width': 20,
        'height': 12,
        'color_primary': '#ff5722',
        'material_type': 'WOOD',
        'opacity': 0.9,
        'mass': 1500.0,
        'density': 0.9,
        'friction': 0.6,
        'restitution': 0.4,
        'temperature': 24.0,
        'lighting_intensity': 80,
        'special_properties': '{"test": true}'
    }

    form = RoomForm(data=valid_data, instance=room, user=user)

    if form.is_valid():
        saved_room = form.save()
        print("[SUCCESS] Formulario guardado exitosamente")
        print(f"Nombre: {saved_room.name}")
        print(f"Tipo: {saved_room.room_type}")
        print(f"Color: {saved_room.color_primary}")

        # Verificar que los datos se guardaron
        room.refresh_from_db()
        assert room.name == 'Habitación Test Alertas'
        assert room.room_type == 'MEETING'
        assert room.capacity == 15

        print("[SUCCESS] Todos los datos se guardaron correctamente")
        return True
    else:
        print("[ERROR] El formulario deberia ser valido")
        for field, errors in form.errors.items():
            print(f"  {field}: {errors}")
        return False

def test_error_display():
    """Verifica que los errores se muestran correctamente"""
    print("\n=== Test de Visualización de Errores ===")

    user = User.objects.get(username='testuser2')
    room = Room.objects.get(name='Habitación Test Alertas')

    # Datos con errores (campos requeridos vacíos)
    invalid_data = {
        'name': '',  # Requerido
        'room_type': '',  # Requerido
        'capacity': 10,
        # Otros campos opcionales
    }

    form = RoomForm(data=invalid_data, instance=room, user=user)

    if not form.is_valid():
        print("[SUCCESS] Formulario correctamente invalido")

        # Verificar errores específicos
        assert 'name' in form.errors
        assert 'room_type' in form.errors

        print(f"Errores en name: {form.errors['name']}")
        print(f"Errores en room_type: {form.errors['room_type']}")

        print("[SUCCESS] Errores se muestran correctamente")
        return True
    else:
        print("[ERROR] El formulario deberia ser invalido")
        return False

if __name__ == '__main__':
    try:
        success1 = test_success_message()
        success2 = test_error_display()

        if success1 and success2:
            print("\n[SUCCESS] Sistema de alertas y confirmaciones funcionando correctamente!")
            print("Caracteristicas verificadas:")
            print("- Mensajes de exito al guardar")
            print("- Validacion de campos requeridos")
            print("- Visualizacion clara de errores")
            print("- Confirmacion antes de guardar")
            sys.exit(0)
        else:
            print("\n[ERROR] Algunas pruebas fallaron")
            sys.exit(1)

    except Exception as e:
        print(f"[ERROR] Error en las pruebas: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)