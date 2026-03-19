# Arquitectura JavaScript - Sistema de Gestión Unificado

## 📁 Estructura de Archivos JavaScript

```
static/assets/js/
├── panel-scripts.js          # 🎯 Core PanelManager (funciones reutilizables)
├── project-panel.js          # 📁 Funciones específicas de proyectos
├── task-panel.js            # ✅ Funciones específicas de tareas
├── event-panel.js           # 📅 Funciones específicas de eventos
└── management-dashboard.js  # 🏠 Funciones específicas del dashboard
```

## 🏗️ Arquitectura Modular

### 1. PanelManager Core (`panel-scripts.js`)
**Funciones globales reutilizables:**
- ✅ `init(config)` - Inicialización con configuración específica
- ✅ `searchItems(query)` - Búsqueda en tiempo real
- ✅ `bulkAction(action, confirmMessage)` - Acciones masivas
- ✅ `exportItems(url)` - Exportación de datos
- ✅ `filterByStatus(statusId)` - Filtrado por estado
- ✅ `toggleView(viewType)` - Cambio de vista (tabla/cards)

### 2. Paneles Específicos
Cada panel tiene su propio archivo JavaScript que:
- ✅ Configura el PanelManager con IDs específicos
- ✅ Define URLs de acciones específicas
- ✅ Implementa funciones específicas del panel
- ✅ Se auto-inicializa cuando está en la página correcta

## 🎯 Uso en Templates

### ✅ Forma CORRECTA (Separación de responsabilidades)
```html
<!-- Solo incluir archivos JavaScript externos -->
<script src="{% static 'assets/js/panel-scripts.js' %}"></script>
<script src="{% static 'assets/js/project-panel.js' %}"></script>
```

### ❌ Forma INCORRECTA (Scripts embebidos)
```html
<!-- NO incluir scripts directamente en templates -->
<script>
// Todo este código debería estar en archivos .js externos
document.addEventListener('DOMContentLoaded', function() {
    // Código JavaScript embebido...
});
</script>
```

## 🔧 Configuración por Panel

### Proyectos (`project-panel.js`)
```javascript
const projectPanelConfig = {
    searchInputId: 'searchInput',
    selectedCountId: 'selectedCount',
    selectAllId: 'selectAll',
    checkboxName: 'selected_projects',
    tableSelector: '.datatable tbody tr',
    tabSelector: '#projectTabs .nav-link'
};
```

### Tareas (`task-panel.js`)
```javascript
const taskPanelConfig = {
    searchInputId: 'taskSearchInput',
    selectedCountId: 'taskSelectedCount',
    selectAllId: 'taskSelectAll',
    checkboxName: 'selected_tasks',
    tableSelector: '.datatable tbody tr',
    tabSelector: '#taskTabs .nav-link'
};
```

### Eventos (`event-panel.js`)
```javascript
const eventPanelConfig = {
    searchInputId: 'eventSearchInput',
    selectedCountId: 'eventSelectedCount',
    selectAllId: 'eventSelectAll',
    checkboxName: 'selected_events',
    tableSelector: '.datatable tbody tr',
    tabSelector: '#eventTabs .nav-link'
};
```

## 🚀 Funciones Disponibles

### Funciones Globales (PanelManager)
```javascript
// Búsqueda
PanelManager.searchItems('query');

// Acciones masivas
PanelManager.bulkAction('delete', '¿Confirmar eliminación?');

// Exportación
PanelManager.exportItems('/export-url/');

// Filtros
PanelManager.filterByStatus('active');

// Cambio de vista
PanelManager.toggleView('cards');
```

### Funciones Específicas por Panel

#### Proyectos
```javascript
clearSearch();           // Limpiar búsqueda
exportProjects();        // Exportar proyectos
bulkAction('delete');    // Acción masiva
toggleView('cards');     // Cambiar vista
```

#### Tareas
```javascript
clearTaskSearch();       // Limpiar búsqueda de tareas
exportTasks();          // Exportar tareas
bulkTaskAction('complete'); // Completar tareas
filterTasksByStatus('1');   // Filtrar por estado
```

#### Eventos
```javascript
clearEventSearch();      // Limpiar búsqueda de eventos
exportEvents();         // Exportar eventos
bulkEventAction('activate'); // Activar eventos
refreshEventData();     // Refrescar datos
```

## 🎨 Beneficios de la Arquitectura

### ✅ **Mantenibilidad**
- **Código organizado** por funcionalidad
- **Cambios centralizados** en archivos específicos
- **Fácil debugging** y testing

### ✅ **Reutilización**
- **Componentes modulares** reutilizables
- **Configuración flexible** por panel
- **Funciones genéricas** extendibles

### ✅ **Performance**
- **Carga condicional** de scripts
- **Auto-inicialización** inteligente
- **Caché del navegador** optimizado

### ✅ **Escalabilidad**
- **Fácil agregar** nuevos paneles
- **Extensión simple** de funcionalidades
- **Módulos independientes** no conflictivos

## 🔄 Auto-Inicialización

Cada panel se auto-inicializa cuando detecta que está en la página correcta:

```javascript
document.addEventListener('DOMContentLoaded', function() {
    // Proyectos
    if (document.querySelector('.project-panel') ||
        window.location.pathname.includes('/projects/')) {
        initProjectPanel();
    }

    // Tareas
    if (document.querySelector('.task-panel') ||
        window.location.pathname.includes('/tasks/')) {
        initTaskPanel();
    }

    // Eventos
    if (document.querySelector('.event-panel') ||
        window.location.pathname.includes('/events/')) {
        initEventPanel();
    }
});
```

## 📝 Mejores Prácticas

### ✅ **Hacer:**
- ✅ Usar archivos JavaScript externos
- ✅ Modularizar por funcionalidad
- ✅ Configurar IDs únicos por panel
- ✅ Documentar funciones públicas
- ✅ Usar auto-inicialización inteligente

### ❌ **Evitar:**
- ❌ Scripts embebidos en templates
- ❌ Código JavaScript en línea
- ❌ IDs duplicados entre paneles
- ❌ Dependencias globales no controladas
- ❌ Funciones anónimas complejas

## 🐛 Debugging

### Console Logs
Cada panel incluye logs de inicialización:
```javascript
console.log('Project panel initialized');
console.log('Task panel initialized');
console.log('Event panel initialized');
```

### Verificación de Carga
```javascript
// Verificar que PanelManager está disponible
console.log(window.PanelManager);

// Verificar configuración específica
console.log(window.PanelManager.config);
```

## 🔧 Extensión

### Agregar Nuevo Panel
1. **Crear archivo específico:** `new-panel.js`
2. **Configurar PanelManager** con IDs únicos
3. **Implementar funciones específicas**
4. **Agregar auto-inicialización**
5. **Incluir en template:** `<script src="new-panel.js"></script>`

### Agregar Nueva Funcionalidad Global
1. **Agregar al PanelManager** en `panel-scripts.js`
2. **Documentar nueva función**
3. **Actualizar configuración** si es necesario
4. **Probar en todos los paneles**

---

## 🎯 Resumen Ejecutivo

Esta arquitectura JavaScript proporciona un **sistema modular, mantenible y escalable** para la gestión unificada de eventos, proyectos y tareas. La **separación clara de responsabilidades** entre código reutilizable y específico por panel facilita el desarrollo, mantenimiento y extensión del sistema.

**Beneficio clave:** Los desarrolladores pueden trabajar en funcionalidades específicas sin afectar otros paneles, mientras mantienen consistencia en la experiencia del usuario.