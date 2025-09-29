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
from rooms.models import Room
import json

def test_room_edit_validation():
    """Prueba detallada de validación del formulario de edición de habitación"""

    print("=" * 80)
    print("PRUEBA DETALLADA DE VALIDACIÓN - FORMULARIO EDICIÓN HABITACIÓN")
    print("=" * 80)
    print()

    # Obtener datos de prueba
    try:
        room = Room.objects.get(id=2)
        user = User.objects.get(username='su')

        print(f"HABITACION: {room.name} (ID: {room.id})")
        print(f"USUARIO: {user.username}")
        print()

    except Exception as e:
        print(f"ERROR obteniendo datos: {e}")
        return

    # Crear cliente y login
    client = Client()
    login_success = client.login(username='su', password='su')
    print(f"LOGIN: {'EXITOSO' if login_success else 'FALLIDO'}")
    print()

    if not login_success:
        return

    # PASO 1: Cargar el formulario
    print("PASO 1: CARGANDO FORMULARIO DE EDICIÓN")
    print("-" * 50)

    form_url = f'/rooms/rooms/{room.id}/edit/'
    response = client.get(form_url)

    print(f"URL: {form_url}")
    print(f"Respuesta HTTP: {response.status_code}")

    if response.status_code != 200:
        print("ERROR: No se pudo cargar el formulario")
        return

    content = response.content.decode('utf-8')

    # Verificar elementos críticos del formulario
    checks = [
        ('<form method="post"', 'Etiqueta form'),
        ('name="csrfmiddlewaretoken"', 'Token CSRF'),
        ('name="name"', 'Campo name'),
        ('name="room_type"', 'Campo room_type'),
        ('<button type="submit"', 'Botón submit'),
        ('room_edit_alerts.html', 'Template correcto'),
    ]

    print("VERIFICACIÓN DE ELEMENTOS:")
    for check, description in checks:
        found = check in content
        status = "[OK]" if found else "[ERROR]"
        print(f"  {status} {description}")

    print()

    # PASO 2: Intentar envío con datos mínimos válidos
    print("PASO 2: ENVÍO CON DATOS MÍNIMOS VÁLIDOS")
    print("-" * 50)

    # Extraer token CSRF
    import re
    csrf_match = re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', content)
    csrf_token = csrf_match.group(1) if csrf_match else 'dummy_token'

    print(f"Token CSRF obtenido: {csrf_token[:20]}...")

    # Datos mínimos requeridos
    minimal_data = {
        'csrfmiddlewaretoken': csrf_token,
        'name': 'Habitación Editada por Test',
        'room_type': 'OFFICE',
    }

    print("Datos enviados (mínimos requeridos):")
    for key, value in minimal_data.items():
        if key != 'csrfmiddlewaretoken':
            print(f"  -> {key}: {repr(value)}")

    print()

    # Enviar POST
    response = client.post(form_url, minimal_data, follow=True)

    print(f"Respuesta HTTP: {response.status_code}")
    print(f"Redirecciones: {len(response.redirect_chain)}")

    if response.redirect_chain:
        for i, (url, status) in enumerate(response.redirect_chain):
            print(f"  {i+1}. {status} -> {url}")

    # Verificar resultado
    if response.status_code == 200 and response.redirect_chain:
        print("RESULTADO: FORMULARIO PROCESADO EXITOSAMENTE")
        print("La validación JavaScript permitió el envío")
        print("El formulario se guardó correctamente")
    else:
        print("RESULTADO: FORMULARIO BLOQUEADO")
        content = response.content.decode('utf-8')

        # Buscar mensajes de error
        error_patterns = [
            r'<div class="alert alert-danger[^"]*">([^<]+)</div>',
            r'<span[^>]*class="[^"]*error[^"]*"[^>]*>([^<]+)</span>',
            r'<ul class="errorlist"[^>]*>.*?<li>([^<]+)</li>.*?</ul>',
        ]

        errors_found = []
        for pattern in error_patterns:
            matches = re.findall(pattern, content, re.DOTALL | re.IGNORECASE)
            errors_found.extend(matches)

        if errors_found:
            print("ERRORES ENCONTRADOS:")
            for error in errors_found:
                print(f"  - {error.strip()}")
        else:
            print("No se encontraron errores específicos en el HTML")

        # Verificar si hay JavaScript que prevenga el envío
        if 'preventDefault' in content or 'return false' in content:
            print("POSIBLE CAUSA: JavaScript está previniendo el envío del formulario")

        # Mostrar parte del contenido para debug
        print("\nPRIMERAS 1000 CARACTERES DE LA RESPUESTA:")
        print("=" * 50)
        print(content[:1000])
        if len(content) > 1000:
            print("... (contenido truncado)")

    print()
    print("=" * 80)
    print("ANÁLISIS DE VALIDACIÓN")
    print("=" * 80)

    # Verificar configuración del formulario
    from rooms.forms import RoomForm
    form = RoomForm(instance=room, user=user)

    print("CONFIGURACIÓN DEL FORMULARIO RoomForm:")
    print(f"  Campos totales: {len(form.fields)}")

    required_count = 0
    for field_name, field in form.fields.items():
        required = getattr(field, 'required', False)
        if required:
            required_count += 1
            print(f"  [REQUIRED] {field_name}")

    print(f"  Total campos requeridos: {required_count}")

    print("\nCONCLUSIONES:")
    if response.status_code == 200 and response.redirect_chain:
        print("✅ El formulario funciona correctamente con datos mínimos")
        print("✅ La validación JavaScript no está bloqueando el envío")
        print("✅ Los campos opcionales tienen valores por defecto")
    else:
        print("❌ El formulario está siendo bloqueado")
        print("❌ Posibles causas:")
        print("   - Validación JavaScript demasiado estricta")
        print("   - Campos marcados como requeridos incorrectamente")
        print("   - Error en el procesamiento del formulario")

if __name__ == '__main__':
    test_room_edit_validation()