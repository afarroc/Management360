#!/usr/bin/env python
"""
Script para probar que los vínculos de navegación en las conexiones funcionan correctamente
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

def setup_navigation_test():
    """Configurar habitaciones y conexiones para probar navegación"""
    try:
        # Obtener usuario admin
        user = User.objects.filter(is_superuser=True).first()
        if not user:
            user = User.objects.filter(is_staff=True).first()
        if not user:
            user = User.objects.first()
        if not user:
            logger.error("No hay usuarios en la base de datos")
            return None, None

        # Crear habitaciones de prueba si no existen
        room1, created1 = Room.objects.get_or_create(
            name='oficina_principal',
            defaults={
                'description': 'Oficina principal para pruebas',
                'room_type': 'OFFICE',
                'owner': user
            }
        )

        room2, created2 = Room.objects.get_or_create(
            name='sala_reuniones',
            defaults={
                'description': 'Sala de reuniones conectada',
                'room_type': 'MEETING',
                'owner': user
            }
        )

        room3, created3 = Room.objects.get_or_create(
            name='base_central',
            defaults={
                'description': 'Base central del edificio',
                'room_type': 'LOUNGE',
                'owner': user
            }
        )

        # Establecer jerarquía: oficina_principal -> base_central
        room1.parent_room = room3
        room1.save()

        # Crear conexiones físicas
        # Puerta Norte de oficina_principal -> sala_reuniones
        entrance1, _ = EntranceExit.objects.get_or_create(
            room=room1,
            name='Puerta Norte',
            defaults={
                'face': 'NORTH',
                'description': 'Salida hacia sala de reuniones'
            }
        )

        entrance2, _ = EntranceExit.objects.get_or_create(
            room=room2,
            name='Puerta Sur',
            defaults={
                'face': 'SOUTH',
                'description': 'Entrada desde oficina principal'
            }
        )

        # Conectar las habitaciones
        connection, _ = RoomConnection.objects.get_or_create(
            from_room=room1,
            to_room=room2,
            entrance=entrance1,
            defaults={
                'bidirectional': True,
                'energy_cost': 5
            }
        )

        logger.info("=== CONFIGURACIÓN DE PRUEBA COMPLETADA ===")
        logger.info(f"Habitación principal: {room1.name} (ID: {room1.pk})")
        logger.info(f"Habitación padre: {room3.name} (ID: {room3.pk})")
        logger.info(f"Habitación conectada: {room2.name} (ID: {room2.pk})")
        logger.info(f"Conexión: {entrance1.name} -> {room2.name}")

        return room1, user

    except Exception as e:
        logger.error(f"Error configurando navegación: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return None, None

def test_navigation_links():
    """Probar que los vínculos de navegación funcionan correctamente"""
    try:
        test_room, user = setup_navigation_test()
        if not test_room or not user:
            return

        # Crear cliente de pruebas
        client = Client()
        client.force_login(user)

        logger.info("=== PROBANDO VÍNCULOS DE NAVEGACIÓN ===")

        # 1. Probar vínculo a habitación padre
        if test_room.parent_room:
            parent_url = f'/rooms/rooms/{test_room.parent_room.pk}/'
            logger.info(f"Probando vínculo a habitación padre: {parent_url}")

            response = client.get(parent_url, follow=True)
            if response.status_code == 200:
                # Verificar que estamos en la habitación correcta
                if hasattr(response, 'context') and response.context:
                    room_in_context = response.context.get('room')
                    if room_in_context and room_in_context.name == test_room.parent_room.name:
                        logger.info("✅ Vínculo a habitación padre funciona correctamente")
                    else:
                        logger.warning("❌ Vínculo a habitación padre no lleva a la habitación correcta")
                else:
                    logger.info("✅ Vínculo a habitación padre - respuesta OK (sin contexto)")
            else:
                logger.error(f"❌ Error en vínculo a habitación padre: {response.status_code}")

        # 2. Probar vínculos a habitaciones hijo
        child_rooms = test_room.child_of_rooms.all()
        if child_rooms.exists():
            for child in child_rooms:
                child_url = f'/rooms/rooms/{child.pk}/'
                logger.info(f"Probando vínculo a habitación hijo: {child_url}")

                response = client.get(child_url, follow=True)
                if response.status_code == 200:
                    logger.info("✅ Vínculo a habitación hijo funciona correctamente")
                else:
                    logger.error(f"❌ Error en vínculo a habitación hijo: {response.status_code}")

        # 3. Probar vínculos a través de conexiones físicas
        entrances = test_room.entrance_exits.filter(connection__isnull=False)
        if entrances.exists():
            for entrance in entrances:
                if entrance.connection:
                    # Determinar la habitación destino
                    if entrance.connection.from_room == test_room:
                        target_room = entrance.connection.to_room
                    else:
                        target_room = entrance.connection.from_room

                    target_url = f'/rooms/rooms/{target_room.pk}/'
                    logger.info(f"Probando vínculo de conexión '{entrance.name}': {target_url}")

                    response = client.get(target_url, follow=True)
                    if response.status_code == 200:
                        logger.info(f"✅ Vínculo de conexión '{entrance.name}' funciona correctamente")
                    else:
                        logger.error(f"❌ Error en vínculo de conexión '{entrance.name}': {response.status_code}")

        # 4. Verificar que los botones están presentes en el HTML del formulario
        logger.info("=== VERIFICANDO PRESENCIA DE BOTONES EN FORMULARIO ===")

        edit_url = f'/rooms/rooms/{test_room.pk}/edit/'
        response = client.get(edit_url)

        if response.status_code == 200:
            html_content = response.content.decode('utf-8')

            # Verificar botones de navegación
            checks = [
                ('Botón habitación padre', f'href="/rooms/rooms/{test_room.parent_room.pk}/"' if test_room.parent_room else None),
                ('Botón habitaciones hijo', 'btn-success' if child_rooms.exists() else None),
                ('Botones de conexiones', 'btn-info' if entrances.exists() else None),
            ]

            for check_name, expected in checks:
                if expected and expected in html_content:
                    logger.info(f"✅ {check_name} presente en el formulario")
                elif expected:
                    logger.warning(f"❌ {check_name} no encontrado en el formulario")
                else:
                    logger.info(f"ℹ️ {check_name} no aplicable (sin datos)")

            logger.info("=== PRUEBA DE NAVEGACIÓN COMPLETADA ===")
            logger.info("Todos los vínculos de navegación han sido verificados")

        else:
            logger.error(f"❌ No se pudo acceder al formulario de edición: {response.status_code}")

    except Exception as e:
        logger.error(f"=== ERROR GENERAL ===")
        logger.error(f"Error: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")

if __name__ == '__main__':
    test_navigation_links()