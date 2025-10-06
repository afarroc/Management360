#!/usr/bin/env python
import os
import django
import sys

# Configurar Django
sys.path.append(os.path.dirname(__file__))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'panel.settings')
django.setup()

from bitacora.templatetags.bitacora_tags import render_content_block

def test_template_tag():
    """Probar el template tag directamente"""

    # Datos de prueba - simular lo que viene de la base de datos
    test_data = {
        'type': 'ad_banner',
        'title': '¡Lleva tu Álgebra al Siguiente Nivel!',
        'content': {
            'header': '¿Te está gustando el curso?',
            'subheader': 'Descubre todas las ventajas de la versión PREMIUM',
            'features': ['💻 **Acceso ilimitado** a todos los módulos y lecciones', '🤖 **Ejercicios personalizados** con inteligencia artificial'],
            'offer': '**OFERTA ESPECIAL:** 40% de descuento por tiempo limitado',
            'price': {'original': '$99.000', 'discounted': '$59.400', 'period': 'acceso vitalicio'},
            'cta': {'text': '¡QUIERO SER PREMIUM!', 'url': '#premium-upgrade', 'color': 'success'}
        }
    }

    print("=== DATOS DE PRUEBA ===")
    print(f"Tipo: {test_data['type']}")
    print(f"Título: {test_data['title']}")
    print(f"Content keys: {list(test_data['content'].keys())}")

    print("\n=== LLAMANDO TEMPLATE TAG ===")
    result = render_content_block(test_data)

    print(f"Tipo de resultado: {type(result)}")
    print(f"Longitud del resultado: {len(str(result))}")

    print("\n=== RESULTADO HTML (primeros 500 chars) ===")
    result_str = str(result)
    print(result_str[:500] + "..." if len(result_str) > 500 else result_str)

    # Verificar si contiene elementos esperados
    checks = [
        ('ad-banner', 'Banner publicitario'),
        ('bg-primary', 'Estilos Bootstrap'),
        ('btn', 'Botones'),
        ('PREMIUM', 'Texto del banner'),
    ]

    print("\n=== VERIFICACIONES ===")
    for check, description in checks:
        found = check in result_str
        status = "[OK]" if found else "[FAIL]"
        print(f"{status} {description}: {'Encontrado' if found else 'No encontrado'}")

if __name__ == '__main__':
    test_template_tag()