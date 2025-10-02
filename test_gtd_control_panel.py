#!/usr/bin/env python3
"""
Script de prueba específico para el Panel de Control de Acciones GTD
Prueba todas las funcionalidades del panel mejorado
"""
import requests
import json
import re
from bs4 import BeautifulSoup
from datetime import datetime

# Configuración de la prueba
BASE_URL = "http://192.168.18.47:5000"
INBOX_ITEM_ID = 115

class GTDControlPanelTester:
    """Clase para probar el Panel de Control de Acciones GTD"""

    def __init__(self, base_url):
        self.base_url = base_url
        self.session = requests.Session()
        self.csrf_token = None
        self.test_results = []

    def log_test(self, test_name, status, message, details=None):
        """Registrar resultado de prueba"""
        result = {
            'test': test_name,
            'status': status,
            'message': message,
            'details': details,
            'timestamp': datetime.now().isoformat()
        }
        self.test_results.append(result)
        icon = {'PASS': '[OK]', 'FAIL': '[FAIL]', 'INFO': '[INFO]'}[status]
        print(f"{icon} {test_name}: {message}")
        if details:
            print(f"   Detalles: {details}")

    def test_panel_access(self):
        """Probar acceso al panel de control GTD"""
        print(f"\n[TEST] Probando acceso al Panel de Control GTD")
        print(f"URL: {self.base_url}/events/inbox/process/{INBOX_ITEM_ID}/")

        try:
            response = self.session.get(f"{self.base_url}/events/inbox/process/{INBOX_ITEM_ID}/")

            if response.status_code == 200:
                # Verificar elementos clave del panel
                panel_elements = [
                    'Panel de Control del Inbox',
                    'Panel de Control de Acciones',
                    'Vincular a Tarea Existente',
                    'Crear Nueva Tarea',
                    'Crear Nuevo Proyecto',
                    'taskSelectorModal',
                    'Elegir Tarea'
                ]

                found_elements = []
                missing_elements = []

                for element in panel_elements:
                    if element in response.text:
                        found_elements.append(element)
                    else:
                        missing_elements.append(element)

                if len(found_elements) >= 5:  # Al menos 5 elementos encontrados
                    self.log_test(
                        "Panel Access - Elementos UI",
                        "PASS",
                        f"Panel cargado correctamente ({len(found_elements)}/{len(panel_elements)} elementos)",
                        f"Encontrados: {found_elements[:3]}... Faltantes: {missing_elements}"
                    )
                    return True
                else:
                    self.log_test(
                        "Panel Access - Elementos UI",
                        "FAIL",
                        f"Panel incompleto ({len(found_elements)}/{len(panel_elements)} elementos)",
                        f"Encontrados: {found_elements} Faltantes: {missing_elements}"
                    )
                    return False

            elif response.status_code == 404:
                self.log_test("Panel Access - HTTP", "FAIL", "Panel no encontrado (404)")
                return False
            elif response.status_code == 403:
                self.log_test("Panel Access - HTTP", "FAIL", "Acceso denegado (403)")
                return False
            else:
                self.log_test("Panel Access - HTTP", "FAIL", f"Error HTTP {response.status_code}")
                return False

        except Exception as e:
            self.log_test("Panel Access - Exception", "FAIL", f"Error de conexión: {str(e)}")
            return False

    def test_gtd_actions_structure(self):
        """Probar que todas las acciones GTD están presentes en el panel"""
        print(f"\n[TEST] Probando estructura de acciones GTD")

        response = self.session.get(f"{self.base_url}/events/inbox/process/{INBOX_ITEM_ID}/")

        if response.status_code != 200:
            self.log_test("GTD Structure - Access", "FAIL", f"No se pudo acceder al panel: {response.status_code}")
            return False

        # Verificar acciones GTD disponibles
        gtd_actions = {
            'Crear Nueva Tarea': ['convert_to_task', 'Nueva Tarea'],
            'Vincular a Tarea Existente': ['link_to_task', 'Elegir Tarea'],
            'Crear Nuevo Proyecto': ['convert_to_project', 'Nuevo Proyecto'],
            'Vincular a Proyecto Existente': ['link_to_project', 'Elegir Proyecto'],
            'Guardar como Referencia': ['reference', 'Referencia'],
            'Algún día / Quizás': ['someday', 'Algún día'],
            'Eliminar': ['delete', 'Eliminar'],
            'Posponer': ['postpone', 'Posponer']
        }

        found_actions = 0
        total_actions = len(gtd_actions)

        for action_name, identifiers in gtd_actions.items():
            action_found = False
            for identifier in identifiers:
                if identifier in response.text:
                    action_found = True
                    break

            if action_found:
                found_actions += 1
                print(f"   [OK] {action_name}")
            else:
                print(f"   [FALTANTE] {action_name}")

        if found_actions == total_actions:
            self.log_test(
                "GTD Structure - Acciones",
                "PASS",
                f"Todas las acciones GTD presentes ({found_actions}/{total_actions})"
            )
            return True
        else:
            self.log_test(
                "GTD Structure - Acciones",
                "FAIL",
                f"Acciones GTD faltantes ({found_actions}/{total_actions})"
            )
            return False

    def test_javascript_functionality(self):
        """Probar elementos de JavaScript en el panel"""
        print(f"\n[TEST] Probando elementos de JavaScript")

        response = self.session.get(f"{self.base_url}/events/inbox/process/{INBOX_ITEM_ID}/")

        if response.status_code != 200:
            self.log_test("JS Test - Access", "FAIL", f"No se pudo acceder al panel: {response.status_code}")
            return False

        # Verificar funciones JavaScript críticas
        js_functions = [
            'showTaskSelector',
            'loadAvailableTasks',
            'selectTask',
            'confirmTaskLink',
            'linkToExistingTask',
            'showProjectSelector',
            'displayTasks',
            'displayProjects'
        ]

        found_functions = 0
        for func in js_functions:
            if func in response.text:
                found_functions += 1

        if found_functions >= 6:  # Al menos 6 funciones encontradas
            self.log_test(
                "JS Test - Funciones",
                "PASS",
                f"Funciones JavaScript presentes ({found_functions}/{len(js_functions)})"
            )
            return True
        else:
            self.log_test(
                "JS Test - Funciones",
                "FAIL",
                f"Funciones JavaScript faltantes ({found_functions}/{len(js_functions)})"
            )
            return False

    def test_modal_structure(self):
        """Probar estructura de modales del panel"""
        print(f"\n[TEST] Probando estructura de modales")

        response = self.session.get(f"{self.base_url}/events/inbox/process/{INBOX_ITEM_ID}/")

        if response.status_code != 200:
            self.log_test("Modal Test - Access", "FAIL", f"No se pudo acceder al panel: {response.status_code}")
            return False

        # Verificar modales importantes
        modals = [
            'taskSelectorModal',
            'projectSelectorModal',
            'classificationModal'
        ]

        found_modals = 0
        for modal in modals:
            if modal in response.text:
                found_modals += 1

        if found_modals >= 2:  # Al menos 2 modales encontrados
            self.log_test(
                "Modal Test - Estructura",
                "PASS",
                f"Modales presentes ({found_modals}/{len(modals)})"
            )
            return True
        else:
            self.log_test(
                "Modal Test - Estructura",
                "FAIL",
                f"Modales faltantes ({found_modals}/{len(modals)})"
            )
            return False

    def test_tasks_api_basic(self):
        """Probar la API de tareas disponibles (sin autenticación)"""
        print(f"\n[TEST] Probando API de tareas disponibles")
        url = f"{self.base_url}/events/inbox/api/tasks/"

        try:
            response = self.session.get(url, headers={
                'X-Requested-With': 'XMLHttpRequest',
                'Content-Type': 'application/json',
            })

            if response.status_code == 403:
                self.log_test("Tasks API - Autenticacion", "INFO", "API requiere autenticacion (esperado)")
                return True  # Es esperado sin autenticacion
            elif response.status_code == 200:
                try:
                    data = response.json()

                    if data.get('success'):
                        tasks_count = data.get('total', 0)
                        self.log_test(
                            "Tasks API - Respuesta",
                            "PASS",
                            f"API funcional ({tasks_count} tareas disponibles)",
                            f"Tareas encontradas: {tasks_count}"
                        )
                        return True
                    else:
                        self.log_test("Tasks API - Estado", "FAIL", f"API reportó error: {data.get('error', 'Desconocido')}")
                        return False

                except json.JSONDecodeError:
                    self.log_test("Tasks API - JSON", "FAIL", "Respuesta no es JSON válido")
                    return False
            else:
                self.log_test("Tasks API - HTTP", "FAIL", f"Error HTTP {response.status_code}")
                return False

        except Exception as e:
            self.log_test("Tasks API - Exception", "FAIL", f"Error de conexión: {str(e)}")
            return False

    def generate_report(self):
        """Generar reporte completo de pruebas"""
        print(f"\n[REPORTE] GENERANDO REPORTE DE PRUEBAS")
        print("=" * 60)

        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r['status'] == 'PASS'])
        failed_tests = len([r for r in self.test_results if r['status'] == 'FAIL'])
        info_tests = len([r for r in self.test_results if r['status'] == 'INFO'])

        print(f"Total de pruebas: {total_tests}")
        print(f"[OK] Pruebas exitosas: {passed_tests}")
        print(f"[FAIL] Pruebas fallidas: {failed_tests}")
        print(f"[INFO] Pruebas informativas: {info_tests}")

        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        print(f"Tasa de éxito: {success_rate:.1f}%")

        print(f"\n[DETALLE] DETALLE DE PRUEBAS:")
        for result in self.test_results:
            icon = {'PASS': '[OK]', 'FAIL': '[FAIL]', 'INFO': '[INFO]'}[result['status']]
            print(f"{icon} {result['test']}: {result['message']}")
            if result.get('details'):
                print(f"     └─ {result['details']}")

        print(f"\n[FINAL] PRUEBAS DEL PANEL GTD COMPLETADAS")
        return {
            'total': total_tests,
            'passed': passed_tests,
            'failed': failed_tests,
            'success_rate': success_rate,
            'results': self.test_results
        }

def run_gtd_panel_tests():
    """Ejecutar todas las pruebas del panel GTD"""
    print("INICIANDO PRUEBAS DEL PANEL DE CONTROL DE ACCIONES GTD")
    print("=" * 70)

    tester = GTDControlPanelTester(BASE_URL)

    print("NOTA: Estas pruebas verifican la estructura del panel.")
    print("Para pruebas funcionales completas, se necesita autenticación válida.")
    print()

    # Ejecutar pruebas básicas (sin autenticación)
    print("EJECUTANDO PRUEBAS BÁSICAS (SIN AUTENTICACIÓN)")
    print("-" * 50)

    # Probar acceso básico al panel
    tester.test_panel_access()

    # Probar estructura de acciones GTD
    tester.test_gtd_actions_structure()

    # Probar elementos de JavaScript
    tester.test_javascript_functionality()

    # Probar estructura de modales
    tester.test_modal_structure()

    # Probar API de tareas (sin autenticación - debería requerir auth)
    tester.test_tasks_api_basic()

    # Generar reporte final
    return tester.generate_report()

if __name__ == "__main__":
    try:
        report = run_gtd_panel_tests()

        print("\nRECOMENDACIONES:")
        print("   1. Para pruebas completas, configura credenciales válidas")
        print("   2. Verifica que el servidor Django esté corriendo")
        print("   3. Asegúrate de que el inbox item 115 existe")
        print("   4. Revisa los permisos de usuario para tareas/proyectos")

        if report['success_rate'] >= 80:
            print("\nCONCLUSION: El Panel de Control GTD parece estar funcionando correctamente!")
        elif report['success_rate'] >= 50:
            print("\nCONCLUSION: El Panel de Control GTD tiene algunos problemas que requieren atención")
        else:
            print("\nCONCLUSION: El Panel de Control GTD tiene problemas significativos que necesitan ser resueltos")
    except KeyboardInterrupt:
        print("\nPruebas interrumpidas por el usuario")
    except Exception as e:
        print(f"\nError inesperado durante las pruebas: {e}")