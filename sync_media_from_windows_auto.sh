#!/bin/bash
# Script automático que NO pide confirmación
# Se ejecuta en Termux y copia desde Windows

echo "=== Sincronización Automática desde Windows a Termux ==="
echo "Sin confirmaciones - ejecuta automáticamente"
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

# Verificar conexión SSH
echo "🔗 Verificando conexión SSH..."
if ! ssh -o ConnectTimeout=5 $WINDOWS_USER@$WINDOWS_IP "echo 'SSH OK'" 2>/dev/null; then
    echo "❌ Error: No se puede conectar a Windows SSH"
    exit 1
fi
echo "✅ Conexión SSH verificada"

# Preparar directorio
echo "📁 Preparando directorio local..."
mkdir -p "$TERMUX_MEDIA_PATH"
rm -rf "$TERMUX_MEDIA_PATH"/*
echo "✅ Directorio preparado"

echo "🚀 Iniciando sincronización automática..."

# Copiar archivos
if command -v rsync &> /dev/null; then
    echo "📦 Usando rsync..."
    rsync -avz --delete -e ssh $WINDOWS_USER@$WINDOWS_IP:"$WINDOWS_PROJECT_PATH/media/" "$TERMUX_MEDIA_PATH/"
else
    echo "📦 Usando scp..."
    scp -r $WINDOWS_USER@$WINDOWS_IP:"$WINDOWS_PROJECT_PATH/media/*" "$TERMUX_MEDIA_PATH/"
fi

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Sincronización completada exitosamente!"
    echo ""
    echo "📊 Resumen:"
    echo "  - Archivos copiados: $(find "$TERMUX_MEDIA_PATH" -type f | wc -l)"
    echo "  - Tamaño total: $(du -sh "$TERMUX_MEDIA_PATH" | cut -f1)"
    echo ""
    echo "🎯 Listo para iniciar servidor:"
    echo "  python media_server.py"
else
    echo "❌ Error en sincronización"
    exit 1
fi