from django.contrib.auth.models import User
from django.utils.crypto import get_random_string
from django.contrib.auth.hashers import make_password
from chat.models import RoomMember, Room


# To speed up test users creation it's possible to add MD5PasswordHasher temporarily
# and use make_password(password, None, 'md5').
# PASSWORD_HASHERS = [
#     "django.contrib.auth.hashers.PBKDF2PasswordHasher",
#     "django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher",
#     "django.contrib.auth.hashers.Argon2PasswordHasher",
#     "django.contrib.auth.hashers.BCryptSHA256PasswordHasher",
#     "django.contrib.auth.hashers.ScryptPasswordHasher",
#     "django.contrib.auth.hashers.MD5PasswordHasher",
# ]
def create_users(n):
    users = []
    total = 0
    for _ in range(n):
        username = get_random_string(10)
        email = f"{username}@example.com"
        password = get_random_string(50)
        user = User(username=username, email=email, password=make_password(password, None, 'md5'))
        users.append(user)

        if len(users) >= 100:
            total += len(users)
            User.objects.bulk_create(users)
            users = []
            print("Total users created:", total)

    # Create remaining users.
    if users:
        total += len(users)
        User.objects.bulk_create(users)
        print("Total users created:", total)


def create_room(name):
    return Room.objects.create(name=name)


def fill_room(room_id, limit):
    members = []
    total = 0
    room = Room.objects.get(pk=room_id)
    for user in User.objects.all()[:limit]:
        members.append(RoomMember(room=room, user=user))

        if len(members) >= 100:
            total += len(members)
            RoomMember.objects.bulk_create(members, ignore_conflicts=True)
            members = []
            print("Total members created:", total)

    # Create remaining members.
    if members:
        total += len(members)
        RoomMember.objects.bulk_create(members, ignore_conflicts=True)
        print("Total members created:", total)


def setup_dev():
    create_users(100_000)
    r1 = create_room('Centrifugo')
    fill_room(r1.pk, 100_000)
    r2 = create_room('Movies')
    fill_room(r2.pk, 10_000)
    r3 = create_room('Programming')
    fill_room(r3.pk, 1_000)
    r4 = create_room('Football')
    fill_room(r4.pk, 100)
    
from django.contrib.auth.models import User
from django.utils.crypto import get_random_string
from django.contrib.auth.hashers import make_password
from .models import PlayerProfile, Room, RoomObject, EntranceExit
import random
from datetime import datetime, timedelta

# Generación de usuarios con perfiles de jugador
def create_players(n):
    users = []
    profiles = []
    total = 0
    
    for _ in range(n):
        username = f"player_{get_random_string(6)}"
        email = f"{username}@simworld.com"
        password = get_random_string(12)
        
        user = User(
            username=username,
            email=email,
            password=make_password(password)
        )
        users.append(user)
        
        if len(users) >= 100:
            User.objects.bulk_create(users)
            # Crear perfiles para los usuarios recién creados
            for user in users:
                profiles.append(PlayerProfile(
                    user=user,
                    energy=random.randint(30, 100),
                    productivity=random.randint(20, 80),
                    social=random.randint(20, 80),
                    position_x=random.randint(0, 30),
                    position_y=random.randint(0, 30)
                ))
            
            PlayerProfile.objects.bulk_create(profiles)
            total += len(users)
            users = []
            profiles = []
            print(f"Total players created: {total}")

    if users:
        User.objects.bulk_create(users)
        for user in users:
            profiles.append(PlayerProfile(
                user=user,
                energy=random.randint(30, 100),
                productivity=random.randint(20, 80),
                social=random.randint(20, 80)
            ))
        PlayerProfile.objects.bulk_create(profiles)
        total += len(users)
        print(f"Total players created: {total}")

# Generación de habitaciones con objetos básicos
def create_room_with_objects(name, room_type, owner):
    room = Room.objects.create(
        name=name,
        room_type=room_type,
        owner=owner,
        length=30,
        width=30,
        capacity=random.randint(5, 20)
    )
    
    # Crear objetos según el tipo de habitación
    if room_type == 'OFFICE':
        create_workstations(room, random.randint(3, 10))
    elif room_type == 'LOUNGE':
        create_social_areas(room, random.randint(2, 5))
    
    # Crear entradas básicas
    create_basic_entrances(room)
    
    return room

def create_workstations(room, count):
    for i in range(count):
        RoomObject.objects.create(
            name=f"Workstation {i+1}",
            room=room,
            position_x=random.randint(1, room.length-1),
            position_y=random.randint(1, room.width-1),
            object_type='WORK',
            effect={'productivity': 10, 'energy_cost': 5}
        )

def create_social_areas(room, count):
    for i in range(count):
        RoomObject.objects.create(
            name=f"Social Area {i+1}",
            room=room,
            position_x=random.randint(1, room.length-1),
            position_y=random.randint(1, room.width-1),
            object_type='SOCIAL',
            effect={'social': 8, 'energy_cost': 3}
        )

def create_basic_entrances(room):
    directions = ['NORTH', 'SOUTH', 'EAST', 'WEST']
    for direction in random.sample(directions, random.randint(1, 3)):
        EntranceExit.objects.create(
            name=f"{direction} Entrance",
            room=room,
            face=direction,
            enabled=True
        )

# Simulación de actividades
def simulate_day():
    players = PlayerProfile.objects.all()
    for player in players:
        # Reducción natural de energía
        player.energy = max(0, player.energy - random.randint(1, 5))
        
        # Cambio de estado aleatorio
        if player.current_room:
            room_objects = player.current_room.objects.all()
            if room_objects and random.random() > 0.7:
                obj = random.choice(room_objects)
                obj.interact(player)
        
        player.save()

# Configuración inicial del mundo
def setup_world():
    admin = User.objects.create_superuser('admin', 'admin@simworld.com', 'admin123')
    
    # Crear habitaciones principales
    offices = [
        create_room_with_objects('Main Office', 'OFFICE', admin),
        create_room_with_objects('Design Dept', 'OFFICE', admin)
    ]
    
    common_areas = [
        create_room_with_objects('Lounge', 'LOUNGE', admin),
        create_room_with_objects('Cafeteria', 'KITCHEN', admin)
    ]
    
    # Conectar habitaciones
    connect_rooms(offices[0], offices[1], 'EAST')
    connect_rooms(offices[0], common_areas[0], 'SOUTH')
    
    # Crear jugadores
    create_players(50)
    
    print("World setup complete!")

def connect_rooms(room1, room2, direction):
    # Crear conexión bidireccional entre habitaciones
    entrance1 = room1.entrances.filter(face=direction).first()
    entrance2 = room2.entrances.filter(face=get_opposite_direction(direction)).first()
    
    if entrance1 and entrance2:
        connection = RoomConnection.objects.create(
            from_room=room1,
            to_room=room2,
            entrance=entrance1,
            bidirectional=True
        )
        entrance1.connection = connection
        entrance1.save()

def get_opposite_direction(direction):
    opposites = {
        'NORTH': 'SOUTH',
        'SOUTH': 'NORTH',
        'EAST': 'WEST',
        'WEST': 'EAST'
    }
    return opposites.get(direction, 'NORTH')