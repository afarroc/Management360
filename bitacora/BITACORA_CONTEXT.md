# Mapa de Contexto — App `bitacora`

> Generado por `m360_map.sh`  |  2026-03-18 21:17:09
> Ruta: `/data/data/com.termux/files/home/projects/Management360/bitacora`  |  Total archivos: **20**

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
| 7 | 🧪 `tests` | 1 |
| 8 | 📄 `other` | 8 |

---

## Archivos por Categoría


### VIEWS (1 archivos)

| Archivo | Líneas | Ruta relativa |
|---------|--------|---------------|
| `views.py` | 314 | `views.py` |

### TEMPLATES (6 archivos)

| Archivo | Líneas | Ruta relativa |
|---------|--------|---------------|
| `content_blocks_list.html` | 233 | `templates/bitacora/content_blocks_list.html` |
| `dashboard.html` | 432 | `templates/bitacora/dashboard.html` |
| `entry_confirm_delete.html` | 69 | `templates/bitacora/entry_confirm_delete.html` |
| `entry_detail.html` | 774 | `templates/bitacora/entry_detail.html` |
| `entry_form.html` | 709 | `templates/bitacora/entry_form.html` |
| `entry_list.html` | 579 | `templates/bitacora/entry_list.html` |

### MODELS (1 archivos)

| Archivo | Líneas | Ruta relativa |
|---------|--------|---------------|
| `models.py` | 119 | `models.py` |

### FORMS (1 archivos)

| Archivo | Líneas | Ruta relativa |
|---------|--------|---------------|
| `forms.py` | 36 | `forms.py` |

### URLS (1 archivos)

| Archivo | Líneas | Ruta relativa |
|---------|--------|---------------|
| `urls.py` | 19 | `urls.py` |

### ADMIN (1 archivos)

| Archivo | Líneas | Ruta relativa |
|---------|--------|---------------|
| `admin.py` | 3 | `admin.py` |

### TESTS (1 archivos)

| Archivo | Líneas | Ruta relativa |
|---------|--------|---------------|
| `tests.py` | 3 | `tests.py` |

### OTHER (8 archivos)

| Archivo | Líneas | Ruta relativa |
|---------|--------|---------------|
| `BITACORA_CONTEXT.md` | 169 | `BITACORA_CONTEXT.md` |
| `BITACORA_DESIGN.md` | 182 | `BITACORA_DESIGN.md` |
| `BITACORA_DEV_REFERENCE.md` | 251 | `BITACORA_DEV_REFERENCE.md` |
| `__init__.py` | 0 | `__init__.py` |
| `apps.py` | 6 | `apps.py` |
| `__init__.py` | 0 | `templatetags/__init__.py` |
| `bitacora_tags.py` | 323 | `templatetags/bitacora_tags.py` |
| `utils.py` | 58 | `utils.py` |

---

## Árbol de Directorios

```
bitacora/
├── templates
│   └── bitacora
│       ├── content_blocks_list.html
│       ├── dashboard.html
│       ├── entry_confirm_delete.html
│       ├── entry_detail.html
│       ├── entry_form.html
│       └── entry_list.html
├── templatetags
│   ├── __init__.py
│   └── bitacora_tags.py
├── BITACORA_CONTEXT.md
├── BITACORA_DESIGN.md
├── BITACORA_DEV_REFERENCE.md
├── __init__.py
├── admin.py
├── apps.py
├── forms.py
├── models.py
├── tests.py
├── urls.py
├── utils.py
└── views.py
```

---

## Endpoints registrados

Fuente: `urls.py`  |  namespace: `bitacora`

```python
  path('', views.BitacoraListView.as_view(), name='dashboard'),
  path('list/', views.BitacoraListView.as_view(template_name='bitacora/entry_list.html'), name='list'),
  path('<uuid:pk>/', views.BitacoraDetailView.as_view(), name='detail'),
  path('create/', views.BitacoraCreateView.as_view(), name='create'),
  path('<uuid:pk>/update/', views.BitacoraUpdateView.as_view(), name='update'),
  path('<uuid:pk>/delete/', views.BitacoraDeleteView.as_view(), name='delete'),
  path('content-blocks/', views.content_blocks_list, name='content_blocks'),
  path('<uuid:entry_id>/insert-block/<int:block_id>/', views.insert_content_block, name='insert_content_block'),
  path('upload-image/', views.upload_image, name='upload_image'),
```

---

## Modelos detectados

**`models.py`**

- línea 11: `class CategoriaChoices(models.TextChoices):`
- línea 22: `class MoodChoices(models.TextChoices):`
- línea 30: `class BitacoraEntry(models.Model):`
- línea 99: `class BitacoraAttachment(models.Model):`


---

## Migraciones

| Archivo | Estado |
|---------|--------|
| `0001_initial` | aplicada |
| `0002_alter_bitacoraentry_contenido` | aplicada |
| `0003_refactor_conventions` | aplicada |
| `0004_uuid_primary_keys` | aplicada |

---

## Funciones clave (views/ y services/)


---

## Compartir con Claude

```bash
cat /data/data/com.termux/files/home/projects/Management360/bitacora/views/mi_vista.py | termux-clipboard-set
```
