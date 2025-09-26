# 💬 Ejemplos de Comandos para el Chat del Asistente IA

Este documento contiene ejemplos de comandos que puedes usar en el chat del asistente IA para ejecutar funciones del sistema.

## 🚀 Cómo Usar los Comandos

1. Ve al chat del asistente: `/chat/ui/`
2. Escribe los comandos en lenguaje natural
3. El asistente detectará automáticamente el comando y lo ejecutará
4. Verás el resultado inmediatamente en el chat
5. Consulta el historial completo en: `/chat/commands/`

## 📋 Funciones Disponibles

### 🏗️ Gestión de Proyectos

#### Crear Proyectos
```
crea un proyecto llamado "Desarrollo Web"
crea un proyecto llamado "App Móvil" con descripcion "Desarrollo de aplicación iOS/Android"
nuevo proyecto "Sistema de Inventario" con descripción "Control de stock y productos"
```

#### Listar Proyectos
```
lista mis proyectos
muestra proyectos
ver mis proyectos
```

#### Actualizar Proyectos
```
actualiza proyecto 1 title="Proyecto Web Actualizado"
cambia proyecto 2 description="Nueva descripción del proyecto"
modifica proyecto 3 title="Nombre Nuevo" description="Descripción actualizada"
```

#### Eliminar Proyectos
```
elimina proyecto 5
borra proyecto 10
delete proyecto 3
```

## 📊 Ejemplos Prácticos Completos

### Escenario 1: Gestión de Proyecto Web
```
Usuario: crea un proyecto llamado "Sitio Web Corporativo" con descripcion "Desarrollo de sitio web responsive para empresa"

Asistente: ✅ Proyecto "Sitio Web Corporativo" creado exitosamente con ID 15

Usuario: lista mis proyectos

Asistente: ✅ Encontrados 3 proyectos
- Sitio Web Corporativo (ID: 15) - Desarrollo de sitio web responsive...
- App Móvil (ID: 12) - Desarrollo de aplicación iOS/Android
- Sistema ERP (ID: 8) - Gestión empresarial completa

Usuario: actualiza proyecto 15 title="Sitio Web Corporativo v2.0"

Asistente: ✅ Proyecto 15 actualizado: title
```

### Escenario 2: Organización de Tareas
```
Usuario: crea un proyecto llamado "Reorganización Oficina"

Asistente: ✅ Proyecto "Reorganización Oficina" creado exitosamente con ID 16

Usuario: actualiza proyecto 16 description="Planificación y ejecución de reorganización del espacio de trabajo"

Asistente: ✅ Proyecto 16 actualizado: description
```

### Escenario 3: Proyecto de Marketing
```
Usuario: nuevo proyecto "Campaña Digital Q4" con descripción "Estrategia de marketing digital para último trimestre"

Asistente: ✅ Proyecto "Campaña Digital Q4" creado exitosamente con ID 17

Usuario: lista mis proyectos

Asistente: ✅ Encontrados 4 proyectos
- Campaña Digital Q4 (ID: 17) - Estrategia de marketing digital...
- Sitio Web Corporativo v2.0 (ID: 15) - Desarrollo de sitio web responsive...
- App Móvil (ID: 12) - Desarrollo de aplicación iOS/Android
- Sistema ERP (ID: 8) - Gestión empresarial completa
```

## 🎯 Consejos para Usar los Comandos

### ✅ Sintaxis Correcta
- Usa comillas para títulos y descripciones largas
- Los comandos son case-insensitive (no importa mayúsculas/minúsculas)
- Puedes usar sinónimos: "crea", "nuevo", "crear" funcionan igual

### ✅ Variaciones Aceptadas
```
✅ crea un proyecto llamado "X"
✅ Crea un Proyecto llamado "X"
✅ CREA UN PROYECTO LLAMADO "X"
✅ nuevo proyecto "X"
✅ crear proyecto "X"
```

### ❌ Errores Comunes a Evitar
```
❌ crea proyecto sin nombre  // Falta "llamado"
❌ actualiza proyecto title="X"  // Falta ID del proyecto
❌ elimina proyecto 999  // Proyecto no existe
```

## 🔍 Verificación de Resultados

Después de ejecutar comandos, puedes:

1. **Ver en el chat**: El asistente confirma cada acción
2. **Consultar historial**: `/chat/commands/` muestra todos los comandos ejecutados
3. **Ver estadísticas**: Tasa de éxito, tiempos de ejecución, etc.

## 📈 Próximas Funciones (Planificadas)

- Gestión de tareas (CRUD completo)
- Gestión de eventos
- Búsqueda avanzada
- Reportes y estadísticas
- Integración con calendario

## 🆘 Solución de Problemas

### Comando no reconocido
- Verifica la sintaxis en los ejemplos
- Asegúrate de usar las palabras clave correctas
- Consulta el panel de funciones: `/chat/functions/`

### Error de permisos
- Solo puedes modificar tus propios proyectos
- Verifica que el ID del proyecto sea correcto

### Proyecto no encontrado
- Usa "lista mis proyectos" para ver IDs disponibles
- Los IDs son números únicos asignados automáticamente

---

**💡 Tip**: Copia y pega los ejemplos directamente en el chat para probarlos rápidamente.