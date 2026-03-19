#!/bin/bash
# Script para mover los archivos de vistas a un subdirectorio 'views'
# Ejecutar desde la raíz del proyecto: ./events/move_views_to_package.sh

echo "=== MOVIENDO ARCHIVOS DE VISTAS A events/views/ ==="
echo ""

# Crear directorio de destino si no existe
mkdir -p events/views

# Lista de archivos a mover
ARCHIVOS=(
    "events_views.py"
    "projects_views.py"
    "tasks_views.py"
    "gtd_views.py"
    "status_views.py"
    "classification_views.py"
    "kanban_views.py"
    "eisenhower_views.py"
    "templates_views.py"
    "dependencies_views.py"
    "schedules_views.py"
    "reminders_views.py"
    "credits_views.py"
    "dashboard_views.py"
    "bot_views.py"
    "test_views.py"
)

# Mover cada archivo
for archivo in "${ARCHIVOS[@]}"; do
    if [ -f "events/$archivo" ]; then
        echo "Moviendo $archivo..."
        mv "events/$archivo" "events/views/"
        echo "✅ Movido: $archivo"
    else
        echo "⚠️  events/$archivo no encontrado, omitiendo..."
    fi
done

echo ""
echo "=== CREANDO __init__.py ==="

# Crear __init__.py en el directorio views
cat > events/views/__init__.py << 'EOF'
# events/views/__init__.py
# Este archivo expone todas las vistas desde el paquete

from .events_views import *
from .projects_views import *
from .tasks_views import *
from .gtd_views import *
from .status_views import *
from .classification_views import *
from .kanban_views import *
from .eisenhower_views import *
from .templates_views import *
from .dependencies_views import *
from .schedules_views import *
from .reminders_views import *
from .credits_views import *
from .dashboard_views import *
from .bot_views import *
from .test_views import *
EOF

echo "✅ __init__.py creado"

echo ""
echo "=== VERIFICANDO ARCHIVOS EN EL NUEVO DIRECTORIO ==="
echo ""
ls -la events/views/

echo ""
echo "=== VERIFICANDO ARCHIVOS ORIGINALES ==="
echo "Archivos que deberían haberse movido (ya no deben estar en events/):"
for archivo in "${ARCHIVOS[@]}"; do
    if [ -f "events/$archivo" ]; then
        echo "❌ $archivo todavía está en events/"
    else
        echo "✅ $archivo ya no está en events/"
    fi
done

echo ""
echo "=== ACTUALIZANDO IMPORTACIONES EN events/urls.py ==="

# Verificar si urls.py existe y actualizar importaciones
if [ -f "events/urls.py" ]; then
    # Hacer backup
    cp "events/urls.py" "events/urls.py.bak"
    echo "✅ Backup creado: events/urls.py.bak"
    
    # Actualizar importaciones en urls.py
    sed -i 's/from \. import views/from \.views import \*/g' "events/urls.py"
    sed -i 's/from \. import base_views/from \.views import \*/g' "events/urls.py"
    sed -i 's/from \.views import views/from \.views import \*/g' "events/urls.py"
    
    # Eliminar líneas redundantes si existen
    echo "✅ events/urls.py actualizado"
else
    echo "⚠️  events/urls.py no encontrado"
fi

echo ""
echo "=== VERIFICANDO IMPORTACIONES EN events/views/*.py ==="
echo "Buscando importaciones problemáticas..."

# Buscar importaciones que puedan estar rotas
grep -r "from \.\.views\|from \.views\|import views" --include="*.py" events/views/ || echo "✅ No se encontraron importaciones problemáticas"

echo ""
echo "=== PROCESO COMPLETADO ==="
echo ""
echo "📋 PRÓXIMOS PASOS:"
echo "1. Verifica que events/views/ contenga todos los archivos:"
echo "   ls -la events/views/"
echo ""
echo "2. Revisa que events/urls.py tenga la nueva importación:"
echo "   head -5 events/urls.py"
echo ""
echo "3. Prueba la aplicación:"
echo "   python manage.py check"
echo "   python manage.py runserver"
echo ""
echo "4. Si todo funciona, puedes eliminar el backup:"
echo "   rm events/urls.py.bak"
echo ""