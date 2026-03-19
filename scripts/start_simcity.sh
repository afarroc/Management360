#!/usr/bin/env bash
# =============================================================
# start_simcity.sh — Arranca el engine SimCity + M360
# Uso: bash scripts/start_simcity.sh
# =============================================================

M360_DIR="/data/data/com.termux/files/home/projects/Management360"
ENGINE_DIR="/root/micropolis/simcity_web"
ENGINE_VENV="/root/micropolis/venv"
M360_VENV="$M360_DIR/venv"
ENGINE_LOG="$M360_DIR/logs/engine.log"
ENGINE_PID="$M360_DIR/logs/engine.pid"

mkdir -p "$M360_DIR/logs"

# ── 1. Verificar si el engine ya está corriendo ──────────────
if [ -f "$ENGINE_PID" ]; then
    OLD_PID=$(cat "$ENGINE_PID")
    if kill -0 "$OLD_PID" 2>/dev/null; then
        echo "⚡ Engine ya corriendo (PID $OLD_PID) — omitiendo"
    else
        echo "🔄 PID obsoleto, reiniciando engine..."
        rm -f "$ENGINE_PID"
    fi
fi

# ── 2. Arrancar engine en proot (background persistente) ─────
if [ ! -f "$ENGINE_PID" ]; then
    echo "🚀 Arrancando engine SimCity en proot:8001..."
    proot-distro login ubuntu -- bash -c "
        source $ENGINE_VENV/bin/activate
        cd $ENGINE_DIR
        setsid python manage.py runserver 0.0.0.0:8001 > $ENGINE_LOG 2>&1 &
        disown
        echo \$! > $ENGINE_PID
    "
    sleep 4

    # Verificar que levantó
    if curl -s --max-time 3 http://localhost:8001/api/games/ > /dev/null 2>&1; then
        echo "✅ Engine OK en http://localhost:8001"
    else
        echo "⚠️  Engine arrancando — logs: tail -f $ENGINE_LOG"
    fi
fi

# ── 3. Arrancar M360 ─────────────────────────────────────────
echo "🚀 Arrancando M360 en :8000..."
cd "$M360_DIR"
source "$M360_VENV/bin/activate"
python manage.py runserver
