#!/bin/bash
# Script para corregir TODAS las importaciones relativas en events/views/
# Versión con patrones más flexibles

echo "=== CORRIGIENDO IMPORTACIONES RELATIVAS EN events/views/ ==="
echo ""

# Directorio de las vistas
VIEWS_DIR="events/views"

# Función para corregir importaciones con patrón más flexible
fix_imports() {
    local file=$1
    local pattern=$2
    local replacement=$3
    
    # Buscar líneas que coincidan con el patrón y reemplazar
    sed -i "s/^\(from \)\.\(${pattern}\)/\1..\2/g" "$file"
    sed -i "s/^\(import \)\.\(${pattern}\)/\1..\2/g" "$file"
}

# Procesar cada archivo .py en views/
for file in "$VIEWS_DIR"/*.py; do
    if [ -f "$file" ] && [ "$(basename "$file")" != "__init__.py" ]; then
        echo "Procesando: $(basename "$file")"
        
        # Crear backup si no existe
        if [ ! -f "$file.bak3" ]; then
            cp "$file" "$file.bak3"
            echo "✅ Backup creado: $(basename "$file").bak3"
        fi
        
        # Corregir importaciones de modelos y formularios
        fix_imports "$file" "models\..*"
        fix_imports "$file" "forms\..*"
        
        # Corregir importaciones de utilidades
        fix_imports "$file" "my_utils\..*"
        fix_imports "$file" "utils\..*"
        
        # Corregir importaciones de gestión
        fix_imports "$file" "management\..*"
        
        # Corregir importaciones de servicios
        fix_imports "$file" "services\..*"
        
        # Corregir importaciones de GTD utils
        fix_imports "$file" "gtd_utils\..*"
        
        echo "   Importaciones corregidas"
        echo ""
    fi
done

echo "=== VERIFICANDO CORRECCIONES ==="
echo "Buscando importaciones problemáticas restantes..."
echo ""

echo "=== IMPORTACIONES CON UN SOLO PUNTO (DEBEN SER CORREGIDAS) ==="
grep -r "from \.\w" --include="*.py" "$VIEWS_DIR/" | grep -v "__init__" || echo "✅ No se encontraron importaciones con un solo punto"

echo ""
echo "=== IMPORTACIONES CON DOS PUNTOS (CORRECTAS) ==="
grep -r "from \.\.\w" --include="*.py" "$VIEWS_DIR/" | head -10
echo "..."

echo ""
echo "=== PROCESO COMPLETADO ==="
echo ""
echo "📋 PRÓXIMOS PASOS:"
echo "1. Verifica que no queden errores: python manage.py check"
echo "2. Si todo funciona, elimina los backups:"
echo "   rm events/views/*.bak*"
echo ""