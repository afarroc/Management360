# Script de carga automática para GTD
# Ejecutar: python load_gtd.py [opciones]

import subprocess
import sys
import os

def run_command(cmd):
    """Ejecutar comando y mostrar output"""
    print(f"\n▶️  Ejecutando: {cmd}")
    print("-" * 50)
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    
    if result.stdout:
        print(result.stdout)
    
    if result.stderr:
        print(f"STDERR: {result.stderr}")
    
    return result.returncode == 0

def main():
    """Función principal"""
    print("🚀 SCRIPT DE CARGA AUTOMÁTICA GTD")
    print("=" * 60)
    
    # Verificar que el script setup_gtd.py existe
    if not os.path.exists("setup_gtd.py"):
        print("❌ Error: setup_gtd.py no encontrado")
        print("   Copia setup_gtd.py a esta carpeta o ajusta la ruta")
        return False
    
    # Opciones por defecto
    user_id = 1
    verbose = "--verbose"
    
    # Verificar argumentos
    if len(sys.argv) > 1:
        user_id = sys.argv[1]
    
    print(f"👤 Usuario ID: {user_id}")
    print(f"📁 Carpeta base: gtd_setup")
    
    # Ejecutar pasos en orden
    steps = [
        f"python setup_gtd.py --step categories --user-id {user_id} {verbose}",
        f"python setup_gtd.py --step classifications --user-id {user_id} {verbose}",
        f"python setup_gtd.py --step status --user-id {user_id} {verbose}",
        f"python setup_gtd.py --step inbox --user-id {user_id} {verbose}",
        f"python setup_gtd.py --step templates --user-id {user_id} {verbose}",
        f"python setup_gtd.py --step settings --user-id {user_id} {verbose}",
    ]
    
    results = []
    for step in steps:
        success = run_command(step)
        results.append(success)
    
    # Resumen
    print("\n" + "=" * 60)
    print("📊 RESUMEN DE EJECUCIÓN")
    print("=" * 60)
    
    success_count = sum(1 for r in results if r)
    total_steps = len(results)
    
    if success_count == total_steps:
        print("🎉 ¡TODOS LOS PASOS COMPLETADOS CON ÉXITO!")
    else:
        print(f"⚠️  Completados: {success_count}/{total_steps} pasos")
    
    # Mostrar estadísticas finales
    print("\n📈 ESTADÍSTICAS FINALES:")
    run_command(f"python setup_gtd.py --stats --user-id {user_id}")
    
    return success_count == total_steps

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
