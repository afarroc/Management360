#!/usr/bin/env python
"""
Script de prueba para el asistente de chat
"""
import requests
import json
import time

def test_ollama_connection():
    """Prueba la conexión con Ollama"""
    print("[INFO] Probando conexión con Ollama...")
    try:
        response = requests.get('http://localhost:11434/api/tags', timeout=5)
        if response.status_code == 200:
            models = response.json()
            print(f"[OK] Ollama funcionando. Modelos disponibles: {len(models.get('models', []))}")
            for model in models.get('models', []):
                print(f"   - {model['name']}")
            return True
        else:
            print(f"[ERROR] Error en Ollama: {response.status_code}")
            return False
    except Exception as e:
        print(f"[ERROR] Error conectando a Ollama: {str(e)}")
        return False

def test_django_connection():
    """Prueba la conexión con Django"""
    print("\n[INFO] Probando conexión con Django...")
    try:
        response = requests.get('http://127.0.0.1:8000/', timeout=5)
        print(f"[OK] Django funcionando: {response.status_code}")
        return True
    except Exception as e:
        print(f"[ERROR] Error conectando a Django: {str(e)}")
        return False

def test_assistant_endpoint():
    """Prueba el endpoint del asistente"""
    print("\n[INFO] Probando endpoint del asistente...")

    # Crear sesión para mantener cookies
    session = requests.Session()

    # Intentar login
    login_url = 'http://127.0.0.1:8000/accounts/login/'
    login_data = {
        'username': 'testuser',
        'password': 'testpass123'
    }

    try:
        # Hacer login
        response = session.post(login_url, data=login_data, allow_redirects=True)
        print(f"[LOGIN] Login status: {response.status_code}")

        if response.status_code == 200 and 'chat/ui' in response.url:
            print("[OK] Login exitoso")

            # Probar el endpoint del asistente
            assistant_url = 'http://127.0.0.1:8000/chat/assistant/'
            test_data = {
                'user_input': 'Hola, ¿cómo estás?',
                'chat_history': '[]'
            }

            response = session.post(assistant_url, data=test_data, timeout=30)
            print(f"[ASSISTANT] Asistente status: {response.status_code}")

            if response.status_code == 200:
                print("[OK] Endpoint del asistente funcionando")
                print(f"[RESPONSE] Respuesta preview: {response.text[:200]}...")
                return True
            else:
                print(f"[ERROR] Error en endpoint: {response.text[:200]}")
                return False
        else:
            print("[ERROR] Login fallido")
            return False

    except Exception as e:
        print(f"[ERROR] Error en prueba del asistente: {str(e)}")
        return False

def main():
    """Función principal de pruebas"""
    print("[START] Iniciando pruebas del asistente de chat\n")

    results = []

    # Probar conexiones básicas
    results.append(("Ollama", test_ollama_connection()))
    results.append(("Django", test_django_connection()))
    results.append(("Asistente", test_assistant_endpoint()))

    # Resumen
    print("\n[SUMMARY] RESUMEN DE PRUEBAS:")
    print("-" * 30)
    for name, result in results:
        status = "[PASSED]" if result else "[FAILED]"
        print(f"{name:<12} | {status}")

    passed = sum(1 for _, result in results if result)
    total = len(results)

    print(f"\n[RESULT] Resultado general: {passed}/{total} pruebas pasaron")

    if passed == total:
        print("[SUCCESS] ¡Todas las pruebas pasaron exitosamente!")
        return True
    else:
        print("[WARNING] Algunas pruebas fallaron. Revisa la configuración.")
        return False

if __name__ == "__main__":
    main()