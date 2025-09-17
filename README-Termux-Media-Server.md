# Media Server para Termux

Servidor HTTP robusto para servir archivos del directorio `/media` desde Termux en Android, optimizado para redes LAN.

## Características

- ✅ Servidor HTTP con soporte CORS para acceso desde cualquier dispositivo en la LAN
- ✅ Configurado específicamente para IP `192.168.18.46`
- ✅ Puerto configurable (por defecto 8000)
- ✅ Logging detallado para monitoreo
- ✅ Manejo robusto de errores
- ✅ Optimizado para Android/Termux
- ✅ Soporte para archivos estáticos (imágenes, PDFs, documentos)

## Requisitos Previos

1. **Termux instalado** en tu dispositivo Android
2. **Python 3** (viene preinstalado en Termux moderno)
3. **Archivos del proyecto** copiados al dispositivo

## Instalación y Configuración

### 1. Instalar Termux (si no lo tienes)

Descarga Termux desde F-Droid o Google Play Store.

### 2. Actualizar Termux

```bash
pkg update && pkg upgrade
```

### 3. Instalar Python (si no está instalado)

```bash
pkg install python
```

### 4. Verificar instalación

```bash
python --version
# Debería mostrar Python 3.x.x
```

## Copia de Archivos al Dispositivo

### Opción A: Sincronización desde Termux (Recomendado)

**Para Termux (se ejecuta en Android):**
```bash
# 1. Copiar el script a Termux
scp -P 8022 sync_media_from_windows.sh u0_a211@192.168.18.46:/data/data/com.termux/files/home/projects/Management360/

# 2. Ejecutarlo en Termux
cd /data/data/com.termux/files/home/projects/Management360
chmod +x sync_media_from_windows.sh
./sync_media_from_windows.sh
```

**Para Windows (Git Bash - alternativo):**
```bash
# Script optimizado que pide contraseña solo una vez
./sync_media_to_termux_optimized.sh
```

**Para Windows (Command Prompt):**
```cmd
# Ejecutar el script de sincronización
sync_media_to_termux.bat
```

**Para Linux/Mac:**
```bash
# Ejecutar el script de sincronización
./sync_media_to_termux.sh
```

Este script automáticamente:
- ✅ **Se ejecuta en Termux** (no en Windows)
- ✅ **Una sola petición de contraseña SSH**
- ✅ **Copia TODOS los archivos** desde Windows incluyendo subdirectorios
- ✅ **Limpia archivos antiguos** antes de sincronizar
- ✅ **Verifica la sincronización completa**
- ✅ **Usa rsync cuando está disponible** (más eficiente)

**Nota:** Este enfoque es más robusto porque se ejecuta en el destino final (Termux) y puede verificar correctamente todos los archivos copiados.

### Opción B: Copia Manual con SCP

```bash
# Copiar script del servidor
scp -P 8022 media_server.py u0_a211@192.168.18.46:/data/data/com.termux/files/home/projects/Management360/

# Copiar directorio media completo
scp -P 8022 -r media/ u0_a211@192.168.18.46:/data/data/com.termux/files/home/projects/Management360/media/
```

### Opción C: Usando ADB

1. Conecta tu dispositivo Android al PC
2. Habilita "Depuración USB" en Ajustes > Opciones de desarrollador
3. Copia los archivos:

```bash
# Desde el directorio del proyecto
adb push media_server.py /sdcard/
adb push media/ /sdcard/media/
```

### Opción D: Usando almacenamiento compartido

1. Copia `media_server.py` y el directorio `media/` a tu almacenamiento interno
2. En Termux, accede a los archivos:

```bash
cd /sdcard/
ls -la
```

### Opción E: Usando Git

```bash
# Clonar el repositorio completo
git clone <tu-repositorio>
cd <directorio-del-proyecto>
```

## Ejecución del Servidor

### Comando Básico

```bash
python media_server.py
```

### Con Opciones Personalizadas

```bash
# Puerto personalizado
python media_server.py --port 8080

# IP diferente (si es necesario)
python media_server.py --host 192.168.1.100

# Nivel de logging detallado
python media_server.py --log-level DEBUG

# Directorio diferente
python media_server.py --directory /ruta/a/tu/media
```

### Ejecución en Background

Para ejecutar el servidor en segundo plano:

```bash
# Ejecutar en background
python media_server.py &

# Ver procesos en ejecución
ps aux | grep python

# Detener el servidor
kill <PID-del-proceso>
```

## Verificación de Sincronización

### Verificar archivos copiados en Termux

```bash
# Verificar que el directorio media existe y tiene contenido
ls -la /data/data/com.termux/files/home/projects/Management360/media/

# Deberías ver:
# courses/
# profile_pics/
# (y otros archivos si existen)
```

### Verificar contenido específico

```bash
# Verificar directorio courses
ls -la media/courses/
# Deberías ver: assignments/ lesson_attachments/ thumbnails/

# Verificar directorio profile_pics
ls -la media/profile_pics/
# Deberías ver: thumb-1920-29144.jpg

# Contar archivos totales
find media/ -type f | wc -l
# Deberías ver: 7 (o el número correcto de archivos)
```

### Archivos que deben estar presentes:

```
media/
├── courses/
│   ├── assignments/
│   │   ├── 3004.pdf
│   │   └── Proceso_reporte_VENTAS_-_FIJA.docx
│   ├── lesson_attachments/
│   │   └── 3004.pdf
│   └── thumbnails/
│       ├── 20667.jpg
│       ├── 21262.jpg
│       ├── Microsoft-Power-BI-Symbol_7FyyVyd.png
│       └── Microsoft-Power-BI-Symbol.png
└── profile_pics/
    └── thumb-1920-29144.jpg
```

## Verificación del Funcionamiento

### 1. Verificar que el servidor está ejecutándose

```bash
# En Termux
netstat -tlnp | grep :8000
# Deberías ver: 192.168.18.46:8000 LISTENING
```

### 2. Probar desde otro dispositivo en la LAN

Abre un navegador web en otro dispositivo conectado a la misma red y accede a:

```
http://192.168.18.46:8000/
```

Deberías ver el listado de archivos en el directorio `/media` con:
- `courses/`
- `profile_pics/`

### 3. Probar archivos específicos

```
http://192.168.18.46:8000/courses/thumbnails/imagen.jpg
http://192.168.18.46:8000/profile_pics/foto.jpg
```

## Configuración de Red

### Verificar IP local

```bash
# En Termux
ip route show
# o
ifconfig
```

### Verificar conectividad en la LAN

```bash
# Ping a otro dispositivo en la red
ping 192.168.18.1  # Gateway/router

# Ver dispositivos en la red (opcional)
arp -a
```

## Solución de Problemas

### Error: "Port already in use"

```bash
# Cambiar puerto
python media_server.py --port 8080
```

### Error: "Cannot assign requested address"

```bash
# Verificar IP disponible
python media_server.py --host 0.0.0.0
# o usar la IP que muestra el comando ip route
```

### Error: "Permission denied"

```bash
# Asegurarse de que los archivos tengan permisos de lectura
chmod -R 644 media/
```

### El servidor no es accesible desde otros dispositivos

1. **Verificar firewall**: Asegúrate de que no haya firewall bloqueando el puerto
2. **Verificar IP**: Confirma que `192.168.18.46` es la IP correcta de tu dispositivo
3. **Verificar red**: Asegúrate de que ambos dispositivos estén en la misma subred LAN

### Los archivos no aparecen en el servidor

**Síntoma**: El servidor funciona pero no muestra `courses/` y `profile_pics/`

**Solución**:
```bash
# 1. Verificar ubicación del directorio media
ls -la /data/data/com.termux/files/home/projects/Management360/media/

# 2. Si no existe, crear y sincronizar
mkdir -p /data/data/com.termux/files/home/projects/Management360/media

# 3. Desde Windows, ejecutar sincronización
sync_media_to_termux.bat

# 4. Verificar contenido después de sincronización
ls -la media/
# Deberías ver: courses/ profile_pics/
```

### Error de conexión SSH durante sincronización

**Síntoma**: `ssh: connect to host 192.168.18.46 port 8022: Connection refused`

**Solución**:
```bash
# 1. Verificar que SSH está ejecutándose en Termux
ps aux | grep ssh

# 2. Si no está ejecutándose, iniciarlo
sshd

# 3. Verificar puerto SSH
netstat -tlnp | grep :8022
```

### Archivos no se sincronizan correctamente

**Síntoma**: La sincronización parece exitosa pero los archivos no aparecen

**Solución**:
```bash
# Verificar permisos en Termux
ls -la /data/data/com.termux/files/home/projects/Management360/

# Ajustar permisos si es necesario
chmod -R 755 /data/data/com.termux/files/home/projects/Management360/media/

# Verificar espacio disponible
df -h /data/data/com.termux/files/home/
```

### Solo se copian algunos archivos (room_images pero no courses/profile_pics)

**Síntoma**: La sincronización copia `room_images/` y `__init__.py` pero no `courses/` y `profile_pics/`

**Causa**: Problema con el patrón de copia de archivos en algunos scripts

**Solución**: Usa el script optimizado
```bash
# Usa el script optimizado que copia el directorio completo
./sync_media_to_termux_optimized.sh

# O verifica manualmente
ls -la media/
# Deberías ver: courses/ profile_pics/ room_images/
```

### Error "Connection refused" o "Permission denied"

**Síntoma**: No se puede conectar al servidor SSH

**Solución**:
```bash
# Verificar que SSH está ejecutándose en Termux
ssh -p 8022 u0_a211@192.168.18.46 "echo 'SSH funcionando'"

# Si no funciona, reiniciar SSH en Termux
sshd

# Verificar puerto
netstat -tlnp | grep :8022
```

### Logs no aparecen

```bash
# Ejecutar con logging detallado
python media_server.py --log-level DEBUG
```

## Archivos Servidos

El servidor sirve automáticamente todos los archivos en el directorio `/media/`:

- **Cursos**: assignments, lesson_attachments, thumbnails
- **Perfiles**: profile_pics
- **Otros**: Cualquier archivo agregado al directorio

## Seguridad

⚠️ **Importante**: Este servidor está configurado para desarrollo y pruebas en red local. No lo uses en redes públicas sin configuración de seguridad adicional.

- El servidor permite acceso desde cualquier origen (CORS *)
- No incluye autenticación
- Los archivos son servidos sin restricciones

## Comandos Útiles

```bash
# Ver logs en tiempo real
tail -f /data/data/com.termux/files/usr/var/log/termux.log

# Ver uso de memoria
ps aux | grep python

# Ver conexiones activas
netstat -tlnp

# Liberar puerto
fuser -k 8000/tcp
```

## Detener el Servidor

```bash
# Ctrl+C en la terminal donde está ejecutándose
# o
killall python
# o
pkill -f media_server.py
```

## Comandos de Verificación Completos

### Verificación Final del Servidor

```bash
# 1. Verificar archivos sincronizados
echo "=== Verificación de archivos ==="
ls -la media/
echo ""
echo "Contenido de courses:"
ls -la media/courses/
echo ""
echo "Contenido de profile_pics:"
ls -la media/profile_pics/

# 2. Iniciar servidor
echo ""
echo "=== Iniciando servidor ==="
python media_server.py

# 3. En otra terminal/ventana, verificar servidor
echo ""
echo "=== Verificación del servidor ==="
curl -I http://192.168.18.46:8000/
echo ""
echo "Listado de archivos:"
curl http://192.168.18.46:8000/
echo ""
echo "Verificar directorio courses:"
curl http://192.168.18.46:8000/courses/
echo ""
echo "Verificar archivo específico:"
curl -I http://192.168.18.46:8000/courses/thumbnails/20667.jpg
```

## Próximos Pasos

Una vez que el servidor esté funcionando:

1. **Sincronización inicial**:
   ```bash
   # En Windows
   sync_media_to_termux.bat

   # En Termux
   cd /data/data/com.termux/files/home/projects/Management360
   python media_server.py
   ```

2. **Pruebas de acceso**:
   - Abre `http://192.168.18.46:8000/` en cualquier dispositivo de la LAN
   - Verifica que se listen `courses/` y `profile_pics/`
   - Prueba descargar archivos específicos

3. **Configuración avanzada**:
   - Configura el servidor para iniciarse automáticamente
   - Considera agregar autenticación si necesitas restringir el acceso
   - Configura logs persistentes si es necesario

4. **Mantenimiento**:
   - Ejecuta la sincronización cuando actualices archivos en Windows
   - Monitorea los logs del servidor para detectar problemas
   - Verifica el espacio disponible periódicamente

---

**Nota**: Asegúrate de que tu dispositivo Android esté conectado a la misma red WiFi que los otros dispositivos que necesitan acceder al servidor.