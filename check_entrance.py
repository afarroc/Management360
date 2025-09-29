#!/usr/bin/env python
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'panel.settings')
sys.path.append('.')
django.setup()

from rooms.models import EntranceExit, RoomConnection, PlayerProfile
from django.contrib.auth.models import User

def check_entrance():
    try:
        # Obtener la puerta 18
        entrance = EntranceExit.objects.get(id=18)
        print(f"Entrance ID: {entrance.id}")
        print(f"Entrance Name: {entrance.name}")
        print(f"Enabled: {entrance.enabled}")
        print(f"Room: {entrance.room.name} (ID: {entrance.room.id})")
        print(f"Face: {entrance.face}")
        print(f"Connection: {entrance.connection}")

        if entrance.connection:
            connection = entrance.connection
            print(f"Connection ID: {connection.id}")
            print(f"From room: {connection.from_room.name} (ID: {connection.from_room.id})")
            print(f"To room: {connection.to_room.name} (ID: {connection.to_room.id})")
            print(f"Bidirectional: {connection.bidirectional}")
            print(f"Energy cost: {connection.energy_cost}")
        else:
            print("ERROR: No connection found for this entrance!")
            return

        # Verificar si hay un usuario para probar
        try:
            user = User.objects.filter(username='su').first()
            if user:
                print(f"\nTesting with user: {user.username}")
                player_profile = user.player_profile
                print(f"Player current room: {player_profile.current_room.name if player_profile.current_room else 'None'}")
                print(f"Player energy before: {player_profile.energy}")

                # Aumentar energía si es necesario
                if player_profile.energy < 10:
                    player_profile.energy = 100
                    player_profile.save()
                    print(f"Player energy set to: {player_profile.energy}")

                # Probar la transición
                from rooms.transition_manager import get_room_transition_manager
                manager = get_room_transition_manager()
                result = manager.attempt_transition(player_profile, entrance)
                print(f"Transition result: {result}")

        except Exception as e:
            print(f"Error testing transition: {e}")
            import traceback
            traceback.print_exc()

    except EntranceExit.DoesNotExist:
        print("ERROR: Entrance with ID 18 does not exist!")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    check_entrance()