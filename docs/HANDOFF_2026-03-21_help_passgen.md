# Handoff — Sesión Analista Dev · Management360
> **Fecha:** 2026-03-21
> **Apps:** `passgen`, `help`
> **Sprint:** 9
> **Bugs cerrados:** #96 #98 #101 #102 #103 #104 #107 #110
> **Archivos modificados:** 3 Python + 3 templates HTML

---

## `passgen` — bugs #96 y #98

### Archivos modificados
```
passgen/generators.py
```

### #98 — `MIN_ENTROPY = 60` bloqueaba 5/7 patrones predefinidos

`_validate_password()` rechazaba con `ValueError: Password entropy too low` cualquier
contraseña generada por los patrones `pin` (~20 bits), `phrase` (~35 bits), `basic`
(~45 bits), `date_based` (~40 bits) y `accented` (~55 bits).

Fix: `MIN_ENTROPY = 60` → `20` (valor del patrón más bajo documentado, `pin`).

### #96 — `self.CATEGORIES` no definido → `AttributeError` en `password_help`

`get_context_data()` referenciaba `self.CATEGORIES` que nunca se asignaba en `__init__`.

Fix: derivado dinámicamente al final de `__init__`, agrupando `PREDEFINED_PATTERNS`
por su campo `'category'`:

```python
self.CATEGORIES: Dict[str, List[str]] = {}
for _key, _data in self.PREDEFINED_PATTERNS.items():
    self.CATEGORIES.setdefault(_data['category'], []).append(_key)
```

Resultado: `{'Básico': ['basic'], 'Seguro': ['strong', 'secure'], ...}` — sin hardcodear,
si se añade un patrón nuevo aparece automáticamente en `CATEGORIES`.

---

## `help` — bugs #101 #102 #103 #104 #107 #110

### Archivos modificados
```
help/models.py
help/views.py
help/templates/help/faq_list.html        ← nuevo
help/templates/help/video_tutorials.html ← nuevo
help/templates/help/quick_start.html     ← nuevo
```

### #101 — import `courses.models` a nivel de módulo (cadena de fallo)

`from courses.models import Course, Lesson, ContentBlock, CourseCategory` y
`User = get_user_model()` a nivel de módulo hacían que si `courses` o `auth`
fallaban al arrancar, `help` tampoco cargaba.

Fix: FKs convertidos a strings lazy:
- `Course` → `'courses.Course'`
- `Lesson` → `'courses.Lesson'`
- `ContentBlock` → `'courses.ContentBlock'`
- `User` FKs → `settings.AUTH_USER_MODEL`
- `CourseCategory` eliminado (importado sin uso)
- Header: `from django.conf import settings` + `from django.utils import timezone`

Los métodos `_get_*_content()` no necesitaban el import — ya trabajan con `self.referenced_X`
(objeto cargado por Django al acceder al FK).

### #102 — `article_feedback_stats` accesible sin autenticación

Solo verificaba `request.user.is_staff` manualmente — un anónimo recibía 403 pero
el endpoint era accesible sin sesión.

Fix: `@login_required` añadido antes de la vista.

### #104 — `submit_feedback` sobreescribía todos los campos del artículo

`article.save()` sin `update_fields` escribía todos los campos incluyendo `view_count`,
`updated_at`, etc.

Fix:
```python
if was_helpful:
    article.helpful_count += 1
    article.save(update_fields=['helpful_count'])
else:
    article.not_helpful_count += 1
    article.save(update_fields=['not_helpful_count'])
```

### #103 y #110 — doble `count()` + race condition en `search_help`

Dos problemas en la misma función:
- `total_results` se calculaba dos veces (líneas 344 y 356 del original)
- El log se buscaba por `HelpSearchLog.objects.filter(query=query).last()` — race condition
  si dos usuarios buscan el mismo término simultáneamente

Fix: guardar la instancia en `search_log` al hacer `create()`, calcular `total_results`
una sola vez y actualizar con `save(update_fields=['results_count', 'has_results'])`.

### #107 — 3 templates faltantes (TemplateDoesNotExist en runtime)

Creados desde cero siguiendo el patrón de `category_detail.html` (mismo CSS, Bootstrap 5,
Bootstrap Icons, `layouts/base.html`):

| Template | Contexto disponible | Features |
|----------|---------------------|---------|
| `faq_list.html` | `faqs` (paginado), `categories`, `current_category`, `query` | Accordion, búsqueda, filtro por categoría, paginación |
| `video_tutorials.html` | `videos` (paginado), `categories`, `current_category`, `current_difficulty`, `difficulty_choices` | Cards con modal de video embed, filtros categoría+dificultad, paginación |
| `quick_start.html` | `guides`, `current_audience`, `audience_choices` | Cards con contenido colapsable, filtro por audiencia |

---

## Bugs help abiertos (no tocados esta sesión)

| # | Descripción | Esfuerzo |
|---|-------------|---------|
| #100 | `get_user_model()` a nivel de módulo — ya corregido como parte de #101 | ✅ resuelto |
| #103 | Doble `count()` en `search_help` | ✅ resuelto |
| #105 | `mark_completed(user)` — `user` ignorado, `UserGuideProgress` no implementado | Baja |
| #106 | `get_related_articles()` ignora tags | Media |
| #108 | Sin UUID PK — todos AutoField | Breaking change — diferir |
| #109 | `author`/`user` en vez de `created_by` — excepción documentada | Baja |
| #110 | Race condition en search log | ✅ resuelto |

---

## Rutas de los archivos en el proyecto

```
passgen/generators.py
help/models.py
help/views.py
help/templates/help/faq_list.html
help/templates/help/video_tutorials.html
help/templates/help/quick_start.html
```

---

## Migración requerida

`help/models.py` tuvo cambios en FKs (de objetos importados a strings lazy). Django
no genera migración automática para este cambio porque la columna de BD no cambia —
pero hay que verificar:

```bash
python manage.py makemigrations help --check
# Si no genera nada → OK, no se necesita migración
```

---

## Comandos de commit

```bash
# passgen
git add passgen/generators.py
git commit -m "fix(passgen): bugs #96 #98 — CATEGORIES no definido + MIN_ENTROPY bloqueante

#96 generators.py: self.CATEGORIES derivado de PREDEFINED_PATTERNS en __init__
#98 generators.py: MIN_ENTROPY 60→20 — 5/7 patrones predefinidos eran inaccesibles"

# help
git add help/models.py help/views.py
git add help/templates/help/faq_list.html
git add help/templates/help/video_tutorials.html
git add help/templates/help/quick_start.html
git commit -m "fix(help): bugs #101 #102 #103 #104 #107 #110

#101 models.py: imports courses.* lazy ('courses.X'), User→settings.AUTH_USER_MODEL
#102 views.py: @login_required en article_feedback_stats
#103 views.py: total_results calculado una sola vez en search_help
#104 views.py: article.save(update_fields=[...]) en submit_feedback
#107 templates: crear faq_list.html, video_tutorials.html, quick_start.html
#110 views.py: search log actualizado por instancia — elimina race condition"

git add docs/HANDOFF_2026-03-21_help_passgen.md
git commit -m "docs: handoff sesión 2026-03-21 (passgen, help)"

git push origin main
```

---

## Estado del Sprint 9 tras esta sesión

### Bugs cerrados hoy (acumulado sesión completa)

| # | App | Estado |
|---|-----|--------|
| #111–#120 | `panel`, `api` | ✅ |
| `board` | eliminado | ✅ |
| #96, #98 | `passgen` | ✅ |
| #101–#104, #107, #110 | `help` | ✅ |

### Bugs críticos aún abiertos

| # | App | Fix | Esfuerzo |
|---|-----|-----|---------|
| #75 | `cv` | Imports `events.management` en cadena | 15 min |
| #76 | `cv` | `reverse('project_detail')` sin namespace | 5 min |

### Features Sprint 9 pendientes

| ID | App | Prioridad |
|----|-----|-----------|
| BOT-2 | `bots` + `sim` | 🔴 |
| BOT-3 | `bots` + `campaigns` | 🟠 |
| BOT-5 | `bots` + `sim` | 🟡 |
| SIM-7e | `sim` | 🔴 |
| REFACTOR-1/2/3 | `chat`, `rooms`, `courses` | 🟠 |
| API-ARCH | `api` | 🟠 (decisión tomada esta sesión) |
