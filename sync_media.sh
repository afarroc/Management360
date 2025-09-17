#!/bin/bash
# Script FINAL para sincronizar archivos media desde Windows a Termux
# Se ejecuta en Termux - Único script necesario

echo "=== Sincronización Media: Windows → Termux ==="
echo "Script único y definitivo"
echo ""

# Configuración
WINDOWS_IP="192.168.18.47"
WINDOWS_USER="asistente"
TERMUX_MEDIA_PATH="/data/data/com.termux/files/home/projects/Management360/media"
WINDOWS_PROJECT_PATH="C:/Projects/Management360"

# Verificar que estamos en Termux
if [ ! -d "/data/data/com.termux" ]; then
    echo "❌ Error: Este script debe ejecutarse en Termux"
    echo "   Ubicación actual: $(pwd)"
    exit 1
fi

echo "📍 Ejecutándose en Termux"
echo "🔗 Conectando a: $WINDOWS_USER@$WINDOWS_IP"
echo ""

# Función para verificar conexión SSH
check_ssh() {
    echo "🔗 Verificando conexión SSH..."
    if ! ssh -o ConnectTimeout=5 -o StrictHostKeyChecking=no $WINDOWS_USER@$WINDOWS_IP "echo 'SSH OK'" 2>/dev/null; then
        echo "❌ Error: No se puede conectar a Windows"
        echo "   Verifica que SSH esté habilitado en Windows"
        echo "   IP: $WINDOWS_IP, Usuario: $WINDOWS_USER"
        exit 1
    fi
    echo "✅ Conexión SSH verificada"
}

# Función para verificar archivos en Windows
check_files() {
    echo ""
    echo "🔍 Verificando archivos en Windows..."

    ssh $WINDOWS_USER@$WINDOWS_IP "
    if [ -d '$WINDOWS_PROJECT_PATH/media' ]; then
        echo '✅ Directorio encontrado: $WINDOWS_PROJECT_PATH/media'
        echo ''
        echo '📁 Contenido:'
        ls -la '$WINDOWS_PROJECT_PATH/media' | grep -E '\.(jpg|png|pdf|docx)$|^d' | head -10
        echo ''
        echo '📊 Estadísticas:'
        find '$WINDOWS_PROJECT_PATH/media' -type f 2>/dev/null | wc -l 2>/dev/null | xargs echo 'Total archivos:'
    else
        echo '❌ ERROR: Directorio no encontrado'
        echo '   Ruta verificada: $WINDOWS_PROJECT_PATH/media'
        exit 1
    fi
    "
}

# Función para sincronizar archivos
sync_files() {
    echo ""
    echo "📤 Iniciando sincronización..."

    # Preparar directorio local
    echo "📁 Preparando directorio local..."
    mkdir -p "$TERMUX_MEDIA_PATH"
    rm -rf "$TERMUX_MEDIA_PATH"/*
    echo "✅ Directorio preparado"

    # Copiar archivos
    echo "📦 Copiando archivos desde Windows..."
    if scp -r $WINDOWS_USER@$WINDOWS_IP:"$WINDOWS_PROJECT_PATH/media" "$(dirname "$TERMUX_MEDIA_PATH")/" 2>/dev/null; then
        echo "✅ Archivos copiados exitosamente"
    else
        echo "❌ Error al copiar archivos"
        return 1
    fi
}

# Función para verificar resultado
verify_result() {
    echo ""
    echo "🔍 Verificando resultado..."

    if [ -d "$TERMUX_MEDIA_PATH" ] && [ "$(ls -A "$TERMUX_MEDIA_PATH" 2>/dev/null)" ]; then
        echo "✅ Sincronización completada exitosamente!"
        echo ""
        echo "📊 Resumen:"
        echo "  - Archivos copiados: $(find "$TERMUX_MEDIA_PATH" -type f 2>/dev/null | wc -l 2>/dev/null)"
        echo "  - Tamaño total: $(du -sh "$TERMUX_MEDIA_PATH" 2>/dev/null | cut -f1 2>/dev/null)"
        echo ""
        echo "📁 Estructura copiada:"
        find "$TERMUX_MEDIA_PATH" -type d 2>/dev/null | head -5
        echo ""
        echo "🎯 PRÓXIMOS PASOS:"
        echo "1. Iniciar servidor: python media_server.py"
        echo "2. Probar acceso: curl http://192.168.18.46:8000/"
        echo "3. Deberías ver: courses/, profile_pics/, room_images/"
    else
        echo "❌ Error: No se copiaron archivos correctamente"
        return 1
    fi
}

# Ejecutar flujo principal
main() {
    check_ssh
    check_files

    echo ""
    read -p "¿Continuar con la sincronización? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "❌ Sincronización cancelada"
        exit 0
    fi

    if sync_files && verify_result; then
        echo ""
        echo "🎉 ¡TODO LISTO! El servidor media está configurado."
    else
        echo ""
        echo "❌ Error durante la sincronización"
        echo "Revisa los mensajes de error arriba"
        exit 1
    fi
}

# Ejecutar
main