#!/usr/bin/env python
"""
Test completo del flujo CRUD de habitaciones con alertas y confirmaciones
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

def test_crud_flow():
    """Prueba completa del flujo CRUD: Create, Read, Update, Delete"""
    print("=== Test Completo del Flujo CRUD ===\n")

    # Crear usuario de prueba
    user, created = User.objects.get_or_create(
        username='crud_test_user',
        defaults={'email': 'crud@test.com'}
    )
    if created:
        user.set_password('testpass123')
        user.save()
        print("[OK] Usuario de prueba creado")

    # === CREATE ===
    print("\n--- 1. CREAR HABITACIÓN ---")
    create_data = {
        'name': 'Habitación CRUD Test',
        'description': 'Habitación para testing completo del CRUD',
        'room_type': 'OFFICE',
        'capacity': 10,
        'permissions': 'public',
        'length': 20,
        'width': 15,
        'height': 8,
        'color_primary': '#4CAF50',
        'material_type': 'WOOD',
        'opacity': 1.0,
        'mass': 500.0,
        'density': 0.8,
        'friction': 0.6,
        'restitution': 0.2,
        'temperature': 25.0,
        'lighting_intensity': 80,
        'sound_ambient': 'office_ambient.mp3',
        'special_properties': '{"test": "crud_flow"}'
    }

    form = RoomForm(data=create_data, user=user)
    if form.is_valid():
        room = form.save(commit=False)
        room.owner = user
        room.creator = user
        room.save()
        print("[OK] Habitación creada exitosamente")
        print(f"  Nombre: {room.name}")
        print(f"  Tipo: {room.room_type}")
        print(f"  ID: {room.pk}")
    else:
        print("[ERROR] Error al crear habitación:")
        for field, errors in form.errors.items():
            print(f"  {field}: {errors}")
        return False

    # === READ ===
    print("\n--- 2. LEER HABITACIÓN ---")
    try:
        read_room = Room.objects.get(name='Habitación CRUD Test')
        print("[OK] Habitación encontrada en la base de datos")
        print(f"  Descripción: {read_room.description}")
        print(f"  Capacidad: {read_room.capacity}")
        print(f"  Color primario: {read_room.color_primary}")
    except Room.DoesNotExist:
        print("[ERROR] Habitación no encontrada")
        return False

    # === UPDATE ===
    print("\n--- 3. ACTUALIZAR HABITACIÓN ---")
    update_data = {
        'name': 'Habitación CRUD Test - Actualizada',
        'description': 'Habitación actualizada en el test CRUD',
        'room_type': 'MEETING',
        'capacity': 15,
        'permissions': 'private',
        'length': 25,
        'width': 20,
        'height': 10,
        'color_primary': '#2196F3',
        'material_type': 'METAL',
        'opacity': 0.9,
        'mass': 750.0,
        'density': 0.9,
        'friction': 0.4,
        'restitution': 0.3,
        'temperature': 22.0,
        'lighting_intensity': 90,
        'sound_ambient': 'meeting_room.mp3',
        'special_properties': '{"updated": true, "test": "crud_flow"}'
    }

    update_form = RoomForm(data=update_data, instance=read_room, user=user)
    if update_form.is_valid():
        updated_room = update_form.save()
        print("[OK] Habitación actualizada exitosamente")
        print(f"  Nuevo nombre: {updated_room.name}")
        print(f"  Nuevo tipo: {updated_room.room_type}")
        print(f"  Nueva capacidad: {updated_room.capacity}")
    else:
        print("[ERROR] Error al actualizar habitación:")
        for field, errors in update_form.errors.items():
            print(f"  {field}: {errors}")
        return False

    # === DELETE ===
    print("\n--- 4. ELIMINAR HABITACIÓN ---")
    try:
        room_name = updated_room.name
        room_id = updated_room.pk
        updated_room.delete()
        print("[OK] Habitación eliminada exitosamente")
        print(f"  Nombre eliminado: {room_name}")
        print(f"  ID eliminado: {room_id}")

        # Verificar que ya no existe
        try:
            Room.objects.get(pk=room_id)
            print("[ERROR] La habitación aún existe después de eliminar")
            return False
        except Room.DoesNotExist:
            print("[OK] Confirmado: La habitación ya no existe en la base de datos")

    except Exception as e:
        print(f"[ERROR] Error al eliminar habitación: {e}")
        return False

    return True

def test_form_validations():
    """Prueba las validaciones del formulario"""
    print("\n=== Test de Validaciones del Formulario ===\n")

    user = User.objects.get(username='crud_test_user')

    # Test 1: Formulario vacío (debe fallar)
    print("--- Test 1: Formulario vacío ---")
    empty_form = RoomForm(data={}, user=user)
    if not empty_form.is_valid():
        print("[OK] Formulario vacío correctamente rechazado")
        if 'name' in empty_form.errors and 'room_type' in empty_form.errors:
            print("[OK] Campos requeridos correctamente validados")
        else:
            print("[ERROR] Campos requeridos no validados correctamente")
            return False
    else:
        print("[ERROR] Formulario vacío debería ser inválido")
        return False

    # Test 2: Solo campos requeridos (debe pasar)
    print("\n--- Test 2: Solo campos requeridos ---")
    minimal_data = {
        'name': 'Habitación Mínima',
        'room_type': 'OFFICE'
    }
    minimal_form = RoomForm(data=minimal_data, user=user)
    if minimal_form.is_valid():
        room = minimal_form.save(commit=False)
        room.owner = user
        room.creator = user
        room.save()
        print("[OK] Habitación con campos mínimos creada exitosamente")
        # Limpiar
        room.delete()
    else:
        print("[ERROR] Error con campos mínimos:")
        for field, errors in minimal_form.errors.items():
            print(f"  {field}: {errors}")
        return False

    # Test 3: Nombre duplicado (debe fallar)
    print("\n--- Test 3: Nombre duplicado ---")
    # Crear primera habitación
    Room.objects.create(
        name='Habitación Duplicada',
        room_type='OFFICE',
        owner=user,
        creator=user
    )

    duplicate_data = {
        'name': 'Habitación Duplicada',  # Mismo nombre
        'room_type': 'MEETING'
    }
    duplicate_form = RoomForm(data=duplicate_data, user=user)
    if not duplicate_form.is_valid():
        print("[OK] Nombre duplicado correctamente rechazado")
        if 'name' in duplicate_form.errors:
            print("[OK] Error de unicidad correctamente detectado")
        else:
            print("[ERROR] Error de unicidad no detectado")
            return False
    else:
        print("[ERROR] Nombre duplicado debería ser rechazado")
        return False

    # Limpiar
    Room.objects.filter(name='Habitación Duplicada').delete()

    return True

if __name__ == '__main__':
    try:
        print("Iniciando tests completos del sistema CRUD de habitaciones\n")

        success1 = test_crud_flow()
        success2 = test_form_validations()

        if success1 and success2:
            print("\n" + "="*60)
            print("EXITO: ¡TODOS LOS TESTS PASARON EXITOSAMENTE!")
            print("="*60)
            print("\nFuncionalidades verificadas:")
            print("[OK] Creación de habitaciones con validaciones")
            print("[OK] Lectura de datos de habitaciones")
            print("[OK] Actualización de habitaciones existentes")
            print("[OK] Eliminación de habitaciones")
            print("[OK] Validaciones de campos requeridos")
            print("[OK] Validaciones de unicidad")
            print("[OK] Manejo de campos opcionales")
            print("[OK] Integración completa del formulario")
            print("\nEXITO: El sistema CRUD está completamente funcional!")
            sys.exit(0)
        else:
            print("\n" + "="*60)
            print("ERROR: ALGUNOS TESTS FALLARON")
            print("="*60)
            sys.exit(1)

    except Exception as e:
        print(f"\nERROR CRITICO: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)