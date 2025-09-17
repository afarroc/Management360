#!/bin/bash
# Script para sincronizar archivos media desde Windows (Git Bash) a Termux
# Uso: ./sync_media_to_termux_gitbash.sh

echo "=== Sincronización de archivos Media a Termux (Git Bash) ==="
echo "Asegúrate de tener SSH configurado en Termux"
echo ""

# Configuración - MODIFICAR SEGÚN TU CONFIGURACIÓN
TERMUX_IP="192.168.18.46"
TERMUX_PORT="8022"
TERMUX_USER="u0_a211"
TERMUX_PATH="/data/data/com.termux/files/home/projects/Management360/media"

# Verificar que existe el directorio media local
if [ ! -d "./media" ]; then
    echo "❌ Error: Directorio ./media no encontrado"
    exit 1
fi

echo "📁 Directorio media local encontrado"
echo "🔍 Verificando archivos a sincronizar..."

# Mostrar archivos que se van a sincronizar
echo ""
echo "Archivos a sincronizar:"
find ./media -type f | while read file; do
    echo "  📄 ${file#./}"
done

echo ""
echo "📊 Resumen:"
echo "  - $(find ./media -type f | wc -l) archivos"
echo "  - $(du -sh ./media | cut -f1) de tamaño total"
echo ""

# Confirmar antes de proceder
read -p "¿Continuar con la sincronización? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Sincronización cancelada"
    exit 1
fi

echo ""
echo "🚀 Iniciando sincronización..."

# Verificar si scp está disponible
if ! command -v scp &> /dev/null; then
    echo "❌ Error: SCP no encontrado. Asegúrate de tener OpenSSH instalado"
    echo "   En Git Bash: Usa 'ssh' y 'scp' que vienen incluidos"
    exit 1
fi

# Crear directorio remoto si no existe
echo "📁 Creando directorio remoto..."
ssh -p $TERMUX_PORT $TERMUX_USER@$TERMUX_IP "mkdir -p $TERMUX_PATH"

# Limpiar directorio remoto antes de sincronizar
echo "🧹 Limpiando directorio remoto..."
ssh -p $TERMUX_PORT $TERMUX_USER@$TERMUX_IP "rm -rf $TERMUX_PATH/*"

# Sincronizar archivos usando scp (copia el directorio completo)
echo "📤 Sincronizando archivos..."
scp -P $TERMUX_PORT -r ./media $TERMUX_USER@$TERMUX_IP:$(dirname $TERMUX_PATH)/

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Sincronización completada exitosamente!"
    echo ""
    echo "🔍 Verificando archivos en Termux..."
    ssh -p $TERMUX_PORT $TERMUX_USER@$TERMUX_IP "ls -la $TERMUX_PATH"

    echo ""
    echo "📋 Instrucciones para verificar:"
    echo "1. En Termux: cd /data/data/com.termux/files/home/projects/Management360"
    echo "2. Ejecutar: python media_server.py"
    echo "3. Probar: curl http://192.168.18.46:8000/"
    echo "4. Deberías ver: courses/, profile_pics/"
else
    echo ""
    echo "❌ Error durante la sincronización"
    exit 1
fi