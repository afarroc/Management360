#!/bin/bash
# Script optimizado para sincronizar archivos media desde Windows (Git Bash) a Termux
# Usa una sola conexión SSH para evitar múltiples peticiones de contraseña
# Uso: ./sync_media_to_termux_optimized.sh

echo "=== Sincronización Optimizada de archivos Media a Termux ==="
echo "Una sola petición de contraseña SSH"
echo ""

# Configuración - MODIFICAR SEGÚN TU CONFIGURACIÓN
TERMUX_IP="192.168.18.46"
TERMUX_PORT="8022"
TERMUX_USER="u0_a211"
TERMUX_PATH="/data/data/com.termux/files/home/projects/Management360/media"
LOCAL_MEDIA_DIR="./media"

# Verificar que existe el directorio media local
if [ ! -d "$LOCAL_MEDIA_DIR" ]; then
    echo "❌ Error: Directorio $LOCAL_MEDIA_DIR no encontrado"
    exit 1
fi

echo "📁 Directorio media local encontrado"
echo "🔍 Verificando archivos a sincronizar..."

# Mostrar archivos que se van a sincronizar
echo ""
echo "Archivos a sincronizar:"
find "$LOCAL_MEDIA_DIR" -type f | while read file; do
    echo "  📄 ${file#./}"
done

echo ""
echo "📊 Resumen:"
echo "  - $(find "$LOCAL_MEDIA_DIR" -type f | wc -l) archivos"
echo "  - $(du -sh "$LOCAL_MEDIA_DIR" | cut -f1) de tamaño total"
echo ""

# Confirmar antes de proceder
read -p "¿Continuar con la sincronización? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Sincronización cancelada"
    exit 1
fi

echo ""
echo "🚀 Iniciando sincronización optimizada..."

# Crear un script temporal para ejecutar en el servidor remoto
TEMP_SCRIPT=$(mktemp)
cat > "$TEMP_SCRIPT" << 'EOF'
#!/bin/bash
# Script que se ejecuta en el servidor remoto
MEDIA_PATH="/data/data/com.termux/files/home/projects/Management360/media"

echo "📁 Creando/limpiando directorio remoto..."
mkdir -p "$MEDIA_PATH"
rm -rf "$MEDIA_PATH"/*
echo "✅ Directorio preparado"

echo "📂 Estructura esperada:"
echo "  - courses/"
echo "  - profile_pics/"
echo "  - room_images/"
EOF

# Ejecutar el script remoto y mantener la conexión abierta
echo "🔗 Estableciendo conexión SSH y ejecutando comandos remotos..."
ssh -p $TERMUX_PORT $TERMUX_USER@$TERMUX_IP "bash -s" < "$TEMP_SCRIPT"

# Limpiar script temporal
rm "$TEMP_SCRIPT"

# Sincronizar archivos usando rsync sobre SSH (más eficiente)
echo "📤 Sincronizando archivos con rsync..."
if command -v rsync &> /dev/null; then
    rsync -avz --delete -e "ssh -p $TERMUX_PORT" "$LOCAL_MEDIA_DIR/" $TERMUX_USER@$TERMUX_IP:"$TERMUX_PATH/"
else
    echo "⚠️  rsync no disponible, usando scp..."
    scp -P $TERMUX_PORT -r "$LOCAL_MEDIA_DIR"/* $TERMUX_USER@$TERMUX_IP:"$TERMUX_PATH/"
fi

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Sincronización completada exitosamente!"
    echo ""
    echo "🔍 Verificando archivos en Termux..."
    ssh -p $TERMUX_PORT $TERMUX_USER@$TERMUX_IP "ls -la $TERMUX_PATH && echo && echo '=== Contenido detallado ===' && find $TERMUX_PATH -type f | head -10"

    echo ""
    echo "📋 Instrucciones para verificar:"
    echo "1. En Termux: cd /data/data/com.termux/files/home/projects/Management360"
    echo "2. Ejecutar: python media_server.py"
    echo "3. Probar: curl http://192.168.18.46:8000/"
    echo "4. Deberías ver: courses/, profile_pics/, room_images/"
else
    echo ""
    echo "❌ Error durante la sincronización"
    exit 1
fi