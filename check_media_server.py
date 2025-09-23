#!/usr/bin/env python
"""
Script para verificar el estado del servidor de media y proporcionar instrucciones
para solucionarlo si hay problemas.
"""
import requests
import time
import subprocess
import sys
import os

def check_media_server(host='192.168.18.46', port=8000):
    """Verifica si el servidor de media está corriendo"""
    url = f"http://{host}:{port}/"
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            print(f"SUCCESS: Servidor de media esta corriendo en {host}:{port}")
            return True
        else:
            print(f"WARNING: Servidor responde pero con codigo {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"ERROR: No se puede conectar al servidor de media en {host}:{port}")
        print(f"   Error: {e}")
        return False

def start_media_server():
    """Intenta iniciar el servidor de media"""
    print("\nIniciando servidor de media...")

    # Verificar que existe el directorio media
    if not os.path.exists('media'):
        print("ERROR: El directorio 'media' no existe")
        return False

    try:
        # Iniciar el servidor en background
        cmd = [sys.executable, 'media_server.py', '--host', '192.168.18.46', '--port', '8000']
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        # Esperar un poco para que inicie
        time.sleep(3)

        # Verificar si está corriendo
        if check_media_server():
            print("SUCCESS: Servidor de media iniciado exitosamente")
            return True
        else:
            print("ERROR: El servidor no pudo iniciarse correctamente")
            # Terminar el proceso si falló
            process.terminate()
            return False

    except Exception as e:
        print(f"ERROR: Error al iniciar el servidor: {e}")
        return False

def provide_instructions():
    """Proporciona instrucciones para solucionar problemas"""
    print("\nInstrucciones para solucionar problemas con el servidor de media:")
    print()
    print("1. Verificar que el directorio 'media' existe:")
    print("   ls -la media/")
    print()
    print("2. Iniciar el servidor de media manualmente:")
    print("   python media_server.py --host 192.168.18.46 --port 8000")
    print()
    print("3. Si hay problemas con la IP, usar localhost:")
    print("   python media_server.py --host 127.0.0.1 --port 8000")
    print()
    print("4. O usar 0.0.0.0 para todas las interfaces:")
    print("   python media_server.py --host 0.0.0.0 --port 8000")
    print()
    print("5. Verificar que el puerto 8000 no esté ocupado:")
    print("   netstat -tulpn | grep :8000")
    print()
    print("6. Si usas un puerto diferente, actualizar settings.py:")
    print("   MEDIA_URL = 'http://TU_IP:TU_PUERTO/'")
    print()

def main():
    print("Verificando estado del servidor de media...")
    print("=" * 50)

    if check_media_server():
        print("\nTodo esta funcionando correctamente!")
        return

    print("\nEl servidor de media no esta disponible.")

    # Proporcionar instrucciones manuales
    provide_instructions()

if __name__ == '__main__':
    main()