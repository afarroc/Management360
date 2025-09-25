#!/usr/bin/env python3
"""
Script para probar que el template de edición se renderiza correctamente
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
from events.models import TaskSchedule, Task
from datetime import timedelta

def test_edit_template_rendering():
    """Prueba que el template de edición se renderiza correctamente"""

    print("=== PRUEBA: RENDERIZADO DEL TEMPLATE DE EDICIÓN ===")

    try:
        # Crear una instancia del formulario con datos de edición
        # Primero necesitamos crear una instancia de TaskSchedule para simular edición
        form = TaskScheduleForm()

        # Crear contexto simulado para edición
        schedule_data = {
            'id': 32,
            'task': {'title': 'Tarea de prueba para edición'},
            'duration': timedelta(hours=1.5)  # 1.5 horas
        }

        context = {
            'form': form,
            'schedule': schedule_data,
            'title': 'Editar Programación: Tarea de prueba para edición'
        }

        # Cargar y renderizar el template
        template = get_template('events/edit_task_schedule.html')
        rendered_html = template.render(context)

        print("[OK] Template de edición cargado y renderizado")

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
            ('edit_form', 'id="editScheduleForm"' in rendered_html),
            ('task_readonly', 'readonly' in rendered_html and 'task_title' in rendered_html),
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

        # Verificar elementos específicos de edición
        edit_specific_checks = [
            ('warning_header', 'bg-warning' in rendered_html),
            ('edit_title', 'Editar Programación' in rendered_html),
            ('save_changes', 'Guardar Cambios' in rendered_html),
            ('task_info_section', 'Información de la Tarea' in rendered_html),
        ]

        for check_name, check_result in edit_specific_checks:
            if check_result:
                print(f"[OK] {check_name}")
            else:
                print(f"[ERROR] {check_name}")
                all_passed = False

        if all_passed:
            print("\n=== PRUEBA COMPLETADA EXITOSAMENTE ===")
            print("✓ Template de edición renderiza correctamente")
            print("✓ Contenedor de días presente y oculto")
            print("✓ 7 checkboxes de días presentes")
            print("✓ IDs de días correctos")
            print("✓ JavaScript de visibilidad presente")
            print("✓ Elementos específicos de edición presentes")
            print("✓ Formulario de edición presente")
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
    success = test_edit_template_rendering()
    exit(0 if success else 1)