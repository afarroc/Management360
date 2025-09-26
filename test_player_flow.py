#!/usr/bin/env python
"""
Test script para verificar el flujo de registro de presencia y comandos por mensaje
"""
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'panel.settings')
django.setup()

from django.contrib.auth.models import User
from rooms.models import PlayerProfile, Room
from rooms.views import process_message_command

def test_player_registration():
    """Prueba el registro de presencia de un jugador"""
    print("=== Prueba de Registro de Presencia ===")

    # Crear usuario de prueba
    user, created = User.objects.get_or_create(
        username='test_player',
        defaults={'email': 'test@example.com'}
    )

    # Simular registro de presencia
    player_profile, created = PlayerProfile.objects.get_or_create(
        user=user,
        defaults={
            'energy': 100,
            'productivity': 50,
            'social': 50,
            'position_x': 0,
            'position_y': 0
        }
    )

    player_profile.state = 'AVAILABLE'
    player_profile.energy = 100

    # Crear habitación inicial si no existe
    initial_room, room_created = Room.objects.get_or_create(
        name='Lobby Principal',
        defaults={
            'description': 'Habitación principal para nuevos usuarios',
            'owner': user,
            'permissions': 'public',
            'room_type': 'LOUNGE'
        }
    )

    player_profile.current_room = initial_room
    player_profile.save()

    print(f"[OK] Usuario {user.username} registrado como {player_profile.get_state_display()}")
    print(f"[OK] Ingresado a habitación: {initial_room.name}")
    print(f"[OK] Energía: {player_profile.energy}")

    return user, player_profile

def test_message_commands(user):
    """Prueba los comandos por mensaje"""
    print("\n=== Prueba de Comandos por Mensaje ===")

    commands = [
        '/work',
        '/rest',
        '/social',
        '/status',
        '/disconnect',
        '/invalid_command'
    ]

    for cmd in commands:
        print(f"\nProbando comando: {cmd}")
        response = process_message_command(cmd, user)
        if response:
            print(f"Respuesta: {response}")
        else:
            print("No es un comando")

def main():
    try:
        user, player = test_player_registration()
        test_message_commands(user)
        print("\n=== Prueba Completada Exitosamente ===")
    except Exception as e:
        print(f"Error en la prueba: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()