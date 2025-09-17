#!/bin/bash
# Script optimizado que usa una sola conexión SSH
# Se ejecuta en Termux y copia desde Windows

echo "=== Sincronización Optimizada desde Windows a Termux ==="
echo "Una sola petición de contraseña SSH"
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

# Crear un script temporal para ejecutar comandos en Windows
TEMP_SCRIPT=$(mktemp)
cat > "$TEMP_SCRIPT" << 'EOF'
#!/bin/bash
# Script que se ejecuta en Windows para verificar archivos
PROJECT_PATH="C:/Projects/Management360"

echo "🔍 Verificando archivos en Windows..."
if [ -d "$PROJECT_PATH/media" ]; then
    echo "📊 Información de archivos:"
    echo "Total archivos: $(find '$PROJECT_PATH/media' -type f | wc -l)"
    echo "Tamaño total: $(du -sh '$PROJECT_PATH/media' | cut -f1)"
    echo ""
    echo "📁 Estructura de directorios:"
    find "$PROJECT_PATH/media" -type d | head -10
    echo ""
    echo "✅ Archivos encontrados en Windows"
else
    echo "❌ Error: Directorio media no encontrado en Windows"
    exit 1
fi
EOF

# Ejecutar verificación en Windows usando una sola conexión
echo "🔗 Verificando archivos en Windows (una sola conexión)..."
ssh $WINDOWS_USER@$WINDOWS_IP "bash -s" < "$TEMP_SCRIPT"

if [ $? -ne 0 ]; then
    echo "❌ Error al verificar archivos en Windows"
    rm "$TEMP_SCRIPT"
    exit 1
fi

# Limpiar script temporal
rm "$TEMP_SCRIPT"

echo ""
echo "📁 Preparando directorio local..."
mkdir -p "$TERMUX_MEDIA_PATH"
rm -rf "$TERMUX_MEDIA_PATH"/*
echo "✅ Directorio local preparado"

# Confirmar antes de proceder
read -p "¿Continuar con la sincronización? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Sincronización cancelada"
    exit 1
fi

echo ""
echo "🚀 Iniciando sincronización optimizada..."

# Usar rsync sobre SSH para copia eficiente (una sola conexión)
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