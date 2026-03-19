#!/usr/bin/env bash
# =============================================================================
# app_map.sh  —  Mapa completo de una app Django + auditoría de residuos nav
#
# Uso:
#   bash app_map.sh [opciones] [ruta_app]
#
# Opciones:
#   --audit [ruta_nav]   Audita nav HTMLs buscando URLs sin namespace.
#                        ruta_nav por defecto: ../templates/layouts/includes/nav-content/
#   --out <archivo>      Archivo de salida  (default: APPNAME_CONTEXT.md)
#   --no-map             Solo auditoría, sin generar el mapa
#   --help               Esta ayuda
#
# Ejemplos:
#   bash app_map.sh                             → mapea ./analyst
#   bash app_map.sh ./crm                       → mapea ./crm → CRM_CONTEXT.md
#   bash app_map.sh --audit                     → mapea + audita nav (ruta default)
#   bash app_map.sh --audit ./nav/ ./crm        → mapea crm + audita ./nav/
#   bash app_map.sh --no-map --audit ./nav/     → solo auditoría
# =============================================================================

set -euo pipefail

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
CYAN='\033[0;36m'; BOLD='\033[1m'; RESET='\033[0m'
info()    { echo -e "${CYAN}▸ $*${RESET}"; }
ok()      { echo -e "${GREEN}✔ $*${RESET}"; }
warn()    { echo -e "${YELLOW}⚠ $*${RESET}"; }
err()     { echo -e "${RED}✘ $*${RESET}"; }
section() { echo -e "\n${BOLD}$*${RESET}"; }

# ── Parsear argumentos ────────────────────────────────────────────────────────
DO_AUDIT=false
DO_MAP=true
NAV_DIR=""
OUT_FILE=""
APP_DIR=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --audit)
      DO_AUDIT=true; shift
      if [[ $# -gt 0 && ("$1" == .* || "$1" == /*) ]]; then
        if [[ -d "$1" ]]; then NAV_DIR="$1"; shift; fi
      fi ;;
    --no-map)  DO_MAP=false;   shift ;;
    --out)     OUT_FILE="$2";  shift 2 ;;
    --help)    sed -n '2,18p' "$0" | sed 's/^# \?//'; exit 0 ;;
    *)         APP_DIR="$1";   shift ;;
  esac
done

APP_DIR="$(realpath "${APP_DIR:-./analyst}")"
[[ -d "$APP_DIR" ]] || { err "No se encontró: $APP_DIR"; exit 1; }

APP_NAME="$(basename "$APP_DIR")"
APP_UPPER="$(echo "$APP_NAME" | tr '[:lower:]' '[:upper:]')"
OUT_FILE="${OUT_FILE:-${APP_UPPER}_CONTEXT.md}"

# Nav dir default: <project_root>/templates/layouts/includes/nav-content
if [[ -z "$NAV_DIR" ]]; then
  CANDIDATE="$(dirname "$APP_DIR")/templates/layouts/includes/nav-content"
  [[ -d "$CANDIDATE" ]] && NAV_DIR="$CANDIDATE" || NAV_DIR=""
fi

section "═══ app_map.sh ══════════════════════════════════════════════"
info "App:    $APP_DIR"
[[ "$DO_MAP"   == true ]] && info "Salida: $OUT_FILE"
[[ "$DO_AUDIT" == true ]] && info "Nav:    ${NAV_DIR:-'(no encontrado, usa --audit /ruta/)'}"

# ── Recolectar archivos ───────────────────────────────────────────────────────
section "▸ Escaneando..."
mapfile -t ALL_FILES < <(
  find "$APP_DIR" -type f \
    \( -name "*.py" -o -name "*.html" -o -name "*.js" -o -name "*.css" \
       -o -name "*.json" -o -name "*.md" -o -name "*.sh" \
       -o -name "*.yaml" -o -name "*.yml" -o -name "*.sql" \) \
    ! -path "*/__pycache__/*" ! -path "*/.git/*" \
    ! -path "*/node_modules/*" ! -path "*/migrations/*" \
    ! -name "*.pyc" | sort
)
TOTAL=${#ALL_FILES[@]}
ok "$TOTAL archivos encontrados"

categorize() {
  local rel="${1#$APP_DIR/}"
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

declare -A CAT_COUNT
for f in "${ALL_FILES[@]}"; do
  c=$(categorize "$f")
  CAT_COUNT[$c]=$((${CAT_COUNT[$c]:-0} + 1))
done

# =============================================================================
# MAPA COMPLETO
# =============================================================================
if [[ "$DO_MAP" == true ]]; then
  section "▸ Generando $OUT_FILE..."
  NOW=$(date "+%Y-%m-%d %H:%M:%S")

  {
  # Header
  echo "# Mapa de Contexto — App \`${APP_NAME}\`"
  echo ""
  echo "> Generado por \`app_map.sh\`  |  $NOW"
  echo "> Ruta: \`$APP_DIR\`  |  Total archivos: **$TOTAL**"
  echo ""
  echo "---"
  echo ""
  echo "## Índice"
  echo ""
  echo "| # | Categoría | Archivos |"
  echo "|---|-----------|----------|"
  idx=1
  for cat in views templates models forms services utils urls admin management static tests config migrations other; do
    cnt="${CAT_COUNT[$cat]:-0}"; [[ $cnt -eq 0 ]] && continue
    icon="📄"
    case $cat in
      views)      icon="👁"  ;; templates)  icon="🎨" ;;
      models)     icon="🗃"  ;; forms)      icon="📝" ;;
      services)   icon="⚙️"  ;; utils)      icon="🔧" ;;
      urls)       icon="🔗"  ;; admin)      icon="🛡"  ;;
      tests)      icon="🧪"  ;; static)     icon="📦" ;;
      migrations) icon="🔄"  ;;
    esac
    echo "| $idx | $icon \`$cat\` | $cnt |"; ((idx++))
  done

  # Archivos por categoría
  echo ""; echo "---"; echo ""
  echo "## Archivos por Categoría"; echo ""
  for cat in views templates models forms services utils urls admin management static tests config migrations other; do
    cnt="${CAT_COUNT[$cat]:-0}"; [[ $cnt -eq 0 ]] && continue
    echo ""
    echo "### $(echo "$cat" | tr '[:lower:]' '[:upper:]') ($cnt archivos)"
    echo ""
    echo "| Archivo | Líneas | Ruta relativa |"
    echo "|---------|--------|---------------|"
    for f in "${ALL_FILES[@]}"; do
      [[ $(categorize "$f") == "$cat" ]] || continue
      rel="${f#$APP_DIR/}"
      lines=$(wc -l < "$f" 2>/dev/null || echo "?")
      echo "| \`$(basename "$f")\` | $lines | \`$rel\` |"
    done
  done

  # Árbol
  echo ""; echo "---"; echo ""; echo "## Árbol de Directorios"; echo ""; echo "\`\`\`"
  if command -v tree &>/dev/null; then
    tree "$APP_DIR" --noreport -I "__pycache__|*.pyc|.git|node_modules" --dirsfirst -L 4
  else
    # Pure bash fallback — construye árbol con dirs y archivos correctamente indentados
    python3 - "$APP_DIR" <<'PYTREE'
import os, sys
root = sys.argv[1]
SKIP = {'__pycache__', '.git', 'node_modules', 'migrations'}
EXT  = {'.py', '.html', '.js', '.css', '.md', '.sh', '.json', '.sql', '.yaml', '.yml'}

def _tree(path, prefix=''):
    entries = sorted(os.listdir(path))
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
  fi
  echo "\`\`\`"

  # Endpoints
  echo ""; echo "---"; echo ""; echo "## Endpoints registrados"; echo ""
  URLS_F=""; for c in "$APP_DIR/urls.py" "$APP_DIR/urls/urls.py"; do [[ -f "$c" ]] && URLS_F="$c" && break; done
  if [[ -n "$URLS_F" ]]; then
    echo "Fuente: \`${URLS_F#$APP_DIR/}\`"; echo ""; echo "\`\`\`python"
    grep -E "path\(" "$URLS_F" | sed "s/^[[:space:]]*/  /" || true
    echo "\`\`\`"
  else echo "_No se encontró urls.py_"; fi

  # Modelos
  echo ""; echo "---"; echo ""; echo "## Modelos detectados"; echo ""
  for mf in "$APP_DIR/models.py" "$APP_DIR/models/"*.py; do
    [[ -f "$mf" ]] || continue
    echo "**\`${mf#$APP_DIR/}\`**"; echo ""
    grep -n "^class " "$mf" | while IFS= read -r line; do
      echo "- línea $(echo "$line"|cut -d: -f1): \`$(echo "$line"|cut -d: -f2-)\`"
    done; echo ""
  done

  # Migraciones
  echo ""; echo "---"; echo ""; echo "## Migraciones"; echo ""
  echo "| Archivo | Estado |"; echo "|---------|--------|"
  if [[ -d "$APP_DIR/migrations" ]]; then
    find "$APP_DIR/migrations" -name "*.py" ! -name "__init__.py" | sort | while read -r mf; do
      echo "| \`$(basename "$mf" .py)\` | aplicada |"
    done
  else echo "_Sin migrations/_"; fi

  # Funciones clave
  echo ""; echo "---"; echo ""; echo "## Funciones clave (views/ y services/)"; echo ""
  for dir_p in "views" "services"; do
    for pyf in "$APP_DIR/$dir_p"/*.py "$APP_DIR/$dir_p"/*/. ; do
      [[ -f "$pyf" ]] || continue
      rel="${pyf#$APP_DIR/}"
      funcs=$(grep -n "^def \|^    def " "$pyf" 2>/dev/null | grep -v "__\b" | head -25 || true)
      [[ -z "$funcs" ]] && continue
      echo "**\`$rel\`**"; echo ""; echo "\`\`\`"; echo "$funcs"; echo "\`\`\`"; echo ""
    done
  done
  # Also scan subpackages
  for pyf in "$APP_DIR/views/"*/*.py; do
    [[ -f "$pyf" ]] || continue
    rel="${pyf#$APP_DIR/}"
    funcs=$(grep -n "^def \|^    def " "$pyf" 2>/dev/null | grep -v "__\b" | head -25 || true)
    [[ -z "$funcs" ]] && continue
    echo "**\`$rel\`**"; echo ""; echo "\`\`\`"; echo "$funcs"; echo "\`\`\`"; echo ""
  done

  # report_functions.py
  RPT="$APP_DIR/report_functions.py"
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

  # Footer
  cat <<FOOT

---

## Compartir archivos con Claude

\`\`\`bash
ls -1 $APP_DIR/views/*.py
ls -1 $APP_DIR/services/*.py 2>/dev/null
cat $APP_DIR/views/mi_vista.py | termux-clipboard-set
\`\`\`
FOOT

  } > "$OUT_FILE"
  ok "Mapa generado: $OUT_FILE"
  # Keep a copy inside the app directory itself for future reference
  cp "$OUT_FILE" "$APP_DIR/$OUT_FILE"
  ok "Copia guardada en: $APP_DIR/$OUT_FILE"
fi

# =============================================================================
# AUDITORÍA — residuos en nav HTMLs
# =============================================================================
if [[ "$DO_AUDIT" == true ]]; then
  section "▸ Auditoría de residuos en nav HTMLs..."

  if [[ -z "$NAV_DIR" || ! -d "$NAV_DIR" ]]; then
    warn "No se encontró directorio de nav."
    warn "Especifica la ruta: bash app_map.sh --audit /ruta/nav-content/ ./app"
    exit 0
  fi

  URLS_F="$APP_DIR/urls.py"
  [[ -f "$URLS_F" ]] || { warn "No se encontró urls.py en $APP_DIR"; exit 0; }

  # Namespace de la app
  APP_NS=$(grep -m1 "app_name\s*=" "$URLS_F" | grep -oP "'[^']+'" | tr -d "'" 2>/dev/null || echo "")
  info "Namespace: ${APP_NS:-'(sin namespace)'}"

  # URL names registradas en esta app
  mapfile -t APP_URLS < <(
    grep -oP "name='[^']+'" "$URLS_F" | tr -d "'" | sed "s/^name=//" | sort -u
  )
  info "URLs en la app: ${#APP_URLS[@]}"

  mapfile -t NAV_FILES < <(find "$NAV_DIR" -name "*.html" | sort)
  info "Nav files: ${#NAV_FILES[@]}"
  echo ""

  RESIDUE=0; CORRECT=0; EMPTY=0; OTHER=0

  # Header tabla
  printf "${BOLD}%-30s %-32s %-14s %s${RESET}\n" "Nav file" "URL name" "Estado" "Línea"
  printf "%-30s %-32s %-14s %s\n" \
    "------------------------------" "--------------------------------" "--------------" "----"

  for nav_file in "${NAV_FILES[@]}"; do
    nav_name=$(basename "$nav_file")
    # Extract all {% url '...' %} references with line numbers
    url_refs=$(grep -noP "url\s+'[^']+'" "$nav_file" 2>/dev/null || true)

    if [[ -z "$url_refs" ]]; then
      printf "%-30s %-32s ${CYAN}%-14s${RESET}\n" "$nav_name" "(sin urls)" "vacío"
      ((EMPTY++)); continue
    fi

    while IFS= read -r ref; do
      [[ -z "$ref" ]] && continue
      line_num=$(echo "$ref" | cut -d: -f1)
      url_raw=$(echo "$ref"  | grep -oP "url\s+'[^']+'" | grep -oP "'[^']+'" | tr -d "'")

      has_ns=false; ns_part=""; bare="$url_raw"
      [[ "$url_raw" == *:* ]] && has_ns=true && ns_part="${url_raw%%:*}" && bare="${url_raw##*:}"

      # Is this URL in our app?
      is_app_url=false
      for au in "${APP_URLS[@]}"; do
        [[ "$au" == "$bare" ]] && is_app_url=true && break
      done

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
  echo "────────────────────────────────────────────────────────────────────"
  echo -e "  ${RED}Residuos (sin namespace '${APP_NS}:'):${RESET}  $RESIDUE"
  echo -e "  ${GREEN}Correctos:${RESET}                           $CORRECT"
  echo -e "  ${YELLOW}Otras apps:${RESET}                          $OTHER"
  echo -e "  ${CYAN}Sin urls:${RESET}                            $EMPTY"
  echo ""

  if [[ $RESIDUE -gt 0 ]]; then
    section "▸ Residuos — detalle y corrección:"
    echo ""
    for nav_file in "${NAV_FILES[@]}"; do
      nav_name=$(basename "$nav_file")
      url_refs=$(grep -noP "url\s+'[^']+'" "$nav_file" 2>/dev/null || true)
      [[ -z "$url_refs" ]] && continue

      while IFS= read -r ref; do
        [[ -z "$ref" ]] && continue
        line_num=$(echo "$ref" | cut -d: -f1)
        url_raw=$(echo "$ref"  | grep -oP "url\s+'[^']+'" | grep -oP "'[^']+'" | tr -d "'")
        [[ "$url_raw" == *:* ]] && continue   # already namespaced
        bare="$url_raw"
        is_app_url=false
        for au in "${APP_URLS[@]}"; do [[ "$au" == "$bare" ]] && is_app_url=true && break; done
        [[ "$is_app_url" == false ]] && continue

        echo -e "  ${YELLOW}$(printf '%-28s' "$nav_name")${RESET}  L${line_num}"
        context_line=$(sed -n "${line_num}p" "$nav_file" | xargs)
        echo -e "    ${RED}Actual:   ${context_line}${RESET}"
        fixed_line=$(echo "$context_line" | sed "s|url '${bare}'|url '${APP_NS}:${bare}'|g")
        echo -e "    ${GREEN}Correcto: ${fixed_line}${RESET}"
        echo ""
      done <<< "$url_refs"
    done

    echo "  Para corregir en lote (¡revisar antes de ejecutar!):"
    echo ""
    for nav_file in "${NAV_FILES[@]}"; do
      url_refs=$(grep -noP "url\s+'[^']+'" "$nav_file" 2>/dev/null || true)
      [[ -z "$url_refs" ]] && continue
      while IFS= read -r ref; do
        [[ -z "$ref" ]] && continue
        url_raw=$(echo "$ref" | grep -oP "url\s+'[^']+'" | grep -oP "'[^']+'" | tr -d "'")
        [[ "$url_raw" == *:* ]] && continue
        bare="$url_raw"
        is_app_url=false
        for au in "${APP_URLS[@]}"; do [[ "$au" == "$bare" ]] && is_app_url=true && break; done
        [[ "$is_app_url" == false ]] && continue
        echo -e "    ${CYAN}sed -i \"s|url '${bare}'|url '${APP_NS}:${bare}'|g\" $nav_file${RESET}"
      done <<< "$url_refs"
    done | sort -u
    echo ""
  else
    ok "Sin residuos. Todas las referencias están correctamente namespaciadas."
  fi
fi

section "▸ Uso rápido"
echo ""
echo "  bash app_map.sh                      # mapa de ./analyst"
echo "  bash app_map.sh ./crm                # mapa de ./crm"
echo "  bash app_map.sh --audit              # mapa + auditoría nav (ruta default)"
echo "  bash app_map.sh --no-map --audit     # solo auditoría"
echo ""
ok "¡Listo!"
