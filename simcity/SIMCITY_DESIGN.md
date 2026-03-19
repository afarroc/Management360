# SimCity — Diseño, Arquitectura y Roadmap

> **Última actualización:** 2026-03-18
> **App:** `simcity` | **Namespace:** `simcity` | **Endpoints:** 14
> **Sprint de integración:** S7 (completado) | **Estado:** ✅ Operativo

---

## Visión General

`simcity` es un simulador urbano interactivo integrado en Management360. Combina el motor
de simulación Micropolis (C/Python) con un modelo ABM (Agent-Based Model) multi-agente
para simular el crecimiento de ciudades con zonas residenciales, comerciales, industriales,
infraestructura eléctrica y carreteras.

La app incluye un modo especial "Tablero Monopoly Peruano" que genera un mapa urbano
basado en las 40 casillas del Monopoly localizado (avenidas de Lima).

---

## Arquitectura Híbrida

```
┌──────────────────────────────────────┐   HTTP interno
│  TERMUX — Management360 (:8000)      │◄─────────────►┐
│                                      │               │
│  simcity/                            │               │  PROOT UBUNTU (:8001)
│  ├── models.py  (Game + User FK)     │               │
│  ├── views.py   (proxy + auth)       │               │  simcity_web (Django 6)
│  ├── services.py (cliente HTTP)      │               │  ├── micropolisengine.so
│  └── templates/ (UI del juego)      │               │  ├── ABM (agentes)
│                                      │               │  ├── engine views
│  Auth: accounts.User                 │               │  └── SQLite (temporal)
│  BD: MariaDB (Game + created_by)    │               └──────────────────────┘
└──────────────────────────────────────┘
```

### Principio de separación

| Responsabilidad | Dónde vive |
|-----------------|-----------|
| Autenticación y permisos | M360 / Termux |
| Persistencia de partidas (Game) | MariaDB de M360 |
| Lógica del engine Micropolis | proot Ubuntu |
| Modelo ABM (agentes) | proot Ubuntu |
| UI (HTML/JS/Canvas) | M360 templates |
| CSRF y seguridad | M360 middleware |

---

## Stack Tecnológico

| Componente | Detalle |
|------------|---------|
| Motor de simulación | `micropolisengine` (C compilado, SWIG Python) |
| Modelo ABM | Mesa (Python) — agentes tipo `Persona` |
| Frontend | Canvas 2D (HTML5), JS vanilla, CSS custom |
| Proxy HTTP | `requests` desde `services.py` |
| BD principal | MariaDB — modelo `Game` con `created_by` |
| BD engine | SQLite en proot (solo temporal, sin auth) |
| Renderizado | Tiles de 10×10px, zoom 0.5×–3×, responsive |

---

## Modos de Juego

### Modo estándar
Mapa de 64×64 tiles con bloque inicial de carreteras (configurable 3×3 a 7×7).
El jugador coloca zonas residenciales, comerciales, industriales, carreteras,
cables eléctricos y plantas de carbón.

### Cuadrante (modal)
Genera un bloque con perímetro de carretera y 4 zonas residenciales en esquinas.
Tamaños: Pequeño (11×11), Mediano (13×13), Grande (17×17).
Opción de conectar automáticamente al resto de la ciudad.

### Cuadrante ZR 10×10
Bloque residencial de 32×32 tiles con 10 zonas en cada lado (top, bottom, left, right).

### Tablero Monopoly Peruano
Mapa de 200×200 tiles. Las 40 casillas del Monopoly peruano se convierten en
parcelas de 15×15 tiles separadas por calles. Cada grupo de propiedades genera
un tipo de zona diferente:

| Grupo | Tipo de zona |
|-------|-------------|
| Marrón, Celeste | Residencial (4 casas) |
| Rosa, Naranja | Comercial (3 tiendas) |
| Rojo, Amarillo | Industrial (2 fábricas) |
| Verde, Azul | Comercial (4 edificios) |
| Ferrocarriles | Industrial (estación 5×5) |
| Servicios | Comercial (planta 4×4) |

---

## Modelos

### `Game` (M360 / MariaDB)

```python
class Game(models.Model):
    name         = CharField(max_length=100)
    created_by   = ForeignKey(settings.AUTH_USER_MODEL)   # M360 auth
    created_at   = DateTimeField(auto_now_add=True)
    updated_at   = DateTimeField(auto_now=True)
    money        = IntegerField(default=20000)
    map_data     = JSONField(default=list)       # mapa [x][y] = tile
    size         = IntegerField(default=64)
    abm_state    = JSONField(default=dict)       # estado de agentes
    engine_game_id = IntegerField(null=True)     # ID en simcity_web/proot
```

El campo `engine_game_id` vincula cada `Game` de M360 con su contraparte
en el SQLite de proot. M360 es el master; proot es el worker del engine.

---

## Endpoints (14)

| URL | Método | Descripción |
|-----|--------|-------------|
| `/simcity/` | GET | UI del juego (index) |
| `/simcity/api/games/` | GET | Lista partidas del usuario |
| `/simcity/api/games/new/` | POST | Crear nueva partida |
| `/simcity/api/game/<id>/map/` | GET | Estado del mapa + agentes |
| `/simcity/api/game/<id>/tick/` | POST | Avanzar N ticks |
| `/simcity/api/game/<id>/build/` | POST | Construir tile (herramienta) |
| `/simcity/api/game/<id>/reset/` | POST | Reiniciar ciudad |
| `/simcity/api/game/<id>/generate_block/` | POST | Generar cuadrante |
| `/simcity/api/game/<id>/generate_zr_block/` | POST | Generar cuadrante ZR 10×10 — SC-1 ✅ |
| `/simcity/api/game/<id>/census/` | GET | Censo de estructuras |
| `/simcity/api/game/<id>/tasks/` | GET | Estado de tareas ABM |
| `/simcity/api/game/<id>/add_money/` | POST | Añadir fondos |
| `/simcity/api/game/<id>/delete/` | POST | Eliminar partida |
| `/simcity/api/game/<id>/export_analyst/` | POST | Exportar partida a analyst dataset — SC-4 ✅ |

Todos los endpoints requieren `@login_required`. El CSRF se maneja por cookie
siguiendo el patrón estándar de M360 (`csrf()` en JS).

---

## Herramientas del Juego

| Código | Herramienta | Costo |
|--------|-------------|-------|
| `r` | Zona residencial | $100 |
| `c` | Zona comercial | $150 |
| `i` | Zona industrial | $150 |
| `t` | Carretera | $50 |
| `e` | Planta de carbón | variable |
| `w` | Cable eléctrico | variable |
| `b` | Bulldozer | variable |
| `s` | Seleccionar (info) | $0 |

---

## Flujo de una partida

```
1. Usuario abre /simcity/
2. JS carga lista de partidas (GET /api/games/)
3. Usuario funda ciudad → POST /api/games/new/ → POST /api/game/<id>/reset/
4. M360 crea Game en MariaDB + crea game en proot vía HTTP
5. JS renderiza mapa con Canvas 2D
6. Cada acción (build, tick) → M360 proxy → proot engine → respuesta
7. M360 sincroniza map_data y money en MariaDB
8. Sesión persiste en localStorage (key: simcity_m360_session)
```

---

## Integración con M360

| Integración | App destino | Estado |
|-------------|-------------|--------|
| Exportar datos de partida como dataset | `analyst` | ✅ SC-4 — `/export_analyst/` |
| Enlace en nav del dashboard | `core` | ✅ sidebar Tools section |
| Slot en panel de administración | `panel` | ✅ `/admin/simcity/` — GameAdmin |
| KPIs urbanos (población, energía, etc.) | `kpis` | ⬜ Pendiente |
| Crear tareas desde hitos del juego | `events` | ⬜ Pendiente |

---

## Arranque del sistema

### Método recomendado — aliases (una terminal por proceso)

```bash
# ~/.zshrc — agregar una vez
alias engine='ubuntu run "source /root/micropolis/venv/bin/activate && cd /root/micropolis/simcity_web && python manage.py runserver 0.0.0.0:8001"'
alias m360='cd ~/projects/Management360 && source venv/bin/activate && python manage.py runserver'
```

Terminal 1: `engine` | Terminal 2: `m360`

### Método alternativo — script automático

```bash
bash scripts/start_simcity.sh
```

> ⚠️ El script intenta arrancar el engine en background usando `proot-distro`.
> En algunos casos puede requerir intervención manual si el engine no levanta.
> Verificar con: `curl -s http://localhost:8001/api/games/`

`micropolisengine` **solo está disponible en proot Ubuntu**. No intentar
importarlo en el venv de M360/Termux — dará `ModuleNotFoundError`.

---

## Roadmap

| Tarea | Prioridad | Estado |
|-------|-----------|--------|
| Migración desde simcity_web | 🔴 | ✅ |
| Auth con accounts.User | 🔴 | ✅ |
| Proxy HTTP M360 ↔ proot | 🔴 | ✅ |
| Template index.html adaptado | 🔴 | ✅ |
| Endpoint add_money | 🟠 | ✅ |
| SC-1: generate_zr_block URL+view | 🟠 | ✅ `bf037497` |
| SC-2: mobMoneyBtn → add_money API | 🟠 | ✅ `bf037497` |
| SC-3: EngineUnavailableError 503 | 🔴 | ✅ `bf037497` |
| Nav link en core dashboard | 🟡 | ✅ `fa01b4f9` |
| Slot /admin/simcity/ | 🟡 | ✅ `fa01b4f9` |
| Exportar partida a analyst dataset | 🟠 | ✅ `c0f8c47c` |
| Script de inicio automático | 🟡 | ✅ `scripts/start_simcity.sh` |
| Tests básicos del proxy | 🟡 | ⬜ |