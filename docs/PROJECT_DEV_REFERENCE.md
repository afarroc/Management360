# Referencia de Desarrollo — Proyecto Management360

> **Audiencia:** Desarrolladores del proyecto y asistentes de IA (Claude, Copilot, etc.)
> **Actualizado:** 2026-03-19 | **Apps:** 20 | **Archivos Python+HTML:** ~710

---

## Índice rápido

| Sección | Contenido |
|---------|-----------|
| 1. Estructura del proyecto | Árbol, apps, convenciones |
| 2. Patrones comunes en todas las apps | Models, views, URLs, templates |
| 3. Manejo de fechas (CRÍTICO) | Estándar por app |
| 4. Sistema de caché | Redis keys, TTLs, patrones |
| 5. Seguridad | CSRF, permisos, namespaces |
| 6. Modelo User (accounts) | Campos custom, imports correctos |
| 7. Integración analyst ↔ sim | ETL, dashboards, reportes |
| 8. App simcity — arquitectura híbrida | Engine proot, proxy, arranque |
| 9. APIs internas | Estructura de respuestas, autenticación |
| 10. Frontend unificado | HTMX, Bootstrap, Chart.js |
| 11. Testing | Por app, cobertura |
| 12. Despliegue | build.sh, variables de entorno |
| 13. Migraciones | Orden, dependencias entre apps |
| 14. Documentación | Estándar por app |
| 15. Bugs conocidos globales | Issues que afectan múltiples apps |

---

## 1. Estructura del Proyecto

### Resumen de apps

| App | Namespace | Endpoints | Notas |
|-----|-----------|-----------|-------|
| `accounts` | `accounts` | 11 | Autenticación, Perfiles, CV |
| `analyst` | `analyst` | 99 | Plataforma de datos (5 fases, SIM-4 integrado) |
| `api` | `api` | 4 | API REST pública |
| `bitacora` | `bitacora` | 9 | Bitácora personal GTD |
| `board` | `board` | 8 | Kanban board |
| `bots` | `bots` | 11 | Automatizaciones, bots |
| `campaigns` | `campaigns` | 6 | Campañas, outreach |
| `chat` | `chat` | 40 | Chat en tiempo real, rooms, mensajes |
| `core` | `core` | 16 | Dashboard, URL-map, Home |
| `courses` | `courses` | 59 | Cursos, lecciones, curriculum |
| `cv` | `cv` | 14 | Curriculum Vitae dinámico |
| `events` | `events` | 145 | Eventos, Proyectos, Tareas (app principal) |
| `help` | `help` | 10 | Centro de ayuda, tickets |
| `kpis` | `kpis` | 4 | KPIs, AHT Dashboard, CallRecord |
| `memento` | `memento` | 6 | Recordatorios, memoria personal |
| `panel` | `panel` | 27 | Panel de configuración del proyecto |
| `passgen` | `passgen` | 2 | Generador de contraseñas |
| `rooms` | `rooms` | 53 | Salas virtuales, channels |
| `sim` | `sim` | 48 | Simulador WFM — SIM-1→SIM-7a completo |
| `simcity` | `simcity` | **14** | Simulador urbano — proxy proot:8001 |

### Convenciones de nomenclatura

| Elemento | Convención | Ejemplo |
|----------|------------|---------|
| Apps | snake_case, singular | `analyst`, `events`, `sim` |
| Modelos | CamelCase | `CallRecord`, `SimAccount`, `Project` |
| Vistas | snake_case | `dashboard_view`, `project_list` |
| URLs | kebab-case | `/kpis/dashboard/`, `/events/projects/` |
| Namespaces | snake_case | `app_name = 'kpis'` |
| Templates | snake_case | `upload_data_csv.html` |
| Archivos de doc | MAYÚSCULAS + _ | `PROJECT_DESIGN.md` |

---

## 2. Patrones Comunes en Todas las Apps

### Models

    # PK pública — TODAS las apps excepto simcity
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='%(class)s_created',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

> **Excepciones documentadas:**
> - `events`: usa `host` para Project/Task/Event — NO cambiar
> - `rooms`: usa `owner` para Room — NO cambiar
> - `bitacora`: usa `fecha_creacion`/`fecha_actualizacion` (en español)
> - `simcity.Game`: usa `AutoField` (int) como PK — heredado del engine original

### TextChoices — módulo-level vs clase interna

`bitacora` define `CategoriaChoices` y `MoodChoices` a nivel de módulo, no como
clases internas de `BitacoraEntry`. Importar siempre directamente:

```python
# CORRECTO
from bitacora.models import CategoriaChoices, MoodChoices

# INCORRECTO
BitacoraEntry.CategoriaChoices  # AttributeError
```

### Import correcto de User

    # CORRECTO — en models.py
    from django.conf import settings
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, ...)

    # CORRECTO — en views.py, forms.py, otros
    from django.contrib.auth import get_user_model
    User = get_user_model()

    # INCORRECTO
    from django.contrib.auth.models import User

### Views

    @login_required
    @require_POST
    def api_action(request):
        try:
            data = json.loads(request.body)
            return JsonResponse({'success': True, 'data': result})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)

### CSRF Token en JavaScript

    function csrf() {
        return document.cookie.match(/csrftoken=([^;]+)/)?.[1] || '';
    }
    fetch(url, { method: 'POST', headers: { 'X-CSRFToken': csrf() }, body: ... })

### Respuestas JSON unificadas

    {"success": true, "data": {...}}
    {"success": false, "error": "..."}

---

## 3. Manejo de Fechas — CRÍTICO ⚠️

| App | Modelo | Campo(s) de fecha | Ordenamiento |
|-----|--------|-------------------|--------------|
| **sim** | `Interaction` | `fecha` (DateField) + `hora_inicio` (DateTimeField) | `order_by('fecha', 'hora_inicio')` |
| **kpis** | `CallRecord` | `fecha` (DateField) + `semana` (IntegerField calculado) | `order_by('fecha', 'agente')` |
| **events** | `Task` | `due_date` (DateField) | `order_by('due_date')` |
| **events** | `Event` | `start_date` (DateTimeField) | `order_by('start_date')` |
| **chat** | `Message` | `timestamp` (DateTimeField) | `order_by('timestamp')` |
| **bitacora** | `BitacoraEntry` | `fecha_creacion` (DateTimeField) | `order_by('-fecha_creacion')` |
| **courses** | `Lesson` | `created_at` (DateTimeField) | `order_by('order', 'created_at')` |
| **simcity** | `Game` | `created_at` / `updated_at` (DateTimeField) | `order_by('-created_at')` |

### ⚠️ `timedelta` NO es parte de `django.utils.timezone`

    from datetime import timedelta   # CORRECTO
    # timezone.timedelta            # INCORRECTO — AttributeError

### ⚠️ Campos que NO existen

    # kpis.CallRecord — NO usar start_time → usar fecha
    # sim.Interaction — NO usar started_at → usar fecha + hora_inicio

---

## 4. Sistema de Caché (Redis)

| Prefix | App | TTL | Ejemplo |
|--------|-----|-----|---------|
| `df_preview_` | analyst | 2h | `df_preview_{uuid}` |
| `stored_dataset_` | analyst | ∞ | `stored_dataset_{uuid}` |
| `clip_` | analyst | 24h | `clip_{session_key}_{key}` |
| `gtr:session:` | sim | 4h | `gtr:session:{sid}` |
| `chat:presence:` | chat | 5min | `chat:presence:{user_id}` |
| `kpis:dashboard:` | kpis | 5min | `kpis:dashboard:{user_id}:{desde}:{hasta}` |

`simcity` no usa Redis — estado del mapa persiste en MariaDB (JSONField).

---

## 5. Seguridad

    obj = get_object_or_404(MyModel, pk=pk, created_by=request.user)

**`@csrf_exempt` — PROHIBIDO** en vistas con datos de usuario. Bugs #12 (bitacora) y SC-2 (simcity) documentan este problema.

---

## 6. Modelo User (`accounts`)

```python
class User(AbstractUser):
    phone      = models.CharField(max_length=20, blank=True, null=True)
    avatar     = models.ImageField(upload_to='avatars/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

    # panel/settings.py
    AUTH_USER_MODEL = 'accounts.User'

---

## 7. Integración analyst ↔ sim

Ver `ANALYST_DEV_REFERENCE.md` y `SIM_DEV_REFERENCE.md`.
`sim` incluye SIM-7a (ACD multi-agente) — migraciones 0005+0006 aplicadas.

---

## 8. App `simcity` — Arquitectura Híbrida

`simcity` es la única app de M360 que depende de un proceso externo.
`micropolisengine` (C/SWIG) solo existe en proot Ubuntu — **nunca importar en Termux**.

### Endpoints (14)

| URL | Método | Descripción |
|-----|--------|-------------|
| `/simcity/` | GET | UI del juego |
| `/simcity/api/games/` | GET | Lista partidas |
| `/simcity/api/games/new/` | POST | Nueva partida |
| `/simcity/api/game/<id>/map/` | GET | Mapa + agentes |
| `/simcity/api/game/<id>/tick/` | POST | Avanzar ticks |
| `/simcity/api/game/<id>/build/` | POST | Construir tile |
| `/simcity/api/game/<id>/reset/` | POST | Reiniciar ciudad |
| `/simcity/api/game/<id>/generate_block/` | POST | Cuadrante Monopoly |
| `/simcity/api/game/<id>/generate_zr_block/` | POST | Cuadrante ZR 10×10 ✅ SC-1 |
| `/simcity/api/game/<id>/census/` | GET | Censo |
| `/simcity/api/game/<id>/tasks/` | GET | Tareas ABM |
| `/simcity/api/game/<id>/add_money/` | POST | Añadir fondos |
| `/simcity/api/game/<id>/delete/` | POST | Eliminar partida |
| `/simcity/api/game/<id>/export_analyst/` | POST | → StoredDataset ✅ SC-6 |

### Arranque

```bash
# ~/.zshrc — agregar una vez
alias engine='ubuntu run "source /root/micropolis/venv/bin/activate && cd /root/micropolis/simcity_web && python manage.py runserver 0.0.0.0:8001"'
alias m360='cd ~/projects/Management360 && source venv/bin/activate && python manage.py runserver'

# Alternativa
bash scripts/start_simcity.sh
```

### Patrón de vista con SC-3

```python
from .services import EngineUnavailableError

@login_required
@require_POST
def tick(request, game_id):
    game = get_object_or_404(Game, pk=game_id, created_by=request.user)
    try:
        data = engine.engine_tick(game.engine_game_id, body.get('n', 1))
        game.map_data = data.get('map', game.map_data)
        game.money = data.get('money', game.money)
        game.save()
        return JsonResponse(data)
    except EngineUnavailableError as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=503)
```

### Integración con analyst (SC-6)

`POST /simcity/api/game/<id>/export_analyst/` crea un `StoredDataset` con columnas:
`x, y, tile, zone_type, has_power, has_road, money, game_name, game_id`

Responde con `analyst_url` para ir directo al preview.

### Admin

`GameAdmin` registrado en `/admin/simcity/` con fieldsets para Partida, Engine,
Estado (colapsable) y Timestamps (readonly).

---

## 9. APIs Internas

    @login_required
    def api_items(request):
        items = Item.objects.filter(created_by=request.user)
        return JsonResponse({'success': True, 'data': list(items.values('id', 'name'))})

---

## 10. Frontend Unificado

Bootstrap 5 + HTMX en todas las apps. **Excepción: `simcity`** — JS vanilla + Canvas 2D + CSS custom. No agregar Bootstrap al template del juego.

---

## 11. Testing

| App | Tests | Cobertura |
|-----|-------|-----------|
| sim | 157 | 100% |
| analyst | 34/50 | 68% |
| simcity | 0 | 0% — pendiente SC-8 |

---

## 12. Despliegue

### build.sh

    python manage.py migrate auth
    python manage.py migrate contenttypes
    python manage.py migrate accounts   # ← CRÍTICO: antes que el resto
    python manage.py migrate --no-input
    python manage.py collectstatic --no-input

### Variables de entorno (.env)

    SECRET_KEY=...
    DEBUG=False
    DATABASE_URL=mysql://user:pass@localhost:3306/projects
    REDIS_URL=redis://:password@localhost:6379/0
    SIMCITY_ENGINE_URL=http://localhost:8001

---

## 13. Migraciones

### Estado actual (2026-03-19)

| App | Última migración | Notas |
|-----|-----------------|-------|
| accounts | 0001_initial | User custom con phone, avatar, timestamps |
| bitacora | 0004_uuid_primary_keys | UUID pk en entry + attachment |
| sim | 0006_rename_... | SIM-7a ACD multi-agente completo |
| simcity | 0001_initial | Game con created_by + engine_game_id |
| events | 0003_alter_... | — |
| kpis | 0002_refactor_callrecord | UUID + fecha DateField + 5 índices (IF NOT EXISTS) |

### Orden de dependencias

1. `contenttypes`, `auth`
2. **`accounts`** — PRIMERO
3. `events`, `analyst`, `sim`, `courses`, `simcity`
4. `chat`, `rooms`, `bitacora`, `bots`

### ⚠️ REGLA: Nunca ignorar migrations/ en .gitignore

---

## 14. Documentación

| Tipo | Propósito |
|------|-----------|
| `APP_CONTEXT.md` | Mapa estructural (auto) |
| `APP_DEV_REFERENCE.md` | Manual técnico |
| `APP_DESIGN.md` | Diseño, fases, roadmap |

    bash scripts/m360_map.sh app ./simcity
    bash scripts/m360_map.sh              # PROJECT_CONTEXT.md completo

---

## 15. Bugs Conocidos Globales

| # | Estado | App | Descripción |
|---|--------|-----|-------------|
| 1 | ✅ | analyst | `clean_file()` duplicado en forms.py |
| 2 | ✅ | analyst/sim | `started_at` inexistente en sim.Interaction |
| 3 | ✅ | analyst | UUID Python en JS → `_safe_json_str()` |
| 4 | ✅ | sim | `@keyframes` dentro de `<script>` |
| 5 | ⬜ | chat | Notificaciones no siempre marcan como leídas |
| 6 | ⬜ | events | Consultas N+1 en dashboard de proyectos |
| 7 | ✅ | kpis | Índices compuestos + fecha DateField + UUID |
| 8 | ⬜ | courses | Editor de contenido lento con muchos bloques |
| 9 | ✅ | sim | `expected_vol` gauss negativo |
| 10 | ✅ | accounts | `accounts_user` tabla inexistente — INC-001 |
| 11 | ✅ | bitacora | `timezone.timedelta` → `from datetime import timedelta` |
| 12 | ✅ | bitacora | `@csrf_exempt` en `upload_image` |
| 13 | ✅ | bitacora | N+1 en `total_attachments` |
| 14 | ✅ | bitacora | HTML render en modelos → templatetags |
| 15 | ✅ | bitacora | Imports lazy → movidos al tope |
| 16 | ✅ | bitacora | `content_block` no renderizaba en bitacora_tags |
| 17 | ✅ | bitacora | `urls.py` usaba `<int:pk>` → `<uuid:pk>` (BIT-6) |
| 18 | ✅ | events | Bloque `try` sin `except` en `assign_to_available_user()` |
| 19 | ✅ | events | `STATUS_CHOICES` incorrecto en `TaskFilterForm` |
| 20 | ✅ | events | Campos incorrectos en `TaskScheduleForm` |
| 21 | ✅ | events | Campos incorrectos en `InboxItemForm` |
| 22 | ✅ | events | Falta `get_user_model()` en `AssignAttendeesForm` |
| 23 | ✅ | events | Falta import de `Group` en `setup_views.py` |
| 24 | ✅ | cv | Admin con campos inexistentes |
| 25 | ✅ | kpis | Migración con dependencia incorrecta |
| 26 | ✅ | kpis | `ForeignKey(User)` → `settings.AUTH_USER_MODEL` |
| 27 | ✅ | kpis | `Duplicate column name created_at` en 0002 — IF NOT EXISTS |
| 28 | ✅ | scripts | `m360_map.sh`/`app_map.sh` convertidos en stubs — restaurados |
| 29 | ✅ | bitacora | `entry.autor` en template → `entry.created_by` |
| 30 | ✅ | bitacora | `entry.mood` raw en templates → `entry.get_mood_display` |
| 31 | ✅ | bitacora | `entry.CATEGORIA_CHOICES` en templates → `categoria_choices` del contexto |
| 32 | ✅ | bitacora | `entry.get_categoria_choices` en dashboard → `categoria_choices` |
| 33 | ✅ | bitacora | `BitacoraEntry.CategoriaChoices` en views → `CategoriaChoices` (módulo-level) |
| 34 | ⬜ | bitacora | Nav prev/next no filtra por `created_by`+`is_active` (BIT-17) |
| 35 | ⬜ | bitacora | TinyMCE CDN usa `no-api-key` — registrar en tiny.cloud (BIT-18) |
| SC-1 | ✅ `bf037497` | simcity | `generate_zr_block` no estaba en urls.py de M360 |
| SC-2 | ✅ `bf037497` | simcity | `mobMoneyBtn` solo logueaba warning — ahora llama API |
| SC-3 | ✅ `bf037497` | simcity | Engine offline daba 500 — ahora 503 EngineUnavailableError |
