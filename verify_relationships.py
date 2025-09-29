#!/usr/bin/env python
import os
import sys
import django

# Setup Django
sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'panel.settings')
django.setup()

from rooms.models import Room, EntranceExit, RoomConnection

print("=== VERIFICACION COMPLETA DE RELACIONES ===")
print("=" * 60)

# 1. Mostrar todas las habitaciones
print("\n1. HABITACIONES:")
print("-" * 30)
rooms = Room.objects.all().order_by('id')
for room in rooms:
    status = "[ACTIVA]" if room.is_active else "[INACTIVA]"
    print(f"ID {room.id}: {room.name} - {status}")

# 2. Mostrar todas las conexiones
print("\n2. CONEXIONES:")
print("-" * 30)
connections = RoomConnection.objects.all().order_by('id')
for conn in connections:
    bidirectional = "[BIDIRECCIONAL]" if conn.bidirectional else "[UNIDIRECCIONAL]"
    print(f"ID {conn.id}: {conn.from_room.name} -> {conn.to_room.name}")
    print(f"    Puerta: {conn.entrance.name} | Costo: {conn.energy_cost} | {bidirectional}")

# 3. Mostrar todas las entradas con sus conexiones
print("\n3. ENTRADAS Y SUS CONEXIONES:")
print("-" * 40)
entrances = EntranceExit.objects.all().order_by('id')
for entrance in entrances:
    enabled = "[HABILITADA]" if entrance.enabled else "[DESHABILITADA]"
    has_connection = "[CONECTADA]" if entrance.connection else "[SIN CONEXION]"

    print(f"ID {entrance.id}: {entrance.name}")
    print(f"    Habitacion: {entrance.room.name} ({entrance.face})")
    print(f"    Estado: {enabled} | {has_connection}")

    if entrance.connection:
        conn = entrance.connection
        target_room = conn.to_room if conn.from_room == entrance.room else (conn.from_room if conn.bidirectional else "N/A")
        print(f"    Conecta a: {target_room.name if hasattr(target_room, 'name') else target_room}")
        print(f"    Conexion ID: {conn.id} | Costo: {conn.energy_cost}")
    print()

# 4. Verificar consistencia
print("4. VERIFICACION DE CONSISTENCIA:")
print("-" * 40)

issues = []

# Verificar que todas las conexiones tengan entradas validas
for conn in connections:
    if not conn.entrance:
        issues.append(f"[ERROR] Conexion {conn.id} no tiene entrada asignada")

    # Verificar que la entrada pertenezca a la habitacion correcta
    if conn.entrance and conn.entrance.room != conn.from_room:
        issues.append(f"[ERROR] Conexion {conn.id}: La entrada '{conn.entrance.name}' no pertenece a la habitacion origen '{conn.from_room.name}'")

# Verificar que todas las entradas conectadas tengan conexiones validas
for entrance in entrances:
    if entrance.connection:
        if entrance.connection.entrance != entrance:
            issues.append(f"[ERROR] Entrada {entrance.id} ({entrance.name}) tiene conexion {entrance.connection.id} pero la conexion apunta a otra entrada")

# Verificar habitaciones activas
inactive_rooms = Room.objects.filter(is_active=False)
if inactive_rooms:
    for room in inactive_rooms:
        issues.append(f"[WARNING] Habitacion '{room.name}' esta inactiva")

if not issues:
    print("[OK] No se encontraron problemas de consistencia")
else:
    print("[ERROR] Se encontraron los siguientes problemas:")
    for issue in issues:
        print(f"   {issue}")

print("\n" + "=" * 60)
print("VERIFICACION COMPLETADA")