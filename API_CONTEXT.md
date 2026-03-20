# Mapa de Contexto — App `api`

> Generado por `m360_map.sh`  |  2026-03-20 14:56:13
> Ruta: `/data/data/com.termux/files/home/projects/Management360/api`  |  Total archivos: **6**

---

## Índice

| # | Categoría | Archivos |
|---|-----------|----------|
| 1 | 👁 `views` | 1 |
| 2 | 🗃 `models` | 1 |
| 3 | 🔗 `urls` | 1 |
| 4 | 🛡 `admin` | 1 |
| 5 | 📄 `other` | 2 |

---

## Archivos por Categoría


### VIEWS (1 archivos)

| Archivo | Líneas | Ruta relativa |
|---------|--------|---------------|
| `views.py` | 3 | `views.py` |

### MODELS (1 archivos)

| Archivo | Líneas | Ruta relativa |
|---------|--------|---------------|
| `models.py` | 3 | `models.py` |

### URLS (1 archivos)

| Archivo | Líneas | Ruta relativa |
|---------|--------|---------------|
| `urls.py` | 8 | `urls.py` |

### ADMIN (1 archivos)

| Archivo | Líneas | Ruta relativa |
|---------|--------|---------------|
| `admin.py` | 3 | `admin.py` |

### OTHER (2 archivos)

| Archivo | Líneas | Ruta relativa |
|---------|--------|---------------|
| `__init__.py` | 0 | `__init__.py` |
| `apps.py` | 6 | `apps.py` |

---

## Árbol de Directorios

```
api/
├── __init__.py
├── admin.py
├── apps.py
├── models.py
├── urls.py
└── views.py
```

---

## Endpoints registrados

Fuente: `urls.py`

```python
  path('csrf/', views.get_csrf, name='api-csrf'),
  path('login/', views.login_view, name='api-login'),
  path('logout/', views.logout_view, name='api-logout'),
  path('signup/', views.signup_view, name='api-signup'),
```

---

## Modelos detectados

**`models.py`**

