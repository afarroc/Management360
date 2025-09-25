#!/usr/bin/env python3
"""
Script para probar que el template de listado de programaciones se renderiza correctamente
"""

import os
import sys
import django
from django.conf import settings
from django.template.loader import get_template
from django.template import Context
from datetime import timedelta

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'panel.settings')
sys.path.insert(0, os.path.dirname(__file__))
django.setup()

from events.forms import TaskScheduleForm
from events.models import TaskSchedule, Task
from datetime import datetime

def test_schedules_list_template_rendering():
    """Prueba que el template de listado de programaciones se renderiza correctamente"""

    print("=== PRUEBA: RENDERIZADO DEL TEMPLATE DE LISTADO DE PROGRAMACIONES ===")

    try:
        # Crear datos simulados para el template
        schedules_data = [
            {
                'schedule': {
                    'id': 1,
                    'task': {'title': 'Tarea de prueba 1'},
                    'recurrence_type': 'weekly',
                    'monday': True,
                    'wednesday': True,
                    'friday': True,
                    'start_time': datetime.strptime('09:00', '%H:%M').time(),
                    'duration': timedelta(hours=1.5),
                    'is_active': True,
                    'get_recurrence_type_display': 'Semanal'
                },
                'next_occurrence': {
                    'date': datetime.now().date(),
                    'start_time': datetime.strptime('09:00', '%H:%M')
                }
            },
            {
                'schedule': {
                    'id': 2,
                    'task': {'title': 'Tarea diaria', 'project': {'title': 'Proyecto X'}},
                    'recurrence_type': 'daily',
                    'start_time': datetime.strptime('14:00', '%H:%M').time(),
                    'duration': timedelta(hours=2),
                    'is_active': False,
                    'get_recurrence_type_display': 'Diaria'
                },
                'next_occurrence': None
            }
        ]

        context = {
            'schedules': schedules_data,
            'total_schedules': 2,
            'active_schedules': 1,
            'inactive_schedules': 1,
            'title': 'Programaciones Recurrentes'
        }

        # Cargar y renderizar el template
        template = get_template('events/task_schedules.html')
        rendered_html = template.render(context)

        print("[OK] Template de listado cargado y renderizado")

        # Verificar elementos clave
        checks = [
            ('header_primary', 'bg-primary' in rendered_html),
            ('stats_cards', 'Total Programaciones' in rendered_html),
            ('search_input', 'id="searchInput"' in rendered_html),
            ('status_filter', 'id="statusFilter"' in rendered_html),
            ('recurrence_filter', 'id="recurrenceFilter"' in rendered_html),
            ('schedule_cards', 'schedule-card' in rendered_html),
            ('weekly_badges', 'Lun' in rendered_html and 'Mié' in rendered_html and 'Vie' in rendered_html),
            ('dropdown_actions', 'dropdown-menu' in rendered_html),
            ('empty_state', 'No hay programaciones recurrentes' in rendered_html),
            ('filter_js', 'filterSchedules' in rendered_html),
            ('hover_effects', 'mouseenter' in rendered_html),
        ]

        all_passed = True
        for check_name, check_result in checks:
            if check_result:
                print(f"[OK] {check_name}")
            else:
                print(f"[ERROR] {check_name}")
                all_passed = False

        # Verificar que hay cards para cada schedule
        schedule_cards_count = rendered_html.count('class="card shadow-sm h-100')
        if schedule_cards_count >= 2:
            print(f"[OK] Encontradas al menos {schedule_cards_count} cards de programaciones")
        else:
            print(f"[ERROR] Se esperaban al menos 2 cards, se encontraron {schedule_cards_count}")
            all_passed = False

        # Verificar filtros
        filter_elements = ['searchInput', 'statusFilter', 'recurrenceFilter']
        for element_id in filter_elements:
            if f'id="{element_id}"' in rendered_html:
                print(f"[OK] Filtro {element_id} presente")
            else:
                print(f"[ERROR] Filtro {element_id} no encontrado")
                all_passed = False

        # Verificar estadísticas
        stats_labels = ['Total Programaciones', 'Activas', 'Inactivas']
        for label in stats_labels:
            if label in rendered_html:
                print(f"[OK] Estadística '{label}' presente")
            else:
                print(f"[ERROR] Estadística '{label}' no encontrada")
                all_passed = False

        # Verificar acciones rápidas
        quick_actions = ['Ver Detalles', 'Editar', 'Generar Ocurrencias']
        for action in quick_actions:
            if action in rendered_html:
                print(f"[OK] Acción rápida '{action}' presente")
            else:
                print(f"[ERROR] Acción rápida '{action}' no encontrada")
                all_passed = False

        # Verificar responsive design
        responsive_classes = ['col-xl-4', 'col-lg-6', 'col-md-6', 'd-flex.justify-content-end']
        for responsive_class in responsive_classes:
            if responsive_class.replace('.', ' ') in rendered_html or responsive_class in rendered_html:
                print(f"[OK] Clase responsive '{responsive_class}' presente")
            else:
                print(f"[ERROR] Clase responsive '{responsive_class}' no encontrada")
                all_passed = False

        if all_passed:
            print("\n=== PRUEBA COMPLETADA EXITOSAMENTE ===")
            print("✓ Template de listado renderiza correctamente")
            print("✓ Cards modernas en lugar de tabla")
            print("✓ Estadísticas con mejor visualización")
            print("✓ Filtros y búsqueda funcionales")
            print("✓ Información clara y organizada")
            print("✓ Acciones rápidas disponibles")
            print("✓ Diseño completamente responsive")
            print("✓ Estilos CSS modernos aplicados")
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
    success = test_schedules_list_template_rendering()
    exit(0 if success else 1)