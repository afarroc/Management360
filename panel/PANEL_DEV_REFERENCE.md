# Referencia de Desarrollo — App `panel`

> **Actualizado:** 2026-03-20 (Sesión Analista Doc — lote 4)
> **Audiencia:** Desarrolladores y Claude
> **Stats:** 9 archivos · settings.py 526L · storages.py 140L · views.py 117L · urls.py 60L · middleware.py 33L
> **Bugs registrados:** #114–#120
> **Nota:** `panel` NO es una app Django convencional — es el **paquete de configuración del proyecto**

---

## Índice

| # | Sección |
|---|---------|
| 1 | Resumen |
| 2 | Vistas (`views.py`) |
| 3 | Enrutador raíz (`urls.py`) |
| 4 | Configuración (`settings.py`) |
| 5 | Almacenamiento remoto (`storages.py`) |
| 6 | Middleware (`middleware.py`) |
| 7 | ASGI (`asgi.py`) |
| 8 | Variables de entorno requeridas |
| 9 | Settings específicos por app |
| 10 | Convenciones críticas |
| 11 | Bugs conocidos |
| 12 | Deuda técnica |

---

## 1. Resumen

`panel` es el **paquete de configuración del proyecto** Management360 (equivale al directorio `config/` en otros proyectos Django). Contiene:

- `settings.py` — configuración global del proyecto
- `urls.py` — enrutador raíz que incluye las 20 apps
- `views.py` — 6 vistas de autenticación/utilidad de la API y una vista de diagnóstico Redis
- `middleware.py` — middleware de selección de base de datos
- `storages.py` — backend de almacenamiento remoto (desarrollo)
- `asgi.py` / `wsgi.py` — entry points del servidor

Tiene `tests/test_urls.py` (58L) — la única app del proyecto con tests de URLs.

---

## 2. Vistas (`views.py`)

Siete vistas, divididas en dos grupos funcionales:

### Grupo API — autenticación JSON

Todos responden JSON. Usados por clientes SPA o el frontend HTMX para flujos de auth sin redirección.

| Vista | Método | Auth | Descripción |
|-------|--------|------|-------------|
| `get_csrf` | GET | No | Devuelve `{}` con header `X-CSRFToken` para inicializar sesión CSRF |
| `login_view` | POST | No | Acepta JSON `{username, password}` → crea sesión Django. Devuelve `{user: {id, username}}` |
| `logout_view` | POST | Sí | Invalida sesión. Devuelve `{}` |
| `signup_view` | GET/POST | No | ⚠️ Vista **web** (no JSON) — usa `UserCreationForm` → redirige a `'index'` |
| `get_connection_token` | GET | Sí | JWT para Centrifugo — ⚠️ **incompleto** (bug #114) |
| `get_subscription_token` | GET | Sí | JWT para canal personal Centrifugo `personal:<user_pk>` |

#### `get_connection_token` — bug crítico

```python
def get_connection_token(request):
    # ... construye token_claims ...
    # ← FALTA: jwt.encode(...) y return JsonResponse(...)
    # La función no retorna nada → respuesta HTTP vacía (None)
```

La función construye `token_claims` pero no llama a `jwt.encode()` ni retorna nada. Cualquier cliente que llame a `/api/token/connection/` recibe una respuesta vacía (bug #114).

#### `get_subscription_token` — implementación correcta

```python
token_claims = {
    'sub': str(request.user.pk),
    'exp': int(time.time()) + 300,  # 5 min
    'channel': channel              # 'personal:<pk>'
}
token = jwt.encode(token_claims, settings.CENTRIFUGO_TOKEN_SECRET)
return JsonResponse({'token': token})
```

Solo permite suscripción al canal propio (`personal:<user_pk>`). Requiere `CENTRIFUGO_TOKEN_SECRET` en settings/env.

#### `signup_view` — mezcla de paradigma

Es la única vista web (no JSON) del archivo. Usa `UserCreationForm` de Django (sin campos custom como `phone` o `avatar` del modelo `accounts.User`). Redirige a `'index'` al registrarse — puede coexistir con `accounts.views` si los templates/flujos son distintos.

### Grupo Diagnóstico

| Vista | Clase | Auth | Descripción |
|-------|-------|------|-------------|
| `RedisTestView` | CBV `View` | No | GET — conecta a Redis, hace `set/get` de test, devuelve JSON con resultado |

`RedisTestView` está expuesta en `/redis-test/` sin ninguna protección de autenticación (bug #117).

---

## 3. Enrutador raíz (`urls.py`)

`ROOT_URLCONF = 'panel.urls'` — este archivo es el punto de entrada de todas las rutas del proyecto.

### Apps incluidas (20)

| Prefijo | App | Namespace |
|---------|-----|-----------|
| `/` | `core.urls` | — (no declarado en core) |
| `/accounts/` | `accounts.urls` | — |
| `/campaigns/` | `campaigns.urls` | — |
| `/chat/` | `chat.urls` | `chat` |
| `/courses/` | `courses.urls` | — |
| `/cv/` | `cv.urls` | `cv` |
| `/events/` | `events.urls` | — |
| `/kpis/` | `kpis.urls` | `kpis` ✅ |
| `/memento/` | `memento.urls` | `memento` ✅ (include externo) |
| `/passgen/` | `passgen.urls` | — ⚠️ bug #95 |
| `/rooms/` | `rooms.urls` | `rooms` |
| `/bots/` | `bots.urls` | `bots` |
| `/help/` | `help.urls` | `help` |
| `/bitacora/` | `bitacora.urls` | `bitacora` |
| `/board/` | `board.urls` | `board` |
| `/analyst/` | `analyst.urls` | `analyst` |
| `/sim/` | `sim.urls` | `sim` |
| `/simcity/` | `simcity.urls` | `simcity` |
| `/api/` | `api.urls` | — ⚠️ bug #111 |
| `/admin/` | `admin.site.urls` | — |

### Rutas directas en `panel/urls.py`

Además de los includes, `panel/urls.py` registra directamente:

| URL | Vista | Name | Nota |
|-----|-------|------|------|
| `/ckeditor5/upload/` | `upload_image` | `ck_editor_5_upload_file` | CKEditor 5 |
| `/api/csrf/` | `views.get_csrf` | `api-csrf` | ⚠️ duplicada con `api.urls` |
| `/api/login/` | `views.login_view` | `api-login` | ⚠️ duplicada |
| `/api/logout/` | `views.logout_view` | `api-logout` | ⚠️ duplicada |
| `/api/signup/` | `views.signup_view` | `api-signup` | ⚠️ duplicada |
| `/api/token/connection/` | `views.get_connection_token` | `api-connection-token` | Solo aquí |
| `/api/token/subscription/` | `views.get_subscription_token` | `api-subscription-token` | Solo aquí |
| `/redis-test/` | `RedisTestView` | `redis_test` | Diagnóstico |

---

## 4. Configuración (`settings.py`)

### Entornos

| Parámetro | `DEBUG=True` (Termux) | `DEBUG=False` (Render) |
|-----------|----------------------|----------------------|
| DB | MySQL en `192.168.18.46:3306` | PostgreSQL via `DATABASE_URL` (dj_database_url) |
| Cache | Redis → fallback FileBasedCache | Redis con SSL (`rediss://`) |
| Storage | `RemoteMediaStorage` → `http://192.168.18.51:8000/` | `RemoteMediaStorage` (mismo) |
| Email | `console.EmailBackend` | SMTP Gmail |
| WebSocket Redis | `redis://` | `rediss://` con `ssl_cert_reqs=None` |
| HSTS/SSL | Off | On — `SECURE_SSL_REDIRECT=True` |

### Cache — lógica de fallback en startup

`settings.py` ejecuta `_build_caches()` en el momento de importación. Intenta conectar a Redis con timeout de 2s:
- Si Redis responde → `django_redis.cache.RedisCache`
- Si falla → `FileBasedCache` en `.django_cache/` (persiste en disco)

```
KEY_PREFIX = 'panel'
TIMEOUT = 1800 (30 min)
MAX_CONNECTIONS = 20
```

### Configuraciones por app registradas en settings

Ver sección 9 para detalle. Resumen:

| Setting | App que lo usa |
|---------|----------------|
| `CLIPBOARD_TIMEOUT = 3600` | `core` (portapapeles) |
| `ANALYST_ETL_ALLOWED_APPS = []` | `analyst` (ETL) |
| `ANALYST_ETL_MAX_ROWS = 100_000` | `analyst` (ETL) |
| `BOARD_CONFIG` | `board` (fix bug #85) |
| `BITACORA_CONFIG` | `bitacora` (upload imágenes) |
| `TINYMCE_DEFAULT_CONFIG` | `bitacora` (editor) |
| `CENTRIFUGO_TOKEN_SECRET` | `rooms`, `panel/views.py` (JWT) |
| `CENTRIFUGO_*` | `rooms` (API Centrifugo) |
| `REDIS_URL` | múltiples |

### Notas importantes de settings

- `AUTH_USER_MODEL = 'accounts.User'` definido **dos veces** al final del archivo (bug #119)
- `from django.utils import timezone` importado a nivel global — solo se usa en `TINYMCE_DEFAULT_CONFIG` (bug #118)
- `DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'` — los modelos sin PK explícito usan BigAutoField (int 64-bit), no UUID
- `ALLOWED_HOSTS` hardcodea IPs de red local (`192.168.18.46`, `192.168.18.47`) — riesgo si cambia la red
- `django_htmx` se agrega a `INSTALLED_APPS` con `+=` al final del archivo — funciona pero frágil (bug #120)

---

## 5. Almacenamiento remoto (`storages.py`)

`RemoteMediaStorage` es el backend custom de archivos de media. Sube archivos via HTTP POST multipart a `MEDIA_URL` (servidor en `192.168.18.51:8000` en dev).

### Métodos implementados

| Método | Comportamiento |
|--------|----------------|
| `_save(name, content)` | POST multipart al servidor remoto. Si falla → `raise Exception` (no fallback silencioso) |
| `_open(name, mode)` | GET al servidor remoto → `BytesIO` |
| `exists(name)` | HEAD request |
| `url(name)` | `f"{server_url}/{name}"` |
| `delete(name)` | `pass` — no implementado |
| `size(name)` | HEAD + `content-length` header |

### Debug prints — problema en producción

`storages.py` tiene **decenas de `print()`** que se ejecutan en producción (bug #116):
- Al importar el módulo: `=== REMOTE MEDIA STORAGE MODULE LOADED ===`
- Al inicializar: 5 prints
- Por cada `_save()`: ~20 prints con detalles del upload

### Inicialización forzada en `settings.py`

```python
# settings.py líneas 253-259
from django.core.files.storage import default_storage
from panel.storages import RemoteMediaStorage

if not isinstance(default_storage, RemoteMediaStorage):
    print("=== FORCING REMOTE MEDIA STORAGE ===")
    default_storage._wrapped = RemoteMediaStorage()
```

Esto fuerza la inicialización del storage custom en el startup de Django, incluso en entornos donde `DEFAULT_FILE_STORAGE` no fue suficiente. Es un workaround que genera prints adicionales.

---

## 6. Middleware (`middleware.py`)

### `DatabaseSelectorMiddleware`

Middleware que intenta conectar a bases de datos en orden de prioridad y setea `request.database_to_use`.

```python
self.db_order = ['default', 'postgres_online', 'sqlite']
```

**Problema:** `postgres_online` y `sqlite` no están definidos en `DATABASES` de `settings.py` (bug #115). El middleware ejecuta `connections[db].ensure_connection()` en **cada request** para las BD que sí existen, lo que agrega latencia. Para BD no configuradas, lanza `KeyError` antes del `OperationalError`, que no está capturado.

**Posición en middleware stack:** último en la lista (`MIDDLEWARE`), después de `XFrameOptionsMiddleware`. Se ejecuta en cada request.

**`request.database_to_use`** — este atributo no se usa en ninguna vista conocida del proyecto. El middleware está activo pero su output es ignorado.

---

## 7. ASGI (`asgi.py`)

```python
application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter(websocket_urlpatterns)  # ← de chat.routing
    ),
})
```

Solo enruta WebSockets de `chat`. `board/consumers.py` tiene un `BoardConsumer` implementado pero **no está registrado aquí** (bug #86, ya registrado). Para activar WebSockets de `board`:

```python
# asgi.py — agregar
from board.routing import board_websocket_urlpatterns  # crear este archivo
# y combinar con websocket_urlpatterns de chat
```

---

## 8. Variables de entorno requeridas

Archivo `.env` con las siguientes variables (vía `python-decouple`):

| Variable | Requerida | Default | Descripción |
|----------|-----------|---------|-------------|
| `SECRET_KEY` | ✅ Sí | — | Django secret key — error en startup si falta |
| `DEBUG` | No | `False` | Activa modo desarrollo |
| `ALLOWED_HOSTS` | No | IPs locales + localhost | Hosts permitidos |
| `DATABASE_NAME` | No | `management360` | Solo en DEBUG |
| `DATABASE_USER` | No | `root` | Solo en DEBUG |
| `DATABASE_PASSWORD` | No | `''` | Solo en DEBUG |
| `DATABASE_HOST` | No | `192.168.18.46` | Solo en DEBUG |
| `DATABASE_PORT` | No | `3306` | Solo en DEBUG |
| `DATABASE_URL` | ✅ en prod | — | PostgreSQL URL — solo en producción |
| `REDIS_HOST` | No | `localhost` | |
| `REDIS_PORT` | No | `6379` | |
| `REDIS_PASSWORD` | No | `''` | |
| `REDIS_DB` | No | `0` | |
| `CENTRIFUGO_TOKEN_SECRET` | ✅ para rooms | — | JWT secret para tokens Centrifugo |
| `EMAIL_HOST` | No | `smtp.gmail.com` | |
| `EMAIL_PORT` | No | `587` | |
| `EMAIL_USE_TLS` | No | `True` | |
| `EMAIL_HOST_USER` | No | — | |
| `EMAIL_HOST_PASSWORD` | No | — | |
| `RENDER_EXTERNAL_HOSTNAME` | No | — | Auto-detectado en Render |

> ⚠️ `CENTRIFUGO_TOKEN_SECRET` no tiene default — si no está en `.env`, `get_subscription_token` lanza `KeyError` o usa `None` como secret.

---

## 9. Settings específicos por app

### `BOARD_CONFIG` (fix bug #85)
```python
BOARD_CONFIG = {
    'CARDS_PER_PAGE': 12,           # board/htmx_views.py
    'ALLOWED_IMAGE_TYPES': [...],
    'MAX_IMAGE_SIZE': 10 * 1024 * 1024,
    'ENABLE_WEBSOCKETS': True,       # no usado todavía
}
```

### `BITACORA_CONFIG`
```python
BITACORA_CONFIG = {
    'IMAGE_UPLOAD_PATH': 'bitacora/images/',
    'IMAGE_MAX_SIZE': 5 * 1024 * 1024,
    'ALLOWED_IMAGE_TYPES': ['image/jpeg', 'image/png', 'image/gif', 'image/webp'],
    'CONTENT_BLOCKS_ENABLED': True,
    'TEMPLATES_ENABLED': True,
    'STRUCTURED_CONTENT_ENABLED': True,
}
```

### `ANALYST_ETL_*`
```python
ANALYST_ETL_ALLOWED_APPS = []       # [] = todas las apps no excluidas
ANALYST_ETL_MAX_ROWS = 100_000      # límite para no-superusers
```

### `TINYMCE_DEFAULT_CONFIG`
Configurado para `bitacora`. `images_upload_url` apunta a `/bitacora/upload-image/`. Tiene 3 plantillas predefinidas: Personal, Trabajo, Meta.

---

## 10. Convenciones críticas

- **`panel` no es una "app" en sentido Django** — no tiene modelos, migrations, admin, ni templates propios
- **Las vistas de `panel/views.py` son accesibles via dos rutas** — directas en `panel/urls.py` Y via `include('api.urls')`. Resolver con bug #112
- **`request.database_to_use`** seteado por `DatabaseSelectorMiddleware` pero no consumido por ninguna vista — actualmente sin efecto útil
- **`RemoteMediaStorage`** falla con `raise Exception` si el servidor `192.168.18.51:8000` no responde — en Termux offline, todos los uploads de archivos fallan
- **`get_connection_token` no retorna nada** (bug #114) — no usar para Centrifugo hasta corregir
- **`CENTRIFUGO_TOKEN_SECRET`** — necesario en `.env` para `rooms` y para `get_subscription_token`
- **`AUTH_USER_MODEL`** definido dos veces al final del archivo — el segundo sobreescribe al primero (mismo valor, no hay conflicto funcional, pero es ruido)

---

## 11. Bugs conocidos

| # | Impacto | Descripción |
|---|---------|-------------|
| **114** | 🔴 | `get_connection_token` no tiene `return` — devuelve `None`, endpoint inaccesible para Centrifugo |
| **115** | 🟠 | `DatabaseSelectorMiddleware` referencia `postgres_online` y `sqlite` que no existen en `DATABASES` — KeyError por request |
| **116** | 🟠 | `storages.py` tiene ~30 `print()` que se ejecutan en producción — spam en logs |
| **117** | 🟠 | `RedisTestView` sin `@login_required` ni restricción staff — accesible públicamente |
| **118** | 🟡 | `from django.utils import timezone` a nivel global en `settings.py` — solo usado en `TINYMCE_DEFAULT_CONFIG` |
| **119** | 🟡 | `AUTH_USER_MODEL = 'accounts.User'` definido dos veces al final del archivo |
| **120** | 🟡 | `INSTALLED_APPS += ['django_htmx']` al final del archivo — frágil, debería estar en el bloque principal |

---

## 12. Deuda técnica

### Alta prioridad

- **Bug #114** — Completar `get_connection_token`: agregar `jwt.encode(token_claims, settings.CENTRIFUGO_TOKEN_SECRET)` y `return JsonResponse({'token': token})`. Idéntico al patrón de `get_subscription_token`.
- **Bug #115** — Limpiar `DatabaseSelectorMiddleware`: eliminar `'postgres_online'` y `'sqlite'` del `db_order` o definirlos en `DATABASES`. Si el middleware no se usa, desactivarlo del stack.

### Media prioridad

- **Bug #116** — Reemplazar todos los `print()` en `storages.py` por `logger.debug()` / `logger.info()`.
- **Bug #117** — Agregar `@login_required` o `@staff_member_required` a `RedisTestView`.
- **Bug #112** — Resolver duplicación de rutas `/api/*` entre `panel/urls.py` y `api/urls.py` (ver `API_DESIGN.md`).

### Baja prioridad

- **Bug #119** — Eliminar el `AUTH_USER_MODEL` duplicado.
- **Bug #120** — Mover `django_htmx` al bloque `INSTALLED_APPS` principal.
- **Bug #118** — Mover `import timezone` al interior de `TINYMCE_DEFAULT_CONFIG` o usar un valor estático.
- `ALLOWED_HOSTS` hardcodeados — parametrizar con `config('ALLOWED_HOSTS_EXTRA', default='').split(',')`.
- `signup_view` usa `UserCreationForm` (Django default) en vez de el form custom de `accounts` — no incluye campos extra (`phone`, `avatar`).
