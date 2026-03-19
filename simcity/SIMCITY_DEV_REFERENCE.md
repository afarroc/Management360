# SimCity — Referencia de Desarrollo

> **Audiencia:** Desarrolladores y asistentes de IA (Claude, Copilot, etc.)
> **Actualizado:** 2026-03-18 | **App:** `simcity` | **Namespace:** `simcity`
> **Endpoints:** 14 | **Bugs resueltos esta sesión:** SC-1, SC-2, SC-3

---

## Estructura de archivos

```
simcity/
├── __init__.py
├── apps.py              # label='simcity' (evita colisión con app 'sim')
├── models.py            # Game con created_by → accounts.User
├── views.py             # proxy @login_required, sin @csrf_exempt
├── services.py          # cliente HTTP hacia proot:8001 + EngineUnavailableError
├── urls.py              # 14 endpoints, app_name='simcity'
├── admin.py             # GameAdmin registrado en /admin/simcity/
├── tests.py
├── migrations/
│   └── 0001_initial.py
└── templates/
    └── simcity/
        └── index.html   # UI completa (Canvas 2D, JS vanilla)
```

---

## Arranque obligatorio

**Siempre levantar proot primero.** Sin el engine en :8001, todos los
endpoints de juego devolverán `503 EngineUnavailableError` (desde SC-3).

```bash
# Método recomendado — aliases en ~/.zshrc
alias engine='ubuntu run "source /root/micropolis/venv/bin/activate && cd /root/micropolis/simcity_web && python manage.py runserver 0.0.0.0:8001"'
alias m360='cd ~/projects/Management360 && source venv/bin/activate && python manage.py runserver'

# Alternativa — script automático
bash scripts/start_simcity.sh

# Verificar conectividad
curl -s http://localhost:8001/api/games/
```

---

## Modelo `Game`

```python
# simcity/models.py
class Game(models.Model):
    name           = models.CharField(max_length=100, default="Mi ciudad")
    created_by     = models.ForeignKey(
                         settings.AUTH_USER_MODEL,
                         on_delete=models.CASCADE,
                         related_name='simcity_games',
                     )
    created_at     = models.DateTimeField(auto_now_add=True)
    updated_at     = models.DateTimeField(auto_now=True)
    money          = models.IntegerField(default=20000)
    map_data       = models.JSONField(default=list)
    size           = models.IntegerField(default=64)
    abm_state      = models.JSONField(default=dict)
    engine_game_id = models.IntegerField(null=True, blank=True)
```

`engine_game_id` es la FK lógica hacia el `Game` del SQLite en proot.
M360 es siempre el master; proot puede perder datos sin consecuencias críticas
(se recrea con `reset`).

---

## `services.py` — Cliente HTTP

Desde SC-3, todas las llamadas al engine propagan `EngineUnavailableError`
si proot no está accesible. Las vistas capturan esta excepción y devuelven 503.

```python
ENGINE_BASE_URL = 'http://localhost:8001'
ENGINE_TIMEOUT  = 30   # segundos

# Excepción a capturar en views.py
from .services import EngineUnavailableError

# Funciones disponibles:
engine_new_game(name)
engine_reset(engine_id, size, num_agents, monopoly=False)
engine_tick(engine_id, n=1)
engine_build(engine_id, herramienta, x, y, agente_id=None)
engine_map(engine_id)
engine_census(engine_id)
engine_generate_block(engine_id, size='medium', conectar=True)
engine_generate_zr(engine_id)        # SC-1 — cuadrante ZR 10×10
engine_add_money(engine_id, cantidad=1000)
engine_tasks(engine_id)
```

---

## Patrón de vistas (proxy + auth + SC-3)

```python
# CORRECTO — patrón estándar M360 con manejo de engine offline
@login_required
@require_POST
def tick(request, game_id):
    game = get_object_or_404(Game, pk=game_id, created_by=request.user)
    try:
        body = json.loads(request.body)
        data = engine.engine_tick(game.engine_game_id, body.get('n', 1))
        game.map_data = data.get('map', game.map_data)
        game.money    = data.get('money', game.money)
        game.save()
        return JsonResponse(data)
    except EngineUnavailableError as e:
        return _engine_error(e)   # → 503 {"success": false, "error": "Engine offline..."}
```

Reglas:
- Siempre `get_object_or_404(Game, pk=..., created_by=request.user)`.
- Siempre `try/except EngineUnavailableError` en cualquier llamada al engine.
- Sincronizar `map_data` y `money` en MariaDB después de cada operación.
- Respuestas: `{'success': True, ...}` / `{'success': False, 'error': '...'}`.

---

## CSRF en JavaScript

```javascript
function csrf() {
    return document.cookie.match(/csrftoken=([^;]+)/)?.[1] || '';
}

async function apiFetch(url, options = {}) {
    return fetch(url, {
        ...options,
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrf(),
            ...(options.headers || {}),
        },
    });
}
```

**Nunca** usar `@csrf_exempt` en vistas de simcity.

---

## URLs del JS

```javascript
const API = {
    newGame:       '/simcity/api/games/new/',
    listGames:     '/simcity/api/games/',
    map:           id => `/simcity/api/game/${id}/map/`,
    tick:          id => `/simcity/api/game/${id}/tick/`,
    build:         id => `/simcity/api/game/${id}/build/`,
    reset:         id => `/simcity/api/game/${id}/reset/`,
    census:        id => `/simcity/api/game/${id}/census/`,
    block:         id => `/simcity/api/game/${id}/generate_block/`,
    zrBlock:       id => `/simcity/api/game/${id}/generate_zr_block/`,  // SC-1
    tasks:         id => `/simcity/api/game/${id}/tasks/`,
    delete:        id => `/simcity/api/game/${id}/delete/`,
    exportAnalyst: id => `/simcity/api/game/${id}/export_analyst/`,     // SC-4
};
```

Si se agregan endpoints nuevos, actualizar este objeto **y** `urls.py`.

---

## Exportar partida a analyst (SC-4)

`POST /simcity/api/game/<id>/export_analyst/`

Genera un `StoredDataset` en `analyst` con una fila por tile no-vacío del mapa.

Columnas del dataset:
`x`, `y`, `tile`, `zone_type`, `has_power`, `has_road`, `money`, `game_name`, `game_id`

`zone_type` es una etiqueta derivada del tile base:
`road`, `wire`, `residential_empty`, `residential`, `commercial_empty`,
`commercial`, `industrial_empty`, `industrial`, `coal_plant`, `terrain`, `other`

Respuesta:
```json
{
  "success": true,
  "dataset_id": "<uuid>",
  "name": "SimCity — Mi ciudad",
  "rows": 1234,
  "columns": ["x", "y", "tile", "zone_type", "has_power", "has_road", "money", "game_name", "game_id"],
  "analyst_url": "/analyst/datasets/<uuid>/preview/"
}
```

---

## Sistema de tiles (Micropolis)

El mapa es una matriz `map_data[x][y]` donde cada celda es un entero de 16 bits.

| Bits | Significado |
|------|-------------|
| 0–9 (0x3FF) | Tile base (tipo de estructura) |
| 10 (0x0400) | ZONEBIT — centro de zona |
| 12 (0x1000) | BULLBIT — demolible |
| 13 (0x2000) | BURNBIT / sin acceso carretera |
| 14 (0x4000) | CONDBIT — conduce electricidad |
| 15 (0x8000) | PWRBIT — tiene electricidad |

Rangos de tiles base más usados:

| Rango | Tipo | Color en UI |
|-------|------|-------------|
| 0 | Tierra vacía | `#090b10` |
| 64–206 | Carreteras | `#555560` |
| 240–248 | Zona residencial vacía | `#2d5a2d` |
| 249–260 | Casas | `#3ecf8e` / `#444c44` |
| 423–609 | Comercial | `#1e4a8a` |
| 612–692 | Industrial | `#8a5a10` |
| 745–760 | Planta de carbón | `#8a1a1a` |

---

## Límites del engine Micropolis

```python
MICROPOLIS_MAX_X = 120   # columnas válidas (0..119)
MICROPOLIS_MAX_Y = 100   # filas válidas (0..99)
```

Mapas mayores de 120×100 tiles se guardan correctamente en `map_data` (JSON),
pero el engine solo procesa tiles dentro de estos límites. El tablero Monopoly
(200×200) funciona porque el render es puramente desde `map_data`.

---

## Migraciones

| Archivo | Estado | Contenido |
|---------|--------|-----------|
| `0001_initial` | ✅ aplicada | Modelo `Game` completo |

---

## Agregar un endpoint nuevo

1. Vista en `views.py` con `@login_required`, `get_object_or_404(..., created_by=request.user)` y `try/except EngineUnavailableError`
2. Función wrapper en `services.py`
3. URL en `urls.py`
4. Entrada en objeto `API` del template `index.html`
5. Regenerar contexto: `bash scripts/m360_map.sh app ./simcity`

---

## Bugs conocidos

| # | Estado | Descripción |
|---|--------|-------------|
| SC-1 | ✅ `bf037497` | `generate_zr_block` no estaba en URLs de M360 — corregido |
| SC-2 | ✅ `bf037497` | `mobMoneyBtn` solo logueaba warning — ahora llama a `add_money` API |
| SC-3 | ✅ `bf037497` | Engine offline daba 500 — ahora devuelve 503 con `EngineUnavailableError` |

---

## Notas para Claude

- `micropolisengine` **nunca** importar en código de M360/Termux — solo existe en proot.
- `engine_game_id` puede ser `None` si la partida se creó en M360 pero el engine
  no respondió. Siempre verificar antes de llamar al engine.
- El `map_data` en MariaDB es la fuente de verdad del mapa. El SQLite de proot
  es temporal y puede divergir.
- `app_label = 'simcity'` en `apps.py` es obligatorio para evitar colisión con `sim`.
- El template NO usa Bootstrap ni HTMX — JS vanilla con CSS custom. No agregar Bootstrap.
- `proot-distro login ubuntu -- <cmd>` es el método correcto para ejecutar comandos
  en proot desde Termux. `ubuntu run` abre shell interactiva, no ejecuta comandos.
- El engine no se puede correr en background fiable desde Termux — usar dos terminales
  con los aliases `engine` y `m360`.