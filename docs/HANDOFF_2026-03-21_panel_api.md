# Handoff — Sesión Analista Dev · Management360
> **Fecha:** 2026-03-21
> **Apps:** `panel`, `api`, eliminación de `board`
> **Sprint:** 9
> **Bugs cerrados:** #111 #112 #113 #114 #115 #116 #117 #118 #119 #120
> **Bugs reabiertos/ajustados:** #85 → CERRADO (BOARD_CONFIG ya existía en settings)

---

## Cambios realizados

### `panel/views.py` — #114, #117

**#114** `get_connection_token` nunca retornaba nada — construía `token_claims` y terminaba. Fix: añadidos `jwt.encode()` + `return JsonResponse({'token': token})` siguiendo el patrón idéntico de `get_subscription_token`.  
También migrado el auth check de manual a `@login_required` para consistencia.

**#117** `RedisTestView` expuesta públicamente en `/redis-test/`. Fix: `@method_decorator(login_required, name='dispatch')`.

De paso: eliminado `User = get_user_model()` a nivel de módulo — no se usaba en ninguna vista del archivo.

---

### `panel/middleware.py` — #115

`connections['postgres_online']` lanzaba `KeyError` (alias inexistente en `DATABASES`) antes de llegar al `except OperationalError` — error sin capturar por cada request. Fix: `db_order = ['default']` + `except (OperationalError, KeyError)`.

---

### `panel/storages.py` — #116

29 `print()` reemplazados por `logger` con niveles por severidad:
- Flujo normal → `logger.debug`
- Upload exitoso → `logger.info`
- Respuesta HTTP no-200 → `logger.warning`
- Excepciones de red → `logger.error`

El `print()` a nivel de módulo (`=== REMOTE MEDIA STORAGE MODULE LOADED ===`) también eliminado.

---

### `api/urls.py` + `panel/urls.py` — #111, #112, #113

**#111** Añadido `app_name = 'api'`.  
**#112** Eliminados 4 registros directos duplicados de `panel/urls.py` — `api/urls.py` es ahora la única fuente de verdad.  
**#113** Añadidos `token/connection/` y `token/subscription/` a `api/urls.py`.

⚠️ **Breaking change en nombres de URL** — hacer grep antes del push:

```bash
grep -r "api-csrf\|api-login\|api-logout\|api-signup\|api-connection-token\|api-subscription-token" .
```

| Antes | Después |
|-------|---------|
| `reverse('api-csrf')` | `reverse('api:csrf')` |
| `reverse('api-login')` | `reverse('api:login')` |
| `reverse('api-logout')` | `reverse('api:logout')` |
| `reverse('api-signup')` | `reverse('api:signup')` |
| `reverse('api-connection-token')` | `reverse('api:connection-token')` |
| `reverse('api-subscription-token')` | `reverse('api:subscription-token')` |

Las URLs HTTP en sí (`/api/csrf/`, `/api/login/`, etc.) **no cambian** — solo los nombres Python. El JS que usa `fetch('/api/...')` hardcodeado no se ve afectado.

---

### `panel/settings.py` — #118, #119, #120 + eliminación de `board`

**#118** Eliminado `from django.utils import timezone` a nivel global. El único uso era en `TINYMCE_DEFAULT_CONFIG['template_replace_values']['fecha']`. Reemplazado por `__import__('datetime').date.today().strftime(...)` — sin import global.

**#119** Eliminada la línea duplicada `AUTH_USER_MODEL = 'accounts.User'` al final del archivo.

**#120** `django_htmx` movido al bloque principal de `INSTALLED_APPS`. Eliminado `INSTALLED_APPS += ['django_htmx']` al final del archivo.

**Board eliminado:**
- `'board.apps.BoardConfig'` → eliminado de `INSTALLED_APPS`
- `BOARD_CONFIG` → eliminado (19 líneas)
- `path('board/', ...)` → eliminado de `panel/urls.py`

Verificación previa al cambio:
```bash
grep -r "board\." */migrations/*.py
# → solo referencias internas a board/migrations/ y un comentario en analyst
# → ninguna app externa tiene FK hacia board → eliminación limpia
```

También aprovechado para: limpiar prints del bloque `_build_caches()` → `logger`, eliminar prints del bloque de logging DEBUG, reorganizar INSTALLED_APPS en bloques coherentes.

---

## Archivos entregados

```
panel/views.py      ← #114 #117
panel/middleware.py ← #115
panel/storages.py   ← #116
panel/urls.py       ← #112 + board eliminado
panel/settings.py   ← #118 #119 #120 + board eliminado
api/urls.py         ← #111 #112 #113
```

---

## Checklist previo al push

```bash
# 1. Eliminar tablas de board de la BD (si hay datos)
python manage.py dbshell
# MariaDB:
SHOW TABLES LIKE 'board%';
DROP TABLE IF EXISTS board_activity;
DROP TABLE IF EXISTS board_card;
DROP TABLE IF EXISTS board_board;
exit

# 2. Eliminar directorio
rm -rf board/

# 3. Verificar nombres de URL rotos (ver sección api)
grep -r "api-csrf\|api-login\|api-logout\|api-signup\|api-connection\|api-subscription" .

# 4. Verificar referencias a board en templates
grep -r "board:" templates/ */templates/
grep -r "url 'board:" templates/ */templates/

# 5. Arrancar Django y confirmar sin errores
python manage.py check
python manage.py runserver
```

---

## Comando de commit

```bash
git add panel/views.py panel/middleware.py panel/storages.py panel/urls.py panel/settings.py api/urls.py
git rm -r board/
git commit -m "fix(panel,api): bugs #111-#120 + eliminar app board

panel/views:      #114 get_connection_token completo; #117 @login_required en RedisTestView
panel/middleware: #115 db_order=['default'], capturar KeyError
panel/storages:   #116 29 print() → logger con niveles apropiados
panel/urls:       #112 eliminar registros directos duplicados api/*; eliminar board
panel/settings:   #118 timezone import global; #119 AUTH_USER_MODEL duplicado;
                  #120 django_htmx a INSTALLED_APPS; board eliminado; prints → logger
api/urls:         #111 app_name='api'; #112 única fuente endpoints; #113 token endpoints

BREAKING: reverse('api-*') → reverse('api:*') — verificar con grep antes del push
board: tablas eliminadas, directorio removido, sin dependencias externas (verificado)"
git push origin main
```

---

## Deuda residual pendiente (Sprint 9 — no tocada esta sesión)

| # | App | Descripción | Esfuerzo |
|---|-----|-------------|---------|
| #84 | `board` | **YA NO APLICA** — board eliminado | — |
| #85 | `board` | **YA NO APLICA** — board eliminado | — |
| #107 | `help` | 3 templates faltantes (TemplateDoesNotExist en runtime) | ~1.5h |
| #96 | `passgen` | `self.CATEGORIES` no definido — 500 en `password_help` | 3 min |
| #98 | `passgen` | `MIN_ENTROPY=60` bloquea 5/7 patrones | 1 min |
| #75 | `cv` | Imports `events.management` a nivel de módulo | 15 min |
| #76 | `cv` | `reverse('project_detail')` sin namespace | 5 min |
| #101 | `help` | Import `courses.models` a nivel de módulo | 5 min |
| #102 | `help` | `article_feedback_stats` sin `@login_required` | 1 min |
| #104 | `help` | `submit_feedback` sin `update_fields` | 3 min |
| BOT-2 | `bots`+`sim` | BotInstance ↔ ACDAgentSlot | sesión dedicada |
| BOT-3 | `bots`+`campaigns` | DiscadorLoad → LeadCampaign | sesión dedicada |
| HELP-1/2/3 | `help` | Templates faltantes | sesión dedicada |
