# Makefile para gestión del sistema GTD
# Uso: make [target]

.PHONY: help create check stats load step-all step-categories step-inbox clean

help:
	@echo "🎯 TARGETS DISPONIBLES:"
	@echo "  make create     - Crear estructura de archivos CSV"
	@echo "  make check      - Verificar estructura de archivos"
	@echo "  make stats      - Mostrar estadísticas del sistema"
	@echo "  make load       - Cargar todos los datos (usuario ID 1)"
	@echo "  make load-user  - Cargar datos para usuario específico"
	@echo "  make step-all   - Ejecutar todos los pasos (dry-run)"
	@echo "  make step-categories - Cargar solo categorías"
	@echo "  make step-inbox - Cargar solo items del inbox"
	@echo "  make clean      - Limpiar archivos generados"
	@echo ""
	@echo "📝 EJEMPLOS:"
	@echo "  make create USER_ID=2"
	@echo "  make load-user USER_ID=2"
	@echo "  make step-inbox USER_ID=3 VERBOSE=--verbose"

# Variables
USER_ID ?= 1
VERBOSE ?= 

create:
	@echo "📁 Creando estructura de archivos..."
	@chmod +x create_gtd_structure.sh
	@./create_gtd_structure.sh $(USER_ID)

check:
	@echo "🔍 Verificando archivos..."
	@python setup_gtd.py --check

stats:
	@echo "📊 Mostrando estadísticas..."
	@python setup_gtd.py --stats

load: check
	@echo "🚀 Cargando todos los datos..."
	@python setup_gtd.py --all --user-id $(USER_ID) $(VERBOSE)

load-user: check
	@if [ -z "$(USER_ID)" ]; then \
		echo "❌ Error: USER_ID no especificado"; \
		echo "   Uso: make load-user USER_ID=2"; \
		exit 1; \
	fi
	@echo "👤 Cargando datos para usuario ID $(USER_ID)..."
	@python setup_gtd.py --all --user-id $(USER_ID) $(VERBOSE)

step-all: check
	@echo "🔧 Ejecutando todos los pasos (dry-run)..."
	@python setup_gtd.py --all --dry-run --verbose

step-categories: check
	@echo "🏷️  Cargando categorías y tags..."
	@python setup_gtd.py --step categories --user-id $(USER_ID) $(VERBOSE)

step-inbox: check
	@echo "📥 Cargando items del inbox..."
	@python setup_gtd.py --step inbox --user-id $(USER_ID) $(VERBOSE)

clean:
	@echo "🧹 Limpiando archivos..."
	@rm -rf __pycache__
	@rm -f *.pyc
	@echo "✅ Limpieza completada"

# Alias
setup: create load
full-setup: create load-user
test: step-all
