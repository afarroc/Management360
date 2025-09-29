"""
Room Transition Manager - Sistema central para gestionar transiciones entre habitaciones
Basado en arquitectura de separación de responsabilidades para sistemas interactivos 3D
"""
import logging
from datetime import timedelta
from django.utils import timezone
from django.db import transaction
from django.contrib.auth.models import User
from .models import Room, EntranceExit, RoomConnection, PlayerProfile
from .exceptions import RoomManagerError

logger = logging.getLogger(__name__)


class RoomTransitionManager:
    """
    Sistema central que orquesta todas las transiciones entre habitaciones.
    Implementa el patrón de separación de responsabilidades donde:
    - EntranceExit: Define la conexión y reglas de acceso
    - RoomTransitionManager: Ejecuta la transición y actualiza el estado global
    """

    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    @transaction.atomic
    def attempt_transition(self, player_profile, entrance_exit, direction=None):
        """
        Intenta realizar una transición a través de una EntranceExit.

        Args:
            player_profile: Instancia de PlayerProfile
            entrance_exit: Instancia de EntranceExit
            direction: Dirección opcional para validación adicional

        Returns:
            dict: Resultado de la transición con estado y datos
        """
        try:
            self.logger.info(f"Intentando transición para {player_profile.user.username} a través de {entrance_exit.name}")

            # 1. Validar que la puerta esté habilitada
            if not entrance_exit.enabled:
                return {
                    'success': False,
                    'reason': 'DOOR_DISABLED',
                    'message': f'La puerta {entrance_exit.name} está deshabilitada.'
                }

            # 2. Validar que tenga conexión
            if not entrance_exit.connection:
                return {
                    'success': False,
                    'reason': 'NO_CONNECTION',
                    'message': f'La puerta {entrance_exit.name} no tiene conexión activa.'
                }

            connection = entrance_exit.connection

            # 3. Validar permisos de acceso
            access_result = self._validate_access(player_profile, entrance_exit)
            if not access_result['allowed']:
                return {
                    'success': False,
                    'reason': access_result['reason'],
                    'message': access_result['message']
                }

            # 4. Validar límites de uso
            if entrance_exit.max_usage_per_hour > 0:
                usage_check = self._check_usage_limits(entrance_exit)
                if not usage_check['allowed']:
                    return {
                        'success': False,
                        'reason': 'USAGE_LIMIT_EXCEEDED',
                        'message': usage_check['message']
                    }

            # 5. Validar cooldown
            if entrance_exit.cooldown > 0:
                cooldown_check = self._check_cooldown(entrance_exit)
                if not cooldown_check['allowed']:
                    return {
                        'success': False,
                        'reason': 'COOLDOWN_ACTIVE',
                        'message': cooldown_check['message']
                    }

            # 6. Determinar habitación destino
            target_room = self._determine_target_room(player_profile.current_room, connection)

            # 7. Validar que la habitación destino existe y está activa
            if not target_room or not target_room.is_active:
                return {
                    'success': False,
                    'reason': 'INVALID_DESTINATION',
                    'message': 'La habitación destino no es válida o está inactiva.'
                }

            # 8. Calcular costo de energía
            energy_cost = self._calculate_energy_cost(connection, entrance_exit)

            # 9. Validar que el jugador tenga suficiente energía
            if player_profile.energy < energy_cost:
                return {
                    'success': False,
                    'reason': 'INSUFFICIENT_ENERGY',
                    'message': f'No tienes suficiente energía. Necesitas {energy_cost}, tienes {player_profile.energy}.'
                }

            # 10. Ejecutar la transición
            transition_result = self._execute_transition(
                player_profile, entrance_exit, target_room, energy_cost
            )

            return {
                'success': True,
                'target_room': target_room,
                'energy_cost': energy_cost,
                'experience_gained': entrance_exit.experience_reward,
                'message': f'Transición exitosa a {target_room.name}'
            }

        except Exception as e:
            self.logger.error(f"Error en transición: {e}", exc_info=True)
            return {
                'success': False,
                'reason': 'SYSTEM_ERROR',
                'message': 'Error interno del sistema. Inténtalo de nuevo.'
            }

    def _validate_access(self, player_profile, entrance_exit):
        """
        Valida si el jugador tiene acceso a la puerta.
        """
        # Verificar nivel de acceso
        if entrance_exit.access_level > 0:
            # Aquí se podría implementar lógica de niveles de acceso
            # Por ahora, asumimos que el usuario tiene acceso básico
            pass

        # Verificar si está bloqueada
        if entrance_exit.is_locked:
            if entrance_exit.required_key:
                # Verificar si el jugador tiene la llave requerida
                # Esto requeriría un sistema de inventario
                return {
                    'allowed': False,
                    'reason': 'REQUIRES_KEY',
                    'message': f'Necesitas la llave: {entrance_exit.required_key}'
                }
            else:
                return {
                    'allowed': False,
                    'reason': 'DOOR_LOCKED',
                    'message': f'La puerta {entrance_exit.name} está cerrada con llave.'
                }

        # Verificar usuarios permitidos
        if entrance_exit.allowed_users.exists():
            if not entrance_exit.allowed_users.filter(id=player_profile.user.id).exists():
                return {
                    'allowed': False,
                    'reason': 'ACCESS_DENIED',
                    'message': 'No tienes permisos para usar esta puerta.'
                }

        return {'allowed': True}

    def _check_usage_limits(self, entrance_exit):
        """
        Verifica límites de uso por hora.
        """
        if entrance_exit.max_usage_per_hour <= 0:
            return {'allowed': True}

        # Contar usos en la última hora
        one_hour_ago = timezone.now() - timedelta(hours=1)
        recent_usage = EntranceExit.objects.filter(
            id=entrance_exit.id,
            last_opened__gte=one_hour_ago
        ).count()

        if recent_usage >= entrance_exit.max_usage_per_hour:
            return {
                'allowed': False,
                'message': f'Límite de uso excedido. Máximo {entrance_exit.max_usage_per_hour} usos por hora.'
            }

        return {'allowed': True}

    def _check_cooldown(self, entrance_exit):
        """
        Verifica si hay cooldown activo.
        """
        if not entrance_exit.last_opened or entrance_exit.cooldown <= 0:
            return {'allowed': True}

        cooldown_end = entrance_exit.last_opened + timedelta(seconds=entrance_exit.cooldown)
        if timezone.now() < cooldown_end:
            remaining_seconds = (cooldown_end - timezone.now()).seconds
            return {
                'allowed': False,
                'message': f'En cooldown. Espera {remaining_seconds} segundos.'
            }

        return {'allowed': True}

    def _determine_target_room(self, current_room, connection):
        """
        Determina la habitación destino basada en la habitación actual.
        """
        if connection.from_room == current_room:
            return connection.to_room
        elif connection.to_room == current_room and connection.bidirectional:
            return connection.from_room
        else:
            return None

    def _calculate_energy_cost(self, connection, entrance_exit):
        """
        Calcula el costo total de energía para la transición.
        """
        base_cost = connection.energy_cost
        modifier = entrance_exit.energy_cost_modifier
        return max(0, base_cost + modifier)

    def _execute_transition(self, player_profile, entrance_exit, target_room, energy_cost):
        """
        Ejecuta la transición física y actualiza todos los estados.
        """
        # Actualizar posición del jugador
        spawn_position = self._calculate_spawn_position(entrance_exit, target_room)
        player_profile.position_x, player_profile.position_y = spawn_position

        # Cambiar habitación del jugador
        player_profile.current_room = target_room

        # Consumir energía
        player_profile.energy -= energy_cost

        # Otorgar experiencia
        if entrance_exit.experience_reward > 0:
            player_profile.productivity += entrance_exit.experience_reward

        # Actualizar estadísticas de la puerta
        entrance_exit.is_open = False  # Cerrar la puerta después del uso
        entrance_exit.last_opened = timezone.now()
        entrance_exit.usage_count += 1

        # Aplicar efectos especiales si existen
        if entrance_exit.special_effects:
            self._apply_special_effects(player_profile, entrance_exit.special_effects)

        # Guardar cambios
        player_profile.save()
        entrance_exit.save()

        self.logger.info(f"Transición completada: {player_profile.user.username} -> {target_room.name}")

    def _calculate_spawn_position(self, entrance_exit, target_room):
        """
        Calcula la posición de spawn en la habitación destino.
        """
        # Buscar la entrada correspondiente en la habitación destino
        opposite_entrance = None
        for entrance in target_room.entrance_exits.all():
            if entrance.connection and (
                (entrance.connection.from_room == entrance_exit.room and entrance.connection.to_room == target_room) or
                (entrance.connection.to_room == entrance_exit.room and entrance.connection.from_room == target_room and entrance.connection.bidirectional)
            ):
                opposite_entrance = entrance
                break

        if opposite_entrance:
            return opposite_entrance.position_x or target_room.length // 2, \
                   opposite_entrance.position_y or target_room.width // 2
        else:
            # Posición por defecto en el centro de la habitación
            return target_room.length // 2, target_room.width // 2

    def _apply_special_effects(self, player_profile, effects):
        """
        Aplica efectos especiales de la puerta.
        """
        if isinstance(effects, dict):
            if effects.get('energy_boost'):
                player_profile.energy = min(100, player_profile.energy + effects['energy_boost'])

            if effects.get('productivity_boost'):
                player_profile.productivity = min(100, player_profile.productivity + effects['productivity_boost'])

            if effects.get('social_boost'):
                player_profile.social = min(100, player_profile.social + effects['social_boost'])

            player_profile.save()

    def get_available_transitions(self, player_profile):
        """
        Obtiene todas las transiciones disponibles para un jugador desde su habitación actual.
        """
        if not player_profile.current_room:
            return []

        transitions = []
        for entrance in player_profile.current_room.entrance_exits.filter(enabled=True):
            if entrance.connection:
                target_room = self._determine_target_room(player_profile.current_room, entrance.connection)
                if target_room:
                    # Verificar acceso rápido
                    access_check = self._validate_access(player_profile, entrance)
                    energy_cost = self._calculate_energy_cost(entrance.connection, entrance)

                    transitions.append({
                        'entrance': entrance,
                        'target_room': target_room,
                        'energy_cost': energy_cost,
                        'accessible': access_check['allowed'],
                        'reason': access_check.get('reason'),
                        'experience_reward': entrance.experience_reward
                    })

        return transitions


# Instancia global del manager
room_transition_manager = RoomTransitionManager()


def get_room_transition_manager():
    """
    Factory function para obtener la instancia del RoomTransitionManager.
    """
    return room_transition_manager