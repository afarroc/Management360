#!/usr/bin/env python3
"""
Script simplificado para verificar permisos del usuario "arturo"
"""
import requests
import json
from bs4 import BeautifulSoup

BASE_URL = "http://192.168.18.47:5000"

def test_basic_access():
    """Probar acceso basico al panel"""
    print("Probando acceso basico al panel GTD...")

    try:
        response = requests.get(f"{BASE_URL}/events/inbox/process/115/")
        print(f"Codigo de respuesta: {response.status_code}")

        if response.status_code == 200:
            print("Panel accesible")

            # Verificar si contiene elementos clave
            if 'Panel de Control del Inbox' in response.text:
                print("Panel de control encontrado")
            else:
                print("Panel de control NO encontrado")

            if 'Vincular a Tarea Existente' in response.text:
                print("Boton de vincular tarea encontrado")
            else:
                print("Boton de vincular tarea NO encontrado")

        elif response.status_code == 403:
            print("ERROR: Acceso denegado (403)")
        elif response.status_code == 404:
            print("ERROR: Panel no encontrado (404)")
        else:
            print(f"ERROR: Codigo inesperado {response.status_code}")

    except Exception as e:
        print(f"Error de conexion: {e}")

def test_api_access():
    """Probar acceso a la API de tareas"""
    print("\nProbando API de tareas...")

    try:
        response = requests.get(f"{BASE_URL}/events/inbox/api/tasks/")
        print(f"Codigo de respuesta API: {response.status_code}")

        if response.status_code == 200:
            try:
                data = response.json()
                print(f"API funcional: {data.get('success', False)}")
                print(f"Tareas disponibles: {data.get('total', 0)}")
            except:
                print("Respuesta no es JSON")
        elif response.status_code == 403:
            print("API requiere autenticacion")
        else:
            print(f"Error en API: {response.status_code}")

    except Exception as e:
        print(f"Error en API: {e}")

def analyze_code_structure():
    """Analizar estructura del codigo"""
    print("\nAnalizando estructura del codigo...")

    print("PROBLEMA IDENTIFICADO:")
    print("La vista process_inbox_item (linea 1964-1966) tiene restriccion:")
    print("  user_inbox_items = InboxItem.objects.filter(")
    print("      Q(created_by=request.user) | Q(assigned_to=request.user)")
    print("  )")

    print("\nEsto significa que un usuario SOLO puede ver:")
    print("1. Items que el mismo creo")
    print("2. Items que le fueron asignados")

    print("\nSOLUCION PROPUESTA:")
    print("Modificar la consulta para incluir authorized_users:")
    print("  user_inbox_items = InboxItem.objects.filter(")
    print("      Q(created_by=request.user) |")
    print("      Q(assigned_to=request.user) |")
    print("      Q(authorized_users=request.user) |  # AGREGAR ESTA LINEA")
    print("      Q(is_public=True)  # Opcional")
    print("  ).distinct()")

def main():
    print("DIAGNOSTICO DEL PROBLEMA: Boton 'Vincular a Tarea Existente'")
    print("=" * 60)

    test_basic_access()
    test_api_access()
    analyze_code_structure()

    print("\n" + "=" * 60)
    print("CONCLUSION:")
    print("El problema es que el usuario 'arturo' no puede acceder")
    print("al item 115 porque no lo creo ni se lo asignaron.")
    print("La solucion es modificar la logica de permisos.")

if __name__ == "__main__":
    main()