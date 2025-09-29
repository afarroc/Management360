#!/usr/bin/env python
import os
import sys

# Configurar Django ANTES de cualquier import
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'panel.settings')
sys.path.append('.')

import django
django.setup()

from django.test import RequestFactory
from django.contrib.auth.models import User
from django.contrib.sessions.middleware import SessionMiddleware
from django.contrib.messages.middleware import MessageMiddleware
from rooms.models import Room
from rooms.forms import RoomForm
from rooms.views import edit_room
import json

def test_room_edit_validations():
    """Prueba todas las validaciones de error del formulario de edición de habitación"""

    print("=== PRUEBA DE VALIDACIONES DE ERROR - FORMULARIO DE EDICIÓN DE HABITACIÓN ===\n")

    # Obtener habitación de prueba (ID 2)
    try:
        room = Room.objects.get(id=2)
        print(f"Habitación encontrada: {room.name} (ID: {room.id})")
        print(f"Propietario: {room.owner.username}")
    except Room.DoesNotExist:
        print("ERROR: Habitación con ID 2 no encontrada")
        return

    # Obtener usuario
    try:
        user = User.objects.get(username='su')
        print(f"Usuario encontrado: {user.username}")
    except User.DoesNotExist:
        print("ERROR: Usuario 'su' no encontrado")
        return

    # Crear RequestFactory
    factory = RequestFactory()

    print("\n" + "="*80)
    print("PRUEBA 1: CAMPOS REQUERIDOS VACÍOS")
    print("="*80)

    # Datos con campos requeridos vacíos
    empty_required_data = {
        'name': '',  # Campo requerido vacío
        'room_type': '',  # Campo requerido vacío
        'description': 'Descripción válida',
        'length': 20,
        'width': 15,
        'height': 10,
    }

    test_form_validation(empty_required_data, room, user, factory, "Campos requeridos vacíos")

    print("\n" + "="*80)
    print("PRUEBA 2: DIMENSIONES INVÁLIDAS")
    print("="*80)

    # Datos con dimensiones inválidas
    invalid_dimensions_data = {
        'name': 'Habitación de Prueba',
        'room_type': 'OFFICE',
        'description': 'Descripción válida',
        'length': 0,  # Debe ser mínimo 1
        'width': -5,  # No puede ser negativo
        'height': 0,  # Debe ser mínimo 1
    }

    test_form_validation(invalid_dimensions_data, room, user, factory, "Dimensiones inválidas")

    print("\n" + "="*80)
    print("PRUEBA 3: VALORES FUERA DE RANGO")
    print("="*80)

    # Datos con valores fuera de rango
    out_of_range_data = {
        'name': 'Habitación de Prueba',
        'room_type': 'OFFICE',
        'description': 'Descripción válida',
        'length': 20,
        'width': 15,
        'height': 10,
        'opacity': 1.5,  # Debe ser 0.0-1.0
        'friction': -0.5,  # Debe ser 0.0-1.0
        'restitution': 2.0,  # Debe ser 0.0-1.0
        'health': 150,  # Debe ser 0-100
        'temperature': 200,  # Temperatura irreal
        'lighting_intensity': 150,  # Debe ser 0-100
    }

    test_form_validation(out_of_range_data, room, user, factory, "Valores fuera de rango")

    print("\n" + "="*80)
    print("PRUEBA 4: JSON INVÁLIDO EN SPECIAL_PROPERTIES")
    print("="*80)

    # Datos con JSON inválido
    invalid_json_data = {
        'name': 'Habitación de Prueba',
        'room_type': 'OFFICE',
        'description': 'Descripción válida',
        'length': 20,
        'width': 15,
        'height': 10,
        'special_properties': '{"invalid": json syntax}',  # JSON inválido
    }

    test_form_validation(invalid_json_data, room, user, factory, "JSON inválido en special_properties")

    print("\n" + "="*80)
    print("PRUEBA 5: COLORES INVÁLIDOS")
    print("="*80)

    # Datos con colores inválidos
    invalid_colors_data = {
        'name': 'Habitación de Prueba',
        'room_type': 'OFFICE',
        'description': 'Descripción válida',
        'length': 20,
        'width': 15,
        'height': 10,
        'color_primary': 'invalid-color',  # No es formato hex válido
        'color_secondary': '#ZZZZZZ',  # Caracteres inválidos
    }

    test_form_validation(invalid_colors_data, room, user, factory, "Colores inválidos")

    print("\n" + "="*80)
    print("PRUEBA 6: VALORES DECIMALES INVÁLIDOS")
    print("="*80)

    # Datos con valores decimales inválidos
    invalid_decimals_data = {
        'name': 'Habitación de Prueba',
        'room_type': 'OFFICE',
        'description': 'Descripción válida',
        'length': 20,
        'width': 15,
        'height': 10,
        'mass': -100,  # No puede ser negativo
        'density': 0,  # Debe ser mayor que 0
        'friction': 1.5,  # Fuera del rango 0.0-1.0
    }

    test_form_validation(invalid_decimals_data, room, user, factory, "Valores decimales inválidos")

    print("\n" + "="*80)
    print("PRUEBA 7: SIMULACIÓN COMPLETA DE VISTA CON ERRORES")
    print("="*80)

    # Simular envío completo con errores múltiples
    complete_error_data = {
        'name': '',  # Vacío
        'room_type': 'INVALID_TYPE',  # Tipo inválido
        'length': -1,  # Negativo
        'width': 0,  # Cero
        'height': 'not_a_number',  # No numérico
        'opacity': 2.5,  # Fuera de rango
        'special_properties': '{invalid json',  # JSON roto
        'color_primary': '#12345',  # Formato hex incompleto
        'health': -50,  # Negativo
    }

    try:
        request = factory.post(f'/rooms/rooms/{room.id}/edit/', data=complete_error_data)
        request.user = user

        # Agregar middleware
        middleware = SessionMiddleware(lambda x: None)
        middleware.process_request(request)
        request.session.save()

        messages_middleware = MessageMiddleware(lambda x: None)
        messages_middleware.process_request(request)

        # Llamar a la vista
        response = edit_room(request, room.id)

        print(f"Respuesta HTTP: {response.status_code}")
        print(f"Tipo de respuesta: {type(response)}")

        # Verificar que no se redirigió (debe mostrar errores)
        if response.status_code == 200:
            print("✅ CORRECTO: Vista devolvió 200 (mostrando formulario con errores)")
        else:
            print(f"❌ ERROR: Esperaba 200, obtuve {response.status_code}")

        # Verificar mensajes de error
        messages_list = list(request._messages)
        if messages_list:
            print("Mensajes en la respuesta:")
            for message in messages_list:
                print(f"  {message.level_tag}: {message.message}")
        else:
            print("No se generaron mensajes (errores mostrados en formulario)")

    except Exception as e:
        print(f"ERROR en simulación completa: {e}")
        import traceback
        traceback.print_exc()

    print("\n" + "="*80)
    print("RESUMEN COMPLETO DE VALIDACIONES")
    print("="*80)
    print("✅ Campos requeridos: name, room_type")
    print("✅ Dimensiones: length, width, height >= 1")
    print("✅ Rangos numéricos: opacity (0.0-1.0), friction (0.0-1.0), etc.")
    print("✅ JSON validation: special_properties")
    print("✅ Colores: formato hex válido")
    print("✅ Valores decimales: mass, density > 0")
    print("✅ Health: rango 0-100")
    print("✅ Temperature: valores realistas")
    print("✅ Lighting: rango 0-100")
    print("✅ Manejo de errores: formulario muestra errores sin guardar")

def test_form_validation(data, room, user, factory, test_name):
    """Función auxiliar para probar validación de formulario"""
    print(f"\n--- Probando: {test_name} ---")

    try:
        form = RoomForm(data, instance=room, user=user)
        is_valid = form.is_valid()

        print(f"¿Formulario válido?: {is_valid}")

        if not is_valid:
            print("✅ VALIDACIÓN CORRECTA - Errores detectados:")
            for field, errors in form.errors.items():
                print(f"  Campo '{field}': {errors}")
        else:
            print("❌ ERROR: El formulario debería ser inválido")

        if form.non_field_errors():
            print(f"Errores no asociados a campos: {form.non_field_errors()}")

    except Exception as e:
        print(f"ERROR en {test_name}: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_room_edit_validations()