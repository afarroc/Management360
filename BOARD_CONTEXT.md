# Mapa de Contexto — App `board`

> Generado por `m360_map.sh`  |  2026-03-20 09:53:32
> Ruta: `/data/data/com.termux/files/home/projects/Management360/board`  |  Total archivos: **17**

---

## Índice

| # | Categoría | Archivos |
|---|-----------|----------|
| 1 | 👁 `views` | 2 |
| 2 | 🎨 `templates` | 6 |
| 3 | 🗃 `models` | 1 |
| 4 | 🔗 `urls` | 1 |
| 5 | 🛡 `admin` | 1 |
| 6 | 📦 `static` | 1 |
| 7 | 🧪 `tests` | 1 |
| 8 | 📄 `other` | 4 |

---

## Archivos por Categoría


### VIEWS (2 archivos)

| Archivo | Líneas | Ruta relativa |
|---------|--------|---------------|
| `htmx_views.py` | 99 | `htmx_views.py` |
| `views.py` | 32 | `views.py` |

### TEMPLATES (6 archivos)

| Archivo | Líneas | Ruta relativa |
|---------|--------|---------------|
| `board_detail.html` | 237 | `templates/board/board_detail.html` |
| `board_form.html` | 94 | `templates/board/board_form.html` |
| `board_list.html` | 116 | `templates/board/board_list.html` |
| `card.html` | 61 | `templates/board/partials/card.html` |
| `card_grid.html` | 14 | `templates/board/partials/card_grid.html` |
| `card_grid_items.html` | 11 | `templates/board/partials/card_grid_items.html` |

### MODELS (1 archivos)

| Archivo | Líneas | Ruta relativa |
|---------|--------|---------------|
| `models.py` | 107 | `models.py` |

### URLS (1 archivos)

| Archivo | Líneas | Ruta relativa |
|---------|--------|---------------|
| `urls.py` | 17 | `urls.py` |

### ADMIN (1 archivos)

| Archivo | Líneas | Ruta relativa |
|---------|--------|---------------|
| `admin.py` | 3 | `admin.py` |

### STATIC (1 archivos)

| Archivo | Líneas | Ruta relativa |
|---------|--------|---------------|
| `board.css` | 92 | `static/board/css/board.css` |

### TESTS (1 archivos)

| Archivo | Líneas | Ruta relativa |
|---------|--------|---------------|
| `tests.py` | 3 | `tests.py` |

### OTHER (4 archivos)

| Archivo | Líneas | Ruta relativa |
|---------|--------|---------------|
| `BOARD_CONTEXT.md` | 159 | `BOARD_CONTEXT.md` |
| `__init__.py` | 0 | `__init__.py` |
| `apps.py` | 6 | `apps.py` |
| `consumers.py` | 46 | `consumers.py` |

---

## Árbol de Directorios

```
board/
├── static
│   └── board
│       └── css
│           └── board.css
├── templates
│   └── board
│       ├── partials
│       │   ├── card.html
│       │   ├── card_grid.html
│       │   └── card_grid_items.html
│       ├── board_detail.html
│       ├── board_form.html
│       └── board_list.html
├── BOARD_CONTEXT.md
├── __init__.py
├── admin.py
├── apps.py
├── consumers.py
├── htmx_views.py
├── models.py
├── tests.py
├── urls.py
└── views.py
```

---

## Endpoints registrados

Fuente: `urls.py`  |  namespace: `board`

```python
  path('', views.BoardListView.as_view(), name='list'),
  path('create/', views.BoardCreateView.as_view(), name='create'),
  path('<int:pk>/', views.BoardDetailView.as_view(), name='detail'),
  path('htmx/<int:board_id>/grid/', htmx_views.board_grid, name='grid'),
  path('htmx/<int:board_id>/create-card/', htmx_views.create_card_htmx, name='create_card_htmx'),
  path('htmx/card/<int:card_id>/delete/', htmx_views.delete_card_htmx, name='delete_card_htmx'),
  path('htmx/card/<int:card_id>/toggle-pin/', htmx_views.toggle_pin_card, name='toggle_pin'),
  path('htmx/<int:board_id>/load-more/', htmx_views.load_more_cards, name='load_more'),
```

---

## Modelos detectados

**`models.py`**

- línea 8: `class Board(models.Model):`
- línea 43: `class Card(models.Model):`
- línea 88: `class Activity(models.Model):`


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
cat /data/data/com.termux/files/home/projects/Management360/board/views/mi_vista.py | termux-clipboard-set
```
