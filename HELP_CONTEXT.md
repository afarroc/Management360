# Mapa de Contexto — App `help`

> Generado por `m360_map.sh`  |  2026-03-20 14:54:25
> Ruta: `/data/data/com.termux/files/home/projects/Management360/help`  |  Total archivos: **15**

---

## Índice

| # | Categoría | Archivos |
|---|-----------|----------|
| 1 | 👁 `views` | 1 |
| 2 | 🎨 `templates` | 5 |
| 3 | 🗃 `models` | 1 |
| 4 | 🔗 `urls` | 1 |
| 5 | 🛡 `admin` | 1 |
| 6 | 📄 `management` | 3 |
| 7 | 🧪 `tests` | 1 |
| 8 | 📄 `other` | 2 |

---

## Archivos por Categoría


### VIEWS (1 archivos)

| Archivo | Líneas | Ruta relativa |
|---------|--------|---------------|
| `views.py` | 424 | `views.py` |

### TEMPLATES (5 archivos)

| Archivo | Líneas | Ruta relativa |
|---------|--------|---------------|
| `article_detail.html` | 506 | `templates/help/article_detail.html` |
| `category_detail.html` | 444 | `templates/help/category_detail.html` |
| `category_list.html` | 165 | `templates/help/category_list.html` |
| `help_home.html` | 430 | `templates/help/help_home.html` |
| `search_results.html` | 487 | `templates/help/search_results.html` |

### MODELS (1 archivos)

| Archivo | Líneas | Ruta relativa |
|---------|--------|---------------|
| `models.py` | 421 | `models.py` |

### URLS (1 archivos)

| Archivo | Líneas | Ruta relativa |
|---------|--------|---------------|
| `urls.py` | 31 | `urls.py` |

### ADMIN (1 archivos)

| Archivo | Líneas | Ruta relativa |
|---------|--------|---------------|
| `admin.py` | 3 | `admin.py` |

### MANAGEMENT (3 archivos)

| Archivo | Líneas | Ruta relativa |
|---------|--------|---------------|
| `__init__.py` | 0 | `management/__init__.py` |
| `__init__.py` | 0 | `management/commands/__init__.py` |
| `setup_help.py` | 1115 | `management/commands/setup_help.py` |

### TESTS (1 archivos)

| Archivo | Líneas | Ruta relativa |
|---------|--------|---------------|
| `tests.py` | 3 | `tests.py` |

### OTHER (2 archivos)

| Archivo | Líneas | Ruta relativa |
|---------|--------|---------------|
| `__init__.py` | 0 | `__init__.py` |
| `apps.py` | 7 | `apps.py` |

---

## Árbol de Directorios

```
help/
├── management
│   ├── commands
│   │   ├── __init__.py
│   │   └── setup_help.py
│   └── __init__.py
├── templates
│   └── help
│       ├── article_detail.html
│       ├── category_detail.html
│       ├── category_list.html
│       ├── help_home.html
│       └── search_results.html
├── __init__.py
├── admin.py
├── apps.py
├── models.py
├── tests.py
├── urls.py
└── views.py
```

---

## Endpoints registrados

Fuente: `urls.py`  |  namespace: `help`

```python
  path('', views.help_home, name='help_home'),
  path('categories/', views.category_list, name='category_list'),
  path('categories/<slug:slug>/', views.category_detail, name='category_detail'),
  path('articles/<slug:slug>/', views.article_detail, name='article_detail'),
  path('faq/', views.faq_list, name='faq_list'),
  path('videos/', views.video_tutorials, name='video_tutorials'),
  path('quick-start/', views.quick_start, name='quick_start'),
  path('search/', views.search_help, name='search'),
  path('articles/<slug:article_slug>/feedback/', views.submit_feedback, name='submit_feedback'),
  path('articles/<slug:article_slug>/feedback-stats/', views.article_feedback_stats, name='article_feedback_stats'),
```

---

## Modelos detectados

**`models.py`**

- línea 9: `class HelpCategory(models.Model):`
- línea 37: `class HelpArticle(models.Model):`
- línea 214: `class FAQ(models.Model):`
- línea 241: `class HelpSearchLog(models.Model):`
- línea 264: `class HelpFeedback(models.Model):`
- línea 295: `class VideoTutorial(models.Model):`
- línea 376: `class QuickStartGuide(models.Model):`


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
cat /data/data/com.termux/files/home/projects/Management360/help/views/mi_vista.py | termux-clipboard-set
```
