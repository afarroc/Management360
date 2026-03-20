# Mapa de Contexto — App `campaigns`

> Generado por `m360_map.sh`  |  2026-03-20 09:53:33
> Ruta: `/data/data/com.termux/files/home/projects/Management360/campaigns`  |  Total archivos: **6**

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
| `views.py` | 157 | `views.py` |

### MODELS (1 archivos)

| Archivo | Líneas | Ruta relativa |
|---------|--------|---------------|
| `models.py` | 69 | `models.py` |

### URLS (1 archivos)

| Archivo | Líneas | Ruta relativa |
|---------|--------|---------------|
| `urls.py` | 19 | `urls.py` |

### ADMIN (1 archivos)

| Archivo | Líneas | Ruta relativa |
|---------|--------|---------------|
| `admin.py` | 3 | `admin.py` |

### OTHER (2 archivos)

| Archivo | Líneas | Ruta relativa |
|---------|--------|---------------|
| `__init__.py` | 0 | `__init__.py` |
| `apps.py` | 5 | `apps.py` |

---

## Árbol de Directorios

```
campaigns/
├── __init__.py
├── admin.py
├── apps.py
├── models.py
├── urls.py
└── views.py
```

---

## Endpoints registrados

Fuente: `urls.py`  |  namespace: `campaigns`

```python
  path('', views.dashboard, name='dashboard'),
  path('campaigns/', views.campaign_list, name='campaign_list'),
  path('campaigns/<uuid:pk>/', views.campaign_detail, name='campaign_detail'),
  path('campaigns/<uuid:campaign_id>/contacts/', views.contact_list, name='contact_list'),
  path('discador/', views.discador_loads, name='discador_loads'),
  path('discador/<int:pk>/', views.discador_load_detail, name='discador_load_detail'),
```

---

## Modelos detectados

**`models.py`**

- línea 6: `class ProviderRawData(models.Model):`
- línea 24: `class ContactRecord(models.Model):`
- línea 52: `class DiscadorLoad(models.Model):`


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
cat /data/data/com.termux/files/home/projects/Management360/campaigns/views/mi_vista.py | termux-clipboard-set
```
