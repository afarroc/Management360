#!/usr/bin/env python
import os
import django
import sys

# Configurar Django
sys.path.append(os.path.dirname(__file__))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'panel.settings')
django.setup()

from bitacora.models import BitacoraEntry
from django.template import Template, Context

def test_json_rendering():
    """Prueba el renderizado completo de contenido estructurado JSON"""
    try:
        # Obtener la entrada
        entry = BitacoraEntry.objects.get(id=3)
        print("=== PRUEBA DE RENDERIZADO JSON ===")
        print(f"Entrada: {entry.titulo}")
        print(f"URL: /bitacora/{entry.id}/")
        print()

        # Obtener bloques estructurados
        structured_blocks = entry.get_structured_content_blocks()
        print(f"Bloques estructurados encontrados: {len(structured_blocks)}")
        print()

        # Procesar cada bloque
        rendered_blocks = []
        for i, block in enumerate(structured_blocks):
            print(f"--- BLOQUE {i+1}: {block.get('title', 'Sin titulo')} ---")
            print(f"Tipo: {block.get('content_type', 'Sin tipo')}")
            print(f"ID: {block.get('id', 'Sin ID')}")

            # Renderizar el bloque
            rendered_html = entry.render_content_block(block)
            rendered_blocks.append(rendered_html)

            print(f"Longitud HTML renderizado: {len(rendered_html)} caracteres")

            # Mostrar preview del HTML (primeros 200 caracteres)
            preview = rendered_html[:200].replace('\n', ' ').replace('\r', '')
            print(f"Preview HTML: {preview}...")
            print()

        # Simular el template de Django
        print("=== SIMULACIÓN DEL TEMPLATE DJANGO ===")

        # Template HTML que se usaría en entry_detail.html
        template_html = """
        {% if entry.structured_content %}
        <div class="mb-4">
            <h5><i class="bi bi-puzzle"></i> Contenido Estructurado:</h5>
            <div class="structured-content">
                {% for rendered_block in rendered_blocks %}
                <div class="content-block mb-3 p-3 border rounded bg-light">
                    <div class="content-body">
                        <!-- CONTENIDO RENDERIZADO AQUÍ -->
                        {{ rendered_block|safe }}
                    </div>
                </div>
                {% endfor %}
            </div>
        </div>
        {% endif %}
        """

        # Crear template y contexto
        template = Template(template_html)
        context = Context({
            'entry': entry,
            'rendered_blocks': rendered_blocks
        })

        # Renderizar
        final_html = template.render(context)

        print("HTML final renderizado:")
        print(f"Longitud total: {len(final_html)} caracteres")
        print("Contiene seccion de contenido estructurado:", "Contenido Estructurado" in final_html)
        print("Contiene bloques renderizados:", "content-block" in final_html)
        print("=" * 50)

        # Verificar que contiene los componentes esperados
        checks = [
            ('ad-banner', 'Banner publicitario'),
            ('ad-card', 'Tarjeta de producto'),
            ('ad-alert', 'Alerta informativa'),
            ('ad-testimonial', 'Testimonial'),
            ('ad-countdown', 'Contador regresivo'),
            ('ad-feature', 'Sección de características'),
            ('ad-comparison', 'Tabla comparativa'),
            ('ad-achievement', 'Sección de logros'),
        ]

        print("\n=== VERIFICACIÓN DE COMPONENTES ===")
        for css_class, description in checks:
            if css_class in final_html:
                print(f"[OK] {description} - ENCONTRADO")
            else:
                print(f"[ERROR] {description} - NO ENCONTRADO")

        print(f"\nTotal de caracteres en HTML final: {len(final_html)}")

        # Guardar el HTML para inspección
        with open('rendered_json_test.html', 'w', encoding='utf-8') as f:
            f.write(final_html)
        print("\nHTML guardado en: rendered_json_test.html")

    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_json_rendering()