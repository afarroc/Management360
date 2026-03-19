#!/usr/bin/env bash
# =============================================================================
# map_lib.sh - Funciones compartidas para scripts de mapeo de Management360
# =============================================================================

# Colores para output
export RED='\033[0;31m'
export GREEN='\033[0;32m'
export YELLOW='\033[1;33m'
export CYAN='\033[0;36m'
export BOLD='\033[1m'
export RESET='\033[0m'

# Funciones de logging
info()    { echo -e "${CYAN}▸ $*${RESET}"; }
ok()      { echo -e "${GREEN}✔ $*${RESET}"; }
warn()    { echo -e "${YELLOW}⚠ $*${RESET}"; }
err()     { echo -e "${RED}✘ $*${RESET}"; }
section() { echo -e "\n${BOLD}$*${RESET}"; }

# =============================================================================
# Detectar raíz del proyecto Django
# =============================================================================
find_project_root() {
    local script_dir="$1"
    local search="$script_dir"
    
    for _ in 1 2 3 4; do
        if [[ -f "$search/manage.py" ]]; then
            echo "$search"
            return 0
        fi
        search="$(dirname "$search")"
    done
    
    return 1
}

# =============================================================================
# Categorización de archivos Django
# =============================================================================
categorize_file() {
    local file="$1"
    local base_dir="$2"
    local rel="${file#$base_dir/}"
    
    [[ "$rel" == migrations/*     ]] && echo "migrations" && return
    [[ "$rel" == tests/* || "$rel" == *test*.py ]] && echo "tests" && return
    [[ "$rel" == templates/* || "$rel" == *templates/* ]] && echo "templates" && return
    [[ "$rel" == static/*  || "$rel" == *static/*  ]] && echo "static" && return
    [[ "$rel" == services/*       ]] && echo "services" && return
    [[ "$rel" == utils/*          ]] && echo "utils" && return
    [[ "$rel" == views/*  || "$rel" == *views*.py  ]] && echo "views" && return
    [[ "$rel" == management/*     ]] && echo "management" && return
    [[ "$rel" == *models*.py      ]] && echo "models" && return
    [[ "$rel" == *urls*.py        ]] && echo "urls" && return
    [[ "$rel" == *admin*.py       ]] && echo "admin" && return
    [[ "$rel" == *forms*.py       ]] && echo "forms" && return
    echo "other"
}

# =============================================================================
# Listar todas las apps Django del proyecto
# =============================================================================
list_django_apps() {
    local project_root="$1"
    
    find "$project_root" -maxdepth 2 \
        -type d \
        ! -path "*/__pycache__/*" \
        ! -path "*/.git/*" \
        ! -path "*/node_modules/*" \
        ! -path "*/migrations/*" \
        ! -path "*/venv/*" \
        ! -path "*/.venv/*" \
        | while read -r d; do
            local rel="${d#$project_root/}"
            [[ "$rel" == "" || "$rel" == "." ]] && continue
            [[ "$rel" == *"/"* ]] && continue
            if [[ -f "$d/__init__.py" ]] && { [[ -f "$d/models.py" ]] || [[ -f "$d/apps.py" ]] || [[ -f "$d/urls.py" ]]; }; then
                echo "$rel"
            fi
        done | sort
}

# =============================================================================
# Obtener namespace de una app
# =============================================================================
get_app_namespace() {
    local app_dir="$1"
    local urls_file="$app_dir/urls.py"
    
    if [[ -f "$urls_file" ]]; then
        grep -m1 "app_name\s*=" "$urls_file" 2>/dev/null | grep -oP "'[^']+'" | tr -d "'" || echo ""
    fi
}

# =============================================================================
# Renderizar árbol de directorios (fallback cuando tree no está disponible)
# =============================================================================
render_tree() {
    local base_dir="$1"
    
    python3 - "$base_dir" << 'PYTREE'
import os, sys
root = sys.argv[1]
SKIP = {'__pycache__', '.git', 'node_modules', 'migrations', 'venv', '.venv'}
EXT  = {'.py', '.html', '.js', '.css', '.md', '.sh', '.json', '.sql', '.yaml', '.yml'}

def _tree(path, prefix=''):
    try: entries = sorted(os.listdir(path))
    except PermissionError: return
    dirs  = [e for e in entries if os.path.isdir(os.path.join(path, e)) and e not in SKIP]
    files = [e for e in entries if os.path.isfile(os.path.join(path, e))
             and os.path.splitext(e)[1] in EXT and not e.endswith('.pyc')]
    items = dirs + files
    for i, item in enumerate(items):
        connector = '└── ' if i == len(items)-1 else '├── '
        full = os.path.join(path, item)
        print(prefix + connector + item)
        if os.path.isdir(full):
            extension = '    ' if i == len(items)-1 else '│   '
            _tree(full, prefix + extension)

print(os.path.basename(root) + '/')
_tree(root)
PYTREE
}

# Exportar funciones (opcional, pero útil)
export -f info ok warn err section
export -f find_project_root categorize_file list_django_apps get_app_namespace render_tree
