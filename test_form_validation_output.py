#!/usr/bin/env python
import os
import sys

# Configurar Django ANTES de cualquier import
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'panel.settings')
sys.path.append('.')

import django
django.setup()

from django.test import Client
from django.contrib.auth.models import User
from rooms.models import Room, EntranceExit
import json

def test_form_validation_output():
    """Prueba el formulario de edición de entrada y muestra mensajes de validación"""

    print("=== PRUEBA DE VALIDACIÓN DE FORMULARIO DE ENTRADA ===\n")

    # Obtener datos de prueba
    try:
        room = Room.objects.get(id=3)
        user = User.objects.get(username='su')
        entrance = EntranceExit.objects.filter(room=room).first()

        print(f"Habitacion: {room.name} (ID: {room.id})")
        print(f"Usuario: {user.username}")
        print(f"Entrada: {entrance.name} (ID: {entrance.id})")
        print()

    except Exception as e:
        print(f"ERROR obteniendo datos: {e}")
        return

    # Crear cliente y login
    client = Client()
    login_success = client.login(username='su', password='su')
    print(f"Login exitoso: {login_success}")
    print()

    # URL del formulario
    form_url = f'/rooms/entrance-exits/{entrance.id}/edit/'
    print(f"URL del formulario: {form_url}")
    print()

    # ===== PRUEBA 1: DATOS INVÁLIDOS =====
    print("=" * 60)
    print("PRUEBA 1: ENVIANDO DATOS INVALIDOS")
    print("=" * 60)

    invalid_data = {
        'name': '',  # Campo requerido vacío
        'face': 'INVALID_DIRECTION',  # Dirección inválida
        'description': 'Descripción de prueba',
        'position_x': 'not_a_number',  # No es número
        'position_y': -10,  # Número negativo
    }

    print("Datos enviados:")
    for key, value in invalid_data.items():
        print(f"  {key}: {repr(value)}")
    print()

    try:
        response = client.post(form_url, invalid_data, follow=True)
        print(f"Respuesta HTTP: {response.status_code}")
        print(f"Redirigido: {response.redirect_chain}")
        print()

        # Obtener contenido de la respuesta
        content = response.content.decode('utf-8')

        # Buscar mensajes de error en el HTML
        print("MENSAJES DE VALIDACIÓN ENCONTRADOS:")
        print("-" * 40)

        # Buscar errores de Django forms (errorlist)
        import re

        # Patrón para encontrar errores de Django
        error_patterns = [
            r'<ul class="errorlist"[^>]*>.*?</ul>',
            r'<div class="text-danger[^"]*">.*?</div>',
            r'<span[^>]*class="[^"]*error[^"]*"[^>]*>.*?</span>',
        ]

        errors_found = False
        for pattern in error_patterns:
            matches = re.findall(pattern, content, re.DOTALL | re.IGNORECASE)
            for match in matches:
                # Limpiar HTML y mostrar solo el texto
                clean_text = re.sub(r'<[^>]+>', '', match).strip()
                if clean_text and len(clean_text) > 5:  # Evitar mensajes vacíos
                    print(f"ERROR: {clean_text}")
                    errors_found = True

        # Buscar mensajes de error específicos
        if 'required' in content.lower():
            print("ERROR: Campo requerido no completado")
            errors_found = True

        if 'invalid' in content.lower() or 'válido' in content.lower():
            print("ERROR: Valor inválido detectado")
            errors_found = True

        if not errors_found:
            print("No se encontraron mensajes de error específicos en el HTML")
            print("\nContenido de respuesta (primeros 1000 caracteres):")
            print("-" * 50)
            print(content[:1000])
            print("-" * 50)

    except Exception as e:
        print(f"ERROR en POST request: {e}")
        import traceback
        traceback.print_exc()

    print("\n" + "=" * 60)
    print("PRUEBA 2: ENVIANDO DATOS VALIDOS")
    print("=" * 60)

    # Datos válidos
    valid_data = {
        'name': 'Puerta Editada por Prueba',
        'face': 'NORTH',
        'description': 'Descripción editada por script de prueba',
        'position_x': 5,
        'position_y': 10,
    }

    print("Datos enviados:")
    for key, value in valid_data.items():
        print(f"  {key}: {repr(value)}")
    print()

    try:
        response = client.post(form_url, valid_data, follow=True)
        print(f"Respuesta HTTP: {response.status_code}")
        print(f"Redirigido: {response.redirect_chain}")
        print()

        if response.status_code == 200 and 'messages' in str(response.context):
            # Verificar mensajes de éxito
            messages = response.context.get('messages', [])
            for message in messages:
                print(f"MENSAJE: {message}")

        # Verificar si fue redirigido exitosamente
        if len(response.redirect_chain) > 0:
            final_url = response.redirect_chain[-1][0]
            print(f"REDIRECCIÓN EXITOSA a: {final_url}")

            # Verificar que la entrada fue actualizada
            entrance.refresh_from_db()
            print("\nEntrada actualizada:")
            print(f"  Nombre: {entrance.name}")
            print(f"  Dirección: {entrance.face}")
            print(f"  Descripción: {entrance.description}")
            print(f"  Posición: ({entrance.position_x}, {entrance.position_y})")

        else:
            print("NO HUBO REDIRECCIÓN - POSIBLE ERROR")
            content = response.content.decode('utf-8')
            # Buscar errores
            if 'error' in content.lower() or 'invalid' in content.lower():
                print("ERRORES ENCONTRADOS EN RESPUESTA:")
                error_matches = re.findall(r'<[^>]*error[^>]*>.*?</[^>]*>', content, re.DOTALL | re.IGNORECASE)
                for match in error_matches[:5]:  # Solo primeros 5
                    clean_match = re.sub(r'<[^>]+>', '', match).strip()
                    if clean_match:
                        print(f"  {clean_match}")

    except Exception as e:
        print(f"ERROR en POST valido: {e}")
        import traceback
        traceback.print_exc()

    print("\n" + "=" * 60)
    print("RESUMEN DE PRUEBA")
    print("=" * 60)
    print("Esta prueba muestra los mensajes de validación exactos")
    print("que aparecen cuando el formulario no permite guardar.")

if __name__ == '__main__':
    test_form_validation_output()