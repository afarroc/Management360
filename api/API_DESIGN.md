# Diseño y Roadmap — App `api`

> **Actualizado:** 2026-03-20
> **Estado:** Placeholder — enrutamiento puro hacia `panel/views.py`
> **Sprint:** Lote 4 documentación

---

## Visión General

`api` es una app de enrutamiento sin lógica propia. Fue creada para centralizar los endpoints REST bajo el prefijo `/api/`, pero la migración de lógica desde `panel/views.py` nunca se completó.

```
Estado actual:
  /api/csrf/    →  panel.views.get_csrf
  /api/login/   →  panel.views.login_view
  /api/logout/  →  panel.views.logout_view
  /api/signup/  →  panel.views.signup_view
  (todos duplicados en panel/urls.py además)

Estado objetivo:
  api/views.py  →  implementación propia
  api/urls.py   →  todos los endpoints /api/* en un solo lugar
  panel/urls.py →  solo include('api.urls'), sin registros directos
```

---

## Estado de Implementación

| Componente | Estado | Notas |
|------------|--------|-------|
| Modelos | ✅ N/A | Intencionalmente vacío |
| Vistas propias | ❌ Stub | Toda lógica en `panel/views.py` |
| URLs | ⚠️ Parcial | Funciona pero duplicado con panel/urls.py |
| Namespace | ❌ Faltante | Sin `app_name` |
| Token endpoints | ❌ Faltante | No incluidos en `api/urls.py` |
| Tests | ❌ Sin tests | |

---

## Arquitectura de Datos

Sin modelos. Sin dependencias de datos propias.

Depende funcionalmente de `panel/views.py` para toda su lógica.

---

## Roadmap

### Decisión de arquitectura requerida (Manager)

Elegir UNA de las dos opciones:

**Opción A — Consolidar en `panel` (mínimo esfuerzo)**
- Eliminar el `include('api.urls')` de `panel/urls.py`
- Marcar `api` como app legacy/vacía
- Documentar que los endpoints `/api/*` viven en `panel`
- Esfuerzo: 5 minutos

**Opción B — Completar la migración (correcto a largo plazo)**
- Mover implementación de `get_csrf`, `login_view`, etc. a `api/views.py`
- Eliminar los registros directos de `panel/urls.py`
- Agregar `app_name = 'api'` y namespace a todos los `name=`
- Mover `token/connection/` y `token/subscription/` a `api/urls.py`
- Esfuerzo: ~1h

### Si se elige Opción B — Sprint 9

| ID | Tarea | Prioridad |
|----|-------|-----------|
| API-1 | Mover vistas a `api/views.py` | 🟠 |
| API-2 | Agregar `app_name = 'api'` | 🟡 |
| API-3 | Mover token endpoints a `api/urls.py` | 🟡 |
| API-4 | Limpiar registros directos en `panel/urls.py` | 🟡 |

---

## Notas para Claude

- **`api/views.py` está vacío** — no buscar lógica aquí
- **Toda implementación está en `panel/views.py`** — leer `PANEL_DEV_REFERENCE.md`
- **Rutas duplicadas son funcionales** — no rompen nada, solo son confusas
- **Sin namespace** — los endpoints se resuelven como `reverse('api-csrf')` (guión, no dos puntos)
- **DRF instalado** en el proyecto — disponible para usar si se quiere expandir esta app
