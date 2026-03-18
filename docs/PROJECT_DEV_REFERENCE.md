# Referencia de Desarrollo — Proyecto Management360

> **Audiencia:** Desarrolladores del proyecto y asistentes de IA (Claude, Copilot, etc.)
> **Actualizado:** 2026-03-17 (sesión nocturna) | **Apps:** 19 | **Archivos Python+HTML:** 696
> **Basado en:** PROJECT_CONTEXT.md, ANALYST_DEV_REFERENCE.md, SIM_DEV_REFERENCE.md

---

## Índice rápido

| Sección | Contenido |
|---------|-----------|
| 1. Estructura del proyecto | Árbol, apps, convenciones |
| 2. Patrones comunes en todas las apps | Models, views, URLs, templates |
| 3. Manejo de fechas (CRÍTICO) | Estándar por app |
| 4. Sistema de caché | Redis keys, TTLs, patrones |
| 5. Seguridad | CSRF, permisos, namespaces |
| 6. Integración analyst ↔ sim | ETL, dashboards, reportes |
| 7. Integración events ↔ chat | Notificaciones, tiempo real |
| 8. APIs internas | Estructura de respuestas, autenticación |
| 9. Frontend unificado | HTMX, Bootstrap, Chart.js |
| 10. Testing | Por app, cobertura |
| 11. Despliegue | build.sh, variables de entorno |
| 12. Migraciones | Orden, dependencias entre apps |
| 13. Documentación | Estándar por app |
| 14. Bugs conocidos globales | Issues que afectan múltiples apps |

---

## 1. Estructura del Proyecto

### Árbol de directorios (nivel 1)

    Management360/
    ├── manage.py
    ├── build.sh
    ├── requirements.txt
    ├── .env
    ├── panel/                 # Configuración principal (settings, middleware, routers)
    ├── docs/                  # Documentación (DESIGN + DEV_REFERENCE por app)
    ├── scripts/               # Utilidades (app_map.sh, m360_map.sh, setup/)
    ├── services/              # Servicios independientes (media_server.py)
    │
    ├── accounts/              # Autenticación, perfiles — AUTH_USER_MODEL
    ├── analyst/               # Plataforma de datos (ver ANALYST_*)
    ├── api/                   # API REST pública
    ├── bitacora/              # Bitácora personal GTD
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
    └── sim/                   # Simulador WFM (ver SIM_*)

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

    # Estándar de IDs — TODAS las apps
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Auditoría — campo estándar: created_by (NO autor, NO host para nuevos modelos)
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

    # Índices compuestos para consultas frecuentes
    class Meta:
        indexes = [
            models.Index(fields=['created_by', 'created_at']),
            models.Index(fields=['is_active', 'created_at']),
        ]

> **Excepciones documentadas:**
> - `events`: usa `host` para Project/Task/Event — convención propia, NO cambiar
> - `rooms`: usa `owner` para Room — convención propia, NO cambiar
> - `bitacora`: usa `fecha_creacion`/`fecha_actualizacion` (en español) — mantener por consistencia interna

### Views

    # Vista GET (HTML)
    @login_required
    def panel_view(request):
        context = {
            'items': Item.objects.filter(created_by=request.user),
        }
        return render(request, 'app/panel.html', context)

    # Vista POST (JSON)
    @login_required
    @require_POST
    def api_action(request):
        try:
            data = json.loads(request.body)
            # ... lógica
            return JsonResponse({'success': True, 'data': result})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)

### URLs

    app_name = 'kpis'

    urlpatterns = [
        path('dashboard/', views.dashboard, name='dashboard'),
        path('export-data/', views.export_data, name='export_data'),
        path('api/stats/', views.api_stats, name='api_stats'),
    ]

### Templates

    {% extends 'base.html' %}
    {% block title %}Mi App - Management360{% endblock %}

    {% block content %}
    <div id="app-root" class="container-fluid">
        <!-- contenido específico de la app -->
    </div>
    {% endblock %}

    {% block extra_js %}
    <script>
        document.addEventListener('DOMContentLoaded', function() {
            // inicialización
        });
    </script>
    {% endblock %}

### CSRF Token en JavaScript

    // FUNCIÓN CORRECTA — usar en todas las apps
    function csrf() {
        return document.cookie.match(/csrftoken=([^;]+)/)?.[1] || '';
    }

    // USO EN FETCH
    fetch(url, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrf()
        },
        body: JSON.stringify(data)
    })

    // INCORRECTO — NO USAR
    // fetch(url, { headers: { 'X-CSRFToken': CSRF_TOKEN } })  // ReferenceError

### Respuestas JSON unificadas

    # Éxito
    {"success": true, "data": {...}, "message": "..."}

    # Error
    {"success": false, "error": "Mensaje de error", "code": "ERROR_CODE"}

---

## 3. Manejo de Fechas — CRÍTICO ⚠️

### Estándar por App

| App | Modelo | Campo(s) de fecha | Ordenamiento |
|-----|--------|-------------------|--------------|
| **sim** | `Interaction` | `fecha` (DateField) + `hora_inicio` (DateTimeField) | `order_by('fecha', 'hora_inicio')` |
| **kpis** | `CallRecord` | `start_time` (DateTimeField) | `order_by('start_time')` |
| **events** | `Task` | `due_date` (DateField) | `order_by('due_date')` |
| **events** | `Event` | `start_date` (DateTimeField) | `order_by('start_date')` |
| **chat** | `Message` | `timestamp` (DateTimeField) | `order_by('timestamp')` |
| **bitacora** | `BitacoraEntry` | `fecha_creacion` (DateTimeField) | `order_by('-fecha_creacion')` |
| **courses** | `Lesson` | `created_at` (DateTimeField) | `order_by('order', 'created_at')` |

### ⚠️ ERROR COMÚN: `timedelta` NO es parte de `django.utils.timezone`

    # INCORRECTO — causa AttributeError en runtime (bug detectado en bitacora/views.py)
    week_start = today - timezone.timedelta(days=today.weekday())

    # CORRECTO
    from datetime import timedelta
    week_start = today - timedelta(days=today.weekday())

### ⚠️ ERROR COMÚN: `started_at` NO EXISTE en `sim.Interaction`

    # INCORRECTO — Causa FieldError
    interactions = Interaction.objects.filter(started_at__gte=date)

    # CORRECTO
    interactions = Interaction.objects.filter(fecha__gte=date).order_by('fecha', 'hora_inicio')

### ⚠️ ERROR COMÚN: Mezclar `DateTimeField` con `DateField`

    # Si filtras por fecha en DateTimeField, usar __date
    calls = CallRecord.objects.filter(start_time__date=target_date)

    # Si tienes DateField separado, usarlo directamente
    interactions = Interaction.objects.filter(fecha=target_date)

---

## 4. Sistema de Caché (Redis)

### Keys y TTLs estándar

| Prefix | App | Contenido | TTL | Ejemplo |
|--------|-----|-----------|-----|---------|
| `df_preview_` | analyst | DataFrame preview | 2h | `df_preview_{uuid}` |
| `stored_dataset_` | analyst | Dataset persistido | ∞ | `stored_dataset_{uuid}` |
| `clip_` | analyst | Portapapeles de sesión | 24h | `clip_{session_key}_{key}` |
| `gtr:session:` | sim | Sesión GTR activa | 4h | `gtr:session:{sid}` |
| `gtr:interactions:` | sim | Interacciones GTR temporales | 4h | `gtr:interactions:{sid}` |
| `chat:presence:` | chat | Presencia de usuario | 5min | `chat:presence:{user_id}` |
| `dashboard:` | kpis | Dashboard cache | 5min | `dashboard:kpis:{user_id}` |

### Patrón de uso en vistas

    from django.core.cache import cache

    def get_dashboard_data(user):
        cache_key = f'dashboard:kpis:{user.id}'
        data = cache.get(cache_key)
        if data is None:
            data = calcular_datos_pesados(user)
            cache.set(cache_key, data, 300)  # 5 minutos
        return data

---

## 5. Seguridad

### Permisos

    # Siempre filtrar por usuario en queryset
    queryset = MyModel.objects.filter(created_by=request.user)

    # NUNCA asumir que pk en URL pertenece al usuario
    obj = get_object_or_404(MyModel, pk=pk, created_by=request.user)

### @csrf_exempt — PROHIBIDO en vistas con datos de usuario

    # INCORRECTO — vulnerabilidad CSRF (detectado en bitacora/views.py upload_image)
    @login_required
    @csrf_exempt
    def upload_image(request): ...

    # CORRECTO — TinyMCE puede enviar CSRF token normalmente
    @login_required
    def upload_image(request): ...

### Renders HTML desde modelos — PROHIBIDO

    # INCORRECTO — XSS potencial + responsabilidad equivocada
    class MyModel(models.Model):
        def render_html(self):
            return f'<div>{self.user_content}</div>'  # user_content sin escapar

    # CORRECTO — usar templatetags o mark_safe con escape explícito
    # En bitacora_tags.py:
    @register.simple_tag
    def render_content_block(block):
        content = escape(block.get('content', ''))
        return mark_safe(f'<div class="content-block">{content}</div>')

---

## 6. Integración analyst ↔ sim

Ver `ANALYST_DEV_REFERENCE.md` y `SIM_DEV_REFERENCE.md` para detalles completos.

    # ETL source apuntando a sim
    source = ETLSource.objects.create(
        model_path='sim.Interaction',
        filters={'sim_account': account_id}
    )

    # Dashboard widget con datos de sim
    widget = DashboardWidget.objects.create(
        dashboard=dashboard,
        source_type='sim_run',
        config={'metric': 'service_level', 'period': 'daily'}
    )

---

## 7. Integración events ↔ chat

    # Notificación de tarea desde events
    from chat.models import Conversation
    conv = Conversation.objects.get_or_create_for_task(task)
    conv.send_system_message(f'Tarea "{task.titulo}" actualizada')

---

## 8. APIs Internas

### Autenticación

    # Todas las APIs internas requieren login
    @login_required
    def api_items(request):
        items = Item.objects.filter(created_by=request.user)
        return JsonResponse({
            'success': True,
            'data': list(items.values('id', 'name'))
        })

---

## 9. Frontend Unificado

### HTMX para interactividad parcial

    <button hx-get="/api/items/?page=2"
            hx-target="#items-list"
            hx-swap="beforeend">
        Cargar más
    </button>

### Bootstrap + Chart.js

    const ctx = document.getElementById('myChart').getContext('2d');
    new Chart(ctx, {
        type: 'bar',
        data: { labels: ['Ene', 'Feb', 'Mar'], datasets: [{ data: [12, 19, 3] }] }
    });

---

## 10. Testing

### Cobertura actual

| App | Tests | Cobertura |
|-----|-------|-----------|
| sim | 157 | 100% |
| analyst | 34/50 | 68% |
| Otras | — | — |

### Ejecutar tests

    python manage.py test sim.tests.test_generators sim.tests.test_gtr_engine -v 2

---

## 11. Despliegue

### build.sh (producción)

    #!/usr/bin/env bash
    set -o errexit
    pip install --no-cache-dir -r requirements.txt
    python manage.py migrate auth
    python manage.py migrate contenttypes
    python manage.py migrate accounts   # ← CRÍTICO: antes que el resto
    python manage.py migrate --no-input
    python manage.py collectstatic --no-input

### Variables de entorno (.env)

    SECRET_KEY=...
    DEBUG=False
    ALLOWED_HOSTS=...
    DATABASE_URL=mysql://user:pass@localhost:3306/projects
    REDIS_URL=redis://:password@localhost:6379/0
    EMAIL_HOST=smtp.gmail.com
    AWS_ACCESS_KEY_ID=...

---

## 12. Migraciones

### Orden de dependencias entre apps

1. `contenttypes`, `auth` (Django core)
2. **`accounts`** — PRIMERO antes que cualquier otra app (AUTH_USER_MODEL)
3. `events` (depende de accounts)
4. `analyst`, `sim`, `courses` (independientes)
5. `chat`, `rooms` (dependen de accounts)
6. `kpis` (independiente)
7. `bots` (depende de events, analyst)
8. `bitacora` (depende de events, rooms, courses)
9. Otras apps

### ⚠️ REGLA CRÍTICA: Nunca ignorar carpetas migrations/ en .gitignore

La pérdida de `accounts/migrations/` causó INC-001 (tabla inexistente en BD).
Verificar que todas las apps tengan migrations/ trackeadas:

    git ls-files --others --exclude-standard | grep migrations
    # Si devuelve algo → hacer git add

### Comandos útiles

    # Ver estado completo
    python manage.py showmigrations

    # Migración con desincronización (BD recreada)
    python manage.py migrate --fake-initial     # aplica fake solo a 0001 donde tabla ya existe

    # Crear migración vacía para RunPython
    python manage.py makemigrations app_name --empty --name descripcion

    # Backup antes de migración riesgosa
    python manage.py dumpdata app_name --indent 2 > backup_app_$(date +%Y%m%d).json

### Proceso para migración con cambio de PK (int → UUID)

    # 1. Backup
    python manage.py dumpdata bitacora --indent 2 > bitacora_backup.json

    # 2. Agregar campo UUID temporal (no-pk) en migración
    # 3. RunPython para popular UUIDs
    # 4. Segunda migración para swap de PK
    # NUNCA hacer el swap en una sola migración con datos existentes

---

## 13. Documentación

### 3 tipos de documento por app

| Tipo | Genera | Propósito |
|------|--------|-----------|
| `APP_CONTEXT.md` | `bash scripts/m360_map.sh app ./app` (auto) | Mapa estructural |
| `APP_DEV_REFERENCE.md` | Devs / Claude | Manual técnico |
| `APP_DESIGN.md` | PM / Claude | Diseño, fases, roadmap |

> El CONTEXT.md es **auto-generado** — nunca editar manualmente.

### Generar mapas

    bash scripts/m360_map.sh app ./bitacora   # → BITACORA_CONTEXT.md
    bash scripts/m360_map.sh app ./kpis       # → KPIS_CONTEXT.md
    bash scripts/m360_map.sh                  # → PROJECT_CONTEXT.md completo

---

## 14. Bugs Conocidos Globales

| # | Estado | App | Descripción |
|---|--------|-----|-------------|
| 1 | ✅ Corregido | analyst | `clean_file()` duplicado en forms.py |
| 2 | ✅ Corregido | analyst/sim | `started_at` inexistente en sim.Interaction |
| 3 | ✅ Corregido | analyst | UUID Python en JS → `_safe_json_str()` |
| 4 | ✅ Corregido | sim | `@keyframes` dentro de `<script>` en training.html |
| 9 | ✅ Corregido | sim | `expected_vol` gauss negativo en `_generate_window_*` |
| 10 | ✅ Resuelto | accounts | `accounts_user` tabla inexistente — INC-001 (ver PROJECT_DESIGN.md) |
| 11 | ⬜ Pendiente | bitacora | `timezone.timedelta` → debe ser `from datetime import timedelta` |
| 12 | ⬜ Pendiente | bitacora | `@csrf_exempt` en `upload_image` — remover |
| 13 | ⬜ Pendiente | bitacora | N+1 en `total_attachments` del dashboard stats |
| 14 | ⬜ Pendiente | bitacora | Lógica HTML render en modelos (350 líneas) → mover a templatetags |
| 15 | ⬜ Pendiente | bitacora | Imports lazy dentro de métodos y en medio del archivo |
| 5  | ⬜ Pendiente | chat | Notificaciones no siempre marcan como leídas |
| 6  | ⬜ Pendiente | events | Consultas N+1 en dashboard de proyectos |
| 7  | ⬜ Pendiente | kpis | Falta de índices en CallRecord |
| 8  | ⬜ Pendiente | courses | Editor de contenido lento con muchos bloques |

---

## Handoff — Resumen para Próxima Sesión

### Estado al 2026-03-17

**BD:** 141 tablas, todas OK. Usuarios `su` (pk=1) y `arturo` (pk=2) restaurados.

**bitacora — trabajo en progreso:**

| Archivo | Estado | Notas |
|---------|--------|-------|
| `models.py` | ✅ Refactorizado | UUID pk, created_by, is_active, TextChoices, sin render HTML |
| `views.py` | ⬜ Pendiente | 5 issues identificados (bugs #11-15) |
| `forms.py` | ✅ OK | Sin cambios necesarios |
| `urls.py` | 🟡 Menor | Naming `dashboard` vs `list` ambiguo |
| `migración 0003` | ⬜ Pendiente | Generada parcialmente, falta RunPython para UUID swap |

### Archivos para arrancar próxima sesión

    # Mapa actualizado
    bash scripts/m360_map.sh app ./bitacora

    # Código pendiente de revisar
    cat bitacora/views.py | termux-clipboard-set
    cat bitacora/templatetags/bitacora_tags.py | termux-clipboard-set

### Checklist bitacora

- [x] Analizar models.py
- [x] Analizar views.py, forms.py, urls.py
- [x] Refactorizar models.py
- [ ] Refactorizar views.py
- [ ] Revisar bitacora_tags.py (render HTML movido desde models)
- [ ] Generar migración 0003 completa con RunPython
- [ ] Generar BITACORA_DESIGN.md
- [ ] Generar BITACORA_DEV_REFERENCE.md

### Checklist Sprint 7 (kpis) — retomar después de bitacora

- [ ] Revisar índices de CallRecord
- [ ] Implementar caching en dashboard de KPIs
- [ ] Crear ETL source para KPIs en analyst
- [ ] Unificar manejo de fechas
- [ ] Documentar KPIs (CONTEXT, DESIGN, DEV_REFERENCE)
