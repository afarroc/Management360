# Mapa de Contexto — App `simcity`

> Generado por `m360_map.sh`  |  2026-03-18 01:38:45
> Ruta: `/data/data/com.termux/files/home/projects/Management360/simcity`  |  Total archivos: **10**

---

## Índice

| # | Categoría | Archivos |
|---|-----------|----------|
| 1 | 👁 `views` | 1 |
| 2 | 🎨 `templates` | 1 |
| 3 | 🗃 `models` | 1 |
| 4 | 🔗 `urls` | 1 |
| 5 | 🛡 `admin` | 1 |
| 6 | 🧪 `tests` | 1 |
| 7 | 📄 `other` | 4 |

---

## Archivos por Categoría


### VIEWS (1 archivos)

| Archivo | Líneas | Ruta relativa |
|---------|--------|---------------|
| `views.py` | 127 | `views.py` |

### TEMPLATES (1 archivos)

| Archivo | Líneas | Ruta relativa |
|---------|--------|---------------|
| `index.html` | 1014 | `templates/simcity/index.html` |

### MODELS (1 archivos)

| Archivo | Líneas | Ruta relativa |
|---------|--------|---------------|
| `models.py` | 26 | `models.py` |

### URLS (1 archivos)

| Archivo | Líneas | Ruta relativa |
|---------|--------|---------------|
| `urls.py` | 18 | `urls.py` |

### ADMIN (1 archivos)

| Archivo | Líneas | Ruta relativa |
|---------|--------|---------------|
| `admin.py` | 3 | `admin.py` |

### TESTS (1 archivos)

| Archivo | Líneas | Ruta relativa |
|---------|--------|---------------|
| `tests.py` | 3 | `tests.py` |

### OTHER (4 archivos)

| Archivo | Líneas | Ruta relativa |
|---------|--------|---------------|
| `SIMCITY_CONTEXT.md` | 126 | `SIMCITY_CONTEXT.md` |
| `__init__.py` | 0 | `__init__.py` |
| `apps.py` | 5 | `apps.py` |
| `services.py` | 53 | `services.py` |

---

## Árbol de Directorios

```
simcity/
├── templates
│   └── simcity
│       └── index.html
├── SIMCITY_CONTEXT.md
├── __init__.py
├── admin.py
├── apps.py
├── models.py
├── services.py
├── tests.py
├── urls.py
└── views.py
```

---

## Endpoints registrados

Fuente: `urls.py`  |  namespace: `simcity`

```python
  path('', views.index, name='index'),
  path('api/games/', views.list_games, name='list_games'),
  path('api/games/new/', views.new_game, name='new_game'),
  path('api/game/<int:game_id>/map/', views.game_map, name='game_map'),
  path('api/game/<int:game_id>/tick/', views.tick, name='tick'),
  path('api/game/<int:game_id>/build/', views.build, name='build'),
  path('api/game/<int:game_id>/reset/', views.reset, name='reset'),
  path('api/game/<int:game_id>/generate_block/', views.generate_block, name='generate_block'),
  path('api/game/<int:game_id>/census/', views.census, name='census'),
  path('api/game/<int:game_id>/tasks/', views.task_status, name='task_status'),
  path('api/game/<int:game_id>/delete/', views.delete_game, name='delete_game'),
  path('api/game/<int:game_id>/add_money/', views.add_money, name='add_money'),
```

---

## Modelos detectados

**`models.py`**

- línea 4: `class Game(models.Model):`


---

## Migraciones

| Archivo | Estado |
|---------|--------|
| `0001_initial` | aplicada |

---

## Funciones clave (views/ y services/)


---

## Compartir con Claude

```bash
cat /data/data/com.termux/files/home/projects/Management360/simcity/views/mi_vista.py | termux-clipboard-set
```
