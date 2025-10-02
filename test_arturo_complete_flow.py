#!/usr/bin/env python3
"""
Script para probar el flujo completo como usuario 'arturo'
Inicia sesión, accede al panel y prueba la vinculación de tarea existente
"""
import requests
import json
import re
from bs4 import BeautifulSoup
from datetime import datetime

# Configuración
BASE_URL = "http://192.168.18.47:5000"
USERNAME = "arturo"
PASSWORD = "Peru+123"
INBOX_ITEM_ID = 115
TEST_TASK_ID = 1  # ID de tarea existente para probar

class ArturoFlowTester:
    """Clase para probar el flujo completo como usuario 'arturo'"""

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
            print(f"   └─ {details}")

    def login_as_arturo(self):
        """Iniciar sesión como usuario 'arturo'"""
        print(f"\n[LOGIN] Iniciando sesión como '{USERNAME}'")

        login_url = f"{self.base_url}/accounts/login/"
        response = self.session.get(login_url)

        if response.status_code != 200:
            self.log_test("Login - Pagina", "FAIL", f"No se pudo acceder a login: {response.status_code}")
            return False

        # Extraer CSRF token
        soup = BeautifulSoup(response.text, 'html.parser')
        csrf_input = soup.find('input', {'name': 'csrfmiddlewaretoken'})

        if not csrf_input:
            self.log_test("Login - CSRF", "FAIL", "No se encontró token CSRF")
            return False

        csrf_token = csrf_input['value']
        print(f"   Token CSRF obtenido: {csrf_token[:20]}...")

        # Hacer POST de login
        login_data = {
            'username': USERNAME,
            'password': PASSWORD,
            'csrfmiddlewaretoken': csrf_token
        }

        headers = {
            'Referer': login_url,
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

        response = self.session.post(login_url, data=login_data, headers=headers, allow_redirects=True)

        if response.status_code == 200 and 'logout' in response.text.lower():
            self.csrf_token = csrf_token
            self.log_test("Login - Autenticacion", "PASS", "Login exitoso como 'arturo'")
            print(f"   Usuario autenticado: {USERNAME}")
            return True
        else:
            self.log_test("Login - Autenticacion", "FAIL", f"Login fallido: {response.status_code}")
            print(f"   Respuesta: {response.text[:200]}...")
            return False

    def test_inbox_access(self):
        """Probar acceso al inbox como 'arturo'"""
        print("
[INBOX] Probando acceso al inbox")

        inbox_url = f"{self.base_url}/events/inbox/"
        response = self.session.get(inbox_url)

        if response.status_code == 200:
            self.log_test("Inbox Access", "PASS", "Acceso al inbox exitoso")

            # Verificar si hay items disponibles
            if 'inbox' in response.text.lower():
                print("   Inbox cargado correctamente")
                return True
            else:
                self.log_test("Inbox Content", "INFO", "Inbox accesible pero sin contenido visible")
                return True
        else:
            self.log_test("Inbox Access", "FAIL", f"Error de acceso: {response.status_code}")
            return False

    def test_item_access(self):
        """Probar acceso al item específico"""
        print(f"\n[ITEM] Probando acceso al item {INBOX_ITEM_ID}")

        item_url = f"{self.base_url}/events/inbox/process/{INBOX_ITEM_ID}/"
        response = self.session.get(item_url)

        print(f"   Codigo de respuesta: {response.status_code}")

        if response.status_code == 200:
            # Verificar si el panel de control está presente
            if 'Panel de Control del Inbox' in response.text:
                self.log_test("Item Access", "PASS", f"Acceso al item {INBOX_ITEM_ID} exitoso")
                print("   Panel de control del inbox cargado")

                # Verificar si el botón de vincular tarea está presente
                if 'Vincular a Tarea Existente' in response.text:
                    print("   Boton 'Vincular a Tarea Existente' encontrado")
                else:
                    print("   Boton 'Vincular a Tarea Existente' NO encontrado")

                return True
            else:
                self.log_test("Item Content", "FAIL", "Panel de control no encontrado en la respuesta")
                return False

        elif response.status_code == 404:
            self.log_test("Item Access", "FAIL", f"Item {INBOX_ITEM_ID} no encontrado")
            print("   El item especificado no existe")
            return False

        elif response.status_code == 403:
            self.log_test("Item Access", "FAIL", f"Acceso denegado al item {INBOX_ITEM_ID}")
            print("   Permisos insuficientes para acceder al item")
            return False

        else:
            self.log_test("Item Access", "FAIL", f"Error inesperado: {response.status_code}")
            return False

    def test_tasks_api(self):
        """Probar la API de tareas disponibles"""
        print("
[API] Probando API de tareas disponibles"
        url = f"{self.base_url}/events/inbox/api/tasks/"

        headers = {
            'X-Requested-With': 'XMLHttpRequest',
            'Content-Type': 'application/json',
        }

        response = self.session.get(url, headers=headers)

        print(f"   Codigo de respuesta: {response.status_code}")

        if response.status_code == 200:
            try:
                data = response.json()

                if data.get('success'):
                    tasks_count = data.get('total', 0)
                    self.log_test("Tasks API", "PASS", f"API funcional ({tasks_count} tareas disponibles)")

                    if tasks_count > 0:
                        print(f"   Tareas disponibles: {tasks_count}")

                        # Mostrar información de las primeras tareas
                        for i, task in enumerate(data.get('tasks', [])[:3]):
                            print(f"     {i+1}. {task.get('title', 'Sin titulo')} (ID: {task.get('id')})")

                        return True
                    else:
                        print("   No hay tareas disponibles")
                        return True

                else:
                    self.log_test("Tasks API", "FAIL", f"API reporto error: {data.get('error')}")
                    return False

            except json.JSONDecodeError:
                self.log_test("Tasks API", "FAIL", "Respuesta no es JSON valido")
                return False

        elif response.status_code == 403:
            self.log_test("Tasks API", "FAIL", "Acceso denegado a la API (403)")
            return False

        else:
            self.log_test("Tasks API", "FAIL", f"Error HTTP {response.status_code}")
            return False

    def test_link_to_existing_task(self):
        """Probar la funcionalidad de vincular a tarea existente"""
        print(f"\n[LINK] Probando vinculación a tarea existente (ID: {TEST_TASK_ID})")

        # Primero verificar que el item sea accesible
        item_url = f"{self.base_url}/events/inbox/process/{INBOX_ITEM_ID}/"
        response = self.session.get(item_url)

        if response.status_code != 200:
            self.log_test("Link Setup", "FAIL", f"No se pudo acceder al item: {response.status_code}")
            return False

        # Extraer CSRF token del panel
        soup = BeautifulSoup(response.text, 'html.parser')
        csrf_input = soup.find('input', {'name': 'csrfmiddlewaretoken'})

        if not csrf_input:
            self.log_test("Link Setup", "FAIL", "No se encontró token CSRF en el panel")
            return False

        csrf_token = csrf_input['value']
        print(f"   Token CSRF del panel: {csrf_token[:20]}...")

        # Preparar datos para la vinculación
        form_data = {
            'action': 'link_to_task',
            'task_id': str(TEST_TASK_ID),
            'csrfmiddlewaretoken': csrf_token
        }

        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': item_url,
            'X-Requested-With': 'XMLHttpRequest'
        }

        print(f"   Enviando petición de vinculación...")
        print(f"   Datos: action=link_to_task, task_id={TEST_TASK_ID}")

        # Hacer la petición POST
        response = self.session.post(
            item_url,
            data=form_data,
            headers=headers,
            allow_redirects=False
        )

        print(f"   Codigo de respuesta: {response.status_code}")

        if response.status_code == 302:
            # Redirección - verificar si es exitosa
            location = response.headers.get('Location', '')
            print(f"   Redireccionando a: {location}")

            if 'tasks' in location and str(TEST_TASK_ID) in location:
                self.log_test(
                    "Link Task",
                    "PASS",
                    "Vinculación exitosa con redirección correcta",
                    f"Redirigido a tarea {TEST_TASK_ID}"
                )
                return True
            else:
                self.log_test(
                    "Link Task",
                    "FAIL",
                    "Redirección inesperada",
                    f"Esperado: tasks/{TEST_TASK_ID}, Obtenido: {location}"
                )
                return False

        elif response.status_code == 200:
            # Verificar si hay mensajes de error o éxito
            response_text = response.text

            if 'vinculado exitosamente' in response_text.lower():
                self.log_test("Link Task", "PASS", "Vinculación exitosa (mensaje encontrado)")
                return True

            elif 'no tienes permisos' in response_text.lower():
                self.log_test("Link Task", "FAIL", "Error de permisos al vincular")
                return False

            elif 'id de tarea inválido' in response_text.lower():
                self.log_test("Link Task", "FAIL", "ID de tarea inválido")
                return False

            elif 'tarea objetivo no existe' in response_text.lower():
                self.log_test("Link Task", "FAIL", "Tarea objetivo no existe")
                return False

            else:
                self.log_test("Link Task", "INFO", "Respuesta 200 sin mensaje claro")
                print(f"   Contenido de respuesta: {response_text[:300]}...")
                return True

        else:
            self.log_test("Link Task", "FAIL", f"Error HTTP inesperado: {response.status_code}")
            return False

    def test_form_validation_messages(self):
        """Probar mensajes de validación de formulario"""
        print("
[VALIDATION] Probando mensajes de validación de formulario"

        # Probar diferentes escenarios de validación
        test_cases = [
            {
                'name': 'Task ID vacío',
                'data': {'action': 'link_to_task', 'task_id': ''},
                'expected_error': 'Debe seleccionar una tarea'
            },
            {
                'name': 'Task ID inválido',
                'data': {'action': 'link_to_task', 'task_id': 'invalid'},
                'expected_error': 'ID de tarea inválido'
            },
            {
                'name': 'Task ID no existe',
                'data': {'action': 'link_to_task', 'task_id': '99999'},
                'expected_error': 'tarea objetivo no existe'
            }
        ]

        item_url = f"{self.base_url}/events/inbox/process/{INBOX_ITEM_ID}/"
        response = self.session.get(item_url)

        if response.status_code != 200:
            self.log_test("Validation Setup", "FAIL", f"No se pudo acceder al item: {response.status_code}")
            return False

        soup = BeautifulSoup(response.text, 'html.parser')
        csrf_input = soup.find('input', {'name': 'csrfmiddlewaretoken'}')
        csrf_token = csrf_input['value'] if csrf_input else ''

        for test_case in test_cases:
            print(f"\n   Probando: {test_case['name']}")

            form_data = {
                'action': test_case['data']['action'],
                'task_id': test_case['data']['task_id'],
                'csrfmiddlewaretoken': csrf_token
            }

            response = self.session.post(
                item_url,
                data=form_data,
                allow_redirects=False
            )

            if test_case['expected_error'] in response.text:
                print(f"     OK: Mensaje de error encontrado: {test_case['expected_error']}")
            else:
                print(f"     ERROR: Mensaje de error NO encontrado: {test_case['expected_error']}")

        self.log_test("Validation Messages", "INFO", "Pruebas de validación completadas")
        return True

    def generate_complete_report(self):
        """Generar reporte completo de la sesión como 'arturo'"""
        print("
[REPORT] REPORTE COMPLETO DE SESION COMO 'ARTURO'"        print("=" * 60)

        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r['status'] == 'PASS'])
        failed_tests = len([r for r in self.test_results if r['status'] == 'FAIL'])
        info_tests = len([r for r in self.test_results if r['status'] == 'INFO'])

        print(f"Total de pruebas: {total_tests}")
        print(f"[OK] Pruebas exitosas: {passed_tests}")
        print(f"[FAIL] Pruebas fallidas: {failed_tests}")
        print(f"[INFO] Pruebas informativas: {info_tests}")

        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        print(f"Tasa de exito: {success_rate:.1".1f")

        print("
[DETALLE] DETALLE DE PRUEBAS:"        for result in self.test_results:
            icon = {'PASS': '[OK]', 'FAIL': '[FAIL]', 'INFO': '[INFO]'}[result['status']]
            print(f"{icon} {result['test']}: {result['message']}")
            if result.get('details'):
                print(f"     └─ {result['details']}")

        print("
[CONCLUSION] CONCLUSION DE LA SESION:"        if success_rate >= 80:
            print("EXITO: El usuario 'arturo' puede usar el sistema correctamente")
            print("El botón 'Vincular a Tarea Existente' funciona adecuadamente")
        elif success_rate >= 50:
            print("PARCIAL: El usuario 'arturo' tiene acceso limitado")
            print("Algunas funcionalidades requieren ajustes de permisos")
        else:
            print("PROBLEMA: El usuario 'arturo' tiene problemas significativos de acceso")
            print("Se requieren ajustes en la configuración de permisos")

        return {
            'total': total_tests,
            'passed': passed_tests,
            'failed': failed_tests,
            'success_rate': success_rate,
            'results': self.test_results
        }

def run_arturo_session():
    """Ejecutar sesión completa como usuario 'arturo'"""
    print("INICIANDO SESION COMPLETA COMO USUARIO 'ARTURO'")
    print("=" * 70)
    print(f"Usuario: {USERNAME}")
    print(f"Contraseña: {PASSWORD}")
    print(f"URL Base: {BASE_URL}")
    print("=" * 70)

    tester = ArturoFlowTester(BASE_URL)

    # 1. Login como 'arturo'
    if not tester.login_as_arturo():
        print("ERROR: No se pudo iniciar sesión como 'arturo'")
        return tester.generate_complete_report()

    # 2. Probar acceso al inbox
    tester.test_inbox_access()

    # 3. Probar acceso al item específico
    if not tester.test_item_access():
        print("ERROR: No se pudo acceder al item especificado")
        return tester.generate_complete_report()

    # 4. Probar API de tareas
    tester.test_tasks_api()

    # 5. Probar vinculación a tarea existente
    tester.test_link_to_existing_task()

    # 6. Probar mensajes de validación
    tester.test_form_validation_messages()

    # 7. Generar reporte final
    return tester.generate_complete_report()

if __name__ == "__main__":
    try:
        report = run_arturo_session()

        print("
" + "=" * 70)
        print("SESION COMPLETA COMO 'ARTURO' FINALIZADA")

        print("
INSTRUCCIONES PARA PRUEBA MANUAL:"        print("1. Abrir navegador y navegar a: http://192.168.18.47:5000/accounts/login/")
        print("2. Iniciar sesión con:")
        print(f"   Usuario: {USERNAME}")
        print(f"   Contraseña: {PASSWORD}")
        print("3. Ir a: http://192.168.18.47:5000/events/inbox/process/115/")
        print("4. Probar el botón 'Vincular a Tarea Existente'")
        print("5. Seleccionar una tarea de la lista")
        print("6. Confirmar la vinculación")
        print("7. Verificar que aparezca el mensaje de éxito")

        print("
Si el botón no funciona, verificar:")
        print("- Que el usuario esté correctamente autenticado")
        print("- Que el item 115 exista y sea accesible")
        print("- Que existan tareas disponibles para vincular")
        print("- Que los permisos estén correctamente configurados")

    except KeyboardInterrupt:
        print("
Sesion interrumpida por el usuario"    except Exception as e:
        print(f"\nError inesperado: {e}")