# Manual de Navegación: Sistema de Programación de Horarios

## Índice
1. [Introducción](#introducción)
2. [Acceso al Sistema](#acceso-al-sistema)
3. [Creación de Tareas](#creación-de-tareas)
4. [Programaciones Recurrentes](#programaciones-recurrentes)
5. [Vista de Calendario](#vista-de-calendario)
6. [Gestión de Programaciones](#gestión-de-programaciones)
7. [Paneles de Administración](#paneles-de-administración)
8. [Solución de Problemas](#solución-de-problemas)

## Introducción

El Sistema de Programación de Horarios permite crear tareas recurrentes que se ejecutan automáticamente según un calendario definido. Soporta programaciones diarias, semanales y personalizadas.

### Características Principales
- ✅ Creación de tareas programadas
- ✅ Programaciones recurrentes (diarias, semanales)
- ✅ Vista de calendario semanal
- ✅ Generación automática de ocurrencias
- ✅ Paneles de administración
- ✅ Integración con sistema de tareas existente

## Acceso al Sistema

### URLs Principales
- **Lista de Programaciones**: `/events/tasks/schedules/`
- **Crear Programación**: `/events/tasks/schedules/create/`
- **Calendario de Programas**: `/events/task_programs_calendar/`
- **Panel de Administración**: `/events/tasks/schedules/admin/`

### Requisitos de Acceso
- Usuario debe estar autenticado
- Para funciones administrativas: permisos de superusuario

## Creación de Tareas

### Paso 1: Crear una Tarea Base
1. Navega a `/events/tasks/create/`
2. Completa el formulario:
   - **Título**: Nombre descriptivo de la tarea
   - **Descripción**: Detalles de la tarea
   - **Proyecto**: (Opcional) Proyecto asociado
   - **Estado**: Selecciona "To Do"
   - **Asignado a**: Usuario responsable
   - **Precio del ticket**: Costo por hora (ej: 0.07)

### Paso 2: Verificar Creación
- La tarea aparecerá en `/events/tasks/`
- Estado inicial: "To Do"

## Programaciones Recurrentes

### Tipos de Programación

#### 1. Programación Diaria
- Se ejecuta todos los días
- Configuración:
  - Tipo: "Diaria"
  - Hora de inicio: Ej: 09:00
  - Duración: Ej: 1 hora
  - Fecha inicio/fin: Rango de validez

#### 2. Programación Semanal
- Días específicos de la semana
- Configuración:
  - Tipo: "Semanal"
  - Días: Marcar Lunes, Miércoles, Viernes, etc.
  - Hora de inicio: Ej: 14:30
  - Duración: Ej: 2 horas

### Creación de Programación

#### Método 1: Desde Lista de Programaciones
1. Ve a `/events/tasks/schedules/`
2. Click "Crear Programación"
3. Selecciona la tarea existente
4. Configura el tipo de recurrencia
5. Define horario y duración
6. Establece período de validez

#### Método 2: Desde Detalle de Tarea
1. Ve al detalle de una tarea: `/events/tasks/[ID]/`
2. Busca opción de "Crear Programación" (si está disponible)

### Configuración Avanzada

#### Campos Obligatorios
- **Tarea**: Seleccionar tarea existente
- **Tipo de Recurrencia**: Diaria/Semanal/Personalizada
- **Hora de Inicio**: Formato HH:MM
- **Duración**: En horas (ej: 1.5 para 1 hora 30 min)
- **Fecha de Inicio**: Cuando comienza la programación

#### Campos Opcionales
- **Fecha de Fin**: Cuando termina la programación
- **Días de la Semana**: Para programaciones semanales
- **Activo**: Checkbox para activar/desactivar

## Vista de Calendario

### Acceso al Calendario
- URL: `/events/task_programs_calendar/`
- Parámetros opcionales:
  - `start_date`: Fecha de inicio (YYYY-MM-DD)
  - `weeks`: Número de semanas a mostrar (1-4)

### Navegación en el Calendario

#### Controles de Navegación
- **Semana Anterior**: Click en "← Semana Anterior"
- **Semana Siguiente**: Click en "→ Semana Siguiente"
- **Hoy**: Click en "Ir a Hoy"
- **Esta Semana**: Click en "Esta Semana"

#### Vista por Defecto
- Muestra la semana actual
- Días: Lunes a Domingo
- Horas: 9:00 AM - 6:00 PM (automático basado en datos)

### Información Mostrada

#### Por Día
- **Fecha**: Día del mes
- **Día de la Semana**: Lunes, Martes, etc.
- **Número de Programas**: Contador de tareas programadas

#### Por Programa
- **Hora**: Hora de inicio y fin
- **Título**: Nombre de la tarea
- **Estado**: Estado actual de la tarea
- **Duración**: Tiempo estimado

### Filtros y Búsqueda
- **Por Fecha**: Usar parámetro `start_date`
- **Por Usuario**: Automáticamente filtra por usuario logueado
- **Por Estado**: Solo muestra programas activos

## Gestión de Programaciones

### Lista de Programaciones
URL: `/events/tasks/schedules/`

#### Acciones Disponibles
- **Ver Detalle**: Click en el título de la programación
- **Editar**: Botón "Editar" en cada fila
- **Eliminar**: Botón "Eliminar" (con confirmación)
- **Generar Ocurrencias**: Crear programas manualmente

### Detalle de Programación
URL: `/events/tasks/schedules/[ID]/`

#### Información Mostrada
- **Tarea Asociada**: Enlace a la tarea original
- **Tipo de Recurrencia**: Diaria/Semanal
- **Horario**: Hora y duración
- **Próximas Ocurrencias**: Lista de próximas ejecuciones
- **Programas Creados**: Historial de ejecuciones

#### Estadísticas
- **Total de Ocurrencias**: Número generado
- **Próxima Ejecución**: Fecha y hora
- **Estado**: Activo/Inactivo

### Edición de Programaciones
URL: `/events/tasks/schedules/[ID]/edit/`

#### Campos Editables
- Todos los campos de creación
- **Historial de Cambios**: Registro de modificaciones
- **Vista Previa**: Preview antes de guardar

#### Validaciones
- Fecha de fin no puede ser anterior a fecha de inicio
- Al menos un día seleccionado para programaciones semanales
- Duración debe ser positiva

## Paneles de Administración

### Panel de Administración de Programaciones
URL: `/events/tasks/schedules/admin/`

#### Funciones Administrativas
- **Vista Global**: Todas las programaciones del sistema
- **Filtros Avanzados**:
  - Por usuario
  - Por estado (activo/inactivo)
  - Por tipo de recurrencia
  - Por fecha de creación

#### Acciones Masivas
- **Activar/Desactivar**: Cambiar estado de múltiples programaciones
- **Eliminar**: Borrar programaciones seleccionadas
- **Generar Ocurrencias**: Crear programas para múltiples schedules

### Panel de Horarios de Usuarios
URL: `/events/schedules/users/`

#### Vista por Usuario
- **Lista de Usuarios**: Usuarios con programaciones
- **Estadísticas por Usuario**:
  - Número de programaciones
  - Tipos de recurrencia
  - Próximas ejecuciones

## Solución de Problemas

### Problemas Comunes

#### 1. Programación No Aparece en Calendario
**Síntomas**: Programación creada pero no visible en calendario
**Soluciones**:
- Verificar que la programación esté "Activa"
- Comprobar fechas de inicio/fin
- Revisar que el usuario tenga permisos

#### 2. Ocurrencias No se Generan
**Síntomas**: Programación existe pero no crea TaskPrograms
**Soluciones**:
- Usar "Generar Ocurrencias" manualmente
- Verificar configuración de días (para semanales)
- Comprobar logs del sistema

#### 3. Error de Zona Horaria
**Síntomas**: Warnings sobre datetime naive
**Soluciones**:
- El sistema maneja automáticamente las zonas horarias
- Los warnings no afectan funcionalidad
- Datos se almacenan correctamente en UTC

#### 4. Permisos Insuficientes
**Síntomas**: Acceso denegado a ciertas funciones
**Soluciones**:
- Verificar rol de usuario (superusuario para admin)
- Contactar administrador del sistema

### Comandos Útiles

#### Crear Datos de Prueba
```bash
python manage.py create_test_schedules
```
Crea tareas y programaciones de ejemplo

#### Verificar Estado del Sistema
- Revisar logs en terminal de Django
- Verificar base de datos para TaskSchedule y TaskProgram

### Contacto y Soporte

Para problemas técnicos o preguntas sobre el sistema:
1. Revisar este manual
2. Verificar logs de error
3. Contactar al equipo de desarrollo

---

## Resumen de URLs Importantes

| Función | URL | Descripción |
|---------|-----|-------------|
| Lista de Programaciones | `/events/tasks/schedules/` | Ver todas las programaciones |
| Crear Programación | `/events/tasks/schedules/create/` | Nueva programación |
| Calendario | `/events/task_programs_calendar/` | Vista semanal de programas |
| Panel Admin | `/events/tasks/schedules/admin/` | Administración global |
| Panel Usuarios | `/events/schedules/users/` | Horarios por usuario |

## Flujo Completo: Crear Programación y Check-in

### Guía Paso a Paso para Programar Tareas y Registrar Trabajo

Esta sección detalla el proceso completo desde la creación de una programación hasta el check-in del trabajo realizado.

#### Paso 1: Preparación - Crear Tarea Base
**URL**: `/events/tasks/create/`

1. **Acceder al formulario de creación de tareas**
2. **Completar campos obligatorios**:
   - Título: Nombre descriptivo (ej: "Revisión diaria de correos")
   - Descripción: Detalles específicos del trabajo
   - Proyecto: Asociar a proyecto existente (opcional)
   - Estado: Seleccionar "To Do"
   - Asignado a: Usuario responsable
   - Precio del ticket: Costo por hora (ej: 0.07)

3. **Guardar la tarea**
   - La tarea aparecerá en el panel de tareas con estado "To Do"

#### Paso 2: Crear Elemento de Programación
**URL**: `/events/tasks/schedules/create/`

1. **Acceder al formulario de creación de programaciones**
2. **Seleccionar tarea existente** del dropdown
3. **Configurar recurrencia**:
   - **Tipo**: Diaria/Semanal/Personalizada
   - **Días de la semana**: Marcar días específicos (para semanal)
   - **Hora de inicio**: Ej: 09:00, 14:30
   - **Duración**: En horas (ej: 1.0 = 1 hora, 1.5 = 1h 30min)
   - **Fecha de inicio**: Cuando comienza la programación
   - **Fecha de fin**: Cuando termina (opcional)

4. **Vista previa**: Revisar próximas ocurrencias generadas
5. **Guardar programación**

#### Paso 3: Verificar Programación Creada
**URL**: `/events/tasks/schedules/`

- La programación aparecerá en la lista con:
  - Estado: Activa
  - Próxima ocurrencia: Fecha y hora calculada
  - Tipo de recurrencia

#### Paso 4: Generar Ocurrencias Manualmente (Opcional)
**URL**: `/events/tasks/schedules/[ID]/generate/`

Si necesitas crear programas inmediatamente:
1. Ir al detalle de la programación
2. Click "Generar Ocurrencias"
3. El sistema creará TaskPrograms para fechas futuras

#### Paso 5: Ver Calendario de Programas
**URL**: `/events/task_programs_calendar/`

1. **Acceder al calendario semanal**
2. **Verificar que los programas aparecen**:
   - Cada ocurrencia se muestra como un bloque horario
   - Información: hora, título, estado, duración

3. **Navegación**:
   - Semana anterior/siguiente
   - Ir a hoy
   - Cambiar número de semanas (1-4)

#### Paso 6: Check-in al Programa/Ticket
**URL**: `/events/task_programs/[ID]/checkin/` (o similar)

Cuando llegue el momento de trabajar:

1. **Localizar el programa en el calendario**
2. **Click en el bloque del programa**
3. **Iniciar trabajo**:
   - Marcar como "En Progreso"
   - Registrar hora de inicio real
   - Agregar notas iniciales

4. **Durante el trabajo**:
   - Actualizar progreso
   - Agregar comentarios
   - Subir archivos relacionados

5. **Completar trabajo**:
   - Marcar como "Completado"
   - Registrar hora de fin real
   - Calcular tiempo efectivo
   - Agregar resumen del trabajo realizado

#### Paso 7: Verificar y Reportar
**URLs importantes**:
- **Detalle del programa**: `/events/task_programs/[ID]/`
- **Historial de la tarea**: `/events/tasks/[ID]/`
- **Reportes de tiempo**: `/events/reports/time/`

### Rutas Más Importantes en Programación de Tareas

| Acción | URL | Descripción |
|--------|-----|-------------|
| Crear tarea base | `/events/tasks/create/` | Paso inicial obligatorio |
| Crear programación | `/events/tasks/schedules/create/` | Configurar recurrencia |
| Lista programaciones | `/events/tasks/schedules/` | Gestionar programaciones existentes |
| Calendario semanal | `/events/task_programs_calendar/` | Vista principal de trabajo |
| Detalle programación | `/events/tasks/schedules/[ID]/` | Ver configuración y estadísticas |
| Generar ocurrencias | `/events/tasks/schedules/[ID]/generate/` | Crear programas manualmente |
| Editar programación | `/events/tasks/schedules/[ID]/edit/` | Modificar configuración |
| Check-in programa | `/events/task_programs/[ID]/checkin/` | Registrar trabajo realizado |
| Panel administración | `/events/tasks/schedules/admin/` | Gestión global (admin) |
| Panel usuarios | `/events/schedules/users/` | Ver programaciones por usuario |

### Estados del Workflow

1. **Tarea**: To Do → In Progress → Completed
2. **Programación**: Creada → Activa → Inactiva
3. **Programa**: Pendiente → En Progreso → Completado

### Consejos para Check-in Efectivo

1. **Tiempo Real**: Registrar inicio y fin exactos
2. **Documentación**: Agregar notas detalladas del trabajo
3. **Evidencia**: Adjuntar archivos, capturas, enlaces
4. **Calidad**: Verificar que el trabajo cumple requisitos
5. **Retroalimentación**: Agregar lecciones aprendidas

### Automatización del Sistema

- **Generación automática**: Los TaskPrograms se crean automáticamente según el schedule
- **Recordatorios**: Sistema puede enviar notificaciones
- **Reportes**: Estadísticas automáticas de tiempo y productividad
- **Integración**: Conecta con sistema de tickets y facturación

## Consejos de Uso

1. **Planificación**: Crear programaciones con anticipación
2. **Revisión Regular**: Verificar calendario semanalmente
3. **Mantenimiento**: Limpiar programaciones obsoletas
4. **Monitoreo**: Usar paneles de administración para supervisión
5. **Check-in Consistente**: Registrar trabajo diariamente para mejor seguimiento

---

*Manual creado para el Sistema de Gestión Management360 - Programaciones Recurrentes y Check-in*