# Bitácora — Referencia de Desarrollo

> **Audiencia:** Desarrolladores y asistentes de IA
> **Actualizado:** 2026-03-18
> **App:** `bitacora` | **Namespace:** `bitacora`

---

## Índice

| Sección | Contenido |
|---------|-----------|
| 1. Modelos | Campos, choices, métodos |
| 2. Vistas | Lógica, filtros, contexto |
| 3. Utils | extract_structured_content |
| 4. Forms | Widgets, filtros de queryset |
| 5. URLs | Patrones, names |
| 6. Templatetags | Render de bloques |
| 7. Integración courses | ContentBlock, structured_content |
| 8. Integración events/rooms | Relaciones opcionales |
| 9. TinyMCE | Upload, configuración |
| 10. Bugs resueltos | Historial |
| 11. Migraciones | Historial completo |

---

## 1. Modelos

### `BitacoraEntry`

```python
class CategoriaChoices(models.TextChoices):
    PERSONAL='personal','Personal' | VIAJE='viaje','Viaje' | TRABAJO='trabajo','Trabajo'
    META='meta','Meta' | IDEA='idea','Idea' | RECUERDO='recuerdo','Recuerdo'
    DIARIO='diario','Diario' | REFLEXION='reflexion','Reflexión'

class MoodChoices(models.TextChoices):
    MUY_BIEN='muy_bien','😄 Muy bien' | BIEN='bien','🙂 Bien' | NEUTRAL='neutral','😐 Neutral'
    MAL='mal','😕 Mal' | MUY_MAL='muy_mal','😞 Muy mal'

class BitacoraEntry(models.Model):
    id         = UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    titulo     = CharField(max_length=200)
    contenido  = TextField()
    created_by = ForeignKey(User, CASCADE, related_name='bitacora_entries')
    categoria  = CharField(choices=CategoriaChoices, default=PERSONAL)
    mood       = CharField(choices=MoodChoices, blank=True)
    is_active  = BooleanField(default=True)
    is_public  = BooleanField(default=False)
    related_event/task/project/room = FK opcionales (SET_NULL, related_name='bitacora_entries')
    tags               = ManyToManyField('events.Tag', blank=True)
    structured_content = JSONField(default=list, blank=True)
    latitud/longitud   = DecimalField(9,6, null=True, blank=True)
    fecha_creacion      = DateTimeField(auto_now_add=True)
    fecha_actualizacion = DateTimeField(auto_now=True)
```

### Método clave

```python
def get_structured_content_blocks(self):
    return self.structured_content if self.structured_content else []
```

### `BitacoraAttachment`

```python
class BitacoraAttachment(models.Model):
    id           = UUIDField(primary_key=True, ...)
    entry        = ForeignKey(BitacoraEntry, CASCADE, related_name='attachments')
    archivo      = FileField(upload_to='bitacora/attachments/')
    tipo         = CharField(choices=TipoChoices)  # image/audio/video/document
    descripcion  = CharField(200, blank=True)
    fecha_subida = DateTimeField(auto_now_add=True)
```

---

## 2. Vistas

### `BitacoraListView`

- `/bitacora/` → `dashboard.html`
- `/bitacora/list/` → `entry_list.html`
- Todos los querysets con `is_active=True`

**Filtros GET:** `q`, `categoria`, `periodo` (hoy/semana/mes), `publico`

**Contexto dashboard:**
```python
context['stats'] = {
    'total_entries', 'entries_this_month', 'public_entries',
    'public_percentage', 'categories_used', 'total_categories',
    'total_attachments',  # query agregada — sin N+1
}
context['category_stats']   # {label: {count, percentage}}
context['recent_entries']   # últimas 10
context['gtd_items']        # InboxItem pendientes[:5] — try/except
context['active_tasks']     # Task activas[:3] — try/except
```

### `BitacoraDetailView`
```python
context['rendered_structured_content']  # bloques con 'rendered_content' añadido
```

### `BitacoraCreateView` / `BitacoraUpdateView`
- `extract_structured_content(html)` desde `bitacora.utils`
- `get_success_url()` → `bitacora:detail` con pk

### `BitacoraDeleteView`
- `form_valid()` (Django 5 — correcto)

### `upload_image`
- Sin `@csrf_exempt`
- Retorna `{"location": url, "uploaded": 1}`

---

## 3. Utils — `bitacora/utils.py`

```python
from bitacora.utils import extract_structured_content

structured = extract_structured_content(html_content)
# → lista de dicts | None
```

Busca:
1. `<div class="content-block" data-block-id="..." data-block-type="...">`
2. JSON embebido `[{"type": "content_block", ...}]` (formato legado)

---

## 4. Forms

```python
fields = ['titulo', 'contenido', 'categoria', 'tags',
          'related_event', 'related_task', 'related_project', 'related_room',
          'latitud', 'longitud', 'is_public', 'mood']

# Filtros queryset verificados contra modelos reales:
related_event/task/project → filter(host=user)   # events usa host
related_room               → filter(owner=user)  # rooms usa owner
```

---

## 5. URLs

```python
app_name = 'bitacora'
# ⚠️ BIT-6: todos los <int:pk> deben cambiar a <uuid:pk>
path('',              name='dashboard')
path('list/',         name='list')
path('<int:pk>/',     name='detail')    # ⚠️ pendiente uuid
path('create/',       name='create')
path('<int:pk>/update/', name='update') # ⚠️ pendiente uuid
path('<int:pk>/delete/', name='delete') # ⚠️ pendiente uuid
path('content-blocks/',  name='content_blocks')
path('<int:entry_id>/insert-block/<int:block_id>/', name='insert_content_block')
path('upload-image/', name='upload_image')
```

---

## 6. Templatetags

```python
{% load bitacora_tags %}
{% render_content_block block %}
```

**`content_block`** (`content_type`): `html`, `bootstrap`, `text`, `markdown`,
`quote`, `code`, `card`, `alert`, `json`

**`ad_*`**: `ad_banner`, `ad_card`, `ad_alert`, `ad_testimonial`, `ad_countdown`,
`ad_feature`, `ad_comparison`, `ad_achievement`

Todas las variables de usuario pasan por `escape()`. Excepción: `html`/`bootstrap`
no se escapan (contenido de TinyMCE — confiado).

---

## 7. Integración con courses.ContentBlock

```python
# Estructura de un bloque en structured_content
{
    'id': block.id, 'type': 'content_block',
    'title': block.title, 'content_type': block.content_type,
    'content': block.get_content(),  # snapshot inmutable
    'inserted_at': timezone.now().isoformat(),
}
```

Flujo: `entry_detail` → `content_blocks_list` → `insert_content_block` → `entry.save()`

---

## 8. Integración con events / rooms

```python
entry.related_project/task/event/room  # None o FK
project.bitacora_entries.all()         # reverse — related_name='bitacora_entries'
entry.tags.all()                       # QuerySet events.Tag
BitacoraEntry.objects.filter(tags__name='sprint7', created_by=user)
```

---

## 9. TinyMCE

Upload: POST a `/bitacora/upload-image/`, archivo en `request.FILES['file']`
Respuesta: `{"location": "/media/bitacora_images/abc.jpg", "uploaded": 1}`

---

## 10. Bugs Resueltos

| # | Descripción | Fix |
|---|-------------|-----|
| B-01 | `timezone.timedelta` | `from datetime import timedelta` |
| B-02 | `@csrf_exempt` en upload | Removido |
| B-03 | N+1 attachments | `.count()` agregado |
| B-04/05 | Imports dispersos | Movidos al tope |
| B-06 | `DeleteView.delete()` | → `form_valid` |
| B-07 | `success_url` a `list` | → `get_success_url()` con detail |
| B-08 | XSS en tags | `escape()` agregado |
| B-09 | `content_block` no renderizaba | Handler agregado |

---

## 11. Migraciones

| Migración | Descripción | Estado |
|-----------|-------------|--------|
| `0001_initial` | Modelos iniciales | ✅ |
| `0002_alter_bitacoraentry_contenido` | Campo contenido | ✅ |
| `0003_refactor_conventions` | autor→created_by, is_active, choices | ✅ |
| `0004_uuid_primary_keys` | UUID pk swap (RunPython + SQL) | ✅ |

**Nota 0003:** usó `SeparateDatabaseAndState` — el rename `autor→created_by` fue
ejecutado manualmente en BD antes (FK int/bigint incompatible en MariaDB).

**Nota 0004:** no reversible. Backup en `backup_pre_0004.json`.

```bash
# Backup antes de migrar
python manage.py dumpdata bitacora --indent 2 > bitacora_backup_$(date +%Y%m%d).json
```
