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
from courses.views import preview_content_block
from django.template.loader import render_to_string

def test_contentblock_preview():
    """Prueba la vista previa del ContentBlock id=25"""

    try:
        # Usar el usuario 'su' que ya existe
        user = User.objects.get(username='su')
        print(f"Usuario de prueba: {user.username} (ID: {user.id})")

        # Crear request factory
        factory = RequestFactory()
        request = factory.get('/courses/content/anuncio/preview/')
        request.user = user

        print("Creando request para /courses/content/anuncio/preview/")

        # Llamar a la vista
        response = preview_content_block(request, slug='anuncio')

        print(f"Response status: {response.status_code}")

        if response.status_code == 200:
            print("[OK] Vista previa renderizada correctamente")

            # Verificar que el contenido incluye elementos del ContentBlock
            content = response.content.decode('utf-8')

            # Guardar el HTML renderizado para inspección
            with open('contentblock_25_preview.html', 'w', encoding='utf-8') as f:
                f.write(content)

            print("\n[INFO] HTML de vista previa guardado en: contentblock_25_preview.html")

            # Verificar elementos específicos del ContentBlock de anuncio (sin emojis problemáticos)
            ad_indicators = [
                'Lleva tu Álgebra al Siguiente Nivel',
                'banner', 'anuncio', 'premium', 'descuento',
                'PREMIUM', 'OFERTA ESPECIAL', '40% de descuento',
                'ad_banner', 'ad_card', 'ad_alert', 'ad_testimonial'
            ]

            print("\n=== Verificación de elementos del anuncio ===")
            found_indicators = []
            for indicator in ad_indicators:
                try:
                    if indicator in content:
                        found_indicators.append(indicator)
                        print(f"[OK] Elemento encontrado: '{indicator}'")
                    else:
                        print(f"[MISSING] Elemento no encontrado: '{indicator}'")
                except UnicodeEncodeError:
                    print(f"[SKIP] Elemento con caracteres especiales: '{indicator}'")

            if found_indicators:
                print(f"\n[SUCCESS] Encontrados {len(found_indicators)} elementos del anuncio")
            else:
                print("\n[WARNING] No se encontraron elementos específicos del anuncio")

            # Verificar que no hay errores de template
            if 'TemplateSyntaxError' in content or 'TemplateDoesNotExist' in content:
                print("[ERROR] Error de template detectado")
            else:
                print("[OK] No se detectaron errores de template")

            # Verificar tamaño aproximado
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
    success = test_contentblock_preview()
    if success:
        print("\n[SUCCESS] Prueba de vista previa completada exitosamente")
    else:
        print("\n[FAILED] Prueba de vista previa fallida")