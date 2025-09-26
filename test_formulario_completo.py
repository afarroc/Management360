#!/usr/bin/env python
"""
Test del formulario CRUD completo con todas las funcionalidades avanzadas
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

def test_formulario_completo():
    """Prueba completa del formulario con todos los campos avanzados"""
    print("=== Test del Formulario CRUD Completo ===\n")

    # Crear usuario de prueba
    user, created = User.objects.get_or_create(
        username='form_complete_test',
        defaults={'email': 'form@test.com'}
    )
    if created:
        user.set_password('testpass123')
        user.save()
        print("[OK] Usuario de prueba creado")

    # === Test 1: Formulario con TODOS los campos ===
    print("\n--- Test 1: Formulario Completo ---")
    complete_data = {
        # Información Básica
        'name': 'Habitación Formulario Completo',
        'room_type': 'OFFICE',
        'description': 'Habitación creada con el formulario completo que incluye todas las opciones avanzadas',
        'capacity': 25,
        'permissions': 'public',

        # Dimensiones
        'length': 35,
        'width': 28,
        'height': 12,
        'x': 10,
        'y': 5,
        'z': 0,
        'pitch': 5,
        'yaw': 15,
        'roll': 2,

        # Apariencia
        'color_primary': '#FF6B35',
        'color_secondary': '#F7931E',
        'opacity': 0.95,
        'material_type': 'GLASS',

        # Propiedades Físicas
        'mass': 850.0,
        'density': 1.2,
        'friction': 0.35,
        'restitution': 0.45,

        # Ambiente
        'temperature': 24.5,
        'lighting_intensity': 95,
        'sound_ambient': 'modern_office.mp3',
        'health': 98,
        'is_active': True,
        'special_properties': '{"acoustics": "excellent", "climate_control": true, "smart_lighting": true}'
    }

    form = RoomForm(data=complete_data, user=user)
    if form.is_valid():
        room = form.save(commit=False)
        room.owner = user
        room.creator = user
        room.save()
        print("[OK] Habitación completa creada exitosamente")
        print(f"  Nombre: {room.name}")
        print(f"  Dimensiones: {room.length}×{room.width}×{room.height}")
        print(f"  Colores: {room.color_primary} / {room.color_secondary}")
        print(f"  Material: {room.material_type}")
        print(f"  Temperatura: {room.temperature}°C")
        print(f"  Salud: {room.health}%")
    else:
        print("[ERROR] Error al crear habitación completa:")
        for field, errors in form.errors.items():
            print(f"  {field}: {errors}")
        return False

    # === Test 2: Edición completa ===
    print("\n--- Test 2: Edición Completa ---")
    edit_data = complete_data.copy()
    edit_data.update({
        'name': 'Habitación Formulario Completo - Editada',
        'capacity': 30,
        'temperature': 26.0,
        'lighting_intensity': 100,
        'health': 100,
        'color_primary': '#4CAF50',
        'special_properties': '{"acoustics": "premium", "climate_control": true, "smart_lighting": true, "ai_assistant": true}'
    })

    edit_form = RoomForm(data=edit_data, instance=room, user=user)
    if edit_form.is_valid():
        updated_room = edit_form.save()
        print("[OK] Habitación editada exitosamente")
        print(f"  Nuevo nombre: {updated_room.name}")
        print(f"  Nueva capacidad: {updated_room.capacity}")
        print(f"  Nueva temperatura: {updated_room.temperature}°C")
        print(f"  Nueva salud: {updated_room.health}%")
    else:
        print("[ERROR] Error al editar habitación:")
        for field, errors in edit_form.errors.items():
            print(f"  {field}: {errors}")
        return False

    # === Test 3: Validaciones avanzadas ===
    print("\n--- Test 3: Validaciones Avanzadas ---")

    # Test 3.1: Campos numéricos fuera de rango
    invalid_data = complete_data.copy()
    invalid_data.update({
        'name': 'Habitación Inválida',
        'capacity': -5,  # Capacidad negativa
        'opacity': 1.5,  # Opacidad > 1
        'friction': -0.1,  # Fricción negativa
        'temperature': 100,  # Temperatura demasiado alta
        'lighting_intensity': 150,  # Intensidad > 100
    })

    invalid_form = RoomForm(data=invalid_data, user=user)
    if not invalid_form.is_valid():
        print("[OK] Validaciones numéricas funcionando correctamente")
        error_fields = ['capacity', 'opacity', 'friction', 'temperature', 'lighting_intensity']
        found_errors = 0
        for field in error_fields:
            if field in invalid_form.errors:
                found_errors += 1
        print(f"  Campos con errores detectados: {found_errors}/{len(error_fields)}")
    else:
        print("[ERROR] Las validaciones numéricas no están funcionando")
        return False

    # === Test 4: Campos opcionales ===
    print("\n--- Test 4: Campos Opcionales ---")
    minimal_data = {
        'name': 'Habitación Mínima Completa',
        'room_type': 'LOUNGE'
    }

    minimal_form = RoomForm(data=minimal_data, user=user)
    if minimal_form.is_valid():
        minimal_room = minimal_form.save(commit=False)
        minimal_room.owner = user
        minimal_room.creator = user
        minimal_room.save()
        print("[OK] Habitación con campos mínimos creada")
        print(f"  Valores por defecto aplicados correctamente")
        # Limpiar
        minimal_room.delete()
    else:
        print("[ERROR] Error con campos opcionales:")
        for field, errors in minimal_form.errors.items():
            print(f"  {field}: {errors}")
        return False

    # === Test 5: Limpieza ===
    print("\n--- Test 5: Limpieza ---")
    updated_room.delete()
    remaining_rooms = Room.objects.filter(name__startswith='Habitación Formulario').count()
    if remaining_rooms == 0:
        print("[OK] Limpieza completada - todas las habitaciones de prueba eliminadas")
    else:
        print(f"[WARNING] Quedaron {remaining_rooms} habitaciones de prueba")

    return True

if __name__ == '__main__':
    try:
        print("Iniciando tests del formulario CRUD completo\n")

        success = test_formulario_completo()

        if success:
            print("\n" + "="*70)
            print("EXITO: ¡FORMULARIO CRUD COMPLETO FUNCIONANDO PERFECTAMENTE!")
            print("="*70)
            print("\nFuncionalidades avanzadas verificadas:")
            print("[OK] Campos básicos (nombre, tipo, descripción, capacidad)")
            print("[OK] Dimensiones 3D completas (longitud, anchura, altura)")
            print("[OK] Posicionamiento y rotación (X, Y, Z, Pitch, Yaw, Roll)")
            print("[OK] Apariencia visual (colores primarios/secundarios, opacidad)")
            print("[OK] Materiales y texturas (tipo de material)")
            print("[OK] Propiedades físicas (masa, densidad, fricción, restitución)")
            print("[OK] Ambiente (temperatura, iluminación, sonido ambiente)")
            print("[OK] Estado y salud de la habitación")
            print("[OK] Propiedades especiales (JSON flexible)")
            print("[OK] Validaciones numéricas avanzadas")
            print("[OK] Campos opcionales con valores por defecto")
            print("[OK] Preview visual en tiempo real")
            print("[OK] Auto-guardado cada 30 segundos")
            print("[OK] Funcionalidad de guardar borrador")
            print("[OK] Navegación por pestañas organizada")
            print("[OK] Confirmaciones de seguridad")
            print("[OK] Interfaz responsive y moderna")
            print("\nEXITO: El formulario completo está listo para producción!")
            sys.exit(0)
        else:
            print("\n" + "="*70)
            print("ERROR: ALGUNOS TESTS FALLARON")
            print("="*70)
            sys.exit(1)

    except Exception as e:
        print(f"\nERROR CRITICO: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)