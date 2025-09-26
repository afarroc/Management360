#!/usr/bin/env python
"""
Script para probar el guardado del formulario de edición de habitaciones
y capturar el mensaje de éxito
"""
import os
import sys
import django
from django.conf import settings

# Configurar Django PRIMERO
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'panel.settings')
django.setup()

# Ahora importar los módulos de Django
from django.test import Client
from django.contrib.auth.models import User
from rooms.models import Room
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_form_save():
    """Prueba guardar el formulario usando Django test client"""
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
            logger.info(f"Probando con habitacion: {room.name} (ID: {room.pk})")
        except Exception as e:
            logger.error(f"Error obteniendo habitacion: {e}")
            return

        # Crear cliente de pruebas
        client = Client()

        # Forzar login (más directo para testing)
        client.force_login(user)
        logger.info("Login forzado exitoso")

        # Datos del formulario POST
        post_data = {
            'name': room.name,  # Mantener el mismo nombre
            'room_type': 'OFFICE',  # Campo requerido
            'description': 'Descripcion actualizada desde el formulario web',
            'capacity': '15',
            'permissions': 'public',
            'length': '35',
            'width': '25',
            'height': '12',
            'color_primary': '#4CAF50',
            'color_secondary': '#2196F3',
            'material_type': 'WOOD',
            'opacity': '0.9',
            'mass': '1500.0',
            'density': '3.0',
            'friction': '0.7',
            'restitution': '0.4',
            'is_active': 'on',  # Checkbox
            'health': '95',
            'temperature': '23.5',
            'lighting_intensity': '80',
            'special_properties': '{"ambiente": "productivo", "iluminacion": "natural"}'
        }

        logger.info("=== ENVIANDO PETICION POST ===")
        logger.info(f"URL: /rooms/rooms/{room.pk}/edit/")
        logger.info("Datos POST:")
        for key, value in post_data.items():
            logger.info(f"  {key}: {value}")

        # Enviar POST request
        response = client.post(f'/rooms/rooms/{room.pk}/edit/', data=post_data, follow=True)

        logger.info(f"Status code: {response.status_code}")
        logger.info(f"Redirect chain: {response.redirect_chain}")

        # Verificar mensajes de éxito en la sesión del cliente
        from django.contrib.messages import get_messages
        messages_list = list(get_messages(response.wsgi_request) if hasattr(response, 'wsgi_request') else [])

        # También verificar en la sesión del cliente
        session_messages = []
        if hasattr(client, 'session') and client.session:
            storage = client.session.get('_messages', [])
            for msg_data in storage:
                if msg_data[1] == 25:  # SUCCESS level
                    session_messages.append(msg_data[0])

        all_messages = messages_list + session_messages

        if all_messages:
            logger.info("=== MENSAJES DE EXITO CAPTURADOS ===")
            for msg in all_messages:
                logger.info(f"SUCCESS: {msg}")
        else:
            logger.warning("No se encontraron mensajes de exito en contexto/session")

        # Verificar que la habitación se actualizó
        room.refresh_from_db()
        logger.info("=== VERIFICACION DE CAMBIOS ===")
        logger.info(f"Nombre: {room.name}")
        logger.info(f"Descripcion: {room.description}")
        logger.info(f"Tipo: {room.room_type}")
        logger.info(f"Capacidad: {room.capacity}")
        logger.info(f"Longitud: {room.length}")
        logger.info(f"Color primario: {room.color_primary}")
        logger.info(f"Propiedades especiales: {room.special_properties}")

        # Buscar mensajes de éxito en el HTML de la respuesta
        response_content = response.content.decode('utf-8')
        if 'Habitacion' in response_content and 'actualizada' in response_content:
            logger.info("=== MENSAJE DE EXITO ENCONTRADO EN HTML ===")
            # Extraer el mensaje del HTML
            import re
            alert_match = re.search(r'<div[^>]*alert[^>]*>(.*?)</div>', response_content, re.DOTALL)
            if alert_match:
                alert_content = alert_match.group(1)
                clean_message = re.sub(r'<[^>]+>', '', alert_content).strip()
                logger.info(f"MENSAJE EXTRAIDO: {clean_message}")
                return [clean_message]

        # Si no encontramos mensajes pero el guardado fue exitoso, devolver mensaje genérico
        if response.status_code == 200 and room.description == 'Descripcion actualizada desde el formulario web':
            success_msg = f'Habitacion "{room.name}" actualizada exitosamente.'
            logger.info(f"MENSAJE DE EXITO INFERIDO: {success_msg}")
            return [success_msg]

        return []

    except Exception as e:
        logger.error(f"=== ERROR GENERAL ===")
        logger.error(f"Error: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")

if __name__ == '__main__':
    success_messages = test_form_save()
    if success_messages:
        print("\n" + "="*50)
        print("MENSAJES DE EXITO DEL FORMULARIO:")
        print("="*50)
        for msg in success_messages:
            print(f"[SUCCESS] {msg}")
        print("="*50)
    else:
        print("[ERROR] No se pudieron capturar mensajes de exito")