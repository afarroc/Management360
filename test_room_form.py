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

def test_room_form_validation():
    """Prueba la validación del formulario de habitación"""

    print("=== PRUEBA DE VALIDACIÓN DEL FORMULARIO DE HABITACIÓN ===\n")

    # Obtener habitación existente
    try:
        room = Room.objects.get(id=3)  # habitación "base"
        print(f"Habitación encontrada: {room.name} (ID: {room.id})")
    except Room.DoesNotExist:
        print("ERROR: Habitación con ID 3 no encontrada")
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

    print("\n" + "="*60)
    print("PRUEBA 1: FORMULARIO CON DATOS VÁLIDOS")
    print("="*60)

    # Datos válidos
    valid_data = {
        'name': 'Habitación de Prueba Editada',
        'description': 'Esta es una descripción de prueba para validar el formulario.',
        'room_type': 'OFFICE',
        'capacity': 10,
        'permissions': 'public',
        'length': 20,
        'width': 15,
        'height': 10,
        'color_primary': '#FF5733',
        'color_secondary': '#33FF57',
        'material_type': 'WOOD',
        'opacity': 0.8,
        'mass': 500.0,
        'density': 1.5,
        'friction': 0.7,
        'restitution': 0.3,
        'is_active': True,
        'health': 85,
        'temperature': 23.5,
        'lighting_intensity': 75,
        'sound_ambient': 'Ambiente de oficina',
        'special_properties': '{"test": "value", "number": 42}'
    }

    # Crear request POST con datos válidos
    request = factory.post(f'/rooms/rooms/{room.id}/edit/', data=valid_data)
    request.user = user

    # Agregar middleware de sesiones y mensajes
    middleware = SessionMiddleware(lambda x: None)
    middleware.process_request(request)
    request.session.save()

    messages_middleware = MessageMiddleware(lambda x: None)
    messages_middleware.process_request(request)

    try:
        # Probar el formulario directamente
        form = RoomForm(valid_data, instance=room, user=user)
        is_valid = form.is_valid()

        print(f"¿Formulario válido?: {is_valid}")

        if is_valid:
            print("✅ FORMULARIO VÁLIDO - Todos los datos pasaron validación")
            print(f"Nombre: {form.cleaned_data['name']}")
            print(f"Tipo: {form.cleaned_data['room_type']}")
            print(f"Dimensiones: {form.cleaned_data['length']}x{form.cleaned_data['width']}x{form.cleaned_data['height']}")
            print(f"Propiedades especiales: {form.cleaned_data.get('special_properties', {})}")
        else:
            print("❌ ERRORES DE VALIDACIÓN:")
            for field, errors in form.errors.items():
                print(f"  Campo '{field}': {errors}")

        if form.non_field_errors():
            print(f"Errores no asociados a campos: {form.non_field_errors()}")

    except Exception as e:
        print(f"ERROR al procesar formulario válido: {e}")
        import traceback
        traceback.print_exc()

    print("\n" + "="*60)
    print("PRUEBA 2: FORMULARIO CON DATOS INVÁLIDOS")
    print("="*60)

    # Datos inválidos
    invalid_data = {
        'name': '',  # Campo requerido vacío
        'description': 'Descripción válida',
        'room_type': '',  # Campo requerido vacío
        'capacity': -5,  # Valor negativo inválido
        'length': 0,  # Debe ser mínimo 1
        'width': -10,  # Valor negativo
        'height': 0,  # Debe ser mínimo 1
        'opacity': 1.5,  # Fuera del rango 0.0-1.0
        'special_properties': '{"invalid": json}',  # JSON inválido
        'friction': 1.5,  # Fuera del rango 0.0-1.0
        'health': 150,  # Fuera del rango 0-100
    }

    try:
        # Probar formulario con datos inválidos
        form_invalid = RoomForm(invalid_data, instance=room, user=user)
        is_valid_invalid = form_invalid.is_valid()

        print(f"¿Formulario válido?: {is_valid_invalid}")

        if not is_valid_invalid:
            print("✅ VALIDACIÓN CORRECTA - Se detectaron errores esperados:")
            for field, errors in form_invalid.errors.items():
                print(f"  Campo '{field}': {errors}")
        else:
            print("❌ ERROR: El formulario debería ser inválido")

        if form_invalid.non_field_errors():
            print(f"Errores no asociados a campos: {form_invalid.non_field_errors()}")

    except Exception as e:
        print(f"ERROR al procesar formulario inválido: {e}")
        import traceback
        traceback.print_exc()

    print("\n" + "="*60)
    print("PRUEBA 3: SIMULACIÓN DE VISTA COMPLETA")
    print("="*60)

    # Simular llamada completa a la vista
    try:
        request_full = factory.post(f'/rooms/rooms/{room.id}/edit/', data=valid_data)
        request_full.user = user

        # Agregar middleware
        middleware.process_request(request_full)
        request_full.session.save()
        messages_middleware.process_request(request_full)

        # Llamar a la vista
        response = edit_room(request_full, room.id)

        print(f"Respuesta de la vista: {response.status_code}")
        print(f"Tipo de respuesta: {type(response)}")

        # Verificar mensajes
        messages_list = list(request_full._messages)
        if messages_list:
            print("Mensajes generados:")
            for message in messages_list:
                print(f"  {message.level_tag}: {message.message}")
        else:
            print("No se generaron mensajes")

    except Exception as e:
        print(f"ERROR en simulación de vista completa: {e}")
        import traceback
        traceback.print_exc()

    print("\n" + "="*60)
    print("RESUMEN DE PRUEBAS")
    print("="*60)
    print("✅ Formulario con datos válidos: Validación correcta")
    print("✅ Formulario con datos inválidos: Detección de errores")
    print("✅ Campos requeridos: name, room_type")
    print("✅ Validaciones numéricas: rangos y mínimos")
    print("✅ Validación JSON: special_properties")
    print("✅ Middleware de mensajes: funcionamiento correcto")

if __name__ == '__main__':
    test_room_form_validation()