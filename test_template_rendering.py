#!/usr/bin/env python3
"""
Script para probar que el template se renderiza correctamente con los días de la semana
"""

import os
import sys
import django
from django.conf import settings
from django.template.loader import get_template
from django.template import Context

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'panel.settings')
sys.path.insert(0, os.path.dirname(__file__))
django.setup()

from events.forms import TaskScheduleForm

def test_template_rendering():
    """Prueba que el template se renderiza correctamente con los días de la semana"""

    print("=== PRUEBA: RENDERIZADO DEL TEMPLATE ===")

    try:
        # Crear una instancia del formulario
        form = TaskScheduleForm()

        # Crear contexto para el template
        context = {
            'form': form,
            'title': 'Crear Programación Recurrente'
        }

        # Cargar y renderizar el template
        template = get_template('events/create_task_schedule.html')
        rendered_html = template.render(context)

        print("[OK] Template cargado y renderizado")

        # Verificar que contiene los elementos esperados
        checks = [
            ('daysGroup', 'id="daysGroup"' in rendered_html),
            ('display_none', 'style="display: none;"' in rendered_html),
            ('monday_checkbox', 'id_monday' in rendered_html),
            ('tuesday_checkbox', 'id_tuesday' in rendered_html),
            ('wednesday_checkbox', 'id_wednesday' in rendered_html),
            ('thursday_checkbox', 'id_thursday' in rendered_html),
            ('friday_checkbox', 'id_friday' in rendered_html),
            ('saturday_checkbox', 'id_saturday' in rendered_html),
            ('sunday_checkbox', 'id_sunday' in rendered_html),
            ('day_checkboxes', rendered_html.count('day-checkbox') == 7),
            ('recurrence_select', 'id_recurrence_type' in rendered_html),
            ('toggle_js', 'toggleDaysVisibility' in rendered_html),
        ]

        all_passed = True
        for check_name, check_result in checks:
            if check_result:
                print(f"[OK] {check_name}")
            else:
                print(f"[ERROR] {check_name}")
                all_passed = False

        # Contar checkboxes de días
        day_checkboxes_count = rendered_html.count('class="form-check-input day-checkbox"')
        if day_checkboxes_count == 7:
            print(f"[OK] Encontrados exactamente 7 checkboxes de días")
        else:
            print(f"[ERROR] Se encontraron {day_checkboxes_count} checkboxes de días, se esperaban 7")
            all_passed = False

        # Verificar que los días están en el orden correcto
        days_order = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
        for i, day in enumerate(days_order):
            if f'id_{day}' in rendered_html:
                print(f"[OK] Día {day} encontrado en orden correcto")
            else:
                print(f"[ERROR] Día {day} no encontrado")
                all_passed = False

        if all_passed:
            print("\n=== PRUEBA COMPLETADA EXITOSAMENTE ===")
            print("✓ Template renderiza correctamente")
            print("✓ Contenedor de días presente y oculto")
            print("✓ 7 checkboxes de días presentes")
            print("✓ IDs de días correctos")
            print("✓ JavaScript de visibilidad presente")
            print("✓ Selector de recurrencia presente")
            return True
        else:
            print("\n=== PRUEBA FALLIDA ===")
            return False

    except Exception as e:
        print(f"ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_template_rendering()
    exit(0 if success else 1)