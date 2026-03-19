#!/usr/bin/env python
"""
Script para actualizar todas las referencias de User en el proyecto
para usar get_user_model() o settings.AUTH_USER_MODEL
"""

import os
import re
import sys
from pathlib import Path

# Configuración
PROJECT_ROOT = Path(__file__).parent.parent
EXCLUDE_DIRS = ['venv', '.git', '__pycache__', 'migrations']
EXCLUDE_FILES = ['update_user_imports.py']

def should_process_file(filepath):
    """Determinar si un archivo debe ser procesado"""
    # Solo archivos .py
    if not filepath.suffix == '.py':
        return False
    
    # Excluir directorios específicos
    for exclude in EXCLUDE_DIRS:
        if exclude in str(filepath):
            return False
    
    # Excluir archivos específicos
    if filepath.name in EXCLUDE_FILES:
        return False
    
    return True

def update_imports(content):
    """Actualizar imports de User"""
    
    # Patrón para encontrar 'from django.contrib.auth.models import User'
    pattern1 = r'from django\.contrib\.auth\.models import User'
    
    # Patrón para encontrar 'from django.contrib.auth.models import User, ...'
    pattern2 = r'from django\.contrib\.auth\.models import (.*)'
    
    # Reemplazar con import de get_user_model
    if re.search(pattern1, content):
        content = re.sub(
            pattern1,
            'from django.contrib.auth import get_user_model',
            content
        )
        # Añadir User = get_user_model() después del import si no existe
        if 'User = get_user_model()' not in content:
            content = content.replace(
                'from django.contrib.auth import get_user_model',
                'from django.contrib.auth import get_user_model\n\nUser = get_user_model()'
            )
    
    return content

def update_user_objects(content):
    """Actualizar referencias a User.objects"""
    
    # Reemplazar User.objects por User._default_manager (pero mejor mantener User.objects)
    # El problema no es User.objects, es el import
    return content

def process_file(filepath):
    """Procesar un archivo individual"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original = content
        
        # Actualizar imports
        content = update_imports(content)
        
        # Si hubo cambios, guardar
        if content != original:
            # Crear backup
            backup = filepath.with_suffix('.py.backup')
            if not backup.exists():
                with open(backup, 'w', encoding='utf-8') as f:
                    f.write(original)
                print(f"✅ Backup creado: {backup.name}")
            
            # Guardar cambios
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ Actualizado: {filepath.relative_to(PROJECT_ROOT)}")
            return True
        else:
            print(f"⏩ Sin cambios: {filepath.relative_to(PROJECT_ROOT)}")
            return False
            
    except Exception as e:
        print(f"❌ Error en {filepath}: {e}")
        return False

def main():
    """Función principal"""
    print("🔄 Actualizando referencias de User en el proyecto...")
    print("=" * 60)
    
    updated = 0
    total = 0
    
    for root, dirs, files in os.walk(PROJECT_ROOT):
        # Modificar dirs in-place para excluir directorios
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        
        for file in files:
            filepath = Path(root) / file
            if should_process_file(filepath):
                total += 1
                if process_file(filepath):
                    updated += 1
    
    print("=" * 60)
    print(f"📊 Resumen: {updated} de {total} archivos actualizados")
    print("✅ Proceso completado")

if __name__ == '__main__':
    main()
