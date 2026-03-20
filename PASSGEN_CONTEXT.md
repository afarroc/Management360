# Mapa de Contexto — App `passgen`

> Generado por `m360_map.sh`  |  2026-03-20 09:53:34
> Ruta: `/data/data/com.termux/files/home/projects/Management360/passgen`  |  Total archivos: **12**

---

## Índice

| # | Categoría | Archivos |
|---|-----------|----------|
| 1 | 👁 `views` | 1 |
| 2 | 🎨 `templates` | 3 |
| 3 | 🗃 `models` | 1 |
| 4 | 📝 `forms` | 1 |
| 5 | 🔗 `urls` | 1 |
| 6 | 🛡 `admin` | 1 |
| 7 | 📄 `other` | 4 |

---

## Archivos por Categoría


### VIEWS (1 archivos)

| Archivo | Líneas | Ruta relativa |
|---------|--------|---------------|
| `views.py` | 95 | `views.py` |

### TEMPLATES (3 archivos)

| Archivo | Líneas | Ruta relativa |
|---------|--------|---------------|
| `generar.html` | 205 | `templates/passgen/generar.html` |
| `info.html` | 93 | `templates/passgen/info.html` |
| `resultado.html` | 9 | `templates/passgen/resultado.html` |

### MODELS (1 archivos)

| Archivo | Líneas | Ruta relativa |
|---------|--------|---------------|
| `models.py` | 3 | `models.py` |

### FORMS (1 archivos)

| Archivo | Líneas | Ruta relativa |
|---------|--------|---------------|
| `forms.py` | 49 | `forms.py` |

### URLS (1 archivos)

| Archivo | Líneas | Ruta relativa |
|---------|--------|---------------|
| `urls.py` | 7 | `urls.py` |

### ADMIN (1 archivos)

| Archivo | Líneas | Ruta relativa |
|---------|--------|---------------|
| `admin.py` | 3 | `admin.py` |

### OTHER (4 archivos)

| Archivo | Líneas | Ruta relativa |
|---------|--------|---------------|
| `__init__.py` | 0 | `__init__.py` |
| `apps.py` | 6 | `apps.py` |
| `generators.py` | 428 | `generators.py` |
| `passgen_tags.py` | 8 | `templatetags/passgen_tags.py` |

---

## Árbol de Directorios

```
passgen/
├── templates
│   └── passgen
│       ├── generar.html
│       ├── info.html
│       └── resultado.html
├── templatetags
│   └── passgen_tags.py
├── __init__.py
├── admin.py
├── apps.py
├── forms.py
├── generators.py
├── models.py
├── urls.py
└── views.py
```

---

## Endpoints registrados

Fuente: `urls.py`

```python
  path('generate/', views.generate_password, name='generate_password'),
  path('help/', views.password_help, name='password_help'),
```

---

## Modelos detectados

**`models.py`**

