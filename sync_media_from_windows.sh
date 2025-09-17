#!/bin/bash
# Script que se ejecuta en Termux para sincronizar archivos desde Windows
# Uso: ./sync_media_from_windows.sh

echo "=== Sincronización desde Windows a Termux ==="
echo "Este script se ejecuta en Termux y copia desde Windows"
echo ""

# Configuración - MODIFICAR SEGÚN TU CONFIGURACIÓN
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

# Verificar conectividad SSH
echo "🔗 Verificando conexión SSH con Windows..."
if ! ssh -o ConnectTimeout=5 $WINDOWS_USER@$WINDOWS_IP "echo 'SSH funcionando'" 2>/dev/null; then
    echo "❌ Error: No se puede conectar a Windows via SSH"
    echo "   Asegúrate de que:"
    echo "   1. SSH esté habilitado en Windows"
    echo "   2. El usuario '$WINDOWS_USER' tenga acceso SSH"
    echo "   3. Windows esté en la misma red (IP: $WINDOWS_IP)"
    exit 1
fi

echo "✅ Conexión SSH exitosa"
echo ""

# Crear directorio local si no existe
echo "📁 Preparando directorio local..."
mkdir -p "$TERMUX_MEDIA_PATH"

# Verificar archivos en Windows
echo "🔍 Verificando archivos en Windows..."
ssh $WINDOWS_USER@$WINDOWS_IP "dir /b '$WINDOWS_PROJECT_PATH/media' 2>nul | head -10" 2>/dev/null || echo "Directorio no encontrado o sin archivos"

echo ""
echo "📊 Información de archivos en Windows:"
TOTAL_FILES=$(ssh $WINDOWS_USER@$WINDOWS_IP "dir /b '$WINDOWS_PROJECT_PATH/media' 2>nul | find /c /v \"\"" 2>/dev/null || echo "0")
echo "Total archivos aproximado: $TOTAL_FILES"
echo "Directorio: $WINDOWS_PROJECT_PATH/media"

echo ""
# Confirmar antes de proceder
read -p "¿Continuar con la sincronización? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Sincronización cancelada"
    exit 1
fi

echo ""
echo "🚀 Iniciando sincronización desde Windows..."

# Limpiar directorio local antes de sincronizar
echo "🧹 Limpiando directorio local..."
rm -rf "$TERMUX_MEDIA_PATH"/*
echo "✅ Directorio local preparado"

# Sincronizar archivos desde Windows usando rsync sobre SSH
echo "📤 Copiando archivos desde Windows..."
if command -v rsync &> /dev/null; then
    echo "📦 Usando rsync para sincronización eficiente..."
    rsync -avz --delete -e ssh $WINDOWS_USER@$WINDOWS_IP:"$WINDOWS_PROJECT_PATH/media/" "$TERMUX_MEDIA_PATH/"
else
    echo "📦 rsync no disponible, usando scp..."
    scp -r $WINDOWS_USER@$WINDOWS_IP:"$WINDOWS_PROJECT_PATH/media/*" "$TERMUX_MEDIA_PATH/"
fi

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
    echo "1. Verificar que todos los archivos están presentes"
    echo "2. Iniciar el servidor: python media_server.py"
    echo "3. Probar acceso: curl http://192.168.18.46:8000/"
    echo "4. Deberías ver: courses/, profile_pics/, room_images/"
else
    echo ""
    echo "❌ Error durante la sincronización"
    exit 1
fi