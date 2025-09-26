#!/usr/bin/env python
"""
Test script para verificar el renderizado 3D de habitaciones
"""
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'panel.settings')
django.setup()

from rooms.models import Room
from rooms.views import generate_room_3d_svg

def test_3d_rendering():
    """Prueba el renderizado 3D de una habitación"""
    print("=== Prueba de Renderizado 3D ===")

    # Obtener primera habitación o crear una de prueba
    room = Room.objects.first()
    if not room:
        print("No hay habitaciones existentes. Creando una de prueba...")
        room = Room.objects.create(
            name='Habitación 3D de Prueba',
            length=25,
            width=20,
            height=15,
            x=0, y=0, z=0,
            room_type='OFFICE'
        )
        print(f"Habitación creada: {room.name}")

    print(f"Renderizando habitación: {room.name}")
    print(f"Dimensiones: {room.length}×{room.width}×{room.height}")
    print(f"Posición: ({room.x}, {room.y}, {room.z})")

    try:
        # Generar SVG
        svg_content = generate_room_3d_svg(room)
        print(f"SVG generado exitosamente! Longitud: {len(svg_content)} caracteres")

        # Verificar que contiene elementos SVG
        if '<svg' in svg_content and '</svg>' in svg_content:
            print("Contenido SVG valido")
        else:
            print("Contenido SVG invalido")

        # Mostrar preview
        print("\n=== Preview del SVG (primeros 500 caracteres) ===")
        print(svg_content[:500])
        print("...")

        # Verificar que contiene información de la habitación
        if room.name in svg_content:
            print("Informacion de la habitacion incluida en el SVG")
        else:
            print("Informacion de la habitacion faltante")

        print("\n=== Prueba Completada ===")
        return True

    except Exception as e:
        print(f"Error en el renderizado: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = test_3d_rendering()
    sys.exit(0 if success else 1)