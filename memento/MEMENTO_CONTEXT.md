# Mapa de Contexto — App `memento`

> Generado por `m360_map.sh`  |  2026-03-19 18:24:44
> Ruta: `/data/data/com.termux/files/home/projects/Management360/memento`  |  Total archivos: **17**

---

## Índice

| # | Categoría | Archivos |
|---|-----------|----------|
| 1 | 👁 `views` | 1 |
| 2 | 🎨 `templates` | 6 |
| 3 | 🗃 `models` | 1 |
| 4 | 📝 `forms` | 1 |
| 5 | 🔗 `urls` | 1 |
| 6 | 🛡 `admin` | 1 |
| 7 | 📦 `static` | 1 |
| 8 | 🧪 `tests` | 1 |
| 9 | 📄 `other` | 4 |

---

## Archivos por Categoría


### VIEWS (1 archivos)

| Archivo | Líneas | Ruta relativa |
|---------|--------|---------------|
| `views.py` | 199 | `views.py` |

### TEMPLATES (6 archivos)

| Archivo | Líneas | Ruta relativa |
|---------|--------|---------------|
| `base.html` | 17 | `templates/memento/base.html` |
| `date_selection.html` | 96 | `templates/memento/date_selection.html` |
| `memento_daily.html` | 55 | `templates/memento/includes/memento_daily.html` |
| `memento_monthly.html` | 105 | `templates/memento/includes/memento_monthly.html` |
| `memento_weekly.html` | 100 | `templates/memento/includes/memento_weekly.html` |
| `memento_mori.html` | 98 | `templates/memento/memento_mori.html` |

### MODELS (1 archivos)

| Archivo | Líneas | Ruta relativa |
|---------|--------|---------------|
| `models.py` | 45 | `models.py` |

### FORMS (1 archivos)

| Archivo | Líneas | Ruta relativa |
|---------|--------|---------------|
| `forms.py` | 77 | `forms.py` |

### URLS (1 archivos)

| Archivo | Líneas | Ruta relativa |
|---------|--------|---------------|
| `urls.py` | 18 | `urls.py` |

### ADMIN (1 archivos)

| Archivo | Líneas | Ruta relativa |
|---------|--------|---------------|
| `admin.py` | 3 | `admin.py` |

### STATIC (1 archivos)

| Archivo | Líneas | Ruta relativa |
|---------|--------|---------------|
| `memento.css` | 94 | `static/css/memento.css` |

### TESTS (1 archivos)

| Archivo | Líneas | Ruta relativa |
|---------|--------|---------------|
| `tests.py` | 68 | `tests.py` |

### OTHER (4 archivos)

| Archivo | Líneas | Ruta relativa |
|---------|--------|---------------|
| `__init__.py` | 0 | `__init__.py` |
| `apps.py` | 6 | `apps.py` |
| `__init__.py` | 0 | `templatetags/__init__.py` |
| `memento_filters.py` | 17 | `templatetags/memento_filters.py` |

---

## Árbol de Directorios

```
memento/
├── static
│   └── css
│       └── memento.css
├── templates
│   └── memento
│       ├── includes
│       │   ├── memento_daily.html
│       │   ├── memento_monthly.html
│       │   └── memento_weekly.html
│       ├── base.html
│       ├── date_selection.html
│       └── memento_mori.html
├── templatetags
│   ├── __init__.py
│   └── memento_filters.py
├── __init__.py
├── admin.py
├── apps.py
├── forms.py
├── models.py
├── tests.py
├── urls.py
└── views.py
```

---

## Endpoints registrados

Fuente: `urls.py`

```python
  path('', memento, name='memento_default'),  # Default view with form
  path('try/', memento, name='memento_try'),  # Temporary trial view
  path('config/create/', MementoConfigCreateView.as_view(), name='memento_create'),
  path('config/update/<int:pk>/', MementoConfigUpdateView.as_view(), name='memento_update'),
  path('view/<str:frequency>/<str:birth_date>/<str:death_date>/', memento, name='memento'),
  path('logout/', LogoutView.as_view(), name='memento_logout'),
```

---

## Modelos detectados

**`models.py`**

- línea 8: `class MementoConfig(models.Model):`


---

## Migraciones

| Archivo | Estado |
|---------|--------|
| `0001_initial` | aplicada |
| `0002_alter_mementoconfig_death_date` | aplicada |
| `0003_alter_mementoconfig_death_date` | aplicada |
| `0004_alter_mementoconfig_death_date` | aplicada |
| `0005_alter_mementoconfig_death_date` | aplicada |
| `0006_alter_mementoconfig_death_date` | aplicada |
| `0007_alter_mementoconfig_death_date` | aplicada |

---

## Funciones clave (views/ y services/)


---

## Compartir con Claude

```bash
cat /data/data/com.termux/files/home/projects/Management360/memento/views/mi_vista.py | termux-clipboard-set
```
