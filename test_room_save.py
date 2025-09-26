#!/usr/bin/env python
"""
Script para probar el guardado de habitaciones y debuggear problemas
"""
import os
import sys
import django
from django.conf import settings

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'panel.settings')
django.setup()

from django.contrib.auth.models import User
from rooms.models import Room
from rooms.forms import RoomForm
import logging

# Configurar logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def test_room_save():
    """Prueba guardar una habitación existente"""
    try:
        # Obtener usuario admin
        try:
            user = User.objects.filter(is_superuser=True).first()
            if not user:
                user = User.objects.filter(is_staff=True).first()
            if not user:
                user = User.objects.first()
            if not user:
                logger.error("No hay usuarios en la base de datos")
                return
            logger.info(f"Usando usuario: {user.username}")
        except Exception as e:
            logger.error(f"Error obteniendo usuario: {e}")
            return

        # Obtener una habitación existente
        try:
            room = Room.objects.first()
            if not room:
                logger.error("No hay habitaciones en la base de datos")
                return
            logger.info(f"Probando con habitación: {room.name} (ID: {room.pk})")
        except Exception as e:
            logger.error(f"Error obteniendo habitación: {e}")
            return

        # Datos de prueba para actualizar
        test_data = {
            'name': room.name,  # Mantener el mismo nombre
            'description': 'Descripción de prueba actualizada',
            'room_type': 'OFFICE',
            'capacity': 10,
            'permissions': 'public',
            'length': 30,
            'width': 30,
            'height': 10,
            'color_primary': '#2196f3',
            'color_secondary': '#1976d2',
            'material_type': 'CONCRETE',
            'opacity': 1.0,
            'mass': 1000.0,
            'density': 2.4,
            'friction': 0.5,
            'restitution': 0.3,
            'is_active': True,
            'health': 100,
            'temperature': 22.0,
            'lighting_intensity': 50,
            'special_properties': '{"test": "value"}'
        }

        logger.info("=== CREANDO FORMULARIO ===")
        logger.info(f"Datos enviados: {test_data}")

        # Crear formulario
        form = RoomForm(data=test_data, instance=room, user=user)
        logger.info(f"Formulario creado. Campos: {list(form.fields.keys())}")
        logger.info(f"Formulario bound: {form.is_bound}")

        # Verificar validación
        is_valid = form.is_valid()
        logger.info(f"form.is_valid(): {is_valid}")

        if not is_valid:
            logger.error("=== ERRORES DE VALIDACIÓN ===")
            logger.error(f"form.errors: {dict(form.errors)}")
            logger.error(f"form.non_field_errors: {form.non_field_errors()}")

            # Log detallado de cada campo
            for field_name, field_errors in form.errors.items():
                logger.error(f"Campo '{field_name}': {field_errors}")
                if field_name in form.fields:
                    field_value = test_data.get(field_name, 'NO_VALUE')
                    logger.error(f"  Valor enviado: {field_value}")
                    logger.error(f"  Tipo de campo: {type(form.fields[field_name])}")

            # Verificar si hay errores de unicidad
            if 'name' in form.errors:
                existing_rooms = Room.objects.filter(name=test_data['name']).exclude(pk=room.pk)
                logger.error(f"Habitaciones con nombre '{test_data['name']}': {list(existing_rooms.values_list('id', 'name'))}")

        else:
            logger.info("=== FORMULARIO VÁLIDO - INTENTANDO GUARDAR ===")
            try:
                # Intentar guardar sin commit primero
                room_instance = form.save(commit=False)
                logger.info(f"save(commit=False) exitoso. Room instance: {room_instance}")

                # Verificar campos del modelo antes de guardar
                logger.info("=== VERIFICANDO CAMPOS DEL MODELO ===")
                for field in room_instance._meta.fields:
                    value = getattr(room_instance, field.name, None)
                    logger.info(f"  {field.name}: {value} (tipo: {type(value)})")

                # Ahora guardar realmente
                saved_room = form.save()
                logger.info(f"form.save() exitoso. Room guardada: {saved_room.name} (ID: {saved_room.pk})")

            except Exception as save_error:
                logger.error(f"=== ERROR DURANTE GUARDADO ===")
                logger.error(f"Error: {save_error}")
                logger.error(f"Error type: {type(save_error)}")
                import traceback
                logger.error(f"Traceback: {traceback.format_exc()}")

    except Exception as e:
        logger.error(f"=== ERROR GENERAL ===")
        logger.error(f"Error: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")

if __name__ == '__main__':
    test_room_save()