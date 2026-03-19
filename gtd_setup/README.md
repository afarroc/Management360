# 📋 SETUP DEL SISTEMA GTD

## 📁 ESTRUCTURA DE ARCHIVOS

```
gtd_setup/
├── 01_categories/           # Categorías, tags y estados
│   ├── tag_categories.csv   # Categorías de tags
│   ├── tags.csv             # Tags específicos
│   ├── classifications.csv  # Clasificaciones generales
│   ├── status_events.csv    # Estados para eventos
│   ├── status_projects.csv  # Estados para proyectos
│   └── status_tasks.csv     # Estados para tareas
├── 02_inbox/                # Items de la bandeja de entrada
│   └── inbox_items.csv      # 36 items GTD organizados
├── 03_templates/            # Plantillas y eventos base
│   ├── project_templates.csv # Plantillas de proyectos
│   ├── base_events.csv      # Eventos base para proyectos
│   └── task_schedules_template.csv # Programaciones recurrentes
├── 04_backups/              # Backups automáticos
├── 05_logs/                 # Logs de ejecución
├── config.yaml              # Configuración del script
└── README.md                # Este archivo
```

## 🚀 USO RÁPIDO

### 1. Ejecutar el script de creación:
```bash
# Dar permisos de ejecución
chmod +x create_gtd_structure.sh

# Ejecutar (usuario ID 1 por defecto)
./create_gtd_structure.sh

# Especificar usuario ID diferente
./create_gtd_structure.sh 2
```

### 2. Cargar datos al sistema:
```bash
# Verificar estructura
python setup_gtd.py --check

# Ver estadísticas actuales
python setup_gtd.py --stats

# Cargar todos los datos
python setup_gtd.py --all --verbose

# Cargar solo items del inbox
python setup_gtd.py --step inbox --user-id 2

# Simular sin guardar (dry run)
python setup_gtd.py --all --dry-run --verbose
```

### 3. Procesar manualmente:
1. Iniciar sesión en: `http://tu-sitio.com/inbox/`
2. Procesar los 36 items del inbox
3. Archivar áreas de responsabilidad
4. Convertir acciones en tareas/proyectos

## 📊 RESUMEN DE DATOS

### Categorías y Tags:
- **7** categorías de tags
- **44** tags específicos
- **9** clasificaciones generales

### Estados del Sistema:
- **6** estados para eventos
- **7** estados para proyectos  
- **7** estados para tareas

### Items del Inbox:
- **36** items organizados
- **14** áreas de responsabilidad
- **22** acciones concretas

### Plantillas:
- **8** plantillas de proyectos
- **7** eventos base
- **3** programaciones recurrentes

## 🔄 FLUJO DE TRABAJO RECOMENDADO

### Día 1: Configuración Base
1. Ejecutar `./create_gtd_structure.sh`
2. Ejecutar `python setup_gtd.py --step categories`
3. Ejecutar `python setup_gtd.py --step classifications`
4. Ejecutar `python setup_gtd.py --step status`

### Día 2: Datos del Inbox
1. Ejecutar `python setup_gtd.py --step inbox`
2. Ir a `/inbox/` en el navegador
3. Procesar áreas de responsabilidad (archivar)

### Día 3: Creación de Proyectos
1. Procesar acciones del inbox
2. Crear proyectos usando plantillas
3. Configurar eventos base

### Día 4: Optimización
1. Configurar programaciones recurrentes
2. Revisar dashboard GTD
3. Ajustar categorías y tags

## 🛠️ HERRAMIENTAS DISPONIBLES

### Scripts:
- `create_gtd_structure.sh` - Crea estructura de archivos
- `setup_gtd.py` - Carga datos al sistema

### Comandos útiles:
```bash
# Ver ayuda
python setup_gtd.py --help
python setup_gtd.py --list-steps

# Verificar archivos
python setup_gtd.py --check

# Ver estadísticas
python setup_gtd.py --stats

# Ver contenido de archivos
head -n 10 gtd_setup/02_inbox/inbox_items.csv
wc -l gtd_setup/**/*.csv
```

## 📝 NOTAS

1. Los archivos CSV usan **UTF-8** encoding
2. Las fechas deben estar en formato **YYYY-MM-DD**
3. Los precios usan **punto decimal** (0.00)
4. Los booleanos son **True/False**
5. Los IDs de usuario deben existir en la base de datos
6. El script valida existencia para no duplicar datos

## 🆘 SOPORTE

Si encuentras problemas:
1. Verifica que los archivos CSV existen
2. Revisa que el usuario ID sea válido
3. Ejecuta con `--verbose` para más detalles
4. Usa `--dry-run` para simular sin guardar

---

**Creado automáticamente: Sat Feb  7 15:01:15 -05 2026**
**Usuario ID configurado: 2**
**Total archivos creados: 0**
```
