# Sistema de Procesamiento de Correos CX (Customer Experience)

Este sistema permite procesar automáticamente correos electrónicos de clientes y crear entradas en el Inbox GTD para su gestión mediante la metodología Getting Things Done.

## 🚀 Características

- **Procesamiento Automático**: Revisa periódicamente el buzón de correos en busca de emails CX
- **Clasificación Inteligente**: Identifica automáticamente emails de clientes basándose en dominios y palabras clave
- **Integración GTD**: Crea InboxItem con categorización GTD automática
- **Asignación Inteligente**: Distribuye automáticamente las tareas a bots/usuarios apropiados
- **Sistema Colaborativo**: Permite clasificación colaborativa de items

## 📋 Requisitos

- Python 3.8+
- Django 5.1+
- Librerías: `imap-tools`, `schedule`
- Cuenta de correo con IMAP habilitado (Gmail recomendado)

## ⚙️ Configuración

### 1. Variables de Entorno

Agrega estas variables a tu archivo `.env`:

```bash
# Habilitar recepción de correos
EMAIL_RECEPTION_ENABLED=True

# Configuración IMAP
EMAIL_IMAP_HOST=imap.gmail.com
EMAIL_IMAP_PORT=993
EMAIL_IMAP_USER=tu-correo@gmail.com
EMAIL_IMAP_PASSWORD=tu-app-password

# Carpeta específica para CX (opcional)
EMAIL_CX_FOLDER=INBOX/CX

# Intervalo de verificación en segundos (5 minutos por defecto)
EMAIL_CHECK_INTERVAL=300

# Dominios de correo CX
CX_EMAIL_DOMAINS=@cliente.com,@support.com

# Palabras clave para identificar emails CX
CX_KEYWORDS=cambio de plan,modificar plan,actualizar plan,solicitud,queja,reclamo
```

### 2. Servicios de Correo Recomendados para Pruebas

#### **🏆 Gmail (Recomendado)**
- **Ventajas**: Confiable, IMAP completo, fácil configuración
- **Configuración**:
  1. Activa verificación en 2 pasos
  2. Genera "Contraseña de aplicación" en https://myaccount.google.com/apppasswords
  3. Usa esa contraseña (sin espacios) en `EMAIL_IMAP_PASSWORD`

#### **📧 Outlook/Hotmail**
- **Configuración IMAP**:
  ```bash
  EMAIL_IMAP_HOST=imap-mail.outlook.com
  EMAIL_IMAP_PORT=993
  ```

#### **🔒 ProtonMail**
- **Limitaciones**: IMAP limitado en free tier
- **Configuración**:
  ```bash
  EMAIL_IMAP_HOST=imap.protonmail.com
  EMAIL_IMAP_PORT=993
  ```

### 3. Configuración Rápida para Pruebas

Usa el archivo `.env.test` incluido para pruebas:

```bash
cp .env.test .env
# Edita EMAIL_IMAP_USER y EMAIL_IMAP_PASSWORD con tus credenciales
```

### 2. Configuración de Gmail

1. **Activa verificación en 2 pasos** en tu cuenta Gmail
2. **Genera una contraseña de aplicación**:
   - Ve a: https://myaccount.google.com/apppasswords
   - Selecciona "Correo" y "Otra"
   - Nombra la app "Django CX Processing"
   - Copia la contraseña generada (sin espacios)
3. **Crea una etiqueta CX** (opcional):
   - En Gmail, crea una etiqueta llamada "CX"
   - Los correos se pueden mover automáticamente a esta carpeta

### 3. Instalación de Dependencias

```bash
pip install imap-tools schedule
```

O usa el archivo `requirements_clean.txt` incluido.

### 4. Configuración Inicial

Ejecuta el script de configuración:

```bash
python setup_cx_email_config.py
```

Este script:
- Crea el usuario sistema necesario
- Muestra las variables de entorno requeridas
- Prueba la conexión IMAP
- Ejecuta una prueba inicial

## 🧪 Verificación del Sistema

### 1. Verificar Configuración

```bash
# Verificar que las variables de entorno están configuradas
python manage.py shell -c "from django.conf import settings; print('IMAP:', settings.EMAIL_IMAP_USER); print('SMTP:', settings.EMAIL_HOST_USER)"
```

### 2. Probar Conexión IMAP

```bash
# Probar conexión al buzón de correo
python setup_cx_email_config.py
```

### 3. Procesar Correos Manualmente

```bash
# Procesar correos CX pendientes
python manage.py process_cx_emails --max-emails=10

# Modo seguro (solo mostrar, no procesar)
python manage.py process_cx_emails --dry-run --max-emails=5
```

### 4. Procesamiento Automático

```bash
# Procesamiento automático cada 5 minutos
python manage.py schedule_cx_email_processing

# Procesamiento cada 1 minuto (para pruebas)
python manage.py schedule_cx_email_processing --interval=60
```

### 5. Monitoreo

```bash
# Ver logs en tiempo real
tail -f django.log

# Ver items del inbox en Django admin
# Acceder a /admin/events/inboxitem/

# Ver estadísticas desde shell
python manage.py shell
>>> from events.models import InboxItem
>>> InboxItem.objects.filter(user_context__source='cx_email').count()
```

## 🎯 Uso

### Procesamiento Manual

Para procesar correos manualmente:

```bash
# Procesar hasta 50 correos
python manage.py process_cx_emails

# Procesar con límite personalizado
python manage.py process_cx_emails --max-emails=10

# Modo dry-run (solo mostrar, no crear items)
python manage.py process_cx_emails --dry-run
```

### Procesamiento Automático

Para ejecutar el procesamiento automático cada 5 minutos:

```bash
python manage.py schedule_cx_email_processing
```

Presiona `Ctrl+C` para detener.

### Personalizar Intervalo

```bash
# Verificar cada 10 minutos
python manage.py schedule_cx_email_processing --interval=600

# Procesar máximo 20 correos por vez
python manage.py schedule_cx_email_processing --max-emails=20
```

## 🔧 Cómo Funciona

### 1. Recepción de Correos

- El sistema se conecta vía IMAP al buzón configurado
- Busca correos no leídos en la carpeta especificada (o INBOX)
- Procesa cada correo encontrado

### 2. Clasificación CX

Un correo se considera CX si:
- El dominio del remitente está en `CX_EMAIL_DOMAINS`
- O contiene alguna palabra clave de `CX_KEYWORDS`

### 3. Extracción de Información

- **Asunto**: Se usa como base para el título
- **Remitente**: Se guarda para referencia
- **Cuerpo**: Se procesa para extraer ID de cliente
- **Fecha**: Se registra cuando llegó el correo

### 4. Creación de InboxItem

Se crea automáticamente un InboxItem con:
- **Categoría GTD**: `accionable`
- **Tipo de acción**: `delegar`
- **Prioridad**: Basada en palabras clave (alta/media/baja)
- **Contexto**: `cliente`
- **Metadatos**: Información completa del correo

### 5. Asignación Inteligente

El sistema intenta asignar el item a:
1. Bot CX específico (si existe)
2. Cualquier bot activo
3. Usuario administrador (fallback)

## 📊 Flujo GTD para CX

```
Correo llega → Clasificación automática → InboxItem creado → Asignación → Procesamiento GTD
    ↓              ↓                        ↓            ↓              ↓
Identificar    accionable + delegar    Título CX: ...   Bot/Usuario   Hacer/Delegar/Proyecto
como CX
```

## 🛠️ Personalización

### Modificar Criterios de Clasificación

Edita las variables de entorno:
- `CX_EMAIL_DOMAINS`: Agrega dominios de clientes
- `CX_KEYWORDS`: Agrega palabras clave específicas

### Crear Reglas de Asignación Personalizadas

Modifica la función `_determine_assigned_user()` en `process_cx_emails.py`:

```python
def _determine_assigned_user(self, email_data):
    # Lógica personalizada de asignación
    if 'urgente' in email_data['subject'].lower():
        return User.objects.get(username='supervisor')
    # ... más lógica
```

### Procesamiento de Contenido Avanzado

Mejora `_get_email_body()` para manejar mejor HTML o adjuntos.

## 📈 Monitoreo

### Logs

Los logs se guardan en `django.log` con el logger `events`.

### Dashboard Administrativo

Accede al panel de administración de Inbox para ver:
- Items procesados automáticamente
- Estadísticas de procesamiento
- Asignaciones realizadas

### Comandos Útiles

```bash
# Ver estado de items del inbox
python manage.py shell
>>> from events.models import InboxItem
>>> InboxItem.objects.filter(user_context__source='cx_email').count()
```

## 🚨 Solución de Problemas

### Error de Conexión IMAP

- Verifica credenciales de Gmail
- Asegúrate de usar contraseña de aplicación
- Verifica que IMAP esté habilitado

### Correos No Procesados

- Revisa logs en `django.log`
- Verifica configuración de palabras clave
- Prueba con `--dry-run` para debug

### Asignación Incorrecta

- Verifica que existan bots activos
- Revisa lógica en `_determine_assigned_user()`
- Crea bots específicos para CX si es necesario

## 🔒 Seguridad

- Las contraseñas se almacenan en variables de entorno
- Los correos se marcan como leídos después del procesamiento
- Solo usuarios autorizados pueden ver los InboxItem creados

## 📝 Notas Técnicas

- El sistema usa `imap-tools` para mejor rendimiento que `imaplib`
- Los correos se procesan en lotes para evitar sobrecarga
- Se incluye manejo de errores robusto
- Compatible con Gmail, Outlook y otros proveedores IMAP

## 🎯 Próximos Pasos

- [ ] Integración con más proveedores de correo
- [ ] Procesamiento de adjuntos
- [ ] Clasificación automática con IA
- [ ] Dashboard de métricas CX
- [ ] Notificaciones push para nuevos items