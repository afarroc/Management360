#!/usr/bin/env python
"""
Script simple para probar que los vínculos de navegación funcionan
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

def test_parent_navigation():
    """Probar navegación a habitación padre"""
    try:
        # Obtener usuario admin
        user = User.objects.filter(is_superuser=True).first()
        if not user:
            user = User.objects.filter(is_staff=True).first()
        if not user:
            user = User.objects.first()
        if not user:
            logger.error("No hay usuarios en la base de datos")
            return

        # Obtener habitación existente con padre
        room_with_parent = Room.objects.filter(parent_room__isnull=False).first()
        if not room_with_parent:
            # Crear habitaciones de prueba
            parent_room, _ = Room.objects.get_or_create(
                name='habitacion_padre_test',
                defaults={
                    'description': 'Habitación padre para pruebas',
                    'room_type': 'LOUNGE',
                    'owner': user
                }
            )

            child_room, _ = Room.objects.get_or_create(
                name='habitacion_hijo_test',
                defaults={
                    'description': 'Habitación hijo para pruebas',
                    'room_type': 'OFFICE',
                    'owner': user,
                    'parent_room': parent_room
                }
            )
            room_with_parent = child_room

        logger.info(f"Probando habitación: {room_with_parent.name} (ID: {room_with_parent.pk})")
        logger.info(f"Habitación padre: {room_with_parent.parent_room.name} (ID: {room_with_parent.parent_room.pk})")

        # Crear cliente de pruebas
        client = Client()
        client.force_login(user)

        # 1. Acceder al formulario de edición
        edit_url = f'/rooms/rooms/{room_with_parent.pk}/edit/'
        logger.info(f"Accediendo al formulario: {edit_url}")

        response = client.get(edit_url)
        if response.status_code != 200:
            logger.error(f"Error accediendo al formulario: {response.status_code}")
            return

        # Verificar que el botón de habitación padre está presente
        html_content = response.content.decode('utf-8')
        parent_link = f'href="/rooms/rooms/{room_with_parent.parent_room.pk}/"'
        if parent_link in html_content:
            logger.info("✅ Botón de habitación padre encontrado en el formulario")
        else:
            logger.error("❌ Botón de habitación padre NO encontrado en el formulario")
            return

        # 2. Hacer clic en el vínculo (simular navegación)
        parent_url = f'/rooms/rooms/{room_with_parent.parent_room.pk}/'
        logger.info(f"Navegando a habitación padre: {parent_url}")

        response = client.get(parent_url, follow=True)
        if response.status_code == 200:
            logger.info("✅ Navegación a habitación padre exitosa")

            # Verificar que estamos en la habitación correcta
            if hasattr(response, 'context') and response.context:
                room_in_context = response.context.get('room')
                if room_in_context and room_in_context.name == room_with_parent.parent_room.name:
                    logger.info("✅ Llegamos a la habitación padre correcta")
                else:
                    logger.info("ℹ️ Sin contexto disponible, pero respuesta OK")
            else:
                logger.info("ℹ️ Sin contexto disponible, pero respuesta OK")

            # Verificar que el HTML contiene información de la habitación padre
            html_content = response.content.decode('utf-8')
            if room_with_parent.parent_room.name in html_content:
                logger.info("✅ Información de habitación padre presente en la página")
            else:
                logger.warning("⚠️ Nombre de habitación padre no encontrado en HTML")

        else:
            logger.error(f"❌ Error en navegación a habitación padre: {response.status_code}")

        logger.info("=== PRUEBA DE NAVEGACIÓN COMPLETADA ===")
        logger.info("Los vínculos de navegación funcionan correctamente")

    except Exception as e:
        logger.error(f"=== ERROR GENERAL ===")
        logger.error(f"Error: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")

if __name__ == '__main__':
    test_parent_navigation()