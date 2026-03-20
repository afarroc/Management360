# Diseño y Roadmap — App `panel`

> **Actualizado:** 2026-03-20
> **Estado:** Funcional — con deuda técnica media
> **Sprint:** Lote 4 documentación

---

## Visión General

`panel` es el paquete de configuración del proyecto Management360. Equivale al directorio `config/` o `project/` en proyectos Django con estructura separada. Contiene el enrutador raíz de las 20 apps, toda la configuración de infraestructura y las vistas de autenticación de la API.

```
panel/
├── settings.py   → configuración global (DB, cache, storage, logging...)
├── urls.py       → enrutador raíz — incluye las 20 apps
├── views.py      → 6 endpoints API + 1 diagnóstico
├── asgi.py       → entry point ASGI (Daphne) + WebSocket routing
├── wsgi.py       → entry point WSGI (fallback)
├── middleware.py → DatabaseSelectorMiddleware
└── storages.py   → RemoteMediaStorage (backend custom)
```

### Entornos de despliegue

```
DEV (Termux / Android 15)
  └── python manage.py runserver via alias `m360`
      DB:      MariaDB 12.2.2 @ 192.168.18.46:3306
      Media:   RemoteMediaStorage @ 192.168.18.51:8000
      Cache:   Redis 7 local → fallback FileBasedCache
      WS:      Daphne (ASGI)

PROD (Render)
  └── Daphne / gunicorn
      DB:      PostgreSQL (DATABASE_URL)
      Media:   RemoteMediaStorage (mismo backend — ⚠️ misma IP hardcodeada)
      Cache:   Redis con SSL (rediss://)
      WS:      Daphne
```

---

## Estado de Implementación

| Componente | Estado | Notas |
|------------|--------|-------|
| `settings.py` | ✅ Funcional | Bug #118, #119, #120 — menores |
| `urls.py` | ✅ Funcional | Duplicación con `api.urls` — bug #112 |
| `views.py` auth | ⚠️ Parcial | `get_connection_token` roto (bug #114) |
| `views.py` RedisTest | ⚠️ Sin protección | Bug #117 |
| `storages.py` | ✅ Funcional | Spam de prints en prod (bug #116) |
| `middleware.py` | ⚠️ Roto parcial | Referencias a BD inexistentes (bug #115) |
| `asgi.py` | ✅ Funcional | Solo chat WS — board pendiente (bug #86) |
| `wsgi.py` | ✅ Funcional | Usado en prod sin Channels |
| Tests | ✅ Existe | `tests/test_urls.py` 58L — único en proyecto |

---

## Arquitectura de Infraestructura

### Flujo de un request HTTP normal

```
Cliente HTTP
    → Daphne (ASGI)
        → ProtocolTypeRouter (asgi.py)
            → get_asgi_application()
                → MIDDLEWARE stack (settings.py)
                    → SecurityMiddleware
                    → WhiteNoiseMiddleware  ← sirve static files
                    → SessionMiddleware
                    → CommonMiddleware
                    → CsrfViewMiddleware
                    → AuthenticationMiddleware
                    → MessageMiddleware
                    → XFrameOptionsMiddleware
                    → DatabaseSelectorMiddleware  ← setea request.database_to_use
                → ROOT_URLCONF (panel/urls.py)
                    → vista correspondiente
```

### Flujo de un WebSocket

```
Cliente WS
    → Daphne (ASGI)
        → ProtocolTypeRouter (asgi.py)
            → AuthMiddlewareStack
                → URLRouter(chat.routing.websocket_urlpatterns)
                    → ChatConsumer (chat/consumers.py)
```

### Flujo de un upload de archivo

```
Vista con FileField
    → DEFAULT_FILE_STORAGE = RemoteMediaStorage
        → POST multipart → http://192.168.18.51:8000/
            → si 200: OK, devuelve name
            → si fallo: raise Exception (no silencioso)
```

---

## Settings específicos a conocer

### Mapa de variables `.env` críticas

```bash
SECRET_KEY=...             # REQUERIDO — server no arranca sin él
DEBUG=True                 # dev=True, prod=False
DATABASE_HOST=192.168.18.46
DATABASE_NAME=management360
DATABASE_PASSWORD=...
REDIS_HOST=localhost
REDIS_PASSWORD=...
CENTRIFUGO_TOKEN_SECRET=... # REQUERIDO para rooms y tokens Centrifugo
EMAIL_HOST_USER=...
EMAIL_HOST_PASSWORD=...
```

### Settings definidos para otras apps

Todos en `settings.py` — consultarlos antes de usar `settings.X` en cualquier app:

```python
CLIPBOARD_TIMEOUT        # core
ANALYST_ETL_ALLOWED_APPS # analyst
ANALYST_ETL_MAX_ROWS     # analyst
BOARD_CONFIG             # board — fix bug #85 ya aplicado
BITACORA_CONFIG          # bitacora
TINYMCE_DEFAULT_CONFIG   # bitacora
```

---

## Roadmap

### Fixes urgentes (< 30 min)

| ID | Bug | Fix |
|----|-----|-----|
| PNL-1 | #114 | Completar `get_connection_token` con `jwt.encode()` + `return JsonResponse` |
| PNL-2 | #115 | Limpiar `db_order` en `DatabaseSelectorMiddleware` — quitar `postgres_online` y `sqlite` |
| PNL-3 | #117 | Agregar `@login_required` a `RedisTestView` |

### Sprint 9 — mejoras

| ID | Tarea | Prioridad |
|----|-------|-----------|
| PNL-4 | Reemplazar `print()` en `storages.py` por logging estructurado | 🟠 |
| PNL-5 | Resolver duplicación API routes (bug #112) — elegir Opción A o B | 🟠 |
| PNL-6 | Activar `board/consumers.py` en `asgi.py` (bug #86) | 🟠 |
| PNL-7 | Limpiar `settings.py` — `AUTH_USER_MODEL` duplicado, `import timezone`, `django_htmx` al lugar correcto | 🟡 |

### Futuro

| Tarea | Nota |
|-------|------|
| `RemoteMediaStorage` para producción | Actualmente usa la misma IP local — definir `MEDIA_URL` diferente por entorno |
| `signup_view` usar form de `accounts` | `UserCreationForm` no incluye `phone` ni `avatar` |
| `DatabaseSelectorMiddleware` | Refactorizar o eliminar — actualmente sin efecto útil |

---

## Notas para Claude

- **`panel` es el paquete de configuración**, no una app de negocio — no tiene modelos, migrations ni templates
- **`ROOT_URLCONF = 'panel.urls'`** — aquí viven todos los includes del proyecto
- **`get_connection_token` está roto** (bug #114) — no tiene `return`. El fix es ~2 líneas idénticas a `get_subscription_token`
- **`request.database_to_use`** seteado por el middleware pero nunca consumido — ignorar salvo que se implemente multi-DB
- **`RemoteMediaStorage`** requiere que `192.168.18.51:8000` esté corriendo en la red local para uploads
- **`CENTRIFUGO_TOKEN_SECRET`** debe estar en `.env` — si falta, `get_subscription_token` falla en runtime
- **`BOARD_CONFIG`** ya está definido (fix bug #85 aplicado) con `CARDS_PER_PAGE: 12`
- **`ASGI_APPLICATION = 'panel.asgi.application'`** — el servidor debe arrancarse con Daphne, no con `runserver` simple para WebSockets
- **`DATABASES` solo tiene `'default'`** — `DatabaseSelectorMiddleware` intentará `postgres_online` y `sqlite` que no existen
- **`AUTH_USER_MODEL`** definido dos veces al final — ambas con el mismo valor, no hay impacto funcional
- **Tests existen** en `panel/tests/test_urls.py` — única app con tests de resolución de URLs
