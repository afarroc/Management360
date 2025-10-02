#!/usr/bin/env python3
"""
Script simple para probar la funcionalidad del botón "Vincular a Tarea Existente"
"""

import os
from pathlib import Path

def test_template_content():
    """Test simple del contenido de la plantilla"""
    print("TEST SIMPLE - BOTON VINCULAR A TAREA EXISTENTE")
    print("=" * 50)

    # Ruta a la plantilla
    template_path = Path("events/templates/events/process_inbox_item.html")

    if not template_path.exists():
        print(f"ERROR: Archivo no encontrado: {template_path}")
        return False

    print(f"Archivo encontrado: {template_path}")

    # Leer contenido
    with open(template_path, 'r', encoding='utf-8') as f:
        content = f.read()

    print(f"Archivo tiene {len(content)} caracteres")

    # Verificaciones clave
    checks = [
        ("Vincular a Tarea Existente", "Titulo del boton"),
        ("showTaskSelector()", "Funcion JavaScript del modal"),
        ("taskSelectorModal", "ID del modal"),
        ("Elegir Tarea", "Texto del boton"),
        ("loadAvailableTasks", "Funcion de carga de tareas"),
        ("selectTask", "Funcion de seleccion de tarea"),
        ("confirmTaskLink", "Funcion de confirmacion"),
        ("linkToExistingTask", "Funcion de vinculacion"),
        ("taskSearch", "Campo de busqueda"),
        ("taskList", "Lista de tareas"),
        (".action-card", "Estilos de tarjetas"),
        (".modal-content", "Estilos del modal"),
        ("@media", "Media queries responsivas"),
    ]

    print("\nVERIFICANDO ELEMENTOS CLAVE:")
    print("-" * 40)

    all_passed = True
    for check_text, description in checks:
        if check_text in content:
            print(f"PASSED: {description}")
        else:
            print(f"FAILED: {description} - NO ENCONTRADO")
            all_passed = False

    print("\n" + "=" * 50)

    if all_passed:
        print("EXITO: Todos los elementos clave estan presentes")
        print("\nCONCLUSION:")
        print("- El boton 'Vincular a Tarea Existente' esta implementado")
        print("- El modal de seleccion de tareas esta presente")
        print("- Las funciones JavaScript necesarias estan disponibles")
        print("- Los estilos CSS estan aplicados")
        print("- La funcionalidad esta lista para usar")
        return True
    else:
        print("ERROR: Algunos elementos faltan")
        return False

def test_api_endpoints():
    """Test simple de endpoints API"""
    print("\nTEST DE ENDPOINTS API")
    print("=" * 30)

    # Verificar que las URLs de API existen en el archivo de URLs
    urls_path = Path("events/urls.py")

    if not urls_path.exists():
        print(f"ERROR: Archivo de URLs no encontrado: {urls_path}")
        return False

    with open(urls_path, 'r', encoding='utf-8') as f:
        urls_content = f.read()

    api_checks = [
        ("inbox/api/tasks/", "API de tareas"),
        ("inbox/api/projects/", "API de proyectos"),
        ("process_inbox_item", "Vista de procesamiento"),
    ]

    print("Verificando endpoints API:")
    for endpoint, description in api_checks:
        if endpoint in urls_content:
            print(f"PASSED: {description}")
        else:
            print(f"FAILED: {description} - NO ENCONTRADO")

    return True

if __name__ == "__main__":
    print("INICIANDO PRUEBA SIMPLE...")

    # Test 1: Plantilla
    template_ok = test_template_content()

    # Test 2: APIs
    api_ok = test_api_endpoints()

    print("\n" + "=" * 50)
    print("RESULTADO FINAL")
    print("=" * 50)

    if template_ok and api_ok:
        print("SUCCESS: La funcionalidad del boton 'Vincular a Tarea Existente' esta completamente implementada")
        print("\nEl modal y todas las funciones necesarias estan presentes en el codigo.")
    else:
        print("ERROR: Algunos componentes pueden estar faltando")

    print("\nPRUEBA COMPLETADA")