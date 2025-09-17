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

### Opción A: Usando ADB (desde PC)

1. Conecta tu dispositivo Android al PC
2. Habilita "Depuración USB" en Ajustes > Opciones de desarrollador
3. Copia los archivos:

```bash
# Desde el directorio del proyecto
adb push media_server.py /sdcard/
adb push media/ /sdcard/media/
```

### Opción B: Usando almacenamiento compartido

1. Copia `media_server.py` y el directorio `media/` a tu almacenamiento interno
2. En Termux, accede a los archivos:

```bash
cd /sdcard/
ls -la
```

### Opción C: Usando Git (recomendado)

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

Deberías ver el listado de archivos en el directorio `/media`.

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

## Próximos Pasos

Una vez que el servidor esté funcionando:

1. Prueba el acceso desde diferentes dispositivos en tu red
2. Verifica que todos los tipos de archivos se sirvan correctamente
3. Configura el servidor para iniciarse automáticamente si es necesario
4. Considera agregar autenticación si necesitas restringir el acceso

---

**Nota**: Asegúrate de que tu dispositivo Android esté conectado a la misma red WiFi que los otros dispositivos que necesitan acceder al servidor.