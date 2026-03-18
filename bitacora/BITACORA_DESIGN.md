# Bitácora — Diseño, Roadmap y Estado de Implementación

> **Última actualización:** 2026-03-18
> **App:** `bitacora` | **Namespace:** `bitacora`
> **Propósito:** Diario personal GTD — registro libre de entradas con contenido enriquecido
> **Archivos:** 17 | **Modelos:** 2 | **Endpoints:** 9

---

## Visión General

`bitacora` es la app de diario personal del proyecto Management360. Permite al usuario
registrar entradas libres con texto enriquecido (TinyMCE), adjuntar archivos, asociar
contenido estructurado reutilizable desde `courses.ContentBlock`, y vincular entradas
con proyectos, tareas, eventos y salas del ecosistema.

### Rol dentro de Management360

    bitacora ─┬──> events.Event / Task / Project  (relaciones opcionales)
              ├──> rooms.Room                      (relaciones opcionales)
              ├──> events.Tag                      (tags M2M)
              └──> courses.ContentBlock            (bloques de contenido estructurado)

Es una app de **lectura/escritura personal** — cada entrada pertenece a un único usuario
y por defecto es privada (`is_public=False`).

---

## Modelos

### `BitacoraEntry` (modelo principal)

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `id` | UUIDField PK | Identificador público (migración 0004) |
| `titulo` | CharField(200) | Título de la entrada |
| `contenido` | TextField | Cuerpo HTML (editado con TinyMCE) |
| `created_by` | FK → User | Autor (renombrado desde `autor` en 0003) |
| `categoria` | CharField choices | CategoriaChoices (8 opciones) |
| `mood` | CharField choices | MoodChoices (5 opciones) |
| `is_active` | BooleanField | Soft delete (agregado en 0003) |
| `is_public` | BooleanField | Visibilidad pública |
| `related_event` | FK → events.Event | Relación opcional |
| `related_task` | FK → events.Task | Relación opcional |
| `related_project` | FK → events.Project | Relación opcional |
| `related_room` | FK → rooms.Room | Relación opcional |
| `tags` | M2M → events.Tag | Tags reutilizados de events |
| `structured_content` | JSONField | Bloques de courses.ContentBlock insertados |
| `latitud` / `longitud` | DecimalField | Ubicación geográfica opcional |
| `fecha_creacion` | DateTimeField | auto_now_add |
| `fecha_actualizacion` | DateTimeField | auto_now |

**Categorías disponibles:** personal, viaje, trabajo, meta, idea, recuerdo, diario, reflexión

**Moods disponibles:** muy_bien 😄, bien 🙂, neutral 😐, mal 😕, muy_mal 😞

### `BitacoraAttachment`

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `id` | UUIDField PK | Identificador público (migración 0004) |
| `entry` | FK → BitacoraEntry | Entrada padre |
| `archivo` | FileField | Archivo subido a `bitacora/attachments/` |
| `tipo` | CharField choices | image / audio / video / document |
| `descripcion` | CharField(200) | Descripción opcional |
| `fecha_subida` | DateTimeField | auto_now_add |

---

## Endpoints

| URL | Name | Vista | Descripción |
|-----|------|-------|-------------|
| `/bitacora/` | `dashboard` | `BitacoraListView` | Dashboard principal |
| `/bitacora/list/` | `list` | `BitacoraListView` | Lista simple (template alternativo) |
| `/bitacora/<pk>/` | `detail` | `BitacoraDetailView` | Detalle de entrada |
| `/bitacora/create/` | `create` | `BitacoraCreateView` | Crear entrada |
| `/bitacora/<pk>/update/` | `update` | `BitacoraUpdateView` | Editar entrada |
| `/bitacora/<pk>/delete/` | `delete` | `BitacoraDeleteView` | Eliminar entrada |
| `/bitacora/content-blocks/` | `content_blocks` | `content_blocks_list` | Bloques disponibles de courses |
| `/bitacora/<eid>/insert-block/<bid>/` | `insert_content_block` | `insert_content_block` | Insertar bloque en entrada |
| `/bitacora/upload-image/` | `upload_image` | `upload_image` | Upload para TinyMCE |

> ⚠️ `urls.py` todavía usa `<int:pk>` — pendiente actualizar a `<uuid:pk>` (BIT-6).

---

## Funcionalidades Implementadas

### ✅ CRUD de entradas
- Crear, leer, actualizar, eliminar entradas con TinyMCE
- Filtros: texto libre, categoría, período, visibilidad
- Paginación: 10 entradas por página
- Soft delete con `is_active`

### ✅ Dashboard con estadísticas
- Total entradas, entradas del mes, % públicas
- Distribución por categoría (query agregada — sin N+1)
- Integración GTD: InboxItems pendientes + Tareas activas

### ✅ Contenido estructurado (integración con courses)
- Inserción de bloques en `structured_content` (JSONField)
- Extracción desde HTML de TinyMCE (`extract_structured_content` en `utils.py`)

### ✅ Upload de imágenes para TinyMCE
- Valida tipo (jpg/png/gif/webp) y tamaño (máx 5MB)

### ✅ Adjuntos
- `BitacoraAttachment`: imagen, audio, video, documento

---

## Estado de Implementación

| Componente | Estado | Notas |
|------------|--------|-------|
| `models.py` | ✅ | UUID pk, created_by, is_active, TextChoices |
| `views.py` | ✅ | 7 bugs corregidos |
| `utils.py` | ✅ | `extract_structured_content` |
| `forms.py` | ✅ | Sin cambios |
| `urls.py` | 🟡 | `<int:pk>` → `<uuid:pk>` pendiente (BIT-6) |
| `bitacora_tags.py` | ✅ | XSS corregido, content_block handler |
| Templates | ⬜ | 6 templates pendientes de auditoría (BIT-5) |
| Tests | ⬜ | BIT-16 |
| Documentación | ✅ | Completa |

---

## Roadmap

### Fase 1 — Estabilización (Sprint 7) — Casi completa

| Tarea | Prioridad | Estado |
|-------|-----------|--------|
| BIT-1 a BIT-4 | 🔴🟠 | ✅ |
| BIT-5: Auditoría templates | 🟡 | ⬜ |
| BIT-6: `urls.py` uuid | 🟡 | ⬜ |

### Fase 2 — Features GTD (Sprint 8+) ⬜

| Tarea | Prioridad |
|-------|-----------|
| BIT-10: Vista de mapa geográfico | 🟡 |
| BIT-11: Exportación a PDF | 🟠 |
| BIT-12: Búsqueda full-text | 🟠 |
| BIT-13: Timeline view | 🟡 |
| BIT-14: Estadísticas de mood | 🟡 |
| BIT-15: Entradas relacionadas | 🟡 |
| BIT-16: Tests unitarios | 🟠 |

---

## Historial de Cambios

### 2026-03-18 — Refactor completo (Claude)
- `models.py`: UUID pk, `created_by`, `is_active`, TextChoices, sin HTML
- `views.py`: 7 bugs corregidos
- `utils.py`: nuevo — `extract_structured_content`
- `bitacora_tags.py`: content_block handler + `escape()` XSS
- Migraciones 0003+0004 aplicadas y commiteadas
- Incidencia: FK int/bigint incompatible en MariaDB — resuelto con SQL manual

---

## Decisiones de Diseño

- **JSONField para `structured_content`:** snapshots inmutables de ContentBlock
- **Reutilizar `events.Tag`:** evita fragmentación de tags
- **TinyMCE:** texto libre más natural para diario personal
- **Render HTML en templatetags:** modelos no deben generar HTML (XSS + SRP)

---

## Notas para Claude

- Campo autor = `created_by` (NO `autor`)
- `fecha_creacion`/`fecha_actualizacion` en español — no cambiar
- `structured_content` siempre lista, nunca `None`
- `forms.py` usa `host` (events) y `owner` (rooms) — correcto
- `upload_image` sin `@csrf_exempt`
- `extract_structured_content` en `bitacora/utils.py`
- `urls.py` aún con `<int:pk>` — BIT-6 pendiente
