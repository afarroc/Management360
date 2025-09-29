from rest_framework import serializers
from .models import Room, RoomMember, Message, EntranceExit, Portal, RoomConnection
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username']


class LastMessageSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = Message
        fields = ['id', 'content', 'user', 'created_at']


class RoomSerializer(serializers.ModelSerializer):
    member_count = serializers.SerializerMethodField()
    last_message = LastMessageSerializer(read_only=True)

    def get_member_count(self, obj):
        return obj.member_count

    class Meta:
        model = Room
        fields = ['id', 'name', 'version', 'bumped_at', 'member_count', 'last_message']


class MessageRoomSerializer(serializers.ModelSerializer):
    class Meta:
        model = Room
        fields = ['id', 'version', 'bumped_at']


class RoomSearchSerializer(serializers.ModelSerializer):

    is_member = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = Room
        fields = ['id', 'name', 'created_at', 'is_member']


class RoomMemberSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    room = RoomSerializer(read_only=True)
    
    class Meta:
        model = RoomMember
        fields = ['room', 'user']


class MessageSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    room = MessageRoomSerializer(read_only=True)

    class Meta:
        model = Message
        fields = ['id', 'content', 'user', 'room', 'created_at']


class RoomCRUDSerializer(serializers.ModelSerializer):
    """
    Serializer específico para operaciones CRUD de habitaciones.
    Incluye todos los campos necesarios para crear, leer, actualizar y eliminar habitaciones.
    """
    owner_username = serializers.CharField(source='owner.username', read_only=True)
    member_count = serializers.SerializerMethodField()

    def get_member_count(self, obj):
        """Cuenta real de miembros de la habitación"""
        return obj.members.filter(is_active=True).count()

    class Meta:
        model = Room
        fields = [
            'id', 'name', 'description', 'room_type', 'capacity', 'permissions',
            'x', 'y', 'z', 'length', 'width', 'height', 'pitch', 'yaw', 'roll',
            'color_primary', 'color_secondary', 'material_type', 'texture_url', 'opacity',
            'mass', 'density', 'friction', 'restitution',
            'is_active', 'health', 'temperature', 'lighting_intensity',
            'sound_ambient', 'special_properties',
            'created_at', 'updated_at', 'owner_username', 'member_count'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'owner_username', 'member_count']

        extra_kwargs = {
            'capacity': {'allow_null': True, 'required': False},
            'description': {'allow_null': True, 'required': False},
            'length': {'allow_null': True, 'required': False},
            'width': {'allow_null': True, 'required': False},
            'height': {'allow_null': True, 'required': False},
            'color_primary': {'allow_null': True, 'required': False},
            'color_secondary': {'allow_null': True, 'required': False},
            'material_type': {'allow_null': True, 'required': False},
            'opacity': {'allow_null': True, 'required': False},
        }

    def create(self, validated_data):
        """Crear habitación asignando el owner automáticamente"""
        validated_data['owner'] = self.context['request'].user
        validated_data['creator'] = self.context['request'].user
        return super().create(validated_data)

    def validate_special_properties(self, value):
        """Validar que special_properties sea JSON válido"""
        if value and isinstance(value, str):
            try:
                import json
                json.loads(value)
            except json.JSONDecodeError:
                raise serializers.ValidationError("Formato JSON inválido.")
        return value

    def to_internal_value(self, data):
        """Preprocesar datos antes de validación"""
        # Crear una copia mutable de los datos
        internal_data = dict(data)

        # Convertir None a valores por defecto para campos que no permiten null
        if internal_data.get('description') is None:
            internal_data['description'] = ''
        if internal_data.get('capacity') is None:
            internal_data['capacity'] = 0  # Valor por defecto del modelo
        if internal_data.get('length') is None:
            internal_data['length'] = 30
        if internal_data.get('width') is None:
            internal_data['width'] = 30
        if internal_data.get('height') is None:
            internal_data['height'] = 10
        if internal_data.get('color_primary') is None:
            internal_data['color_primary'] = '#2196f3'
        if internal_data.get('color_secondary') is None:
            internal_data['color_secondary'] = '#1976d2'
        if internal_data.get('material_type') is None:
            internal_data['material_type'] = 'CONCRETE'
        if internal_data.get('opacity') is None:
            internal_data['opacity'] = 1.0

        return super().to_internal_value(internal_data)


class EntranceExitCRUDSerializer(serializers.ModelSerializer):
    """
    Serializer completo para operaciones CRUD de EntranceExit (puertas).
    Incluye todos los campos necesarios para crear, leer, actualizar y eliminar puertas.
    """
    room_name = serializers.CharField(source='room.name', read_only=True)
    connection_info = serializers.SerializerMethodField()

    def get_connection_info(self, obj):
        """Información sobre la conexión de la puerta"""
        if obj.connection:
            return {
                'id': obj.connection.id,
                'from_room': obj.connection.from_room.name,
                'to_room': obj.connection.to_room.name,
                'bidirectional': obj.connection.bidirectional,
                'energy_cost': obj.connection.energy_cost
            }
        return None

    class Meta:
        model = EntranceExit
        fields = [
            'id', 'name', 'room', 'room_name', 'description', 'face',
            'position_x', 'position_y', 'enabled', 'connection', 'connection_info',

            # Propiedades físicas/visuales
            'width', 'height', 'door_type', 'material', 'color', 'texture_url', 'opacity',

            # Propiedades funcionales
            'is_locked', 'required_key', 'auto_close', 'close_delay',
            'open_speed', 'close_speed', 'sound_open', 'sound_close',

            # Propiedades de interacción
            'interaction_type', 'animation_type', 'requires_both_hands',
            'interaction_distance',

            # Propiedades de estado
            'is_open', 'last_opened', 'usage_count', 'health',

            # Propiedades de seguridad/permisos
            'access_level', 'security_system', 'alarm_triggered',

            # Propiedades ambientales
            'seals_air', 'seals_sound', 'temperature_resistance',
            'pressure_resistance',

            # Propiedades de juego/mecánicas
            'energy_cost_modifier', 'experience_reward', 'special_effects',
            'cooldown', 'max_usage_per_hour',

            # Propiedades de apariencia avanzada
            'glow_color', 'glow_intensity', 'particle_effects', 'decoration_type',

            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'room_name', 'connection_info', 'created_at', 'updated_at']

        extra_kwargs = {
            'room': {'required': True},
            'name': {'required': True},
            'face': {'required': True},
            'description': {'allow_null': True, 'required': False},
            'position_x': {'allow_null': True, 'required': False},
            'position_y': {'allow_null': True, 'required': False},
            'connection': {'allow_null': True, 'required': False},
        }

    def create(self, validated_data):
        """Crear puerta con validaciones adicionales"""
        # Asignar posiciones por defecto si no se especifican
        if validated_data.get('position_x') is None or validated_data.get('position_y') is None:
            room = validated_data['room']
            face = validated_data['face']
            if face == 'NORTH':
                validated_data['position_x'] = room.length // 2
                validated_data['position_y'] = room.width
            elif face == 'SOUTH':
                validated_data['position_x'] = room.length // 2
                validated_data['position_y'] = 0
            elif face == 'EAST':
                validated_data['position_x'] = room.length
                validated_data['position_y'] = room.width // 2
            elif face == 'WEST':
                validated_data['position_x'] = 0
                validated_data['position_y'] = room.width // 2
            else:  # UP, DOWN u otros
                validated_data['position_x'] = room.length // 2
                validated_data['position_y'] = room.width // 2

        return super().create(validated_data)

    def validate_special_effects(self, value):
        """Validar que special_effects sea JSON válido"""
        if value and isinstance(value, str):
            try:
                import json
                json.loads(value)
            except json.JSONDecodeError:
                raise serializers.ValidationError("Formato JSON inválido para special_effects.")
        return value


class PortalCRUDSerializer(serializers.ModelSerializer):
    """
    Serializer completo para operaciones CRUD de Portal.
    Incluye todos los campos necesarios para crear, leer, actualizar y eliminar portales.
    """
    entrance_room_name = serializers.CharField(source='entrance.room.name', read_only=True)
    exit_room_name = serializers.CharField(source='exit.room.name', read_only=True)
    is_active = serializers.SerializerMethodField()

    def get_is_active(self, obj):
        """Verificar si el portal está activo"""
        return obj.is_active()

    class Meta:
        model = Portal
        fields = [
            'id', 'name', 'entrance', 'entrance_room_name', 'exit', 'exit_room_name',
            'energy_cost', 'cooldown', 'last_used', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'entrance_room_name', 'exit_room_name', 'is_active', 'created_at', 'updated_at']

        extra_kwargs = {
            'name': {'required': True},
            'entrance': {'required': True},
            'exit': {'required': True},
            'energy_cost': {'required': False, 'default': 10},
            'cooldown': {'required': False, 'default': 300},
            'last_used': {'allow_null': True, 'required': False},
        }

    def validate(self, data):
        """Validar que entrada y salida no estén en la misma habitación"""
        entrance = data.get('entrance')
        exit_obj = data.get('exit')

        if entrance and exit_obj:
            if entrance.room == exit_obj.room:
                raise serializers.ValidationError("La entrada y salida deben estar en habitaciones distintas.")

            # Verificar que no exista ya un portal con estas entradas/salidas
            if Portal.objects.filter(entrance=entrance, exit=exit_obj).exists():
                if self.instance and (self.instance.entrance != entrance or self.instance.exit != exit_obj):
                    raise serializers.ValidationError("Ya existe un portal con estas entradas y salidas.")

        return data


class RoomConnectionCRUDSerializer(serializers.ModelSerializer):
    """
    Serializer completo para operaciones CRUD de RoomConnection.
    Incluye todos los campos necesarios para crear, leer, actualizar y eliminar conexiones.
    """
    from_room_name = serializers.CharField(source='from_room.name', read_only=True)
    to_room_name = serializers.CharField(source='to_room.name', read_only=True)
    entrance_name = serializers.CharField(source='entrance.name', read_only=True)

    class Meta:
        model = RoomConnection
        fields = [
            'id', 'from_room', 'from_room_name', 'to_room', 'to_room_name',
            'entrance', 'entrance_name', 'bidirectional', 'energy_cost',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'from_room_name', 'to_room_name', 'entrance_name', 'created_at', 'updated_at']

        extra_kwargs = {
            'from_room': {'required': True},
            'to_room': {'required': True},
            'entrance': {'required': True},
            'bidirectional': {'required': False, 'default': True},
            'energy_cost': {'required': False, 'default': 0},
        }

    def validate(self, data):
        """Validar la conexión"""
        from_room = data.get('from_room')
        to_room = data.get('to_room')
        entrance = data.get('entrance')

        if from_room and to_room and entrance:
            # Verificar que la entrada pertenezca a la habitación de origen
            if entrance.room != from_room:
                raise serializers.ValidationError("La entrada debe pertenecer a la habitación de origen.")

            # Verificar que no exista ya una conexión con los mismos parámetros
            if RoomConnection.objects.filter(
                from_room=from_room,
                to_room=to_room,
                entrance=entrance
            ).exists():
                if not self.instance or (
                    self.instance.from_room != from_room or
                    self.instance.to_room != to_room or
                    self.instance.entrance != entrance
                ):
                    raise serializers.ValidationError("Ya existe una conexión con estos parámetros.")

        return data