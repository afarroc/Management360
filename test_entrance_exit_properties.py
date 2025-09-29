#!/usr/bin/env python
"""
Script para probar las nuevas propiedades del modelo EntranceExit
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
from rooms.models import Room, EntranceExit
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_entrance_exit_properties():
    """Probar las nuevas propiedades del modelo EntranceExit"""
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

        # Obtener habitación existente
        room = Room.objects.filter(owner=user).first()
        if not room:
            room = Room.objects.create(
                name='habitacion_test_propiedades',
                description='Habitación para probar propiedades de EntranceExit',
                room_type='OFFICE',
                owner=user
            )

        logger.info(f"Probando con habitación: {room.name} (ID: {room.pk})")

        # Crear EntranceExit con todas las nuevas propiedades
        entrance = EntranceExit.objects.create(
            name='Puerta Inteligente',
            room=room,
            description='Puerta con todas las propiedades avanzadas',
            face='NORTH',

            # Propiedades físicas/visuales
            width=120,
            height=210,
            door_type='DOUBLE',
            material='GLASS',
            color='#87CEEB',
            texture_url='https://example.com/texture.png',
            opacity=0.8,

            # Propiedades funcionales
            is_locked=True,
            required_key='llave_maestra_001',
            auto_close=True,
            close_delay=10,
            open_speed=2.5,
            close_speed=1.8,
            sound_open='https://example.com/open.wav',
            sound_close='https://example.com/close.wav',

            # Propiedades de interacción
            interaction_type='BUTTON',
            animation_type='SLIDE',
            requires_both_hands=False,
            interaction_distance=200,

            # Propiedades de estado
            is_open=False,
            usage_count=42,
            health=85,

            # Propiedades de seguridad
            access_level=3,
            security_system='ELECTRONIC',
            alarm_triggered=False,

            # Propiedades ambientales
            seals_air=True,
            seals_sound=35,
            temperature_resistance=75,
            pressure_resistance=2,

            # Propiedades de juego
            energy_cost_modifier=5,
            experience_reward=10,
            special_effects={'glow': True, 'particles': 'sparkles'},
            cooldown=2,
            max_usage_per_hour=100,

            # Propiedades de apariencia avanzada
            glow_color='#00FF00',
            glow_intensity=50,
            particle_effects='magic_sparkles',
            decoration_type='ORNAMENTAL'
        )

        logger.info("✅ EntranceExit creado exitosamente con todas las propiedades")

        # Verificar que todas las propiedades se guardaron correctamente
        entrance.refresh_from_db()

        # Propiedades físicas/visuales
        assert entrance.width == 120, f"width: esperado 120, obtenido {entrance.width}"
        assert entrance.height == 210, f"height: esperado 210, obtenido {entrance.height}"
        assert entrance.door_type == 'DOUBLE', f"door_type: esperado DOUBLE, obtenido {entrance.door_type}"
        assert entrance.material == 'GLASS', f"material: esperado GLASS, obtenido {entrance.material}"
        assert entrance.color == '#87CEEB', f"color: esperado #87CEEB, obtenido {entrance.color}"
        assert float(entrance.opacity) == 0.8, f"opacity: esperado 0.8, obtenido {entrance.opacity}"

        # Propiedades funcionales
        assert entrance.is_locked == True, f"is_locked: esperado True, obtenido {entrance.is_locked}"
        assert entrance.required_key == 'llave_maestra_001', f"required_key incorrecto"
        assert entrance.auto_close == True, f"auto_close: esperado True, obtenido {entrance.auto_close}"
        assert entrance.close_delay == 10, f"close_delay: esperado 10, obtenido {entrance.close_delay}"
        assert float(entrance.open_speed) == 2.5, f"open_speed: esperado 2.5, obtenido {entrance.open_speed}"
        assert float(entrance.close_speed) == 1.8, f"close_speed: esperado 1.8, obtenido {entrance.close_speed}"

        # Propiedades de interacción
        assert entrance.interaction_type == 'BUTTON', f"interaction_type incorrecto"
        assert entrance.animation_type == 'SLIDE', f"animation_type incorrecto"
        assert entrance.requires_both_hands == False, f"requires_both_hands incorrecto"
        assert entrance.interaction_distance == 200, f"interaction_distance incorrecto"

        # Propiedades de estado
        assert entrance.is_open == False, f"is_open: esperado False, obtenido {entrance.is_open}"
        assert entrance.usage_count == 42, f"usage_count: esperado 42, obtenido {entrance.usage_count}"
        assert entrance.health == 85, f"health: esperado 85, obtenido {entrance.health}"

        # Propiedades de seguridad
        assert entrance.access_level == 3, f"access_level: esperado 3, obtenido {entrance.access_level}"
        assert entrance.security_system == 'ELECTRONIC', f"security_system incorrecto"

        # Propiedades ambientales
        assert entrance.seals_air == True, f"seals_air: esperado True, obtenido {entrance.seals_air}"
        assert entrance.seals_sound == 35, f"seals_sound: esperado 35, obtenido {entrance.seals_sound}"
        assert entrance.temperature_resistance == 75, f"temperature_resistance incorrecto"
        assert entrance.pressure_resistance == 2, f"pressure_resistance incorrecto"

        # Propiedades de juego
        assert entrance.energy_cost_modifier == 5, f"energy_cost_modifier incorrecto"
        assert entrance.experience_reward == 10, f"experience_reward incorrecto"
        assert entrance.special_effects == {'glow': True, 'particles': 'sparkles'}, f"special_effects incorrecto"
        assert entrance.cooldown == 2, f"cooldown incorrecto"
        assert entrance.max_usage_per_hour == 100, f"max_usage_per_hour incorrecto"

        # Propiedades de apariencia avanzada
        assert entrance.glow_color == '#00FF00', f"glow_color incorrecto"
        assert entrance.glow_intensity == 50, f"glow_intensity incorrecto"
        assert entrance.particle_effects == 'magic_sparkles', f"particle_effects incorrecto"
        assert entrance.decoration_type == 'ORNAMENTAL', f"decoration_type incorrecto"

        logger.info("✅ TODAS las propiedades se guardaron y verificaron correctamente")

        # Probar actualización de propiedades dinámicas
        entrance.is_open = True
        entrance.usage_count += 1
        entrance.save()

        entrance.refresh_from_db()
        assert entrance.is_open == True, "No se pudo actualizar is_open"
        assert entrance.usage_count == 43, "No se pudo actualizar usage_count"

        logger.info("✅ Propiedades dinámicas se actualizan correctamente")

        # Limpiar datos de prueba
        entrance.delete()
        if room.name == 'habitacion_test_propiedades':
            room.delete()

        logger.info("✅ Limpieza de datos de prueba completada")
        logger.info("=== PRUEBA DE PROPIEDADES EntranceExit COMPLETADA EXITOSAMENTE ===")

    except Exception as e:
        logger.error(f"=== ERROR GENERAL ===")
        logger.error(f"Error: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")

if __name__ == '__main__':
    test_entrance_exit_properties()