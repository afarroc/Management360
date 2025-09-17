#!/bin/bash
# Script simplificado que usa una sola conexión SSH
# Se ejecuta en Termux y copia desde Windows

echo "=== Sincronización Simple desde Windows a Termux ==="
echo "Una sola conexión SSH"
echo ""

# Configuración
WINDOWS_IP="192.168.18.47"
WINDOWS_USER="asistente"
TERMUX_MEDIA_PATH="/data/data/com.termux/files/home/projects/Management360/media"
WINDOWS_PROJECT_PATH="C:/Projects/Management360"

# Verificar que estamos en Termux
if [ ! -d "/data/data/com.termux" ]; then
    echo "❌ Error: Este script debe ejecutarse en Termux"
    exit 1
fi

echo "📍 Ejecutándose en Termux"
echo "🔍 Conectando a Windows: $WINDOWS_USER@$WINDOWS_IP"
echo ""

# Crear directorio local
echo "📁 Preparando directorio local..."
mkdir -p "$TERMUX_MEDIA_PATH"
rm -rf "$TERMUX_MEDIA_PATH"/*
echo "✅ Directorio preparado"

# Ejecutar todo en una sola conexión SSH
echo "🚀 Iniciando sincronización con una sola conexión..."

ssh $WINDOWS_USER@$WINDOWS_IP "
echo '🔍 Verificando archivos en Windows...'
if [ -d '$WINDOWS_PROJECT_PATH/media' ]; then
    echo '✅ Directorio encontrado'
    ls -la '$WINDOWS_PROJECT_PATH/media'
    echo ''
    echo '📊 Estadísticas:'
    find '$WINDOWS_PROJECT_PATH/media' -type f | wc -l | xargs echo 'Total archivos:'
    du -sh '$WINDOWS_PROJECT_PATH/media' | xargs echo 'Tamaño total:'
else
    echo '❌ ERROR: Directorio no encontrado en $WINDOWS_PROJECT_PATH/media'
    exit 1
fi
" && echo "✅ Verificación exitosa" || { echo "❌ Error en verificación"; exit 1; }

echo ""
echo "📤 Copiando archivos..."
scp -r $WINDOWS_USER@$WINDOWS_IP:"$WINDOWS_PROJECT_PATH/media" "$(dirname "$TERMUX_MEDIA_PATH")/"

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Sincronización completada exitosamente!"
    echo ""
    echo "🔍 Verificando archivos copiados..."
    echo "Contenido del directorio media:"
    ls -la "$TERMUX_MEDIA_PATH"
    echo ""
    echo "Total de archivos copiados:"
    find "$TERMUX_MEDIA_PATH" -type f | wc -l
    echo ""
    echo "Estructura de directorios:"
    find "$TERMUX_MEDIA_PATH" -type d | sort

    echo ""
    echo "📋 Próximos pasos:"
    echo "1. python media_server.py"
    echo "2. curl http://192.168.18.46:8000/"
else
    echo ""
    echo "❌ Error durante la sincronización"
    exit 1
fi