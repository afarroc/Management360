# Referencia de Desarrollo — Proyecto Management360

> **Audiencia:** Desarrolladores del proyecto y asistentes de IA (Claude, Copilot, etc.)
> **Actualizado:** 2026-03-18 | **Apps:** 20 | **Archivos Python+HTML:** ~710
> **Basado en:** PROJECT_CONTEXT.md, ANALYST_DEV_REFERENCE.md, SIM_DEV_REFERENCE.md, SIMCITY_DEV_REFERENCE.md

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

### Árbol de directorios (nivel 1)

    Management360/
    ├── manage.py
    ├── build.sh
    ├── requirements.txt
    ├── .env
    ├── panel/                 # Configuración principal (settings, middleware)
    ├── docs/                  # Documentación (ver estructura completa en PROJECT_DESIGN.md)
    ├── scripts/               # Utilidades (app_map.sh, m360_map.sh, setup/, utils/, tests/)
    ├── services/              # Servicios independientes (media_server.py)
    │
    ├── accounts/              # Autenticación, perfiles — AUTH_USER_MODEL
    ├── analyst/               # Plataforma de datos
    ├── api/                   # API REST pública
    ├── bitacora/              # Bitácora personal GTD ← refactorizada 2026-03-18
    ├── board/                 # Kanban board
    ├── bots/                  # Automatizaciones
    ├── campaigns/             # Campañas outbound
    ├── chat/                  # Chat en tiempo real
    ├── core/                  # Dashboard, URL-map, utilidades
    ├── courses/               # Sistema de aprendizaje
    ├── cv/                    # Currículum dinámico
    ├── events/                # Gestión de proyectos/tareas (app principal)
    ├── help/                  # Centro de ayuda
    ├── kpis/                  # Métricas de contacto (CallRecord)
    ├── memento/               # Recordatorios
    ├── passgen/               # Generador de contraseñas
    ├── rooms/                 # Salas virtuales
    ├── sim/                   # Simulador WFM — SIM-7a ACD completo
    └── simcity/               # Simulador urbano Micropolis ← añadida 2026-03-18

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
| `simcity` | `simcity` | 12 | Simulador urbano — proxy proot:8001 |

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

    # Autoría — campo estándar: created_by
    # SIEMPRE usar settings.AUTH_USER_MODEL, NUNCA importar User directamente
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='%(class)s_created',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Soft delete (donde aplica)
    is_active = models.BooleanField(default=True)

    # Choices — usar TextChoices (estilo moderno)
    class EstadoChoices(models.TextChoices):
        ACTIVO   = 'activo',   'Activo'
        INACTIVO = 'inactivo', 'Inactivo'

> **Excepciones documentadas:**
> - `events`: usa `host` para Project/Task/Event — NO cambiar
> - `rooms`: usa `owner` para Room — NO cambiar
> - `bitacora`: usa `fecha_creacion`/`fecha_actualizacion` (en español) y `created_by`
> - `simcity.Game`: usa `AutoField` (int) como PK — heredado del engine original

### Import correcto de User

    # CORRECTO — en models.py
    from django.conf import settings
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, ...)

    # CORRECTO — en views.py, forms.py, otros
    from django.contrib.auth import get_user_model
    User = get_user_model()

    # INCORRECTO — causa error si AUTH_USER_MODEL cambia
    from django.contrib.auth.models import User

### Views

    @login_required
    def panel_view(request):
        context = {'items': Item.objects.filter(created_by=request.user, is_active=True)}
        return render(request, 'app/panel.html', context)

    @login_required
    @require_POST
    def api_action(request):
        try:
            data = json.loads(request.body)
            return JsonResponse({'success': True, 'data': result})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)

### CSRF Token en JavaScript

    // CORRECTO
    function csrf() {
        return document.cookie.match(/csrftoken=([^;]+)/)?.[1] || '';
    }
    fetch(url, { method: 'POST', headers: { 'X-CSRFToken': csrf() }, body: ... })

    // INCORRECTO
    // fetch(url, { headers: { 'X-CSRFToken': CSRF_TOKEN } })  // ReferenceError

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

    # INCORRECTO — AttributeError en runtime
    week_start = today - timezone.timedelta(days=today.weekday())

    # CORRECTO
    from datetime import timedelta
    week_start = today - timedelta(days=today.weekday())

### ⚠️ `start_time` NO EXISTE en `kpis.CallRecord`

    # INCORRECTO
    CallRecord.objects.filter(start_time__gte=date)
    # CORRECTO — campo migrado en 0002_refactor_callrecord
    CallRecord.objects.filter(fecha__gte=date, fecha__lte=date_to)

### ⚠️ `started_at` NO EXISTE en `sim.Interaction`

    # INCORRECTO
    Interaction.objects.filter(started_at__gte=date)
    # CORRECTO
    Interaction.objects.filter(fecha__gte=date).order_by('fecha', 'hora_inicio')

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

`simcity` no usa Redis — el estado del mapa se persiste directamente en MariaDB (JSONField).

---

## 5. Seguridad

### Permisos

    obj = get_object_or_404(MyModel, pk=pk, created_by=request.user)

### @csrf_exempt — PROHIBIDO en vistas con datos de usuario

    # INCORRECTO (corregido en bitacora/views.py y simcity/views.py)
    @csrf_exempt
    def mi_vista(request): ...

    # CORRECTO
    @login_required
    def mi_vista(request): ...  # CSRF lo maneja el middleware

### Render HTML en modelos — PROHIBIDO

    # INCORRECTO — XSS + responsabilidad única violada
    class MyModel(models.Model):
        def render_html(self):
            return f'<div>{self.user_content}</div>'

    # CORRECTO — en templatetags con escape()
    @register.simple_tag
    def render_block(block):
        return mark_safe(f'<div>{escape(block.get("content",""))}</div>')

---

## 6. Modelo User (`accounts`)

### Campos custom de `accounts.User`

```python
# accounts/models.py
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    phone      = models.CharField(max_length=20, blank=True, null=True)
    avatar     = models.ImageField(upload_to='avatars/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

Campos heredados de `AbstractUser` disponibles: `username`, `email`, `first_name`,
`last_name`, `is_staff`, `is_active`, `date_joined`, `last_login`.

### Settings requerido

    # panel/settings.py
    AUTH_USER_MODEL = 'accounts.User'

### Acceso correcto en cualquier parte del código

    from django.contrib.auth import get_user_model
    User = get_user_model()

    # En models.py — siempre con settings
    from django.conf import settings
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, ...)

---

## 7. Integración analyst ↔ sim

Ver `ANALYST_DEV_REFERENCE.md` y `SIM_DEV_REFERENCE.md`.

`sim` ahora incluye SIM-7a (ACD multi-agente) — migraciones 0005+0006 aplicadas.

---

## 8. App `simcity` — Arquitectura Híbrida

`simcity` es la única app de M360 que depende de un proceso externo. El engine
`micropolisengine` (librería C compilada con SWIG) solo está disponible en
proot Ubuntu y **no puede instalarse en el venv de Termux**.

### Arranque obligatorio

```bash
# Terminal 1 — proot Ubuntu (engine)
ubuntu
cd /root/micropolis/simcity_web
source /root/micropolis/venv/bin/activate
python manage.py runserver 0.0.0.0:8001

# Terminal 2 — Termux (M360)
cd ~/projects/Management360 && source venv/bin/activate
python manage.py runserver
```

### Flujo de una request

```
Browser → M360:8000/simcity/api/game/<id>/tick/
    → simcity/views.py (@login_required, verifica created_by)
    → simcity/services.py (requests.post → proot:8001/api/game/<engine_id>/tick/)
    → simcity_web engine procesa Micropolis + ABM
    → respuesta JSON con map_data actualizado
    → M360 sincroniza Game en MariaDB
    → respuesta al browser
```

### Campo `engine_game_id`

```python
# simcity/models.py
engine_game_id = models.IntegerField(null=True, blank=True)
```

Vincula el `Game` de M360 (MariaDB) con el `Game` del SQLite de proot.
Puede ser `None` si el engine no respondió durante la creación — siempre
verificar antes de llamar a `services.py`.

### Manejo de engine offline (SC-3 pendiente)

```python
from requests.exceptions import ConnectionError as EngineOffline

try:
    data = engine.engine_tick(game.engine_game_id, n)
except EngineOffline:
    return JsonResponse(
        {'success': False, 'error': 'Engine offline — levantar proot:8001'},
        status=503
    )
```

Ver `SIMCITY_DEV_REFERENCE.md` para documentación completa.

---

## 9. APIs Internas

    @login_required
    def api_items(request):
        items = Item.objects.filter(created_by=request.user)
        return JsonResponse({'success': True, 'data': list(items.values('id', 'name'))})

---

## 10. Frontend Unificado

La mayoría de las apps usan Bootstrap 5 + HTMX. **Excepción: `simcity`** usa
JS vanilla con Canvas 2D y CSS custom propio — no agregar Bootstrap al template
del juego.

    <!-- HTMX (apps estándar) -->
    <button hx-get="/api/items/?page=2" hx-target="#items-list" hx-swap="beforeend">
        Cargar más
    </button>

    // Chart.js
    new Chart(ctx, { type: 'bar', data: { labels: [...], datasets: [...] } });

---

## 11. Testing

| App | Tests | Cobertura |
|-----|-------|-----------|
| sim | 157 | 100% |
| analyst | 34/50 | 68% |
| Otras | — | — |

    python manage.py test sim.tests.test_generators sim.tests.test_gtr_engine -v 2

---

## 12. Despliegue

### build.sh (producción)

    pip install --no-cache-dir -r requirements.txt
    python manage.py migrate auth
    python manage.py migrate contenttypes
    python manage.py migrate accounts   # ← CRÍTICO: antes que el resto
    python manage.py migrate --no-input
    python manage.py collectstatic --no-input

> ⚠️ En producción, `simcity` requiere que el engine proot esté accesible
> en `ENGINE_BASE_URL`. Configurar como variable de entorno para prod.

### Variables de entorno (.env)

    SECRET_KEY=...
    DEBUG=False
    AUTH_USER_MODEL=accounts.User
    DATABASE_URL=mysql://user:pass@localhost:3306/projects
    REDIS_URL=redis://:password@localhost:6379/0
    SIMCITY_ENGINE_URL=http://localhost:8001   # URL del engine Micropolis

---

## 13. Migraciones

### Estado actual (2026-03-18)

| App | Última migración | Notas |
|-----|-----------------|-------|
| accounts | 0001_initial | User custom con phone, avatar, timestamps |
| bitacora | 0004_uuid_primary_keys | UUID pk en entry + attachment |
| sim | 0006_rename_... | SIM-7a ACD multi-agente completo |
| simcity | 0001_initial | Game con created_by + engine_game_id |
| events | 0003_alter_... | — |
| cv | 0001_initial | — |
| memento | 0007_alter_... | — |
| kpis | 0002_refactor_callrecord | UUID col + fecha DateField + 5 índices (MySQL-safe IF NOT EXISTS) |

### Orden de dependencias entre apps

1. `contenttypes`, `auth` (Django core)
2. **`accounts`** — PRIMERO (AUTH_USER_MODEL)
3. `events`, `analyst`, `sim`, `courses`, `simcity`
4. `chat`, `rooms`, `bitacora`, `bots`
5. Resto de apps

### ⚠️ REGLA CRÍTICA: Nunca ignorar migrations/ en .gitignore

El `.gitignore` fue corregido (commit `2ea63279`) — regla `*/migrations/*` primero,
excepciones `!app/migrations/**` por app después.

    git ls-files --others --exclude-standard | grep migrations
    # Si devuelve algo → git add -f

### Proceso UUID swap de PK (documentado en bitacora)

1. Backup: `dumpdata`
2. Campo `uuid_new` temporal + `RunPython` para poblar
3. `SeparateDatabaseAndState` con SQL directo via `cursor.execute`
4. No usar `makemigrations` automático para el swap en MariaDB

---

## 14. Documentación

### 3 tipos de documento por app

| Tipo | Genera | Propósito |
|------|--------|-----------|
| `APP_CONTEXT.md` | `bash scripts/m360_map.sh app ./app` (auto) | Mapa estructural |
| `APP_DEV_REFERENCE.md` | Devs / Claude | Manual técnico |
| `APP_DESIGN.md` | PM / Claude | Diseño, fases, roadmap |

    bash scripts/m360_map.sh app ./bitacora
    bash scripts/m360_map.sh app ./simcity
    bash scripts/m360_map.sh app ./kpis
    bash scripts/m360_map.sh              # PROJECT_CONTEXT.md completo

---

## 15. Bugs Conocidos Globales

| # | Estado | App | Descripción |
|---|--------|-----|-------------|
| 1 | ✅ | analyst | `clean_file()` duplicado en forms.py |
| 2 | ✅ | analyst/sim | `started_at` inexistente en sim.Interaction |
| 3 | ✅ | analyst | UUID Python en JS → `_safe_json_str()` |
| 4 | ✅ | sim | `@keyframes` dentro de `<script>` |
| 9 | ✅ | sim | `expected_vol` gauss negativo |
| 10 | ✅ | accounts | `accounts_user` tabla inexistente — INC-001 |
| 11 | ✅ | bitacora | `timezone.timedelta` → `from datetime import timedelta` |
| 12 | ✅ | bitacora | `@csrf_exempt` en `upload_image` |
| 13 | ✅ | bitacora | N+1 en `total_attachments` |
| 14 | ✅ | bitacora | HTML render en modelos → movido a templatetags |
| 15 | ✅ | bitacora | Imports lazy → movidos al tope |
| 16 | ✅ | bitacora | `content_block` no renderizaba en bitacora_tags |
| 18 | ✅ | events | Bloque `try` sin `except` en `assign_to_available_user()` |
| 19 | ✅ | events | `STATUS_CHOICES` incorrecto en `TaskFilterForm` |
| 20 | ✅ | events | Campos incorrectos en `TaskScheduleForm` |
| 21 | ✅ | events | Campos incorrectos en `InboxItemForm` |
| 22 | ✅ | events | Falta `get_user_model()` en `AssignAttendeesForm` |
| 23 | ✅ | events | Falta import de `Group` en `setup_views.py` |
| 24 | ✅ | cv | Admin con campos inexistentes |
| 25 | ✅ | kpis | Migración con dependencia incorrecta |
| 5  | ⬜ | chat | Notificaciones no siempre marcan como leídas |
| 6  | ⬜ | events | Consultas N+1 en dashboard de proyectos |
| 7  | ✅ | kpis | Índices compuestos + fecha DateField + UUID — KPI-1 Sprint 7 |
| 8  | ⬜ | courses | Editor de contenido lento con muchos bloques |
| 17 | ⬜ | bitacora | `urls.py` usa `<int:pk>` en lugar de `<uuid:pk>` (BIT-6) |
| SC-1 | ⬜ | simcity | `generate_zr_block` no está en urls.py de M360 |
| SC-2 | ⬜ | simcity | `mobMoneyBtn` no llama a la API — solo loguea warning |
| SC-3 | ⬜ | simcity | Engine offline da 500 genérico — falta manejo de `ConnectionError` |

| 26 | ✅ | kpis | `ForeignKey(User)` en lugar de `settings.AUTH_USER_MODEL` — E301 |
| 27 | ✅ | kpis | `Duplicate column name created_at` en 0002 — IF NOT EXISTS |
| 28 | ✅ | scripts | `m360_map.sh`/`app_map.sh` convertidos en stubs — restaurados |

> Bugs 18-25 corregidos por DeepSeek — pendientes de commit.
> Bugs SC-1/SC-2/SC-3 documentados en `SIMCITY_DEV_REFERENCE.md`.