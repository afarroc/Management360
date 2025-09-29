#!/usr/bin/env python
"""
Script para probar las conexiones de habitaciones en el formulario de edición
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
from rooms.models import Room, EntranceExit, RoomConnection
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def setup_test_connections():
    """Crear conexiones de prueba para habitaciones"""
    try:
        # Obtener habitaciones existentes
        rooms = list(Room.objects.all()[:3])  # Tomar las primeras 3 habitaciones
        if len(rooms) < 2:
            logger.error("Se necesitan al menos 2 habitaciones para crear conexiones")
            return

        logger.info(f"Configurando conexiones entre habitaciones: {[r.name for r in rooms]}")

        # Crear habitación padre si no existe
        base_room = None
        try:
            base_room = Room.objects.get(name='base')
        except Room.DoesNotExist:
            base_room = Room.objects.create(
                name='base',
                description='Habitación base principal',
                room_type='LOUNGE',
                owner=User.objects.filter(is_superuser=True).first() or User.objects.first()
            )
            logger.info(f"Creada habitación base: {base_room.name}")

        # Establecer parent_room para la primera habitación
        if rooms[0].parent_room != base_room:
            rooms[0].parent_room = base_room
            rooms[0].save()
            logger.info(f"Establecida {base_room.name} como padre de {rooms[0].name}")

        # Crear conexiones a través de EntranceExit
        if len(rooms) >= 2:
            # Crear entrada/salida en la primera habitación
            entrance1, created1 = EntranceExit.objects.get_or_create(
                room=rooms[0],
                name='Puerta Norte',
                defaults={
                    'face': 'NORTH',
                    'description': 'Salida hacia segunda habitación'
                }
            )
            if created1:
                logger.info(f"Creada entrada/salida: {entrance1.name} en {rooms[0].name}")

            # Crear entrada/salida en la segunda habitación
            entrance2, created2 = EntranceExit.objects.get_or_create(
                room=rooms[1],
                name='Puerta Sur',
                defaults={
                    'face': 'SOUTH',
                    'description': 'Entrada desde primera habitación'
                }
            )
            if created2:
                logger.info(f"Creada entrada/salida: {entrance2.name} en {rooms[1].name}")

            # Crear conexión bidireccional
            connection, created_conn = RoomConnection.objects.get_or_create(
                from_room=rooms[0],
                to_room=rooms[1],
                entrance=entrance1,
                defaults={
                    'bidirectional': True,
                    'energy_cost': 5
                }
            )
            if created_conn:
                logger.info(f"Creada conexión: {rooms[0].name} ↔ {rooms[1].name}")

        return rooms[0]  # Retornar la habitación principal para testing

    except Exception as e:
        logger.error(f"Error configurando conexiones: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return None

def test_connections_display():
    """Probar que las conexiones se muestran en el formulario"""
    try:
        # Configurar conexiones de prueba
        test_room = setup_test_connections()
        if not test_room:
            return

        # Obtener usuario admin
        user = User.objects.filter(is_superuser=True).first()
        if not user:
            user = User.objects.filter(is_staff=True).first()
        if not user:
            user = User.objects.first()
        if not user:
            logger.error("No hay usuarios en la base de datos")
            return

        # Crear cliente de pruebas
        client = Client()
        client.force_login(user)

        logger.info(f"Probando conexiones para habitación: {test_room.name} (ID: {test_room.pk})")

        # Hacer GET request al formulario de edición
        response = client.get(f'/rooms/rooms/{test_room.pk}/edit/')
        logger.info(f"Status code: {response.status_code}")

        if response.status_code == 200:
            response_content = response.content.decode('utf-8')

            # Verificar que se muestran las conexiones
            logger.info("=== VERIFICANDO CONEXIONES EN EL FORMULARIO ===")

            # Verificar habitación padre
            if test_room.parent_room:
                if f'href="/rooms/rooms/{test_room.parent_room.pk}/"' in response_content:
                    logger.info(f"✅ Habitación padre '{test_room.parent_room.name}' mostrada correctamente")
                else:
                    logger.warning(f"❌ Habitación padre '{test_room.parent_room.name}' no encontrada en el HTML")

            # Verificar habitaciones hijo
            child_rooms = test_room.child_of_rooms.all()
            if child_rooms.exists():
                for child in child_rooms:
                    if f'href="/rooms/rooms/{child.pk}/"' in response_content:
                        logger.info(f"✅ Habitación hijo '{child.name}' mostrada correctamente")
                    else:
                        logger.warning(f"❌ Habitación hijo '{child.name}' no encontrada en el HTML")

            # Verificar conexiones por EntranceExit
            entrances = test_room.entrance_exits.all()
            if entrances.exists():
                for entrance in entrances:
                    if entrance.name in response_content:
                        logger.info(f"✅ Entrada/Salida '{entrance.name}' mostrada correctamente")
                        if entrance.connection:
                            connected_room = entrance.connection.to_room if entrance.connection.from_room == test_room else entrance.connection.from_room
                            if f'href="/rooms/rooms/{connected_room.pk}/"' in response_content:
                                logger.info(f"✅ Conexión a '{connected_room.name}' mostrada correctamente")
                            else:
                                logger.warning(f"❌ Conexión a '{connected_room.name}' no encontrada")
                    else:
                        logger.warning(f"❌ Entrada/Salida '{entrance.name}' no encontrada en el HTML")

            # Verificar estructura HTML de conexiones
            if 'Conexiones y Navegación' in response_content:
                logger.info("✅ Sección 'Conexiones y Navegación' presente")
            else:
                logger.warning("❌ Sección 'Conexiones y Navegación' no encontrada")

            if 'Salida (Habitación Padre)' in response_content:
                logger.info("✅ Sección 'Salida (Habitación Padre)' presente")
            else:
                logger.warning("❌ Sección 'Salida (Habitación Padre)' no encontrada")

            if 'Entradas (Habitaciones Hijo)' in response_content:
                logger.info("✅ Sección 'Entradas (Habitaciones Hijo)' presente")
            else:
                logger.warning("❌ Sección 'Entradas (Habitaciones Hijo)' no encontrada")

            logger.info("=== PRUEBA COMPLETADA ===")
            logger.info("Las conexiones deberían mostrarse como vínculos activos en el formulario de edición")

        else:
            logger.error(f"Error en la petición GET: {response.status_code}")

    except Exception as e:
        logger.error(f"=== ERROR GENERAL ===")
        logger.error(f"Error: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")

if __name__ == '__main__':
    test_connections_display()