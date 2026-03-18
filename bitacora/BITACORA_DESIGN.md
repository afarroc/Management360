# Bitácora — Diseño, Roadmap y Estado de Implementación

> **Última actualización:** 2026-03-17
> **App:** `bitacora` | **Namespace:** `bitacora`
> **Propósito:** Diario personal GTD — registro libre de entradas con contenido enriquecido
> **Archivos:** 16 | **Modelos:** 2 | **Endpoints:** 9

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
| `id` | UUIDField PK | Identificador público |
| `titulo` | CharField(200) | Título de la entrada |
| `contenido` | TextField | Cuerpo HTML (editado con TinyMCE) |
| `created_by` | FK → User | Autor |
| `categoria` | CharField choices | CategoriaChoices (8 opciones) |
| `mood` | CharField choices | MoodChoices (5 opciones) |
| `is_active` | BooleanField | Soft delete |
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
| `id` | UUIDField PK | Identificador público |
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

---

## Funcionalidades Implementadas

### ✅ CRUD de entradas
- Crear, leer, actualizar, eliminar entradas con TinyMCE
- Filtros en lista: texto libre (q), categoría, período (hoy/semana/mes), visibilidad
- Paginación: 10 entradas por página
- Ordenamiento: `-fecha_creacion`

### ✅ Dashboard con estadísticas
- Total de entradas, entradas del mes, % públicas
- Distribución por categoría
- Entradas recientes (últimas 10)
- Integración GTD: InboxItems pendientes (últimos 5)
- Tareas activas del usuario (últimas 3)

### ✅ Contenido estructurado (integración con courses)
- Biblioteca de `ContentBlock` de courses accesible desde bitácora
- Inserción de bloques en `structured_content` (JSONField)
- Renderizado de bloques en `entry_detail`
- Extracción de bloques embebidos en HTML de TinyMCE (`StructuredContentMixin`)

### ✅ Upload de imágenes para TinyMCE
- Endpoint `/upload-image/` — valida tipo (jpg/png/gif/webp) y tamaño (máx 5MB)
- Genera nombre único con `get_random_string(32)`
- Usa `default_storage` (compatible con RemoteMediaStorage en dev)

### ✅ Adjuntos
- Modelo `BitacoraAttachment` para archivos adicionales
- Tipos: imagen, audio, video, documento

---

## Estado de Implementación

| Componente | Estado | Deuda técnica |
|------------|--------|---------------|
| `models.py` | 🔵 Refactorizado | Migración 0003 pendiente de aplicar |
| `views.py` | 🟠 Bugs conocidos | 5 issues identificados (ver sección Bugs) |
| `forms.py` | ✅ OK | Sin deuda |
| `urls.py` | 🟡 Menor | Ambigüedad dashboard vs list |
| `bitacora_tags.py` | ⬜ No revisado | Render HTML a validar |
| Templates | ⬜ No revisados | 6 templates pendientes de auditoría |
| Tests | ⬜ Sin tests | — |
| Documentación | 🔵 En progreso | Este documento |

---

## Roadmap

### Fase 1 — Estabilización (Sprint 7) 🔵
> Objetivo: dejar la app libre de deuda técnica antes de nuevas features

| Tarea | Prioridad | Estado |
|-------|-----------|--------|
| BIT-1: Refactor `models.py` — convenciones + limpiar render HTML | 🔴 | ✅ |
| BIT-2: Refactor `views.py` — 5 bugs/issues | 🔴 | ⬜ |
| BIT-3: Migración 0003 — UUID pk, `created_by`, `is_active` | 🔴 | ⬜ |
| BIT-4: Revisar `bitacora_tags.py` — consolidar render HTML movido | 🟠 | ⬜ |
| BIT-5: Auditoría de templates (6 archivos) | 🟡 | ⬜ |
| BIT-6: Fix ambigüedad `dashboard` / `list` en urls.py | 🟡 | ⬜ |

### Fase 2 — Features GTD (Sprint 8+) ⬜

| Tarea | Prioridad |
|-------|-----------|
| BIT-10: Vista de mapa geográfico (latitud/longitud) | 🟡 |
| BIT-11: Exportación de entrada a PDF | 🟠 |
| BIT-12: Búsqueda full-text en `contenido` | 🟠 |
| BIT-13: Timeline view (entradas por fecha en línea de tiempo) | 🟡 |
| BIT-14: Estadísticas de mood por período | 🟡 |
| BIT-15: Entradas relacionadas (mismos tags / mismo proyecto) | 🟡 |
| BIT-16: Tests unitarios (models + views) | 🟠 |

---

## Decisiones de Diseño

### ¿Por qué JSONField para `structured_content`?
Los bloques insertados desde `courses.ContentBlock` son snapshots — se guardan
como copia inmutable en la entrada para que cambios posteriores en el ContentBlock
original no afecten la bitácora. El JSONField permite almacenarlos sin FK adicionales.

### ¿Por qué reutilizar `events.Tag` y no crear tags propios?
Reducir fragmentación. El usuario ya categoriza sus proyectos y tareas con tags de
`events` — reutilizarlos permite cruzar búsquedas ("entradas de bitácora relacionadas
con el proyecto X via tags comunes").

### ¿Por qué TinyMCE y no un editor de bloques nativo?
El editor de bloques de `courses` es potente pero orientado a contenido estructurado
de cursos. Para una bitácora personal, el texto libre con formato HTML es más natural
y flexible. Los `ContentBlock` de courses se insertan como complemento, no como
unidad principal.

### Render HTML — decisión de arquitectura
Originalmente (~350 líneas) el render de bloques vivía en `models.py` (anti-patrón).
Fue movido a `templatetags/bitacora_tags.py` en el refactor de 2026-03-17.
**Los modelos no deben generar HTML** — riesgo XSS + violación de responsabilidad única.

---

## Notas para Claude

- El campo de autor se llama `created_by` (renombrado desde `autor` en refactor 0003)
- `fecha_creacion` / `fecha_actualizacion` se mantienen en español — convención interna
- `structured_content` es una lista de dicts, nunca `None` (default=list)
- Los filtros en `forms.py` usan `host` para events y `owner` para rooms — correcto
- La vista `BitacoraListView` sirve dos templates: `dashboard.html` (ruta `''`) y `entry_list.html` (ruta `list/`)
- `upload_image` NO debe tener `@csrf_exempt`
