# Mapa de Contexto — App `panel`

> Generado por `m360_map.sh`  |  2026-03-20 14:55:22
> Ruta: `/data/data/com.termux/files/home/projects/Management360/panel`  |  Total archivos: **9**

---

## Índice

| # | Categoría | Archivos |
|---|-----------|----------|
| 1 | 👁 `views` | 1 |
| 2 | 🔗 `urls` | 1 |
| 3 | 🧪 `tests` | 1 |
| 4 | 📄 `other` | 6 |

---

## Archivos por Categoría


### VIEWS (1 archivos)

| Archivo | Líneas | Ruta relativa |
|---------|--------|---------------|
| `views.py` | 116 | `views.py` |

### URLS (1 archivos)

| Archivo | Líneas | Ruta relativa |
|---------|--------|---------------|
| `urls.py` | 60 | `urls.py` |

### TESTS (1 archivos)

| Archivo | Líneas | Ruta relativa |
|---------|--------|---------------|
| `test_urls.py` | 58 | `tests/test_urls.py` |

### OTHER (6 archivos)

| Archivo | Líneas | Ruta relativa |
|---------|--------|---------------|
| `__init__.py` | 4 | `__init__.py` |
| `asgi.py` | 15 | `asgi.py` |
| `middleware.py` | 33 | `middleware.py` |
| `settings.py` | 525 | `settings.py` |
| `storages.py` | 140 | `storages.py` |
| `wsgi.py` | 5 | `wsgi.py` |

---

## Árbol de Directorios

```
panel/
├── tests
│   └── test_urls.py
├── __init__.py
├── asgi.py
├── middleware.py
├── settings.py
├── storages.py
├── urls.py
├── views.py
└── wsgi.py
```

---

## Endpoints registrados

Fuente: `urls.py`

```python
  path('ckeditor5/upload/', upload_image, name='ck_editor_5_upload_file'),
  path('admin/', admin.site.urls),
  path('', include('core.urls')),  # Home, About, Contact
  path('accounts/', include('accounts.urls')),
  path('campaigns/', include('campaigns.urls')),
  path('chat/', include('chat.urls', namespace='chat')),
  path('courses/', include('courses.urls')),
  path('cv/', include('cv.urls', namespace='cv')),
  path('events/', include('events.urls')),
  path('kpis/', include('kpis.urls')),
  path('memento/', include('memento.urls')),
  path('passgen/', include('passgen.urls')),
  path('rooms/', include('rooms.urls', namespace='rooms')),
  path('bots/', include('bots.urls', namespace='bots')),
  path('help/', include('help.urls', namespace='help')),
  path('bitacora/', include('bitacora.urls', namespace='bitacora')),
  path('board/', include('board.urls', namespace='board')),
  path('analyst/', include('analyst.urls', namespace='analyst')),
  path('sim/', include('sim.urls', namespace='sim')),    
  path('simcity/', include('simcity.urls', namespace='simcity')),
  path('api/csrf/', views.get_csrf, name='api-csrf'),
  path('api/login/', views.login_view, name='api-login'),
  path('api/logout/', views.logout_view, name='api-logout'),
  path('api/signup/', views.signup_view, name='api-signup'),
  path('api/token/connection/', views.get_connection_token, name='api-connection-token'),
  path('api/token/subscription/', views.get_subscription_token, name='api-subscription-token'),
  path('api/', include('api.urls')),  # Crear app "api" para estos endpoints
  path('redis-test/', RedisTestView.as_view(), name='redis_test'),
```

---

## Modelos detectados


---

## Migraciones

| Archivo | Estado |
|---------|--------|
_Sin migrations/_

---

## Funciones clave (views/ y services/)


---

## Compartir con Claude

```bash
cat /data/data/com.termux/files/home/projects/Management360/panel/views/mi_vista.py | termux-clipboard-set
```
