#!/usr/bin/env bash
# =============================================================================
# m360_map.sh  —  Mapa completo del proyecto Django M360
#
# Modos:
#   project   Mapea todo el proyecto (default sin argumentos)
#   app       Mapea una sola app en profundidad (mismo motor que app_map.sh)
#   audit     Audita residuos de URLs sin namespace en nav HTMLs
#   urls      Replica la vista url-map del sistema (core/utils.py) en consola
#
# Uso:
#   bash m360_map.sh                           → project: todo el proyecto
#   bash m360_map.sh app ./analyst             → app: análisis profundo de analyst
#   bash m360_map.sh app ./analyst --audit     → app + auditoría de nav
#   bash m360_map.sh audit ./nav/              → solo auditoría
#   bash m360_map.sh urls                      → mapa de URLs de todas las apps
#   bash m360_map.sh --help                    → esta ayuda
#
# Salida:
#   project  →  PROJECT_CONTEXT.md  (en el directorio del proyecto)
#   app      →  APPNAME_CONTEXT.md  (en el proyecto y dentro de la app)
#   urls     →  pantalla
# =============================================================================

set -euo pipefail

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
CYAN='\033[0;36m'; BOLD='\033[1m'; RESET='\033[0m'
info()    { echo -e "${CYAN}▸ $*${RESET}"; }
ok()      { echo -e "${GREEN}✔ $*${RESET}"; }
warn()    { echo -e "${YELLOW}⚠ $*${RESET}"; }
err()     { echo -e "${RED}✘ $*${RESET}"; }
section() { echo -e "\n${BOLD}$*${RESET}"; }

# ─── Argument parsing ─────────────────────────────────────────────────────────
MODE=""
APP_ARG=""
NAV_DIR=""
DO_AUDIT=false
OUT_FILE=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    project)  MODE="project"; shift ;;
    app)      MODE="app"; shift; [[ $# -gt 0 && "$1" != --* ]] && { APP_ARG="$1"; shift; } ;;
    audit)    MODE="audit"; shift; [[ $# -gt 0 && -d "$1" ]] && { NAV_DIR="$1"; shift; } ;;
    urls)     MODE="urls"; shift ;;
    --audit)  DO_AUDIT=true; shift; [[ $# -gt 0 && -d "$1" ]] && { NAV_DIR="$1"; shift; } ;;
    --out)    OUT_FILE="$2"; shift 2 ;;
    --help)
      sed -n '2,16p' "$0" | sed 's/^# \?//'; exit 0 ;;
    *)
      if [[ -d "$1" ]]; then
        APP_ARG="$1"
        [[ -z "$MODE" ]] && MODE="app"
      fi
      shift ;;
  esac
done

[[ -z "$MODE" ]] && MODE="project"

# ─── Locate project root ──────────────────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT=""
SEARCH="$SCRIPT_DIR"
for _ in 1 2 3 4; do
  if [[ -f "$SEARCH/manage.py" ]]; then PROJECT_ROOT="$SEARCH"; break; fi
  SEARCH="$(dirname "$SEARCH")"
done
if [[ -z "$PROJECT_ROOT" ]]; then
  err "No se encontró manage.py. Ejecuta desde dentro del proyecto Django."
  exit 1
fi

# ─── Identify all local apps ──────────────────────────────────────────────────
_local_apps() {
  find "$PROJECT_ROOT" -maxdepth 2 \
    -type d \
    ! -path "*/__pycache__/*" \
    ! -path "*/.git/*" \
    ! -path "*/node_modules/*" \
    ! -path "*/migrations/*" \
    ! -path "*/venv/*" \
    ! -path "*/.venv/*" \
    | while read -r d; do
        local rel="${d#$PROJECT_ROOT/}"
        [[ "$rel" == "" || "$rel" == "." ]] && continue
        [[ "$rel" == *"/"* ]] && continue
        [[ -f "$d/__init__.py" ]] || continue
        [[ -f "$d/models.py" || -f "$d/apps.py" || -f "$d/urls.py" ]] || continue
        echo "$rel"
      done | sort
}

# ─── Default nav dir ──────────────────────────────────────────────────────────
if [[ -z "$NAV_DIR" ]]; then
  CANDIDATE="$PROJECT_ROOT/templates/layouts/includes/nav-content"
  [[ -d "$CANDIDATE" ]] && NAV_DIR="$CANDIDATE"
fi

# =============================================================================
# SHARED: file categorizer
# =============================================================================
categorize() {
  local rel="${1#$2/}"
  [[ "$rel" == migrations/*     ]] && echo migrations  && return
  [[ "$rel" == tests/* || "$rel" == *test*.py ]] && echo tests && return
  [[ "$rel" == templates/* || "$rel" == *templates/* ]] && echo templates && return
  [[ "$rel" == static/*  || "$rel" == *static/*  ]] && echo static    && return
  [[ "$rel" == services/*       ]] && echo services   && return
  [[ "$rel" == utils/*          ]] && echo utils      && return
  [[ "$rel" == views/*  || "$rel" == *views*.py  ]] && echo views     && return
  [[ "$rel" == management/*     ]] && echo management && return
  [[ "$rel" == *models*.py      ]] && echo models     && return
  [[ "$rel" == *urls*.py        ]] && echo urls       && return
  [[ "$rel" == *admin*.py       ]] && echo admin      && return
  [[ "$rel" == *forms*.py       ]] && echo forms      && return
  [[ "$rel" == *.cfg || "$rel" == *.ini || "$rel" == *.toml \
  || "$rel" == *.yaml || "$rel" == *.yml ]] && echo config && return
  echo other
}

# =============================================================================
# SHARED: Python tree renderer
# =============================================================================
_render_tree() {
  local base_dir="$1"
  python3 - "$base_dir" <<'PYTREE'
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

# =============================================================================
# MODE: urls
# =============================================================================
_mode_urls() {
  section "═══ URL Map — Management360 ═════════════════════════════════"
  echo ""
  printf "${BOLD}%-35s %-50s %s${RESET}\n" "App" "Pattern" "Name/View"
  printf "%-35s %-50s %s\n" "-----------------------------------" "--------------------------------------------------" "-------------------"

  for app in $(_local_apps); do
    urls_file="$PROJECT_ROOT/$app/urls.py"
    [[ -f "$urls_file" ]] || continue
    ns=$(grep -m1 "app_name\s*=" "$urls_file" 2>/dev/null | grep -oP "'[^']+'" | tr -d "'" || echo "")
    label="${ns:-$app}"
    while IFS= read -r line; do
      pattern=$(echo "$line" | grep -oP "path\s*\(\s*['\"][^'\"]*['\"]" | grep -oP "['\"][^'\"]*['\"]" | tr -d "'\"" | head -1)
      name=$(echo "$line" | grep -oP "name=['\"][^'\"]+['\"]" | tr -d "'" | sed "s/name=//" | tr -d '"')
      view=$(echo "$line" | grep -oP ",\s*\w+\.\w+" | head -1 | tr -d ', ')
      [[ -z "$pattern" ]] && continue
      printf "%-35s %-50s %s\n" "$label" "/$app/$pattern" "${name:-$view}"
    done < <(grep -E "path\s*\(" "$urls_file" 2>/dev/null || true)
    echo ""
  done
}

# =============================================================================
# MODE: app — deep analysis of a single app
# =============================================================================
_mode_app() {
  local APP_DIR
  APP_DIR="$(realpath "${APP_ARG:-./analyst}")"
  [[ -d "$APP_DIR" ]] || { err "No se encontró: $APP_DIR"; exit 1; }

  local APP_NAME; APP_NAME="$(basename "$APP_DIR")"
  local APP_UPPER; APP_UPPER="$(echo "$APP_NAME" | tr '[:lower:]' '[:upper:]')"
  local OUT="${OUT_FILE:-${APP_UPPER}_CONTEXT.md}"
  local NOW; NOW=$(date "+%Y-%m-%d %H:%M:%S")

  section "═══ app mode: $APP_NAME ══════════════════════════════════════"
  info "App:    $APP_DIR"
  info "Salida: $OUT"

  mapfile -t ALL_FILES < <(
    find "$APP_DIR" -type f \
      \( -name "*.py" -o -name "*.html" -o -name "*.js" -o -name "*.css" \
         -o -name "*.json" -o -name "*.md" -o -name "*.sh" \
         -o -name "*.yaml" -o -name "*.yml" -o -name "*.sql" \) \
      ! -path "*/__pycache__/*" ! -path "*/.git/*" \
      ! -path "*/node_modules/*" ! -path "*/migrations/*" \
      ! -name "*.pyc" | sort
  )
  local TOTAL=${#ALL_FILES[@]}
  ok "$TOTAL archivos"

  declare -A CAT_COUNT
  for f in "${ALL_FILES[@]}"; do
    local c; c=$(categorize "$f" "$APP_DIR")
    CAT_COUNT[$c]=$((${CAT_COUNT[$c]:-0} + 1))
  done

  {
  echo "# Mapa de Contexto — App \`${APP_NAME}\`"
  echo ""
  echo "> Generado por \`m360_map.sh\`  |  $NOW"
  echo "> Ruta: \`$APP_DIR\`  |  Total archivos: **$TOTAL**"
  echo ""
  echo "---"
  echo ""
  echo "## Índice"
  echo ""
  echo "| # | Categoría | Archivos |"
  echo "|---|-----------|----------|"
  local idx=1
  for cat in views templates models forms services utils urls admin management static tests config migrations other; do
    local cnt="${CAT_COUNT[$cat]:-0}"; [[ $cnt -eq 0 ]] && continue
    local icon="📄"
    case $cat in views) icon="👁";; templates) icon="🎨";; models) icon="🗃";;
      forms) icon="📝";; services) icon="⚙️";; utils) icon="🔧";;
      urls) icon="🔗";; admin) icon="🛡";; tests) icon="🧪";;
      static) icon="📦";; migrations) icon="🔄";; esac
    echo "| $idx | $icon \`$cat\` | $cnt |"; ((idx++))
  done

  echo ""; echo "---"; echo ""; echo "## Archivos por Categoría"; echo ""
  for cat in views templates models forms services utils urls admin management static tests config migrations other; do
    local cnt="${CAT_COUNT[$cat]:-0}"; [[ $cnt -eq 0 ]] && continue
    echo ""; echo "### $(echo "$cat" | tr '[:lower:]' '[:upper:]') ($cnt archivos)"
    echo ""; echo "| Archivo | Líneas | Ruta relativa |"; echo "|---------|--------|---------------|"
    for f in "${ALL_FILES[@]}"; do
      [[ $(categorize "$f" "$APP_DIR") == "$cat" ]] || continue
      local rel="${f#$APP_DIR/}"
      local lines; lines=$(wc -l < "$f" 2>/dev/null || echo "?")
      echo "| \`$(basename "$f")\` | $lines | \`$rel\` |"
    done
  done

  echo ""; echo "---"; echo ""; echo "## Árbol de Directorios"; echo ""; echo "\`\`\`"
  if command -v tree &>/dev/null; then
    tree "$APP_DIR" --noreport -I "__pycache__|*.pyc|.git|node_modules|migrations" --dirsfirst -L 4
  else
    _render_tree "$APP_DIR"
  fi
  echo "\`\`\`"

  echo ""; echo "---"; echo ""; echo "## Endpoints registrados"; echo ""
  local URLS_F=""
  for c in "$APP_DIR/urls.py" "$APP_DIR/urls/urls.py"; do [[ -f "$c" ]] && URLS_F="$c" && break; done
  if [[ -n "$URLS_F" ]]; then
    local ns; ns=$(grep -m1 "app_name\s*=" "$URLS_F" 2>/dev/null | grep -oP "'[^']+'" | tr -d "'" || echo "")
    echo "Fuente: \`${URLS_F#$APP_DIR/}\`${ns:+  |  namespace: \`$ns\`}"; echo ""; echo "\`\`\`python"
    grep -E "path\(" "$URLS_F" | sed "s/^[[:space:]]*/  /" || true
    echo "\`\`\`"
  else echo "_No se encontró urls.py_"; fi

  echo ""; echo "---"; echo ""; echo "## Modelos detectados"; echo ""
  for mf in "$APP_DIR/models.py" "$APP_DIR/models/"*.py; do
    [[ -f "$mf" ]] || continue
    echo "**\`${mf#$APP_DIR/}\`**"; echo ""
    grep -n "^class " "$mf" | while IFS= read -r line; do
      echo "- línea $(echo "$line"|cut -d: -f1): \`$(echo "$line"|cut -d: -f2-)\`"
    done; echo ""
  done

  echo ""; echo "---"; echo ""; echo "## Migraciones"; echo ""
  echo "| Archivo | Estado |"; echo "|---------|--------|"
  if [[ -d "$APP_DIR/migrations" ]]; then
    find "$APP_DIR/migrations" -name "*.py" ! -name "__init__.py" | sort | while read -r mf; do
      echo "| \`$(basename "$mf" .py)\` | aplicada |"
    done
  else echo "_Sin migrations/_"; fi

  echo ""; echo "---"; echo ""; echo "## Funciones clave (views/ y services/)"; echo ""
  for dir_p in "views" "services"; do
    for pyf in "$APP_DIR/$dir_p"/*.py; do
      [[ -f "$pyf" ]] || continue
      local rel="${pyf#$APP_DIR/}"
      local funcs; funcs=$(grep -n "^def \|^    def " "$pyf" 2>/dev/null | grep -v "__\b" | head -25 || true)
      [[ -z "$funcs" ]] && continue
      echo "**\`$rel\`**"; echo ""; echo "\`\`\`"; echo "$funcs"; echo "\`\`\`"; echo ""
    done
  done
  for pyf in "$APP_DIR/views/"*/*.py; do
    [[ -f "$pyf" ]] || continue
    local rel="${pyf#$APP_DIR/}"
    local funcs; funcs=$(grep -n "^def \|^    def " "$pyf" 2>/dev/null | grep -v "__\b" | head -25 || true)
    [[ -z "$funcs" ]] && continue
    echo "**\`$rel\`**"; echo ""; echo "\`\`\`"; echo "$funcs"; echo "\`\`\`"; echo ""
  done

  local RPT="$APP_DIR/report_functions.py"
  if [[ -f "$RPT" ]]; then
    echo ""; echo "---"; echo ""; echo "## Funciones registradas (report_functions.py)"; echo ""
    echo "| key | label | category |"; echo "|-----|-------|----------|"
    python3 - "$RPT" <<'PYEOF'
import sys, re
with open(sys.argv[1]) as f: content = f.read()
for m in re.finditer(r'@register\s*\((.*?)\)\s*def\s+\w+', content, re.DOTALL):
    b = m.group(1)
    key   = re.search(r'key\s*=\s*["\']([^"\']+)', b)
    label = re.search(r'label\s*=\s*["\']([^"\']+)', b)
    cat   = re.search(r'category\s*=\s*["\']([^"\']+)', b)
    print(f"| `{key.group(1) if key else '?'}` | {label.group(1) if label else '?'} | {cat.group(1) if cat else 'General'} |")
PYEOF
  fi

  cat <<FOOT

---

## Compartir con Claude

\`\`\`bash
cat $APP_DIR/views/mi_vista.py | termux-clipboard-set
\`\`\`
FOOT

  } > "$OUT"
  ok "Mapa generado: $OUT"

  cp "$OUT" "$APP_DIR/$OUT"
  ok "Copia en: $APP_DIR/$OUT"
}

# =============================================================================
# MODE: project — full project overview
# =============================================================================
_mode_project() {
  local NOW; NOW=$(date "+%Y-%m-%d %H:%M:%S")
  local OUT="${OUT_FILE:-PROJECT_CONTEXT.md}"
  local FULL_OUT="$PROJECT_ROOT/docs/$OUT"

  section "═══ project mode: Management360 ════════════════════════════"
  info "Raíz:   $PROJECT_ROOT"
  info "Salida: $FULL_OUT"

  mapfile -t APPS < <(_local_apps)
  info "Apps detectadas: ${#APPS[@]} — ${APPS[*]}"

  local TOTAL_FILES=0
  declare -A APP_FILES APP_LINES APP_MODELS APP_URLS APP_NS

  for app in "${APPS[@]}"; do
    local app_dir="$PROJECT_ROOT/$app"
    local count; count=$(find "$app_dir" -type f \( -name "*.py" -o -name "*.html" \) \
      ! -path "*/__pycache__/*" ! -path "*/migrations/*" 2>/dev/null | wc -l)
    APP_FILES[$app]=$count
    TOTAL_FILES=$((TOTAL_FILES + count))

    local models_f="$app_dir/models.py"
    APP_MODELS[$app]=0
    if [[ -f "$models_f" ]]; then
      APP_MODELS[$app]=$(grep -c "^class " "$models_f" 2>/dev/null || echo 0)
      APP_MODELS[$app]=$(echo "${APP_MODELS[$app]}" | tr -d '[:space:]')
    fi

    local urls_f="$app_dir/urls.py"
    APP_URLS[$app]=0
    APP_NS[$app]=""
    if [[ -f "$urls_f" ]]; then
      local raw_urls; raw_urls=$(grep -c "path(" "$urls_f" 2>/dev/null || echo 0)
      APP_URLS[$app]=$(echo "${raw_urls:-0}" | tr -d "[:space:]")
      APP_NS[$app]=$(grep -m1 "app_name" "$urls_f" 2>/dev/null | grep -oP "=\s*'[^']+'" | tr -d "= '" || echo "")
    fi
  done

  {
  cat <<HEADER
# Mapa del Proyecto — Management360

> Generado por \`m360_map.sh\`  |  $NOW
> Raíz: \`$PROJECT_ROOT\`
> Apps: **${#APPS[@]}**  |  Archivos Python+HTML: **$TOTAL_FILES**

---

## Resumen por app

| App | Namespace | Archivos | Modelos | Endpoints | Notas |
|-----|-----------|----------|---------|-----------|-------|
HEADER

  for app in "${APPS[@]}"; do
    local note=""
    [[ "$app" == "analyst"   ]] && note="Plataforma de datos (5 fases, SIM-4 integrado)"
    [[ "$app" == "sim"       ]] && note="Simulador WFM — SIM-1→SIM-7a completo (ACD multi-agente)"
    [[ "$app" == "core"      ]] && note="Dashboard, URL-map, Home"
    [[ "$app" == "events"    ]] && note="Eventos, Proyectos, Tareas (app principal)"
    [[ "$app" == "kpis"      ]] && note="KPIs, AHT Dashboard, CallRecord"
    [[ "$app" == "accounts"  ]] && note="Autenticacion, Perfiles, CV"
    [[ "$app" == "chat"      ]] && note="Chat en tiempo real, rooms, mensajes"
    [[ "$app" == "rooms"     ]] && note="Salas virtuales, channels"
    [[ "$app" == "bitacora"  ]] && note="Bitacora personal GTD"
    [[ "$app" == "courses"   ]] && note="Cursos, lecciones, curriculum"
    [[ "$app" == "cv"        ]] && note="Curriculum Vitae dinamico"
    [[ "$app" == "board"     ]] && note="Kanban board"
    [[ "$app" == "bots"      ]] && note="Automatizaciones, bots"
    [[ "$app" == "campaigns" ]] && note="Campanas, outreach"
    [[ "$app" == "help"      ]] && note="Centro de ayuda, tickets"
    [[ "$app" == "memento"   ]] && note="Recordatorios, memoria personal"
    [[ "$app" == "panel"     ]] && note="Panel de configuracion del proyecto"
    [[ "$app" == "passgen"   ]] && note="Generador de contrasenas"
    [[ "$app" == "api"       ]] && note="API REST publica"
    local ns="${APP_NS[$app]:-—}"
    echo "| \`$app\` | \`$ns\` | ${APP_FILES[$app]} | ${APP_MODELS[$app]} | ${APP_URLS[$app]} | $note |"
  done

  echo ""
  echo "---"
  echo ""
  echo "## Árbol del Proyecto (nivel 1)"
  echo ""
  echo "\`\`\`"
  python3 - "$PROJECT_ROOT" <<'PYTREE1'
import os, sys
root = sys.argv[1]
SKIP = {'__pycache__', '.git', 'node_modules', 'venv', '.venv', 'static', 'media', 'logs'}
print(os.path.basename(root) + '/')
entries = sorted(os.listdir(root))
dirs  = [e for e in entries if os.path.isdir(os.path.join(root, e)) and e not in SKIP]
files = [e for e in entries if os.path.isfile(os.path.join(root, e))
         and os.path.splitext(e)[1] in ('.py', '.sh', '.md', '.cfg', '.env')]
items = dirs + files
for i, item in enumerate(items):
    connector = '└── ' if i == len(items)-1 else '├── '
    full = os.path.join(root, item)
    suffix = '/' if os.path.isdir(full) else ''
    print('    ' + connector + item + suffix)
PYTREE1
  echo "\`\`\`"

  echo ""
  echo "---"
  echo ""
  echo "## URLs por app"
  echo ""
  echo "> Equivalente a la vista \`/url-map/\` del sistema (core/utils.py::get_all_apps_url_structure)"
  echo ""

  for app in "${APPS[@]}"; do
    local urls_f="$PROJECT_ROOT/$app/urls.py"
    [[ -f "$urls_f" ]] || continue
    local ns="${APP_NS[$app]:-$app}"
    echo "### \`$app\` — namespace: \`$ns\`"
    echo ""
    echo "| Pattern | Name |"
    echo "|---------|------|"
    grep -E "path\s*\(" "$urls_f" 2>/dev/null | while IFS= read -r line; do
      local pattern; pattern=$(echo "$line" | grep -oP "path\s*\(\s*['\"][^'\"]*['\"]" | grep -oP "['\"][^'\"]*['\"]" | tr -d "'\"" | head -1)
      local name; name=$(echo "$line" | grep -oP "name=['\"][^'\"]+['\"]" | tr -d "'" | sed "s/name=//" | tr -d '"')
      [[ -z "$pattern" ]] && continue
      echo "| \`/$app/$pattern\` | \`${name:-—}\` |"
    done || true
    echo ""
  done

  echo "---"
  echo ""
  echo "## Modelos por app"
  echo ""
  for app in "${APPS[@]}"; do
    local models_f="$PROJECT_ROOT/$app/models.py"
    [[ -f "$models_f" ]] || continue
    local classes; classes=$(grep "^class " "$models_f" 2>/dev/null | grep -v "Admin\|Config\|Form" || true)
    [[ -z "$classes" ]] && continue
    echo "### \`$app\`"
    echo ""
    grep -n "^class " "$models_f" 2>/dev/null | while IFS= read -r line; do
      echo "- L$(echo "$line"|cut -d: -f1): \`$(echo "$line"|cut -d: -f2-|xargs)\`"
    done || true
    echo ""
  done

  echo "---"
  echo ""
  echo "## Integración con url-map del sistema"
  echo ""
  echo "La vista \`/url-map/\` en el servidor usa \`core/utils.py::get_all_apps_url_structure()\`"
  echo "que parsea todos los \`urls.py\` del proyecto. Este archivo es su equivalente estático."
  echo ""
  echo "\`\`\`"
  echo "GET /url-map/                      → vista HTML de todas las apps"
  echo "GET /url-map/?app_name=analyst     → detalle de una app"
  echo "\`\`\`"

  cat <<FOOT

---

## Comandos útiles

\`\`\`bash
# Análisis profundo de una app específica:
bash scripts/m360_map.sh app ./analyst
bash scripts/m360_map.sh app ./sim

# Auditoría de residuos en nav:
bash scripts/m360_map.sh app ./analyst --audit

# Mapa de URLs en consola:
bash scripts/m360_map.sh urls

# Regenerar este archivo:
bash scripts/m360_map.sh
\`\`\`
FOOT

  } > "$FULL_OUT"

  ok "Proyecto mapeado: $FULL_OUT"
}

# =============================================================================
# MODE: audit
# =============================================================================
_mode_audit() {
  local APP_DIR=""
  [[ -n "$APP_ARG" ]] && APP_DIR="$(realpath "$APP_ARG")" || APP_DIR="$PROJECT_ROOT/analyst"
  local URLS_F="$APP_DIR/urls.py"
  [[ -f "$URLS_F" ]] || { warn "No se encontró $URLS_F"; exit 0; }

  [[ -d "$NAV_DIR" ]] || { warn "No se encontró nav dir. Usa: bash m360_map.sh audit /ruta/nav/"; exit 0; }

  local APP_NS; APP_NS=$(grep -m1 "app_name\s*=" "$URLS_F" | grep -oP "'[^']+'" | tr -d "'" 2>/dev/null || echo "")
  mapfile -t APP_URLS < <(grep -oP "name='[^']+'" "$URLS_F" | tr -d "'" | sed "s/^name=//" | sort -u)
  mapfile -t NAV_FILES < <(find "$NAV_DIR" -name "*.html" | sort)

  section "▸ Auditoría nav — app: $(basename "$APP_DIR") (ns: ${APP_NS:-none})"
  echo ""

  local RESIDUE=0 CORRECT=0 EMPTY=0 OTHER=0

  printf "${BOLD}%-30s %-32s %-14s %s${RESET}\n" "Nav file" "URL name" "Estado" "Línea"
  printf "%-30s %-32s %-14s %s\n" "------------------------------" "--------------------------------" "--------------" "----"

  for nav_file in "${NAV_FILES[@]}"; do
    local nav_name; nav_name=$(basename "$nav_file")
    local url_refs; url_refs=$(grep -noP "url\s+'[^']+'" "$nav_file" 2>/dev/null || true)
    if [[ -z "$url_refs" ]]; then
      printf "%-30s %-32s ${CYAN}%-14s${RESET}\n" "$nav_name" "(sin urls)" "vacío"
      ((EMPTY++)); continue
    fi
    while IFS= read -r ref; do
      [[ -z "$ref" ]] && continue
      local line_num; line_num=$(echo "$ref" | cut -d: -f1)
      local url_raw; url_raw=$(echo "$ref" | grep -oP "url\s+'[^']+'" | grep -oP "'[^']+'" | tr -d "'")
      local has_ns=false ns_part="" bare="$url_raw"
      [[ "$url_raw" == *:* ]] && has_ns=true && ns_part="${url_raw%%:*}" && bare="${url_raw##*:}"
      local is_app_url=false
      for au in "${APP_URLS[@]}"; do [[ "$au" == "$bare" ]] && is_app_url=true && break; done
      if [[ "$is_app_url" == false ]]; then
        printf "%-30s %-32s ${YELLOW}%-14s${RESET} L%s\n" "$nav_name" "$url_raw" "otra app" "$line_num"
        ((OTHER++))
      elif [[ "$has_ns" == true && "$ns_part" == "$APP_NS" ]]; then
        printf "%-30s %-32s ${GREEN}%-14s${RESET} L%s\n" "$nav_name" "$url_raw" "OK (ns)" "$line_num"
        ((CORRECT++))
      elif [[ "$has_ns" == false ]]; then
        printf "%-30s %-32s ${RED}%-14s${RESET} L%s\n" "$nav_name" "$url_raw" "RESIDUO" "$line_num"
        ((RESIDUE++))
      else
        printf "%-30s %-32s ${CYAN}%-14s${RESET} L%s\n" "$nav_name" "$url_raw" "ns: $ns_part" "$line_num"
        ((CORRECT++))
      fi
    done <<< "$url_refs"
  done

  echo ""
  echo "──────────────────────────────────────────────────────────"
  echo -e "  ${RED}Residuos:${RESET}   $RESIDUE  |  ${GREEN}Correctos:${RESET} $CORRECT  |  ${YELLOW}Otras apps:${RESET} $OTHER  |  ${CYAN}Vacíos:${RESET} $EMPTY"
  [[ $RESIDUE -eq 0 ]] && ok "Sin residuos." || warn "$RESIDUE referencias sin namespace '${APP_NS}:'"
}

# =============================================================================
# DISPATCH
# =============================================================================
section "═══ m360_map.sh ═════════════════════════════════════════════"
info "Modo: $MODE  |  Raíz: ${PROJECT_ROOT}"

case "$MODE" in
  project) _mode_project ;;
  app)     _mode_app; [[ "$DO_AUDIT" == true ]] && _mode_audit ;;
  audit)   _mode_audit ;;
  urls)    _mode_urls ;;
  *)       err "Modo desconocido: $MODE"; exit 1 ;;
esac

echo ""
section "▸ Uso rápido"
echo "  bash scripts/m360_map.sh                        # todo el proyecto"
echo "  bash scripts/m360_map.sh app ./analyst          # app profunda"
echo "  bash scripts/m360_map.sh app ./sim              # app profunda"
echo "  bash scripts/m360_map.sh app ./analyst --audit  # app + auditoría nav"
echo "  bash scripts/m360_map.sh urls                   # mapa de URLs"
echo ""
ok "¡Listo!"
