# Mapa de Contexto — App `kpis`

> Generado por `m360_map.sh`  |  2026-03-20 09:23:19
> Ruta: `/data/data/com.termux/files/home/projects/Management360/kpis`  |  Total archivos: **11**

---

## Índice

| # | Categoría | Archivos |
|---|-----------|----------|
| 1 | 👁 `views` | 1 |
| 2 | 🎨 `templates` | 4 |
| 3 | 🗃 `models` | 1 |
| 4 | 📝 `forms` | 1 |
| 5 | 🔗 `urls` | 1 |
| 6 | 🛡 `admin` | 1 |
| 7 | 📄 `other` | 2 |

---

## Archivos por Categoría


### VIEWS (1 archivos)

| Archivo | Líneas | Ruta relativa |
|---------|--------|---------------|
| `views.py` | 338 | `views.py` |

### TEMPLATES (4 archivos)

| Archivo | Líneas | Ruta relativa |
|---------|--------|---------------|
| `generate_data.html` | 99 | `templates/generate_data.html` |
| `form_field.html` | 9 | `templates/includes/form_field.html` |
| `kpi_dashboard.html` | 284 | `templates/kpi_dashboard.html` |
| `home.html` | 180 | `templates/kpis/home.html` |

### MODELS (1 archivos)

| Archivo | Líneas | Ruta relativa |
|---------|--------|---------------|
| `models.py` | 148 | `models.py` |

### FORMS (1 archivos)

| Archivo | Líneas | Ruta relativa |
|---------|--------|---------------|
| `forms.py` | 170 | `forms.py` |

### URLS (1 archivos)

| Archivo | Líneas | Ruta relativa |
|---------|--------|---------------|
| `urls.py` | 13 | `urls.py` |

### ADMIN (1 archivos)

| Archivo | Líneas | Ruta relativa |
|---------|--------|---------------|
| `admin.py` | 48 | `admin.py` |

### OTHER (2 archivos)

| Archivo | Líneas | Ruta relativa |
|---------|--------|---------------|
| `__init__.py` | 0 | `__init__.py` |
| `apps.py` | 6 | `apps.py` |

---

## Árbol de Directorios

```
kpis/
├── templates
│   ├── includes
│   │   └── form_field.html
│   ├── kpis
│   │   └── home.html
│   ├── generate_data.html
│   └── kpi_dashboard.html
├── __init__.py
├── admin.py
├── apps.py
├── forms.py
├── models.py
├── urls.py
└── views.py
```

---

## Endpoints registrados

Fuente: `urls.py`  |  namespace: `kpis`

```python
  path('',                views.kpi_home,           name='home'),
  path('dashboard/',      views.aht_dashboard,      name='dashboard'),
  path('api/',            views.kpi_api,             name='api'),
  path('export/',         views.export_data,         name='export_data'),
  path('generate-data/',  views.generate_fake_data,  name='generate_data'),
```

---

## Modelos detectados

**`models.py`**

- línea 37: `class CallRecord(models.Model):`
- línea 115: `class ExchangeRate(models.Model):`


---

## Migraciones

| Archivo | Estado |
|---------|--------|
| `0001_initial` | aplicada |
| `0002_refactor_callrecord` | aplicada |

---

## Funciones clave (views/ y services/)


---

## Compartir con Claude

```bash
cat /data/data/com.termux/files/home/projects/Management360/kpis/views/mi_vista.py | termux-clipboard-set
```
