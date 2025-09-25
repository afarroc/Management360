#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import django
import sys

# Configurar Django
sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'panel.settings')
django.setup()

from django.test import RequestFactory
from django.contrib.auth.models import User
from courses.views import content_manager
from django.template.loader import render_to_string

def test_content_manager_rendering():
    """Prueba el renderizado de la vista content_manager"""

    try:
        # Usar el usuario 'su' que ya existe
        user = User.objects.get(username='su')
        print(f"Usuario de prueba: {user.username} (ID: {user.id})")

        # Crear request factory
        factory = RequestFactory()
        request = factory.get('/courses/content/')
        request.user = user

        print("Creando request para /courses/content/")

        # Llamar a la vista
        response = content_manager(request)

        print(f"Response status: {response.status_code}")

        if response.status_code == 200:
            print("[OK] Vista renderizada correctamente")

            # Verificar que el contenido incluye elementos del nuevo layout
            content = response.content.decode('utf-8')

            # Verificar elementos clave del nuevo layout
            checks = [
                ('Sidebar', 'content-sidebar'),
                ('Layout principal', 'content-manager-layout'),
                ('Header compacto', 'content-header-bar'),
                ('Acciones rapidas', 'quick-actions-section'),
                ('Panel de creacion', 'create-panel'),
                ('Estadisticas', 'stats-overview'),
                ('Bloques recientes', 'recent-blocks-section'),
            ]

            print("\n=== Verificacion de elementos del layout ===")
            for name, class_name in checks:
                if class_name in content:
                    print(f"[OK] {name}: Presente")
                else:
                    print(f"[ERROR] {name}: NO encontrado")

            # Verificar que no hay errores de template
            if 'TemplateSyntaxError' in content or 'TemplateDoesNotExist' in content:
                print("[ERROR] Error de template detectado")
            else:
                print("[OK] No se detectaron errores de template")

            # Verificar que incluye los includes correctos
            includes_checks = [
                'content_manager_sidebar.html',
                'content_manager_header_compact.html',
                'content_manager_quick_actions.html',
                'content_manager_create_panel.html',
            ]

            print("\n=== Verificacion de includes ===")
            for include_file in includes_checks:
                if include_file in content:
                    print(f"[OK] {include_file}: Incluido")
                else:
                    print(f"[ERROR] {include_file}: NO encontrado")

            # Guardar el HTML renderizado para inspeccion
            with open('content_manager_rendered.html', 'w', encoding='utf-8') as f:
                f.write(content)

            print("\n[INFO] HTML completo guardado en: content_manager_rendered.html")
            # Verificar tamano aproximado
            size_kb = len(content) / 1024
            print(f"Tamano del HTML: {size_kb:.1f} KB")
            return True

        else:
            print(f"[ERROR] Error en la vista: {response.status_code}")
            if hasattr(response, 'content'):
                print("Contenido del error:")
                print(response.content.decode('utf-8')[:500])
            return False

    except Exception as e:
        print(f"[ERROR] Error durante la prueba: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_content_manager_rendering()
    if success:
        print("\n[SUCCESS] Prueba completada exitosamente")
    else:
        print("\n[FAILED] Prueba fallida")