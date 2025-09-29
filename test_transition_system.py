#!/usr/bin/env python
"""
Script para probar el sistema de transición de habitaciones
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
from rooms.models import Room, EntranceExit, RoomConnection, PlayerProfile
import logging
import json

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def setup_transition_test():
    """Configurar habitaciones y conexiones para probar el sistema de transición"""
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

        # Crear habitaciones de prueba
        room_a, _ = Room.objects.get_or_create(
            name='habitacion_transicion_a',
            defaults={
                'description': 'Habitación A para pruebas de transición',
                'room_type': 'OFFICE',
                'owner': user,
                'length': 100,
                'width': 80,
                'height': 30
            }
        )

        room_b, _ = Room.objects.get_or_create(
            name='habitacion_transicion_b',
            defaults={
                'description': 'Habitación B para pruebas de transición',
                'room_type': 'MEETING',
                'owner': user,
                'length': 120,
                'width': 90,
                'height': 25
            }
        )

        # Crear EntranceExit con propiedades avanzadas
        entrance_a = EntranceExit.objects.create(
            name='Puerta Norte Inteligente',
            room=room_a,
            description='Puerta automática con sensor',
            face='NORTH',
            position_x=50,
            position_y=80,
            enabled=True,

            # Propiedades físicas
            width=100,
            height=210,
            door_type='SLIDING',
            material='GLASS',
            color='#E3F2FD',
            opacity=0.9,

            # Propiedades funcionales
            is_locked=False,
            auto_close=True,
            close_delay=3,
            open_speed=2.0,
            close_speed=1.5,

            # Propiedades de interacción
            interaction_type='AUTOMATIC',
            animation_type='SLIDE',
            interaction_distance=200,

            # Propiedades de seguridad
            access_level=0,
            security_system='NONE',

            # Propiedades ambientales
            seals_air=True,
            seals_sound=30,

            # Propiedades de juego
            energy_cost_modifier=2,
            experience_reward=5,
            special_effects={'auto_open': True}
        )

        entrance_b = EntranceExit.objects.create(
            name='Puerta Sur Inteligente',
            room=room_b,
            description='Puerta correspondiente en habitación B',
            face='SOUTH',
            position_x=60,
            position_y=0,
            enabled=True,

            # Propiedades físicas
            width=100,
            height=210,
            door_type='SLIDING',
            material='GLASS',
            color='#F3E5F5',

            # Propiedades funcionales
            is_locked=False,
            auto_close=True,
            close_delay=3,

            # Propiedades de interacción
            interaction_type='AUTOMATIC',
            animation_type='SLIDE',

            # Propiedades de seguridad
            access_level=0,

            # Propiedades ambientales
            seals_air=True,
            seals_sound=30,

            # Propiedades de juego
            energy_cost_modifier=1,
            experience_reward=3
        )

        # Crear conexión bidireccional
        connection = RoomConnection.objects.create(
            from_room=room_a,
            to_room=room_b,
            entrance=entrance_a,
            bidirectional=True,
            energy_cost=8
        )

        # Asignar la conexión a ambas entradas
        entrance_a.connection = connection
        entrance_a.save()
        entrance_b.connection = connection
        entrance_b.save()

        # Configurar perfil del jugador
        player_profile, _ = PlayerProfile.objects.get_or_create(
            user=user,
            defaults={
                'energy': 100,
                'productivity': 50,
                'social': 50,
                'current_room': room_a,
                'position_x': 25,
                'position_y': 40
            }
        )
        player_profile.current_room = room_a
        player_profile.energy = 100
        player_profile.save()

        logger.info("=== CONFIGURACIÓN DE PRUEBA COMPLETADA ===")
        logger.info(f"Habitación A: {room_a.name} (ID: {room_a.pk})")
        logger.info(f"Habitación B: {room_b.name} (ID: {room_b.pk})")
        logger.info(f"Puerta A: {entrance_a.name} (ID: {entrance_a.pk})")
        logger.info(f"Puerta B: {entrance_b.name} (ID: {entrance_b.pk})")
        logger.info(f"Conexión: {connection.energy_cost} energía, bidireccional: {connection.bidirectional}")
        logger.info(f"Jugador: {user.username}, Energía: {player_profile.energy}")

        return player_profile, entrance_a

    except Exception as e:
        logger.error(f"Error configurando transición: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return None, None

def test_transition_api():
    """Probar las APIs del sistema de transición"""
    try:
        player_profile, entrance_a = setup_transition_test()
        if not player_profile or not entrance_a:
            return

        # Crear cliente de pruebas
        client = Client()
        client.force_login(player_profile.user)

        logger.info("=== PRUEBA DEL SISTEMA DE TRANSICIÓN ===")

        # 1. Probar obtener información de la puerta
        logger.info("1. Probando API de información de puerta...")
        response = client.get(f'/rooms/api/entrance/{entrance_a.pk}/info/')
        if response.status_code == 200:
            data = response.json()
            if data['success']:
                logger.info("✅ Información de puerta obtenida correctamente")
                logger.info(f"   - Puerta: {data['entrance']['name']}")
                logger.info(f"   - Tipo: {data['entrance']['door_type']}")
                logger.info(f"   - Puede usar: {data['transition_info']['can_use']}")
                if data['transition_info']['target_room']:
                    logger.info(f"   - Habitación destino: {data['transition_info']['target_room']['name']}")
                    logger.info(f"   - Costo energía: {data['transition_info']['energy_cost']}")
            else:
                logger.error(f"❌ Error en API de info: {data['message']}")
        else:
            logger.error(f"❌ Error HTTP en API de info: {response.status_code}")

        # 2. Probar obtener transiciones disponibles
        logger.info("2. Probando API de transiciones disponibles...")
        response = client.get('/rooms/api/transitions/available/')
        if response.status_code == 200:
            data = response.json()
            if data['success']:
                logger.info("✅ Transiciones disponibles obtenidas correctamente")
                logger.info(f"   - Habitación actual: {data['current_room']['name']}")
                logger.info(f"   - Energía del jugador: {data['player_energy']}")
                logger.info(f"   - Transiciones disponibles: {len(data['available_transitions'])}")
                for transition in data['available_transitions']:
                    logger.info(f"     * {transition['entrance']['name']} -> {transition['target_room']['name']} (Energía: {transition['energy_cost']})")
            else:
                logger.error(f"❌ Error en API de transiciones: {data['message']}")
        else:
            logger.error(f"❌ Error HTTP en API de transiciones: {response.status_code}")

        # 3. Probar usar la puerta (realizar transición)
        logger.info("3. Probando API de usar puerta...")
        initial_energy = player_profile.energy
        response = client.post(f'/rooms/api/entrance/{entrance_a.pk}/use/')

        if response.status_code == 200:
            data = response.json()
            if data['success']:
                logger.info("✅ Transición realizada correctamente")
                logger.info(f"   - Mensaje: {data['message']}")
                logger.info(f"   - Habitación destino: {data['target_room']['name']}")
                logger.info(f"   - Energía gastada: {data['energy_cost']}")
                logger.info(f"   - Experiencia ganada: {data['experience_gained']}")
                logger.info(f"   - Nueva energía: {data['player_stats']['energy']}")

                # Verificar que la energía se consumió correctamente
                expected_energy = initial_energy - data['energy_cost']
                if data['player_stats']['energy'] == expected_energy:
                    logger.info("✅ Energía consumida correctamente")
                else:
                    logger.warning(f"⚠️ Energía no coincide: esperado {expected_energy}, obtenido {data['player_stats']['energy']}")

                # Verificar que el perfil del jugador se actualizó
                player_profile.refresh_from_db()
                if player_profile.current_room.name == data['target_room']['name']:
                    logger.info("✅ Habitación del jugador actualizada correctamente")
                else:
                    logger.error("❌ Habitación del jugador no se actualizó")

            else:
                logger.error(f"❌ Transición fallida: {data['message']}")
        else:
            logger.error(f"❌ Error HTTP en API de usar puerta: {response.status_code}")
            logger.error(f"Contenido: {response.content.decode()}")

        # 4. Probar transición de vuelta
        logger.info("4. Probando transición de vuelta...")
        # Obtener la puerta correspondiente en la habitación B
        entrance_b = EntranceExit.objects.filter(room=player_profile.current_room, connection=entrance_a.connection).first()
        if entrance_b:
            response = client.post(f'/rooms/api/entrance/{entrance_b.pk}/use/')
            if response.status_code == 200:
                data = response.json()
                if data['success']:
                    logger.info("✅ Transición de vuelta realizada correctamente")
                    logger.info(f"   - De vuelta a: {data['target_room']['name']}")
                else:
                    logger.error(f"❌ Transición de vuelta fallida: {data['message']}")
            else:
                logger.error(f"❌ Error HTTP en transición de vuelta: {response.status_code}")
        else:
            logger.warning("⚠️ No se encontró puerta correspondiente para transición de vuelta")

        # 5. Verificar estadísticas de uso
        logger.info("5. Verificando estadísticas de uso...")
        entrance_a.refresh_from_db()
        logger.info(f"   - Puerta A - Usos totales: {entrance_a.usage_count}")
        logger.info(f"   - Puerta A - Último uso: {entrance_a.last_opened}")
        logger.info(f"   - Puerta A - Estado: {'Abierta' if entrance_a.is_open else 'Cerrada'}")

        logger.info("=== PRUEBA DEL SISTEMA DE TRANSICIÓN COMPLETADA ===")

        # Limpiar datos de prueba
        try:
            entrance_a.delete()
            entrance_b.delete()
            if 'connection' in locals():
                connection.delete()
            room_a.delete()
            room_b.delete()
            logger.info("✅ Limpieza de datos de prueba completada")
        except Exception as e:
            logger.warning(f"⚠️ Algunos datos de prueba no pudieron ser eliminados: {e}")

    except Exception as e:
        logger.error(f"=== ERROR GENERAL ===")
        logger.error(f"Error: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")

if __name__ == '__main__':
    test_transition_api()