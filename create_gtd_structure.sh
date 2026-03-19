#!/bin/bash
# archivo: create_gtd_structure.sh
# Script para crear estructura completa de carpetas y archivos CSV del sistema GTD

# ============================================================================
# CONFIGURACIÓN
# ============================================================================
BASE_DIR="gtd_setup"
USER_ID=${1:-1}  # ID de usuario, default: 1

# Colores para output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ============================================================================
# FUNCIONES UTILITARIAS
# ============================================================================
print_header() {
    echo -e "\n${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

create_dir() {
    if [ ! -d "$1" ]; then
        mkdir -p "$1"
        print_success "Creada carpeta: $1"
    else
        print_warning "Carpeta existente: $1"
    fi
}

create_file() {
    if [ ! -f "$1" ]; then
        echo "$2" > "$1"
        print_success "Creado archivo: $1"
    else
        print_warning "Archivo existente: $1 (no se sobrescribe)"
    fi
}

# ============================================================================
# CREAR ESTRUCTURA DE CARPETAS
# ============================================================================
print_header "CREANDO ESTRUCTURA DE CARPETAS"

create_dir "$BASE_DIR"
create_dir "$BASE_DIR/01_categories"
create_dir "$BASE_DIR/02_inbox"
create_dir "$BASE_DIR/03_templates"
create_dir "$BASE_DIR/04_backups"
create_dir "$BASE_DIR/05_logs"

# ============================================================================
# 1. CATEGORÍAS DE TAGS
# ============================================================================
print_header "CREANDO ARCHIVO: tag_categories.csv"

TAG_CATEGORIES_FILE="$BASE_DIR/01_categories/tag_categories.csv"
TAG_CATEGORIES_CONTENT="name,description,color,icon,is_system
Contexto,Lugar o situación donde se puede ejecutar la tarea,#3498db,bi-geo,True
Área,Área de responsabilidad o tema general,#e74c3c,bi-folder,True
Prioridad,Nivel de importancia de la tarea,#f39c12,bi-exclamation,True
Metodología,Sistema o metodología aplicada,#9b59b6,bi-diagram-3,True
Tipo,Tipo de tarea o actividad,#1abc9c,bi-tag,True
GTD,Categorías específicas del sistema GTD,#2ecc71,bi-check2-circle,True
Personal,Tags personalizados del usuario,#34495e,bi-person,False"

create_file "$TAG_CATEGORIES_FILE" "$TAG_CATEGORIES_CONTENT"

# ============================================================================
# 2. TAGS ESPECÍFICOS
# ============================================================================
print_header "CREANDO ARCHIVO: tags.csv"

TAGS_FILE="$BASE_DIR/01_categories/tags.csv"
TAGS_CONTENT="name,category,color,description,is_system
@casa,Contexto,#3498db,Tareas que se hacen en casa,True
@computadora,Contexto,#2ecc71,Tareas que requieren computadora,True
@teléfono,Contexto,#27ae60,Llamadas o comunicación telefónica,True
@taller,Contexto,#f39c12,Tareas en mesa de trabajo/carpintería,True
@salud,Contexto,#e74c3c,Actividades relacionadas con salud,True
@planificación,Contexto,#9b59b6,Tareas de planificación y organización,True
@familia,Contexto,#1abc9c,Actividades familiares,True
@social,Contexto,#34495e,Actividades sociales,True
@creatividad,Contexto,#8e44ad,Actividades artísticas/creativas,True
@fuera,Contexto,#16a085,Tareas fuera de casa,True
@errands,Contexto,#d35400,Recados,True
@auto,Contexto,#c0392b,Tareas en el auto o viaje,True
@lectura,Contexto,#2980b9,Tareas de lectura o estudio,True
@ejercicio,Contexto,#e74c3c,Actividad física,True
@descanso,Contexto,#7f8c8d,Tiempo de descanso o relajación,True
@trabajo,Contexto,#2c3e50,Tareas laborales,True
Ropa,Área,#3498db,Gestión de vestimenta personal,False
Piso,Área,#2980b9,Mantenimiento del hogar,False
Patio,Área,#27ae60,Cuidado de área exterior,False
Alimento,Área,#e67e22,Gestión de alimentación,False
Educación,Área,#9b59b6,Aprendizaje y desarrollo,False
Ocupación,Área,#34495e,Trabajo actual,False
Profesión,Área,#2c3e50,Desarrollo profesional,False
Salud,Área,#e74c3c,Bienestar físico y mental,False
Descanso,Área,#7f8c8d,Sueño y recuperación,False
Noticias,Área,#95a5a6,Mantenerse informado,False
Arte,Área,#8e44ad,Expresión creativa,False
Familia,Área,#1abc9c,Relaciones familiares,False
Amistad,Área,#16a085,Relaciones sociales,False
Creencias,Área,#f39c12,Valores y espiritualidad,False
Alta,Prioridad,#e74c3c,Tareas críticas o urgentes,True
Media,Prioridad,#f39c12,Tareas importantes,True
Baja,Prioridad,#2ecc71,Tareas normales o de bajo impacto,True
GTD,Metodología,#2ecc71,Sistema Getting Things Done,True
Carpintería,Tipo,#8B4513,Proyectos de carpintería,False
Estudio,Tipo,#3498db,Actividades de aprendizaje,False
Limpieza,Tipo,#7f8c8d,Tareas de limpieza,False
Ejercicio,Tipo,#e74c3c,Actividad física,False
Cocina,Tipo,#d35400,Preparación de alimentos,False
Organización,Tipo,#9b59b6,Tareas organizativas,False
Social,Tipo,#1abc9c,Actividades sociales,False
Hábito,Tipo,#34495e,Rutinas diarias,False
Accionable,GTD,#27ae60,Item procesable según GTD,True
No Accionable,GTD,#95a5a6,Item no procesable,True
Referencia,GTD,#7f8c8d,Información para archivar,True
Incubar,GTD,#f39c12,Para reconsiderar en el futuro,True
Eliminar,GTD,#e74c3c,Item para descartar,True"

create_file "$TAGS_FILE" "$TAGS_CONTENT"

# ============================================================================
# 3. CLASIFICACIONES
# ============================================================================
print_header "CREANDO ARCHIVO: classifications.csv"

CLASSIFICATIONS_FILE="$BASE_DIR/01_categories/classifications.csv"
CLASSIFICATIONS_CONTENT="nombre,descripción
Área Personal,Responsabilidades y tareas de vida personal
Área Profesional,Tareas y proyectos relacionados con trabajo
Área Salud,Bienestar físico y mental
Área Aprendizaje,Educación y desarrollo de habilidades
Área Hogar,Mantenimiento y organización del hogar
Área Social,Relaciones y actividades sociales
Área Finanzas,Gestión económica y presupuestos
Área Creatividad,Actividades artísticas y expresión
Área Espiritual,Valores, creencias y crecimiento personal"

create_file "$CLASSIFICATIONS_FILE" "$CLASSIFICATIONS_CONTENT"

# ============================================================================
# 4. ESTADOS DE EVENTOS
# ============================================================================
print_header "CREANDO ARCHIVO: status_events.csv"

STATUS_EVENTS_FILE="$BASE_DIR/01_categories/status_events.csv"
STATUS_EVENTS_CONTENT="status_name,icon,active,color,model
Created,bi-plus-circle,True,#6c757d,Event
Planned,bi-calendar,True,#17a2b8,Event
In Progress,bi-play-circle,True,#007bff,Event
Completed,bi-check-circle,True,#28a745,Event
Cancelled,bi-x-circle,True,#dc3545,Event
Postponed,bi-clock,True,#ffc107,Event"

create_file "$STATUS_EVENTS_FILE" "$STATUS_EVENTS_CONTENT"

# ============================================================================
# 5. ESTADOS DE PROYECTOS
# ============================================================================
print_header "CREANDO ARCHIVO: status_projects.csv"

STATUS_PROJECTS_FILE="$BASE_DIR/01_categories/status_projects.csv"
STATUS_PROJECTS_CONTENT="status_name,icon,active,color,model
To Do,bi-card-checklist,True,#6c757d,Project
Planning,bi-clipboard,True,#17a2b8,Project
Active,bi-play,True,#007bff,Project
Review,bi-eye,True,#ffc107,Project
Completed,bi-check,True,#28a745,Project
On Hold,bi-pause,True,#6c757d,Project
Archived,bi-archive,True,#343a40,Project"

create_file "$STATUS_PROJECTS_FILE" "$STATUS_PROJECTS_CONTENT"

# ============================================================================
# 6. ESTADOS DE TAREAS
# ============================================================================
print_header "CREANDO ARCHIVO: status_tasks.csv"

STATUS_TASKS_FILE="$BASE_DIR/01_categories/status_tasks.csv"
STATUS_TASKS_CONTENT="status_name,icon,active,color,model
To Do,bi-circle,True,#6c757d,Task
In Progress,bi-play-circle,True,#007bff,Task
Waiting,bi-clock,True,#ffc107,Task
Review,bi-eye,True,#17a2b8,Task
Done,bi-check-circle,True,#28a745,Task
Blocked,bi-slash-circle,True,#dc3545,Task
Delegated,bi-person-check,True,#20c997,Task"

create_file "$STATUS_TASKS_FILE" "$STATUS_TASKS_CONTENT"

# ============================================================================
# 7. ITEMS DEL INBOX - VERSIÓN CORREGIDA (8 campos exactos)
# ============================================================================
print_header "CREANDO ARCHIVO: inbox_items.csv"

INBOX_ITEMS_FILE="$BASE_DIR/02_inbox/inbox_items.csv"
INBOX_ITEMS_CONTENT="title,description,gtd_category,priority,action_type,context,energy_required,estimated_time
Ropa,Gestión de vestimenta personal,no_accionable,media,archivar,@casa,media,60
Piso,Mantenimiento del hogar,no_accionable,media,archivar,@casa,media,90
Patio,Cuidado del jardín,no_accionable,media,archivar,@casa,media,120
Alimento,Gestión de alimentación,no_accionable,media,archivar,@casa,media,45
Educación,Aprendizaje continuo,accionable,media,proyecto,@computadora,alta,180
Ocupación,Tareas laborales,accionable,alta,proyecto,@computadora,alta,240
Profesión,Desarrollo profesional,accionable,media,proyecto,@computadora,alta,300
Físico / Salud,Cuidado de salud,accionable,alta,proyecto,@salud,media,60
Descanso,Recuperación y sueño,accionable,media,hacer,@casa,baja,480
Noticias,Mantenerse informado,no_accionable,baja,archivar,@computadora,baja,30
Arte,Expresión creativa,accionable,media,pasatiempo,@creatividad,media,120
Familia,Relaciones familiares,accionable,media,hacer,@familia,media,180
Amistad,Relaciones sociales,accionable,media,hacer,@social,media,120
Creencias,Valores personales,no_accionable,baja,archivar,@personal,media,60
Configurar sistema de tareas GTD,Implementar método GTD,accionable,alta,proyecto,@computadora,alta,240
Planificar proyectos anuales 2024,Definir objetivos anuales,accionable,alta,proyecto,@planificación,alta,180
Establecer metas trimestrales,Definir metas trimestrales,accionable,alta,proyecto,@planificación,alta,120
Programar tiempo para pasatiempos,Agendar horas recreativas,accionable,media,hacer,@casa,media,60
Aprender comandos básicos de Termux,Configurar Termux,accionable,alta,proyecto,@computadora,media,90
Rutina de ejercicios diaria,Rutina de ejercicio,accionable,alta,hacer,@salud,media,30
Lavar ropa,Lavandería semanal,accionable,media,hacer,@casa,media,120
Proyecto de carpintería inicial,Proyecto de carpintería,accionable,media,proyecto,@taller,media,180
Regar plantas,Mantenimiento de plantas,accionable,baja,hacer,@casa,baja,15
Ducha nocturna,Ducha antes de dormir,accionable,media,hacer,@casa,baja,20
Preparar almuerzo,Preparar comida,accionable,media,hacer,@casa,media,60
Ejercicio físico diario,Actividad física diaria,accionable,alta,hacer,@salud,media,45
Revisión inbox diaria,Revisar inbox diario,accionable,alta,hacer,@planificación,media,15
Planificación semanal,Planificar semana,accionable,alta,proyecto,@planificación,alta,60
Compras semanales,Ir al supermercado,accionable,media,hacer,@fuera,media,90
Tiempo de lectura,Leer 30 minutos,accionable,media,hacer,@lectura,baja,30
Llamar a familia,Llamar a familiares,accionable,media,hacer,@teléfono,media,30
Organizar mesa de trabajo,Organizar taller,accionable,media,hacer,@taller,media,60
Aprender nueva habilidad,Aprender algo nuevo,accionable,media,proyecto,@computadora,alta,120
Revisión mensual,Evaluar progreso mensual,accionable,alta,proyecto,@planificación,alta,90
Tiempo creativo,Actividades creativas,accionable,media,hacer,@creatividad,media,120
Socializar,Actividades sociales,accionable,media,hacer,@social,media,180
Descanso activo,Relajación sin pantallas,accionable,media,hacer,@descanso,baja,60"

create_file "$INBOX_ITEMS_FILE" "$INBOX_ITEMS_CONTENT"

# ============================================================================
# 8. PLANTILLAS DE PROYECTO
# ============================================================================
print_header "CREANDO ARCHIVO: project_templates.csv"

PROJECT_TEMPLATES_FILE="$BASE_DIR/03_templates/project_templates.csv"
PROJECT_TEMPLATES_CONTENT="name,description,category,estimated_duration,is_public,created_by_id
Sistema GTD Personal,Implementar método Getting Things Done,Productividad,30,False,$USER_ID
Bienestar Integral,Plan de salud y bienestar,Salud,90,False,$USER_ID
Desarrollo Profesional,Avance en carrera profesional,Profesional,180,False,$USER_ID
Hogar Organizado,Organización completa del hogar,Hogar,60,False,$USER_ID
Proyecto Carpintería Básico,Primer proyecto de carpintería,Carpintería,14,False,$USER_ID
Curso de Aprendizaje,Curso completo sobre tema específico,Educación,30,False,$USER_ID
Rutina Diaria Saludable,Establecer hábitos saludables diarios,Salud,21,True,$USER_ID
Planificación Anual,Planificar objetivos anuales,Productividad,7,True,$USER_ID"

create_file "$PROJECT_TEMPLATES_FILE" "$PROJECT_TEMPLATES_CONTENT"

# ============================================================================
# 9. EVENTOS BASE
# ============================================================================
print_header "CREANDO ARCHIVO: base_events.csv"

BASE_EVENTS_FILE="$BASE_DIR/03_templates/base_events.csv"
BASE_EVENTS_CONTENT="title,description,event_category,venue,max_attendees,ticket_price,status_id,host_id,assigned_to_id
Proyecto Personal,Sistema personal de organización,inbox_personal,Home Office,1,0.00,1,$USER_ID,$USER_ID
Proyecto Salud,Plan de bienestar personal,inbox_health,Casa,1,0.00,1,$USER_ID,$USER_ID
Proyecto Profesional,Desarrollo profesional,inbox_work,Oficina,1,0.00,1,$USER_ID,$USER_ID
Proyecto Hogar,Organización del hogar,inbox_home,Casa,1,0.00,1,$USER_ID,$USER_ID
Proyecto Aprendizaje,Curso o estudio,inbox_learning,Estudio,1,0.00,1,$USER_ID,$USER_ID
Evento Recurrente Semanal,Revisión y planificación semanal,inbox_review,Home Office,1,0.00,2,$USER_ID,$USER_ID
Evento Diario,Rutinas diarias,inbox_daily,Casa,1,0.00,2,$USER_ID,$USER_ID"

create_file "$BASE_EVENTS_FILE" "$BASE_EVENTS_CONTENT"

# ============================================================================
# 10. PLANTILLA DE PROGRAMACIONES RECURRENTES
# ============================================================================
print_header "CREANDO ARCHIVO: task_schedules_template.csv"

TASK_SCHEDULES_FILE="$BASE_DIR/03_templates/task_schedules_template.csv"
TASK_SCHEDULES_CONTENT="recurrence_type,monday,tuesday,wednesday,thursday,friday,saturday,sunday,start_time,duration,start_date,end_date,is_active
weekly,True,False,False,False,False,False,False,10:00,01:00:00,2024-01-01,,True
daily,True,True,True,True,True,True,True,07:00,00:30:00,2024-01-01,,True
weekly,False,False,False,False,False,True,False,09:00,02:00:00,2024-01-01,,True"

create_file "$TASK_SCHEDULES_FILE" "$TASK_SCHEDULES_CONTENT"

# ============================================================================
# 11. ARCHIVO DE CONFIGURACIÓN DEL SCRIPT
# ============================================================================
print_header "CREANDO ARCHIVO: config.yaml"

CONFIG_FILE="$BASE_DIR/config.yaml"
CONFIG_CONTENT="# Configuración del sistema GTD
defaults:
  user_id: $USER_ID
  base_path: \"gtd_setup\"
  verbose: true
  
steps:
  categories:
    enabled: true
    files:
      - \"01_categories/tag_categories.csv\"
      - \"01_categories/tags.csv\"
  
  classifications:
    enabled: true
    files:
      - \"01_categories/classifications.csv\"
  
  status:
    enabled: true
    files:
      - \"01_categories/status_events.csv\"
      - \"01_categories/status_projects.csv\"
      - \"01_categories/status_tasks.csv\"
  
  inbox:
    enabled: true
    files:
      - \"02_inbox/inbox_items.csv\"
  
  templates:
    enabled: true
    files:
      - \"03_templates/project_templates.csv\"
      - \"03_templates/base_events.csv\"
  
  settings:
    enabled: true

# Notas:
# 1. Los archivos CSV deben usar codificación UTF-8
# 2. Las fechas deben estar en formato YYYY-MM-DD
# 3. Los precios usan punto decimal
# 4. Los booleanos: True/False"

create_file "$CONFIG_FILE" "$CONFIG_CONTENT"

# ============================================================================
# 12. README DEL SETUP
# ============================================================================
print_header "CREANDO ARCHIVO: README.md"

README_FILE="$BASE_DIR/README.md"
README_CONTENT="# 📋 SETUP DEL SISTEMA GTD

## 📁 ESTRUCTURA DE ARCHIVOS

\`\`\`
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
\`\`\`

## 🚀 USO RÁPIDO

### 1. Ejecutar el script de creación:
\`\`\`bash
# Dar permisos de ejecución
chmod +x create_gtd_structure.sh

# Ejecutar (usuario ID 1 por defecto)
./create_gtd_structure.sh

# Especificar usuario ID diferente
./create_gtd_structure.sh 2
\`\`\`

### 2. Cargar datos al sistema:
\`\`\`bash
# Verificar estructura
python setup_gtd.py --check

# Ver estadísticas actuales
python setup_gtd.py --stats

# Cargar todos los datos
python setup_gtd.py --all --verbose

# Cargar solo items del inbox
python setup_gtd.py --step inbox --user-id $USER_ID

# Simular sin guardar (dry run)
python setup_gtd.py --all --dry-run --verbose
\`\`\`

### 3. Procesar manualmente:
1. Iniciar sesión en: \`http://tu-sitio.com/inbox/\`
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
1. Ejecutar \`./create_gtd_structure.sh\`
2. Ejecutar \`python setup_gtd.py --step categories\`
3. Ejecutar \`python setup_gtd.py --step classifications\`
4. Ejecutar \`python setup_gtd.py --step status\`

### Día 2: Datos del Inbox
1. Ejecutar \`python setup_gtd.py --step inbox\`
2. Ir a \`/inbox/\` en el navegador
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
- \`create_gtd_structure.sh\` - Crea estructura de archivos
- \`setup_gtd.py\` - Carga datos al sistema

### Comandos útiles:
\`\`\`bash
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
\`\`\`

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
3. Ejecuta con \`--verbose\` para más detalles
4. Usa \`--dry-run\` para simular sin guardar

---

**Creado automáticamente: $(date)**
**Usuario ID configurado: $USER_ID**
**Total archivos creados: $(find $BASE_DIR -name \"*.csv\" -o -name \"*.yaml\" -o -name \"*.md\" | wc -l)**
\`\`\`"

create_file "$README_FILE" "$README_CONTENT"

# ============================================================================
# 13. SCRIPT DE CARGA AUTOMÁTICA
# ============================================================================
print_header "CREANDO ARCHIVO: load_gtd.py"

LOAD_SCRIPT_FILE="$BASE_DIR/load_gtd.py"
LOAD_SCRIPT_CONTENT="# Script de carga automática para GTD
# Ejecutar: python load_gtd.py [opciones]

import subprocess
import sys
import os

def run_command(cmd):
    \"\"\"Ejecutar comando y mostrar output\"\"\"
    print(f\"\\n▶️  Ejecutando: {cmd}\")
    print(\"-\" * 50)
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    
    if result.stdout:
        print(result.stdout)
    
    if result.stderr:
        print(f\"STDERR: {result.stderr}\")
    
    return result.returncode == 0

def main():
    \"\"\"Función principal\"\"\"
    print(\"🚀 SCRIPT DE CARGA AUTOMÁTICA GTD\")
    print(\"=\" * 60)
    
    # Verificar que el script setup_gtd.py existe
    if not os.path.exists(\"setup_gtd.py\"):
        print(\"❌ Error: setup_gtd.py no encontrado\")
        print(\"   Copia setup_gtd.py a esta carpeta o ajusta la ruta\")
        return False
    
    # Opciones por defecto
    user_id = 1
    verbose = \"--verbose\"
    
    # Verificar argumentos
    if len(sys.argv) > 1:
        user_id = sys.argv[1]
    
    print(f\"👤 Usuario ID: {user_id}\")
    print(f\"📁 Carpeta base: gtd_setup\")
    
    # Ejecutar pasos en orden
    steps = [
        f\"python setup_gtd.py --step categories --user-id {user_id} {verbose}\",
        f\"python setup_gtd.py --step classifications --user-id {user_id} {verbose}\",
        f\"python setup_gtd.py --step status --user-id {user_id} {verbose}\",
        f\"python setup_gtd.py --step inbox --user-id {user_id} {verbose}\",
        f\"python setup_gtd.py --step templates --user-id {user_id} {verbose}\",
        f\"python setup_gtd.py --step settings --user-id {user_id} {verbose}\",
    ]
    
    results = []
    for step in steps:
        success = run_command(step)
        results.append(success)
    
    # Resumen
    print(\"\\n\" + \"=\" * 60)
    print(\"📊 RESUMEN DE EJECUCIÓN\")
    print(\"=\" * 60)
    
    success_count = sum(1 for r in results if r)
    total_steps = len(results)
    
    if success_count == total_steps:
        print(\"🎉 ¡TODOS LOS PASOS COMPLETADOS CON ÉXITO!\")
    else:
        print(f\"⚠️  Completados: {success_count}/{total_steps} pasos\")
    
    # Mostrar estadísticas finales
    print(\"\\n📈 ESTADÍSTICAS FINALES:\")
    run_command(f\"python setup_gtd.py --stats --user-id {user_id}\")
    
    return success_count == total_steps

if __name__ == \"__main__\":
    success = main()
    sys.exit(0 if success else 1)"

create_file "$LOAD_SCRIPT_FILE" "$LOAD_SCRIPT_CONTENT"

# ============================================================================
# 14. MAKEFILE SIMPLIFICADO
# ============================================================================
print_header "CREANDO ARCHIVO: Makefile"

MAKEFILE_FILE="$BASE_DIR/Makefile"
MAKEFILE_CONTENT="# Makefile para gestión del sistema GTD
# Uso: make [target]

.PHONY: help create check stats load step-all step-categories step-inbox clean

help:
	@echo \"🎯 TARGETS DISPONIBLES:\"
	@echo \"  make create     - Crear estructura de archivos CSV\"
	@echo \"  make check      - Verificar estructura de archivos\"
	@echo \"  make stats      - Mostrar estadísticas del sistema\"
	@echo \"  make load       - Cargar todos los datos (usuario ID 1)\"
	@echo \"  make load-user  - Cargar datos para usuario específico\"
	@echo \"  make step-all   - Ejecutar todos los pasos (dry-run)\"
	@echo \"  make step-categories - Cargar solo categorías\"
	@echo \"  make step-inbox - Cargar solo items del inbox\"
	@echo \"  make clean      - Limpiar archivos generados\"
	@echo \"\"
	@echo \"📝 EJEMPLOS:\"
	@echo \"  make create USER_ID=2\"
	@echo \"  make load-user USER_ID=2\"
	@echo \"  make step-inbox USER_ID=3 VERBOSE=--verbose\"

# Variables
USER_ID ?= 1
VERBOSE ?= 

create:
	@echo \"📁 Creando estructura de archivos...\"
	@chmod +x create_gtd_structure.sh
	@./create_gtd_structure.sh \$(USER_ID)

check:
	@echo \"🔍 Verificando archivos...\"
	@python setup_gtd.py --check

stats:
	@echo \"📊 Mostrando estadísticas...\"
	@python setup_gtd.py --stats

load: check
	@echo \"🚀 Cargando todos los datos...\"
	@python setup_gtd.py --all --user-id \$(USER_ID) \$(VERBOSE)

load-user: check
	@if [ -z \"\$(USER_ID)\" ]; then \\
		echo \"❌ Error: USER_ID no especificado\"; \\
		echo \"   Uso: make load-user USER_ID=2\"; \\
		exit 1; \\
	fi
	@echo \"👤 Cargando datos para usuario ID \$(USER_ID)...\"
	@python setup_gtd.py --all --user-id \$(USER_ID) \$(VERBOSE)

step-all: check
	@echo \"🔧 Ejecutando todos los pasos (dry-run)...\"
	@python setup_gtd.py --all --dry-run --verbose

step-categories: check
	@echo \"🏷️  Cargando categorías y tags...\"
	@python setup_gtd.py --step categories --user-id \$(USER_ID) \$(VERBOSE)

step-inbox: check
	@echo \"📥 Cargando items del inbox...\"
	@python setup_gtd.py --step inbox --user-id \$(USER_ID) \$(VERBOSE)

clean:
	@echo \"🧹 Limpiando archivos...\"
	@rm -rf __pycache__
	@rm -f *.pyc
	@echo \"✅ Limpieza completada\"

# Alias
setup: create load
full-setup: create load-user
test: step-all"

create_file "$MAKEFILE_FILE" "$MAKEFILE_CONTENT"

# ============================================================================
# LIMPIAR ARCHIVOS DE CORRECCIÓN ANTERIORES
# ============================================================================
print_header "LIMPIANDO ARCHIVOS DE CORRECCIÓN ANTERIORES"

# Eliminar archivos de corrección si existen
if [ -f "fix_inbox_csv.py" ]; then
    rm fix_inbox_csv.py
    print_success "Eliminado: fix_inbox_csv.py"
fi

if [ -f "fix_inbox_items.py" ]; then
    rm fix_inbox_items.py
    print_success "Eliminado: fix_inbox_items.py"
fi

if [ -f "load_inbox_corrected.py" ]; then
    rm load_inbox_corrected.py
    print_success "Eliminado: load_inbox_corrected.py"
fi

if [ -f "gtd_setup/02_inbox/inbox_items_corrected.csv" ]; then
    rm gtd_setup/02_inbox/inbox_items_corrected.csv
    print_success "Eliminado: inbox_items_corrected.csv"
fi

# ============================================================================
# RESUMEN FINAL
# ============================================================================
print_header "RESUMEN DE CREACIÓN"

echo -e "${GREEN}✅ ESTRUCTURA COMPLETA CREADA${NC}"
echo ""
echo "📁 CARPETAS:"
echo "  gtd_setup/01_categories/    - Categorías, tags y estados"
echo "  gtd_setup/02_inbox/         - Items de la bandeja de entrada"
echo "  gtd_setup/03_templates/     - Plantillas y eventos base"
echo "  gtd_setup/04_backups/       - Backups automáticos"
echo "  gtd_setup/05_logs/          - Logs de ejecución"
echo ""
echo "📄 ARCHIVOS CSV:"
echo "  tag_categories.csv          - 7 categorías de tags"
echo "  tags.csv                    - 47 tags específicos"
echo "  classifications.csv         - 9 clasificaciones"
echo "  status_*.csv                - 20 estados del sistema"
echo "  inbox_items.csv             - 36 items GTD (CORREGIDO)"
echo "  project_templates.csv       - 8 plantillas"
echo "  base_events.csv             - 7 eventos base"
echo ""
echo "🛠️ SCRIPTS:"
echo "  create_gtd_structure.sh     - Crea esta estructura"
echo "  setup_gtd.py                - Carga datos al sistema"
echo "  load_gtd.py                 - Carga automática"
echo "  Makefile                    - Comandos simplificados"
echo "  config.yaml                 - Configuración"
echo "  README.md                   - Documentación"
echo ""
echo "👤 USUARIO CONFIGURADO: ID $USER_ID"
echo ""
echo "✅ ARCHIVOS ELIMINADOS:"
echo "  - fix_inbox_csv.py"
echo "  - fix_inbox_items.py"
echo "  - load_inbox_corrected.py"
echo "  - inbox_items_corrected.csv"
echo ""
echo "🚀 SIGUIENTES PASOS:"
echo "  1. Dar permisos: chmod +x create_gtd_structure.sh"
echo "  2. Recrear estructura: ./create_gtd_structure.sh 2"
echo "  3. Verificar: python setup_gtd.py --check"
echo "  4. Cargar inbox: python setup_gtd.py --step inbox --user-id 2 --verbose"
echo ""
echo "📝 O usar Makefile:"
echo "  make create USER_ID=2      # Crear estructura"
echo "  make load-user USER_ID=2   # Cargar datos"
echo "  make stats                 # Ver estadísticas"
echo ""
echo "🎉 ¡LISTO PARA CONFIGURAR EL SISTEMA GTD!"

# ============================================================================
# DAR PERMISOS DE EJECUCIÓN
# ============================================================================
chmod +x "$BASE_DIR/load_gtd.py" 2>/dev/null || true
print_success "Permisos de ejecución configurados"

# Contar archivos creados
TOTAL_FILES=$(find "$BASE_DIR" -type f \( -name "*.csv" -o -name "*.py" -o -name "*.sh" -o -name "*.yaml" -o -name "*.md" -o -name "Makefile" \) | wc -l)
print_success "Total archivos creados: $TOTAL_FILES"