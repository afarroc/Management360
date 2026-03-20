# Handoff — Sesión Analista Doc · Management360
> **Fecha:** 2026-03-20
> **Sesión:** Documentación técnica — lote 4 (última tanda)
> **Apps documentadas esta sesión:** 3 (help, api, panel)
> **Total documentadas en el proyecto:** 20 / 20 ✅

---

## Apps completadas esta sesión

| App | DEV_REFERENCE | DESIGN | Archivos generados |
|-----|:---:|:---:|------------------------|
| `help` | ✅ nuevo | ✅ nuevo | `HELP_DEV_REFERENCE.md`, `HELP_DESIGN.md` |
| `api` | ✅ nuevo | ✅ nuevo | `API_DEV_REFERENCE.md`, `API_DESIGN.md` |
| `panel` | ✅ nuevo | ✅ nuevo | `PANEL_DEV_REFERENCE.md`, `PANEL_DESIGN.md` |

---

## Estado global de documentación

| App | CONTEXT.md | DEV_REFERENCE.md | DESIGN.md | Tests |
|-----|:---:|:---:|:---:|-------|
| analyst | ✅ auto | ✅ | ✅ | ⚠️ stub |
| sim | ✅ auto | ✅ | ✅ | ✅ 100% |
| bitacora | ✅ auto | ✅ | ✅ | ⚠️ stub |
| simcity | ✅ auto | ✅ | ✅ | ⚠️ stub |
| events | ✅ auto | ✅ | ✅ | ✅ |
| accounts | ✅ auto | ✅ | ✅ | ✅ |
| core | ✅ auto | ✅ | ✅ | ✅ |
| memento | ✅ auto | ✅ | ✅ | ✅ |
| chat | ✅ auto | ✅ | ✅ | ❌ |
| rooms | ✅ auto | ✅ | ✅ | ❌ |
| courses | ✅ auto | ✅ | ✅ | ❌ |
| bots | ✅ auto | ✅ | ✅ | ⚠️ stub |
| kpis | ✅ auto | ✅ | ✅ | ❌ |
| cv | ✅ auto | ✅ | ✅ | ❌ |
| board | ✅ auto | ✅ | ✅ | ⚠️ stub |
| campaigns | ✅ auto | ✅ | ✅ | ❌ |
| passgen | ✅ auto | ✅ | ✅ | ❌ |
| **help** | ✅ auto | ✅ **nuevo** | ✅ **nuevo** | ⚠️ stub |
| **api** | ✅ auto | ✅ **nuevo** | ✅ **nuevo** | ❌ |
| **panel** | ✅ auto | ✅ **nuevo** | ✅ **nuevo** | ✅ test_urls.py |

**Progreso: 20 / 20 apps (100%) ✅ — Sprint 7.5 CERRADO**

---

## Bugs registrados esta sesión (#100–#120)

### `help` — Bugs #100–#110

| # | Impacto | Descripción |
|---|---------|-------------|
| 100 | 🟡 | `get_user_model()` a nivel de módulo en `models.py` |
| **101** | 🔴 | `from courses.models import ...` a nivel de módulo — `CourseCategory` sin uso; si `courses` falla, `help` no carga |
| **102** | 🟠 | `article_feedback_stats` sin `@login_required` — accesible por anónimos |
| 103 | 🟡 | `search_help` evalúa `count()` dos veces — doble hit a BD |
| **104** | 🟠 | `submit_feedback` llama `article.save()` sin `update_fields` — sobreescribe todos los campos |
| 105 | 🟡 | `QuickStartGuide.mark_completed(user)` — `user` ignorado, `UserGuideProgress` no implementado |
| 106 | 🟡 | `get_related_articles()` ignora tags a pesar de la docstring |
| **107** | 🔴 | 3 templates faltantes: `faq_list.html`, `video_tutorials.html`, `quick_start.html` — **TemplateDoesNotExist en runtime** |
| 108 | 🟡 | Sin UUID PK en ningún modelo |
| 109 | 🟡 | `author`/`user` en vez de `created_by` — excepción al estándar |
| **110** | 🟠 | Race condition en `HelpSearchLog` — busca por texto de query para actualizar stats |

### `api` — Bugs #111–#113

| # | Impacto | Descripción |
|---|---------|-------------|
| 111 | 🟡 | Sin `app_name` en `urls.py` — sin namespace |
| **112** | 🟠 | 4 endpoints duplicados entre `panel/urls.py` y `api/urls.py` |
| 113 | 🟡 | `api/token/connection/` y `api/token/subscription/` no incluidos en `api/urls.py` |

### `panel` — Bugs #114–#120

| # | Impacto | Descripción |
|---|---------|-------------|
| **114** | 🔴 | `get_connection_token` sin `return` — endpoint Centrifugo devuelve `None` |
| **115** | 🟠 | `DatabaseSelectorMiddleware` referencia `postgres_online`/`sqlite` inexistentes en `DATABASES` |
| **116** | 🟠 | `storages.py` con ~30 `print()` activos en producción |
| **117** | 🟠 | `RedisTestView` sin `@login_required` en `/redis-test/` |
| 118 | 🟡 | `from django.utils import timezone` a nivel global en `settings.py` |
| 119 | 🟡 | `AUTH_USER_MODEL` definido dos veces al final de `settings.py` |
| 120 | 🟡 | `INSTALLED_APPS += ['django_htmx']` al final del archivo — frágil |

---

## Fixes urgentes recomendados (< 10 min cada uno)

```python
# Bug #114 — panel/views.py — get_connection_token (agregar al final de la función)
token = jwt.encode(token_claims, settings.CENTRIFUGO_TOKEN_SECRET)
return JsonResponse({'token': token})

# Bug #115 — panel/middleware.py
self.db_order = ['default']  # eliminar 'postgres_online' y 'sqlite'

# Bug #117 — panel/views.py
from django.contrib.auth.decorators import login_required
@method_decorator(login_required, name='dispatch')
class RedisTestView(View):
    ...

# Bug #102 — help/views.py
@login_required
def article_feedback_stats(request, article_slug):
    ...

# Bug #104 — help/views.py — submit_feedback
if was_helpful:
    article.helpful_count += 1
    article.save(update_fields=['helpful_count'])
else:
    article.not_helpful_count += 1
    article.save(update_fields=['not_helpful_count'])
```

---

## Hallazgos especiales

### `panel` — `get_connection_token` es un endpoint muerto desde el día 1
La función construye `token_claims` correctamente pero nunca llama a `jwt.encode()` ni retorna nada. Cualquier cliente Centrifugo que solicite un connection token recibe una respuesta HTTP vacía. `get_subscription_token` (el otro endpoint JWT) está correcto — el fix es copiar su patrón de retorno.

### `api` — app que no debería existir como está
`api/views.py` y `api/models.py` son stubs de 3 líneas. `api/urls.py` importa directamente desde `panel`. La app existe pero no tiene identidad propia. Requiere una decisión de arquitectura: o se elimina el `include('api.urls')` del enrutador raíz (dejando solo los registros directos en `panel/urls.py`) o se completa la migración moviendo las vistas. El estado mixto actual es confuso pero funcional.

### `help` — 3 endpoints inaccesibles sin ruido de error en startup
Django no valida la existencia de templates en el arranque. `faq_list`, `video_tutorials` y `quick_start` tienen vistas completas y URLs registradas, pero crashean silenciosamente en el primer request con `TemplateDoesNotExist`. Los templates de `category_detail.html` pueden servir de base para los tres.

### Cadena de fallo más larga del proyecto
```
events.management.* (falla)
  → cv no carga (bug #75)
      → courses no carga (import de cv)
          → help no carga (import de courses, bug #101)
```
`help` es el último eslabón. Cuatro apps en cascada si `events.management` tiene un error de sintaxis.

### `panel.storages.py` — debug en producción
30 líneas de `print()` que se ejecutan en cada upload de archivo y en el startup de Django. No rompe nada pero genera spam considerable en los logs de Render. Reemplazar con `logger.debug()` es tarea de 15 minutos.

---

## Archivos generados esta sesión

```
HELP_DEV_REFERENCE.md
HELP_DESIGN.md
API_DEV_REFERENCE.md
API_DESIGN.md
PANEL_DEV_REFERENCE.md
PANEL_DESIGN.md
PROJECT_DEV_REFERENCE.md  (actualizado — bugs #100-#120, doc 20/20)
PROJECT_DESIGN.md         (actualizado — Sprint 7.5 cerrado, handoff lote 4)
TEAM_ROLES.md             (actualizado — Sprint 8 completo, Sprint 9 asignaciones)
```

---

## Comando de commit

```bash
git add help/ api/ panel/ docs/
git add PROJECT_DEV_REFERENCE.md PROJECT_DESIGN.md TEAM_ROLES.md
git commit -m "docs: documentación completa lote 4 (help, api, panel) — 20/20 apps, bugs #100-#120"
git push origin main
```

---

## Próximos pasos — rol Dev (Sprint 9 activo)

### Fixes críticos heredados (ordenados por impacto)

| # | App | Fix | Esfuerzo |
|---|-----|-----|---------|
| #114 | `panel` | Completar `get_connection_token` | 2 min |
| #107 | `help` | Crear 3 templates faltantes | ~1.5h |
| #84 | `board` | IDOR en `BoardDetailView` | 5 min |
| #96 | `passgen` | `self.CATEGORIES` no definido | 3 min |
| #98 | `passgen` | `MIN_ENTROPY = 20` (era 60) | 1 min |
| #75 | `cv` | Imports lazy de `events.management` | 15 min |
| #76 | `cv` | `reverse('events:project_detail', ...)` | 5 min |
| #115 | `panel` | Limpiar `DatabaseSelectorMiddleware` | 2 min |

### Tareas Sprint 9 (del backlog)

| ID | Tarea | Prioridad |
|----|-------|-----------|
| BOT-2 | Integración bots ↔ sim (ACDAgentSlot) | 🟠 |
| BOT-3 | Pipeline ContactRecord → Lead | 🟠 |
| SIM-7e | Agentes simulados perfilados en ACD | 🔴 |
| REFACTOR-1/2/3 | Dividir views.py gigantes (chat 2017L, rooms 2858L, courses 2309L) | 🟠 |
| NEW-T1 | Tests reales para `analyst` (INC-004) | 🟠 |
| API-ARCH | Decisión arquitectura `api` — Opción A o B | 🟠 |
| HELP-1/2/3 | Templates faltantes (faq, videos, quick_start) | 🔴 |
| PNL-4 | `print()` → `logger` en `storages.py` | 🟠 |
