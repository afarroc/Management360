# Mapa de Contexto — App `bots`

> Generado por `m360_map.sh`  |  2026-03-19 14:17:42
> Ruta: `/data/data/com.termux/files/home/projects/Management360/bots`  |  Total archivos: **19**

---

## Índice

| # | Categoría | Archivos |
|---|-----------|----------|
| 1 | 👁 `views` | 1 |
| 2 | 🗃 `models` | 1 |
| 3 | 🔗 `urls` | 1 |
| 4 | 🛡 `admin` | 1 |
| 5 | 📄 `management` | 5 |
| 6 | 🧪 `tests` | 1 |
| 7 | 📄 `other` | 9 |

---

## Archivos por Categoría


### VIEWS (1 archivos)

| Archivo | Líneas | Ruta relativa |
|---------|--------|---------------|
| `views.py` | 382 | `views.py` |

### MODELS (1 archivos)

| Archivo | Líneas | Ruta relativa |
|---------|--------|---------------|
| `models.py` | 737 | `models.py` |

### URLS (1 archivos)

| Archivo | Líneas | Ruta relativa |
|---------|--------|---------------|
| `urls.py` | 26 | `urls.py` |

### ADMIN (1 archivos)

| Archivo | Líneas | Ruta relativa |
|---------|--------|---------------|
| `admin.py` | 3 | `admin.py` |

### MANAGEMENT (5 archivos)

| Archivo | Líneas | Ruta relativa |
|---------|--------|---------------|
| `__init__.py` | 0 | `management/__init__.py` |
| `__init__.py` | 0 | `management/commands/__init__.py` |
| `run_bots.py` | 341 | `management/commands/run_bots.py` |
| `setup_bots.py` | 188 | `management/commands/setup_bots.py` |
| `setup_leads_demo.py` | 215 | `management/commands/setup_leads_demo.py` |

### TESTS (1 archivos)

| Archivo | Líneas | Ruta relativa |
|---------|--------|---------------|
| `tests.py` | 3 | `tests.py` |

### OTHER (9 archivos)

| Archivo | Líneas | Ruta relativa |
|---------|--------|---------------|
| `BOTS_CONTEXT.md` | 157 | `BOTS_CONTEXT.md` |
| `BOTS_DESIGN.md` | 158 | `BOTS_DESIGN.md` |
| `BOTS_DEV_REFERENCE.md` | 842 | `BOTS_DEV_REFERENCE.md` |
| `BOTS_HANDOFF.md` | 197 | `BOTS_HANDOFF.md` |
| `__init__.py` | 0 | `__init__.py` |
| `apps.py` | 6 | `apps.py` |
| `gtd_processor.py` | 386 | `gtd_processor.py` |
| `lead_distributor.py` | 394 | `lead_distributor.py` |
| `utils.py` | 341 | `utils.py` |

---

## Árbol de Directorios

```
bots/
├── management
│   ├── commands
│   │   ├── __init__.py
│   │   ├── run_bots.py
│   │   ├── setup_bots.py
│   │   └── setup_leads_demo.py
│   └── __init__.py
├── BOTS_CONTEXT.md
├── BOTS_DESIGN.md
├── BOTS_DEV_REFERENCE.md
├── BOTS_HANDOFF.md
├── __init__.py
├── admin.py
├── apps.py
├── gtd_processor.py
├── lead_distributor.py
├── models.py
├── tests.py
├── urls.py
├── utils.py
└── views.py
```

---

## Endpoints registrados

Fuente: `urls.py`  |  namespace: `bots`

```python
  path('campaigns/', views.lead_campaign_list, name='campaign_list'),
  path('campaigns/create/', views.lead_campaign_create, name='campaign_create'),
  path('campaigns/<int:pk>/', views.lead_campaign_detail, name='campaign_detail'),
  path('campaigns/<int:campaign_pk>/upload/', views.lead_upload, name='lead_upload'),
  path('campaigns/<int:campaign_pk>/rules/', views.lead_distribution_rules, name='distribution_rules'),
  path('campaigns/<int:campaign_pk>/distribute/', views.trigger_distribution, name='trigger_distribution'),
  path('leads/', views.lead_list, name='lead_list'),
  path('leads/<int:pk>/', views.lead_detail, name='lead_detail'),
  path('leads/export/', views.lead_export, name='lead_export'),
  path('api/campaigns/<int:campaign_pk>/stats/', views.api_campaign_stats, name='api_campaign_stats'),
  path('api/campaigns/<int:campaign_pk>/distribute/', views.api_trigger_distribution, name='api_trigger_distribution'),
```

---

## Modelos detectados

**`models.py`**

- línea 13: `class GenericUser(models.Model):`
- línea 32: `class BotCoordinator(models.Model):`
- línea 88: `class BotInstance(models.Model):`
- línea 208: `class BotTaskAssignment(models.Model):`
- línea 277: `class ResourceLock(models.Model):`
- línea 345: `class BotCommunication(models.Model):`
- línea 392: `class BotLog(models.Model):`
- línea 444: `class LeadCampaign(models.Model):`
- línea 483: `class Lead(models.Model):`
- línea 638: `class LeadDistributionRule(models.Model):`


---

## Migraciones

| Archivo | Estado |
|---------|--------|
| `0001_initial` | aplicada |
| `0002_alter_botlog_category_alter_lead_status` | aplicada |

---

## Funciones clave (views/ y services/)


---

## Compartir con Claude

```bash
cat /data/data/com.termux/files/home/projects/Management360/bots/views/mi_vista.py | termux-clipboard-set
```
