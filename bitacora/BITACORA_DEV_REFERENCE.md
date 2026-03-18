# Bitácora — Referencia de Desarrollo

> **Audiencia:** Desarrolladores y asistentes de IA
> **Actualizado:** 2026-03-17
> **App:** `bitacora` | **Namespace:** `bitacora`

---

## Índice

| Sección | Contenido |
|---------|-----------|
| 1. Modelos | Campos, choices, métodos |
| 2. Vistas | Lógica, filtros, contexto |
| 3. Forms | Widgets, filtros de queryset |
| 4. URLs | Patrones, names |
| 5. Templatetags | Render de bloques |
| 6. Integración courses | ContentBlock, structured_content |
| 7. Integración events/rooms | Relaciones opcionales |
| 8. TinyMCE | Configuración, upload |
| 9. Bugs conocidos | Issues pendientes |
| 10. Migraciones | Historial, pendientes |

---

## 1. Modelos

### `BitacoraEntry`

```python
# bitacora/models.py

class CategoriaChoices(models.TextChoices):
    PERSONAL  = 'personal',  'Personal'
    VIAJE     = 'viaje',     'Viaje'
    TRABAJO   = 'trabajo',   'Trabajo'
    META      = 'meta',      'Meta'
    IDEA      = 'idea',      'Idea'
    RECUERDO  = 'recuerdo',  'Recuerdo'
    DIARIO    = 'diario',    'Diario'
    REFLEXION = 'reflexion', 'Reflexión'

class MoodChoices(models.TextChoices):
    MUY_BIEN = 'muy_bien', '😄 Muy bien'
    BIEN     = 'bien',     '🙂 Bien'
    NEUTRAL  = 'neutral',  '😐 Neutral'
    MAL      = 'mal',      '😕 Mal'
    MUY_MAL  = 'muy_mal',  '😞 Muy mal'

class BitacoraEntry(models.Model):
    id         = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    titulo     = models.CharField(max_length=200)
    contenido  = models.TextField()
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bitacora_entries')
    categoria  = models.CharField(max_length=50, choices=CategoriaChoices.choices, default=CategoriaChoices.PERSONAL)
    mood       = models.CharField(max_length=20, choices=MoodChoices.choices, blank=True)
    is_active  = models.BooleanField(default=True)
    is_public  = models.BooleanField(default=False)
    # FKs opcionales con related_name='bitacora_entries'
    related_event, related_task, related_project, related_room
    tags               = models.ManyToManyField('events.Tag', blank=True)
    structured_content = models.JSONField(default=list, blank=True)
    latitud  = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitud = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    fecha_creacion      = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
```

### Método clave

```python
def get_structured_content_blocks(self):
    """Devuelve la lista de bloques. Nunca retorna None."""
    return self.structured_content if self.structured_content else []
```

### `BitacoraAttachment`

```python
class BitacoraAttachment(models.Model):
    id     = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    entry  = models.ForeignKey(BitacoraEntry, on_delete=models.CASCADE, related_name='attachments')
    archivo = models.FileField(upload_to='bitacora/attachments/')
    tipo   = models.CharField(max_length=20, choices=TipoChoices.choices)
    descripcion  = models.CharField(max_length=200, blank=True)
    fecha_subida = models.DateTimeField(auto_now_add=True)
```

---

## 2. Vistas

### `BitacoraListView`

Sirve dos templates según la URL:
- `/bitacora/` → `dashboard.html` (stats + recent + GTD integration)
- `/bitacora/list/` → `entry_list.html` (lista paginada simple)

**Filtros GET disponibles:**

| Param | Tipo | Ejemplo |
|-------|------|---------|
| `q` | texto libre | `?q=reunión` |
| `categoria` | choice value | `?categoria=trabajo` |
| `periodo` | hoy / semana / mes | `?periodo=semana` |
| `publico` | 1 / 0 | `?publico=1` |

**Contexto del dashboard:**

```python
context['stats'] = {
    'total_entries': int,
    'entries_this_month': int,
    'public_entries': int,
    'public_percentage': int,
    'categories_used': int,
    'total_categories': int,   # len(CategoriaChoices)
    'total_attachments': int,  # ⚠️ N+1 bug pendiente
}
context['category_stats']  # dict: {label: {count, percentage}}
context['recent_entries']  # últimas 10
context['gtd_items']       # InboxItem pendientes (últimas 5) — try/except
context['active_tasks']    # Task activas (últimas 3) — try/except
```

### `BitacoraDetailView`

Carga los bloques de `structured_content` renderizados:
```python
context['rendered_structured_content']  # lista de dicts con 'rendered_content' añadido
```
El render usa `bitacora_tags.render_content_block(block)`.

### `BitacoraCreateView` / `BitacoraUpdateView`

Ambas usan `StructuredContentMixin` que extrae bloques embebidos del HTML de TinyMCE
antes de guardar, limpia el HTML y popula `instance.structured_content`.

Reciben `user` en `get_form_kwargs` para filtrar los querysets de relaciones.

### `BitacoraDeleteView`

```python
# ⚠️ BUG PENDIENTE: en Django 4+/5 el método correcto es form_valid o post, no delete
def delete(self, request, *args, **kwargs):
    messages.success(...)
    return super().delete(...)
```

### `content_blocks_list`

Vista function-based. Filtra `courses.ContentBlock` por `is_public=True` o `author=request.user`.

Filtros GET: `category`, `content_type`, `entry` (id de entrada seleccionada).

### `insert_content_block`

Inserta un bloque en `entry.structured_content` y llama `block.increment_usage()`.
Redirige a `bitacora:update` después de insertar.

### `upload_image`

Upload para TinyMCE. Valida tipo MIME y tamaño (máx 5MB).
Retorna `{"location": url, "uploaded": 1}` — formato esperado por TinyMCE.

```python
# ⚠️ BUG PENDIENTE: @csrf_exempt debe removerse
# TinyMCE puede enviar CSRF token normalmente
```

---

## 3. Forms

### `BitacoraEntryForm`

```python
fields = ['titulo', 'contenido', 'categoria', 'tags',
          'related_event', 'related_task', 'related_project', 'related_room',
          'latitud', 'longitud', 'is_public', 'mood']

widgets = {
    'contenido': TinyMCE(attrs={'cols': 80, 'rows': 30}),
    'tags': forms.SelectMultiple(attrs={'class': 'form-control'}),
}
```

**Filtros de queryset por usuario** (en `__init__`):

```python
# Correcto — verificado contra los modelos de events y rooms
self.fields['related_event'].queryset   = Event.objects.filter(host=user)
self.fields['related_task'].queryset    = Task.objects.filter(host=user)
self.fields['related_project'].queryset = Project.objects.filter(host=user)
self.fields['related_room'].queryset    = Room.objects.filter(owner=user)
```

> `events` usa `host`, `rooms` usa `owner` — convenciones propias de esas apps.

---

## 4. URLs

```python
app_name = 'bitacora'

urlpatterns = [
    path('',                                           name='dashboard'),
    path('list/',                                      name='list'),
    path('<int:pk>/',                                  name='detail'),     # ⚠️ será uuid tras migración 0003
    path('create/',                                    name='create'),
    path('<int:pk>/update/',                           name='update'),     # ⚠️ será uuid
    path('<int:pk>/delete/',                           name='delete'),     # ⚠️ será uuid
    path('content-blocks/',                            name='content_blocks'),
    path('<int:entry_id>/insert-block/<int:block_id>/',name='insert_content_block'),
    path('upload-image/',                              name='upload_image'),
]
```

> ⚠️ Después de aplicar migración 0003, los `<int:pk>` deben cambiar a `<uuid:pk>`.

**Ambigüedad pendiente:** `dashboard` y `list` usan la misma view con distinto template.
`CreateView.success_url = reverse_lazy('bitacora:list')` redirige a `/list/`, no al dashboard.
Definir comportamiento deseado antes de tocar.

---

## 5. Templatetags — `bitacora_tags.py`

### Funciones de render (movidas desde models.py en refactor 2026-03-17)

El render de bloques de contenido estructurado vive en `bitacora/templatetags/bitacora_tags.py`.
Se invoca desde `BitacoraDetailView.get_context_data`:

```python
from .templatetags.bitacora_tags import render_content_block
rendered_content = render_content_block(block)
```

### Tipos de bloque soportados

| `content_type` | Render |
|----------------|--------|
| `html` | `<div class="content-block-html">` |
| `bootstrap` | `<div class="content-block-bootstrap">` |
| `text` | `<p>` wrapeado |
| `markdown` | Conversión básica: `**bold**`, `*italic*`, `` `code` `` |
| `quote` | `<blockquote class="blockquote">` |
| `code` | `<pre><code>` |
| `card` | Bootstrap card |
| `alert` | Bootstrap alert-info |
| `json` | `<pre><code class="language-json">` (formateado) |
| `ad_*` | Componentes publicitarios (ad_banner, ad_card, ad_alert, etc.) |

> ⚠️ Los f-strings con contenido de usuario deben usar `django.utils.html.escape()`
> para evitar XSS. Validar en próxima revisión de bitacora_tags.py.

---

## 6. Integración con courses.ContentBlock

### Flujo de inserción

```
Usuario en entry_detail
    → click "Insertar bloque"
    → GET /bitacora/content-blocks/?entry={pk}
    → selecciona bloque
    → GET /bitacora/{entry_id}/insert-block/{block_id}/
    → entry.structured_content.append({snapshot del bloque})
    → entry.save()
    → redirect a bitacora:update
```

### Estructura de un bloque en `structured_content`

```python
{
    'id': block.id,              # int (PK de ContentBlock)
    'type': 'content_block',
    'title': block.title,
    'content_type': block.content_type,  # html/text/markdown/etc.
    'content': block.get_content(),      # snapshot del contenido
    'inserted_at': timezone.now().isoformat(),
}
```

> Los bloques son **snapshots inmutables** — cambios posteriores en el ContentBlock
> original no afectan las entradas de bitácora existentes.

---

## 7. Integración con events / rooms

### Relaciones opcionales

Todos los FK son `null=True, blank=True, on_delete=SET_NULL`:

```python
# Desde una entrada, acceder al proyecto relacionado
entry.related_project    # events.Project o None
entry.related_task       # events.Task o None
entry.related_event      # events.Event o None
entry.related_room       # rooms.Room o None

# Desde un proyecto, acceder a sus entradas de bitácora
project.bitacora_entries.all()    # related_name='bitacora_entries'
task.bitacora_entries.all()
event.bitacora_entries.all()
room.bitacora_entries.all()
```

### Tags compartidos con events

```python
# Tags de una entrada
entry.tags.all()          # QuerySet de events.Tag

# Entradas con cierto tag
BitacoraEntry.objects.filter(tags__name='sprint7', created_by=user)
```

### GTD Integration en dashboard

```python
# InboxItems pendientes (no procesados) del usuario
InboxItem.objects.filter(created_by=user, is_processed=False).order_by('-created_at')[:5]

# Tareas activas del usuario
Task.objects.filter(host=user, done=False).order_by('-created_at')[:3]
```

Ambas están en `try/except` por si `events` no está disponible.

---

## 8. TinyMCE

### Configuración del widget

```python
TinyMCE(attrs={'cols': 80, 'rows': 30})
```

La configuración extendida (plugins, toolbar, etc.) vive en el template `entry_form.html`
o en `settings.py` bajo `TINYMCE_DEFAULT_CONFIG`.

### Upload de imágenes

TinyMCE llama a `/bitacora/upload-image/` con `POST multipart/form-data`.
La vista espera el archivo en `request.FILES['file']`.

Respuesta esperada por TinyMCE:
```json
{"location": "/media/bitacora_images/abc123.jpg", "uploaded": 1}
```

### StructuredContentMixin

Extrae bloques embebidos directamente en el HTML de TinyMCE antes de guardar:

```python
# Patrón buscado en el HTML
<div class="content-block" data-block-id="123" data-block-type="html">...</div>

# También busca JSON embebido:
[{"type": "content_block", ...}]
```

El HTML limpiado (sin los bloques extraídos) se guarda en `contenido`.
Los bloques extraídos se guardan en `structured_content`.

---

## 9. Bugs Conocidos

| # | Severidad | Archivo | Descripción | Fix |
|---|-----------|---------|-------------|-----|
| B-01 | 🔴 Bug real | `views.py:117` | `timezone.timedelta` no existe | `from datetime import timedelta` |
| B-02 | 🔴 Seguridad | `views.py:353` | `@csrf_exempt` en upload_image | Remover decorator |
| B-03 | 🟠 Performance | `views.py:143` | N+1 en `total_attachments` | `.aggregate(Count('attachments'))` |
| B-04 | 🟠 Organización | `views.py:349` | Imports `JsonResponse`, `csrf_exempt` en medio del archivo | Mover al tope |
| B-05 | 🟠 Organización | `views.py:17,68` | `import json`, `import re` dentro de métodos | Mover al tope |
| B-06 | 🟡 Mantenimiento | `views.py:270` | `DeleteView.delete()` deprecated en Django 5 | Usar `form_valid` o `post` |
| B-07 | 🟡 UX | `views.py:216` | `success_url` de create apunta a `list`, no a `detail` | Usar `get_success_url` |
| B-08 | 🟡 XSS potencial | `bitacora_tags.py` | Variables de usuario en f-strings sin `escape()` | Validar y agregar `escape()` |

---

## 10. Migraciones

### Historial aplicado

| Migración | Descripción | Estado |
|-----------|-------------|--------|
| `0001_initial` | Modelos iniciales | ✅ aplicada |
| `0002_alter_bitacoraentry_contenido` | Altera campo contenido | ✅ aplicada |

### Migración 0003 — Pendiente de aplicar

Cambios del refactor 2026-03-17:

| Cambio | Tipo |
|--------|------|
| `id` AutoField → UUIDField | Requiere RunPython (datos existentes) |
| `autor` → `created_by` | RenameField |
| Agregar `is_active` | AddField |
| `mood` CharField libre → choices | AlterField |
| `related_*` FK agregar `related_name` | AlterField |
| UUID pk en `BitacoraAttachment` | Requiere RunPython |

**Proceso recomendado antes de aplicar:**

```bash
# 1. Backup
python manage.py dumpdata bitacora --indent 2 > bitacora_backup_pre_0003.json

# 2. Verificar entradas existentes
python manage.py shell -c "
from bitacora.models import BitacoraEntry
print(BitacoraEntry.objects.count(), 'entradas')
"

# 3. Generar y revisar migración
python manage.py makemigrations bitacora --name refactor_conventions
# revisar el archivo generado antes de aplicar

# 4. Aplicar
python manage.py migrate bitacora

# 5. Actualizar urls.py: <int:pk> → <uuid:pk>
```

> ⚠️ El swap de PK `int → UUID` en tablas con datos requiere RunPython explícito.
> La migración generada automáticamente puede no manejar esto correctamente.
> Revisar el SQL generado con `python manage.py sqlmigrate bitacora 0003` antes de aplicar.
