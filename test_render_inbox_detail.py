#!/usr/bin/env python
"""
Test de renderizado completo para verificar que la vista inbox_item_detail_admin
muestra correctamente los metadatos del item y la lista de usuarios para delegación.
"""

import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'panel.settings')
django.setup()

# Importaciones después de configurar Django
from django.template import Template, Context, RequestContext
from django.template.loader import get_template
from django.http import HttpRequest
from django.contrib.auth.models import AnonymousUser

from django.contrib.auth.models import User
from events.models import InboxItem, InboxItemClassification, InboxItemHistory
from django.utils import timezone

def test_render_inbox_detail():
    """Test completo de renderizado de la vista inbox_item_detail_admin"""
    print("=== Test de Renderizado inbox_item_detail_admin ===")

    # Obtener el item 110
    try:
        inbox_item = InboxItem.objects.select_related('created_by').get(id=110)
        print(f"Item encontrado: {inbox_item.title}")
    except InboxItem.DoesNotExist:
        print("ERROR: Item 110 no encontrado")
        return

    # Obtener usuarios disponibles
    available_users = User.objects.filter(is_active=True).order_by('username')
    print(f"Usuarios disponibles: {available_users.count()}")

    # Obtener clasificaciones
    classifications = InboxItemClassification.objects.filter(inbox_item=inbox_item)
    print(f"Clasificaciones: {classifications.count()}")

    # Calcular consenso
    consensus_category = inbox_item.get_classification_consensus()
    consensus_action = inbox_item.get_action_type_consensus()
    print(f"Consenso categoría: {consensus_category}")
    print(f"Consenso acción: {consensus_action}")

    # Obtener historial
    activity_history = InboxItemHistory.objects.filter(inbox_item=inbox_item)[:20]
    print(f"Historial: {activity_history.count()} entradas")

    # Preparar contexto como lo hace la vista
    context = {
        'title': f'Administrar: {inbox_item.title}',
        'inbox_item': inbox_item,
        'classifications': classifications,
        'consensus_category': consensus_category,
        'consensus_action': consensus_action,
        'activity_history': activity_history,
        'available_users': available_users,
    }

    # Cargar y renderizar la plantilla
    try:
        # Crear un request mock para el contexto
        request = HttpRequest()
        request.user = available_users.first() if available_users.exists() else AnonymousUser()

        template = get_template('events/inbox_item_detail_admin.html')
        rendered_html = template.render(context, request)

        print("[OK] Plantilla renderizada exitosamente")

        # Verificar contenido clave
        checks = [
            ('Título de la página', f'Administrar: {inbox_item.title}' in rendered_html),
            ('ID del item', str(inbox_item.id) in rendered_html),
            ('Título del item', inbox_item.title in rendered_html),
            ('Creado por', inbox_item.created_by.username in rendered_html),
            ('Categoría GTD', inbox_item.gtd_category in rendered_html),
            ('Prioridad', inbox_item.priority in rendered_html),
            ('Estado procesado', ('Procesado' if inbox_item.is_processed else 'Pendiente') in rendered_html),
            ('Modal de delegación', 'delegateModal' in rendered_html),
            ('Select de usuarios', 'form-select' in rendered_html),
        ]

        print("\n--- Verificación de contenido ---")
        for check_name, result in checks:
            status = "[OK]" if result else "[ERROR]"
            print(f"{status} {check_name}")

        # Verificar usuarios en el select
        if 'form-select' in rendered_html:
            import re
            options = re.findall(r'<option value="\d+">([^<]+)</option>', rendered_html)
            print(f"\nUsuarios en el select ({len(options)}):")
            for i, option_text in enumerate(options[:5]):  # Mostrar primeros 5
                print(f"  {i+1}. {option_text.strip()}")
            if len(options) > 5:
                print(f"  ... y {len(options) - 5} más")

        # Verificar que no hay errores de template
        if 'TemplateSyntaxError' in rendered_html or 'TemplateDoesNotExist' in rendered_html:
            print("\n[ERROR] Errores de template detectados")
        else:
            print("\n[OK] No se detectaron errores de template")

        # Mostrar fragmento del HTML renderizado para debug
        print("\n--- Fragmento del HTML (primeros 1000 caracteres) ---")
        print(rendered_html[:1000] + "..." if len(rendered_html) > 1000 else rendered_html)

        return True

    except Exception as e:
        print(f"ERROR al renderizar plantilla: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = test_render_inbox_detail()
    print(f"\nResultado del test: {'EXITO' if success else 'FALLIDO'}")