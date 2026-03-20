# Referencia de Desarrollo — App `api`

> **Actualizado:** 2026-03-20 (Sesión Analista Doc — lote 4)
> **Audiencia:** Desarrolladores y Claude
> **Stats:** 6 archivos · views.py 3L (stub) · models.py 3L (stub) · urls.py 8L
> **Bugs registrados:** #111–#113

---

## Índice

| # | Sección |
|---|---------|
| 1 | Resumen |
| 2 | Modelos |
| 3 | Vistas |
| 4 | URLs |
| 5 | Relación con `panel` |
| 6 | Convenciones críticas |
| 7 | Bugs conocidos |
| 8 | Deuda técnica |

---

## 1. Resumen

`api` es una **app de enrutamiento puro** — no contiene lógica propia. Su única función es exponer bajo el prefijo `/api/` cuatro endpoints cuya implementación real vive en `panel/views.py`.

La app fue creada como placeholder para una futura API REST independiente (el comentario en `panel/urls.py` lo confirma: `# Crear app "api" para estos endpoints`). En el estado actual, el movimiento está hecho a medias: los URLs apuntan a `api.urls`, pero `api/urls.py` a su vez importa directamente desde `panel`.

**Esto no es un error funcional** — los endpoints responden correctamente. Es deuda de arquitectura.

---

## 2. Modelos

**Ninguno.** `models.py` es el stub generado por `startapp`:

```python
from django.db import models
# Create your models here.
```

---

## 3. Vistas

**Ninguna propia.** `views.py` es el stub generado por `startapp`:

```python
from django.shortcuts import render
# Create your views here.
```

Las vistas reales están en `panel/views.py`. Ver `PANEL_DEV_REFERENCE.md` para documentación de `get_csrf`, `login_view`, `logout_view` y `signup_view`.

---

## 4. URLs

**Namespace:** ⚠️ NO declarado — `app_name` ausente en `urls.py` (bug #111).

El enrutador raíz (`panel/urls.py`) registra los mismos endpoints **dos veces**:

```python
# Registro directo en panel/urls.py (con prefijo /api/)
path('api/csrf/',  views.get_csrf,     name='api-csrf'),
path('api/login/', views.login_view,   name='api-login'),
path('api/logout/', views.logout_view, name='api-logout'),
path('api/signup/', views.signup_view, name='api-signup'),
path('api/token/connection/',     views.get_connection_token,    name='api-connection-token'),
path('api/token/subscription/',   views.get_subscription_token,  name='api-subscription-token'),

# Y también via include (bug #112 — rutas duplicadas)
path('api/', include('api.urls')),
```

Los cuatro endpoints de `api.urls` quedan accesibles en **dos rutas distintas**:

| URL via include | URL directa en panel |
|-----------------|----------------------|
| `/api/csrf/` | `/api/csrf/` |
| `/api/login/` | `/api/login/` |
| `/api/logout/` | `/api/logout/` |
| `/api/signup/` | `/api/signup/` |

Django resuelve el primero que encuentre en orden — en la práctica el `include` llega después de los registros directos, por lo que la resolución inversa (`reverse('api-csrf')`) apunta a los directos. Las rutas via `include` son unreachable en la práctica pero no dan error.

Los endpoints de token (`api/token/connection/` y `api/token/subscription/`) están **solo en el registro directo** — no están en `api/urls.py` (bug #113).

---

## 5. Relación con `panel`

```
panel/urls.py (enrutador raíz)
├── path('api/csrf/', panel_views.get_csrf)        ← directo
├── path('api/login/', panel_views.login_view)     ← directo
├── path('api/logout/', panel_views.logout_view)   ← directo
├── path('api/signup/', panel_views.signup_view)   ← directo
├── path('api/token/connection/', ...)             ← solo aquí
├── path('api/token/subscription/', ...)           ← solo aquí
└── path('api/', include('api.urls'))              ← api/urls.py
                                                        └── from panel import views
                                                            ├── get_csrf
                                                            ├── login_view
                                                            ├── logout_view
                                                            └── signup_view
```

Para documentación de la implementación real de cada endpoint, ver `PANEL_DEV_REFERENCE.md`.

---

## 6. Convenciones críticas

- `api` **no tiene `app_name`** — no usar `reverse('api:...')`, los nombres están en el espacio global (`api-csrf`, `api-login`, etc.)
- Toda la lógica vive en `panel/views.py` — **no modificar `api/views.py`** para agregar lógica; usar `panel` o crear un módulo separado
- Si se quiere convertir en API REST real (DRF), el esqueleto ya está: la app existe, tiene URLs, solo falta migrar las vistas

---

## 7. Bugs conocidos

| # | Impacto | Descripción |
|---|---------|-------------|
| **111** | 🟡 | Sin `app_name` en `urls.py` — sin namespace, igual que bug #95 en `passgen` |
| **112** | 🟠 | Rutas duplicadas — los 4 endpoints registrados tanto en `panel/urls.py` directamente como via `include('api.urls')` |
| **113** | 🟡 | `api/token/connection/` y `api/token/subscription/` no incluidos en `api/urls.py` — inconsistencia en el contrato de la app |

---

## 8. Deuda técnica

### Alta prioridad

- **Bug #112** — Decidir la arquitectura: o eliminar los registros directos en `panel/urls.py` (dejando solo el `include`) o eliminar el `include` y documentar que `api` es solo un placeholder vacío. El estado mixto actual es confuso.

### Media prioridad

- **Bug #113** — Mover `api/token/connection/` y `api/token/subscription/` a `api/urls.py` para que todos los endpoints de la API estén en un solo lugar.
- **Bug #111** — Agregar `app_name = 'api'` y actualizar los `name=` a usar namespace consistente.

### Baja prioridad (futuro)

- Migrar vistas de `panel/views.py` a `api/views.py` — completar la intención original de separación
- Evaluar DRF (Django REST Framework) para esta app — ya está en `INSTALLED_APPS` del proyecto
- Agregar autenticación por token (JWT/sesión) para uso desde clientes externos
