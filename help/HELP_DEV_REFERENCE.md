# Referencia de Desarrollo — App `help`

> **Actualizado:** 2026-03-20 (Sesión Analista Doc — lote 4)
> **Audiencia:** Desarrolladores y Claude
> **Stats:** 15 archivos · models.py 421L · views.py 424L · urls.py 31L · setup_help.py 1115L
> **Bugs registrados:** #100–#110

---

## Índice

| # | Sección | Descripción |
|---|---------|-------------|
| 1 | Resumen | Qué hace la app y sus pilares |
| 2 | Modelos | 7 modelos con campos y relaciones |
| 3 | Vistas | 10 vistas organizadas por módulo |
| 4 | URLs | Mapa de endpoints |
| 5 | Integración con `courses` | Patrón de contenido referenciado |
| 6 | Convenciones críticas | Gotchas y excepciones |
| 7 | Bugs conocidos | #100–#110 |
| 8 | Deuda técnica | Clasificada por prioridad |

---

## 1. Resumen

`help` es el **Centro de Ayuda** de Management360. Es un CMS de documentación interna que organiza artículos, FAQs, tutoriales en video y guías de inicio rápido.

Su característica más importante es la **integración bidireccional con `courses`**: los artículos y tutoriales pueden referenciar objetos de `courses` (`Course`, `Lesson`, `ContentBlock`) para reutilizar contenido sin duplicarlo. `HelpArticle.get_content()` resuelve esta jerarquía en tiempo de render.

**Pilares:**
- CMS de documentación con categorías, artículos, FAQs y videos
- Reutilización de contenido de `courses` por referencia
- Sistema de feedback por artículo (rating + comentario)
- Búsqueda full-text con log analítico (`HelpSearchLog`)
- Guías de inicio rápido segmentadas por audiencia
- Acceso público + artículos con `requires_auth=True` opcionales

**Sin modelos propios de usuario** — el centro de ayuda es de lectura pública por defecto; solo `submit_feedback` requiere autenticación.

---

## 2. Modelos

### `HelpCategory`
Agrupa artículos, FAQs y videos temáticamente.

| Campo | Tipo | Notas |
|-------|------|-------|
| `id` | AutoField (int) | ⚠️ Sin UUID — excepción al estándar |
| `name` | CharField(100) | unique |
| `slug` | SlugField | unique — usado en URLs |
| `description` | TextField | blank=True |
| `icon` | CharField(50) | Clase Bootstrap Icons, ej: `bi-question-circle` |
| `color` | CharField(7) | Hex `#RRGGBB`, default `#007bff` |
| `order` | PositiveIntegerField | Ordenación manual |
| `is_active` | BooleanField | Soft delete |
| `created_at` / `updated_at` | DateTimeField | auto_now_add / auto_now |

**Ordering:** `['order', 'name']`
**Método clave:** `get_active_articles()` → `self.articles.filter(is_active=True)`
**Related names:** `articles`, `faqs`, `video_tutorials`

---

### `HelpArticle`
Artículo de ayuda. Puede tener contenido propio (`content`) o delegar a un objeto de `courses`.

| Campo | Tipo | Notas |
|-------|------|-------|
| `id` | AutoField (int) | ⚠️ Sin UUID |
| `title` | CharField(200) | |
| `slug` | SlugField | unique |
| `content` | TextField | HTML/Markdown — puede estar vacío si usa referencia |
| `excerpt` | TextField | Resumen breve |
| `category` | FK → HelpCategory | CASCADE, related_name=`articles` |
| `author` | FK → User | SET_NULL, null=True — ⚠️ NO `created_by` |
| `referenced_course` | FK → Course | SET_NULL, null=True, optional |
| `referenced_lesson` | FK → Lesson | SET_NULL, null=True, optional |
| `referenced_content_block` | FK → ContentBlock | SET_NULL, null=True, optional |
| `tags` | CharField(500) | Coma-separado — parsear con `get_tags_list()` |
| `difficulty` | CharField choices | `beginner`/`intermediate`/`advanced` |
| `is_active` | BooleanField | Soft delete / publicado |
| `is_featured` | BooleanField | Aparece en portada |
| `requires_auth` | BooleanField | Si True, redirige a login si anónimo |
| `view_count` | PositiveIntegerField | Incrementado con `increment_view_count()` |
| `helpful_count` | PositiveIntegerField | Votos positivos de feedback |
| `not_helpful_count` | PositiveIntegerField | Votos negativos de feedback |
| `meta_title` | CharField(200) | SEO |
| `meta_description` | TextField | SEO |
| `published_at` | DateTimeField | null=True — se auto-asigna en `save()` al activar |
| `created_at` / `updated_at` | DateTimeField | |

**Ordering:** `['-is_featured', '-published_at', '-created_at']`

**Métodos clave:**
- `get_content()` → resuelve jerarquía: propio > curso > lección > content_block
- `_get_course_content()`, `_get_lesson_content()`, `_get_content_block_content()` → generan HTML
- `increment_view_count()` → `update_fields=['view_count']` (eficiente)
- `get_helpful_percentage()` → int (0–100)
- `get_related_articles(limit=5)` → filtra por categoría (⚠️ bug #106)
- `get_tags_list()` → lista de strings

**`save()` override:** Auto-asigna `published_at = timezone.now()` si `is_active=True` y `published_at` es None.

**Solo uno de los tres FKs de referencia debería estar poblado** a la vez. No hay validación que lo enforce.

---

### `FAQ`
Pregunta frecuente. Simple y sin contenido referenciado.

| Campo | Tipo | Notas |
|-------|------|-------|
| `id` | AutoField (int) | ⚠️ Sin UUID |
| `question` | CharField(300) | |
| `answer` | TextField | HTML |
| `category` | FK → HelpCategory | CASCADE, related_name=`faqs` |
| `order` | PositiveIntegerField | Ordenación manual |
| `is_active` | BooleanField | |
| `view_count` | PositiveIntegerField | No hay endpoint para incrementarlo |
| `helpful_count` | PositiveIntegerField | No hay endpoint para incrementarlo |
| `created_at` / `updated_at` | DateTimeField | |

**Ordering:** `['order', 'question']`
> ⚠️ `view_count` y `helpful_count` de FAQ no se incrementan desde ninguna vista — son campos muertos actualmente.

---

### `HelpSearchLog`
Log analítico de búsquedas. No es propietario — es telemetría.

| Campo | Tipo | Notas |
|-------|------|-------|
| `id` | AutoField (int) | |
| `query` | CharField(200) | Término buscado |
| `user` | FK → User | SET_NULL, null=True — anónimos se logean con None |
| `ip_address` | GenericIPAddressField | null=True |
| `user_agent` | TextField | |
| `results_count` | PositiveIntegerField | Actualizado post-búsqueda |
| `has_results` | BooleanField | |
| `created_at` | DateTimeField | Sin `updated_at` |

**Ordering:** `['-created_at']`
> No tiene `updated_at` — el log se crea primero y luego se actualiza con stats, lo que genera un race condition (bug #110).

---

### `HelpFeedback`
Feedback de usuario sobre un artículo.

| Campo | Tipo | Notas |
|-------|------|-------|
| `id` | AutoField (int) | |
| `article` | FK → HelpArticle | CASCADE, related_name=`feedback` |
| `user` | FK → User | SET_NULL, null=True — ⚠️ NO `created_by` |
| `ip_address` | GenericIPAddressField | null=True |
| `was_helpful` | BooleanField | Voto binario |
| `rating` | PositiveIntegerField choices | 1–5 estrellas |
| `comment` | TextField | blank=True |
| `improvement_suggestions` | TextField | blank=True |
| `created_at` | DateTimeField | Sin `updated_at` |

**Ordering:** `['-created_at']`
> Un usuario puede enviar múltiples feedbacks para el mismo artículo — no hay unicidad por (article, user).

---

### `VideoTutorial`
Tutorial en video. Puede referenciar una `Lesson` con video de `courses`.

| Campo | Tipo | Notas |
|-------|------|-------|
| `id` | AutoField (int) | ⚠️ Sin UUID |
| `title` | CharField(200) | |
| `slug` | SlugField | unique |
| `description` | TextField | |
| `video_url` | URLField | YouTube/Vimeo — puede estar vacío si usa `referenced_lesson` |
| `thumbnail_url` | URLField | blank=True |
| `category` | FK → HelpCategory | CASCADE, related_name=`video_tutorials` |
| `author` | FK → User | SET_NULL, null=True — ⚠️ NO `created_by` |
| `referenced_lesson` | FK → Lesson | SET_NULL, null=True |
| `duration` | DurationField | null=True |
| `difficulty` | CharField choices | `beginner`/`intermediate`/`advanced` |
| `tags` | CharField(500) | Coma-separado |
| `is_active` / `is_featured` | BooleanField | |
| `view_count` / `like_count` | PositiveIntegerField | No hay endpoint para incrementarlos |
| `created_at` / `updated_at` | DateTimeField | |

**Ordering:** `['-is_featured', '-created_at']`
**Método clave:** `get_embed_url()` → convierte URLs de YouTube (`watch?v=` y `youtu.be/`) a formato embed. Si `video_url` está vacío, usa `referenced_lesson.video_url`.

---

### `QuickStartGuide`
Guía de inicio rápido para nuevos usuarios. Sin propietario, sin referencias a `courses`.

| Campo | Tipo | Notas |
|-------|------|-------|
| `id` | AutoField (int) | ⚠️ Sin UUID |
| `title` | CharField(200) | |
| `slug` | SlugField | unique |
| `description` | TextField | |
| `content` | TextField | HTML/Markdown |
| `estimated_time` | PositiveIntegerField | Minutos, default=5 |
| `target_audience` | CharField choices | `new_users`/`intermediate`/`power_users`/`administrators` |
| `prerequisites` | TextField | blank=True |
| `order` | PositiveIntegerField | |
| `is_active` / `is_featured` | BooleanField | |
| `completion_count` | PositiveIntegerField | Incrementado con `mark_completed()` |
| `created_at` / `updated_at` | DateTimeField | |

**Ordering:** `['order', 'title']`
**Método:** `mark_completed(user=None)` → incrementa `completion_count`. El parámetro `user` es ignorado — `UserGuideProgress` no implementado (bug #105).

---

## 3. Vistas

Todas son function-based views (FBVs). No hay CBVs ni HTMX en esta app.

### Vistas públicas (sin autenticación requerida)

| Vista | URL | Descripción |
|-------|-----|-------------|
| `help_home` | `/help/` | Portada del centro de ayuda con stats, destacados y FAQs populares |
| `category_list` | `/help/categories/` | Lista todas las categorías con `annotate` de counts |
| `category_detail` | `/help/categories/<slug>/` | Artículos + FAQs + videos de una categoría. Paginación: 12 artículos/página |
| `article_detail` | `/help/articles/<slug>/` | Artículo individual. Maneja `requires_auth` y llama `increment_view_count()` |
| `faq_list` | `/help/faq/` | FAQs con filtro por categoría y búsqueda `?q=`. Paginación: 20/página |
| `video_tutorials` | `/help/videos/` | Videos con filtro por categoría y dificultad. Paginación: 12/página |
| `quick_start` | `/help/quick-start/` | Guías filtradas por `?audience=` |
| `search_help` | `/help/search/` | Búsqueda cross-model en artículos+FAQs+videos+guías. Crea `HelpSearchLog` |

### Vistas autenticadas / con restricción

| Vista | URL | Auth | Descripción |
|-------|-----|------|-------------|
| `submit_feedback` | `/help/articles/<slug>/feedback/` | `@login_required` | POST — crea `HelpFeedback` y actualiza contadores del artículo |
| `article_feedback_stats` | `/help/articles/<slug>/feedback-stats/` | `is_staff` check manual | GET — JSON con stats de feedback para admins |

> ⚠️ `article_feedback_stats` no tiene `@login_required` — solo verifica `request.user.is_staff` manualmente. Un usuario anónimo recibe 403, pero el endpoint es accesible sin sesión (bug #102).

---

## 4. URLs

**Namespace:** `help` ✅ declarado en `urls.py`
**Prefijo en `panel/urls.py`:** `path('help/', include('help.urls', namespace='help'))`

| Name | Método | URL completa |
|------|--------|-------------|
| `help:help_home` | GET | `/help/` |
| `help:category_list` | GET | `/help/categories/` |
| `help:category_detail` | GET | `/help/categories/<slug>/` |
| `help:article_detail` | GET | `/help/articles/<slug>/` |
| `help:faq_list` | GET | `/help/faq/` |
| `help:video_tutorials` | GET | `/help/videos/` |
| `help:quick_start` | GET | `/help/quick-start/` |
| `help:search` | GET | `/help/search/?q=<query>` |
| `help:submit_feedback` | POST | `/help/articles/<slug>/feedback/` |
| `help:article_feedback_stats` | GET | `/help/articles/<slug>/feedback-stats/` |

---

## 5. Integración con `courses`

Esta app tiene **dependencia directa con `courses`** a nivel de módulo:

```python
# models.py línea 6
from courses.models import Course, Lesson, ContentBlock, CourseCategory
```

⚠️ **Si `courses` falla al cargar, `help` tampoco carga** (bug #101). `CourseCategory` se importa pero no se usa en ningún modelo — import muerto.

### Patrón de contenido referenciado

`HelpArticle` y `VideoTutorial` pueden apuntar a objetos de `courses` para reutilizar contenido:

```
HelpArticle
├── content (propio) ← si está relleno, se usa este
├── referenced_course → Course.title/description/modules
├── referenced_lesson → Lesson.title/content/structured_content
└── referenced_content_block → ContentBlock.title/get_content()

VideoTutorial
├── video_url (propio) ← si está relleno, se usa este
└── referenced_lesson.video_url ← fallback
```

`get_content()` resuelve la jerarquía: primero busca contenido propio, luego delega al objeto referenciado. Si el objeto referenciado fue eliminado (FK SET_NULL), el artículo queda sin contenido — no hay fallback de texto vacío explícito (retorna `""`).

---

## 6. Convenciones críticas

### Propietario — excepción al estándar

| Modelo | Campo propietario | Nota |
|--------|-------------------|------|
| `HelpArticle` | `author` | ⚠️ NO `created_by` |
| `VideoTutorial` | `author` | ⚠️ NO `created_by` |
| `HelpFeedback` | `user` | ⚠️ NO `created_by` — es el autor del feedback |
| `HelpSearchLog` | `user` | Telemetría — no es propietario real |
| `HelpCategory`, `FAQ`, `QuickStartGuide` | — | Sin propietario explícito |

### PKs — sin UUID en ningún modelo

Todos los modelos usan `AutoField` (int implícito). Coherente internamente pero no cumple el estándar del proyecto.

### Templates faltantes — crítico

El CONTEXT.md reporta solo 5 templates en `help/templates/help/`:
- `help_home.html` ✅
- `category_list.html` ✅
- `category_detail.html` ✅
- `article_detail.html` ✅
- `search_results.html` ✅

**Faltan (TemplateDoesNotExist en runtime):**
- `faq_list.html` ❌
- `video_tutorials.html` ❌
- `quick_start.html` ❌

> Tres de los 10 endpoints crashean al ser visitados (bug #107).

### `article.save()` sin `update_fields` en feedback

`submit_feedback` llama `article.save()` después de modificar `helpful_count` o `not_helpful_count`. Sin `update_fields`, esto escribe **todos** los campos del artículo, incluyendo `view_count`, timestamps, etc. (bug #104).

---

## 7. Bugs conocidos

| # | Impacto | Descripción |
|---|---------|-------------|
| **100** | 🟡 | `get_user_model()` a nivel de módulo — igual que bug #89 en `board` |
| **101** | 🔴 | `from courses.models import ...` a nivel de módulo — `CourseCategory` importado sin uso; si `courses` falla, `help` no carga |
| **102** | 🟠 | `article_feedback_stats` sin `@login_required` — verifica `is_staff` manualmente pero es accesible por anónimos |
| **103** | 🟡 | `search_help` evalúa `count()` dos veces sobre los mismos querysets — doble hit a DB |
| **104** | 🟠 | `submit_feedback` llama `article.save()` sin `update_fields` — sobreescribe todos los campos |
| **105** | 🟡 | `QuickStartGuide.mark_completed(user)` — `user` ignorado, `UserGuideProgress` no implementado (stub) |
| **106** | 🟡 | `HelpArticle.get_related_articles()` filtra solo por categoría — ignora `tags` a pesar de la docstring |
| **107** | 🔴 | 3 templates faltantes: `faq_list.html`, `video_tutorials.html`, `quick_start.html` — **TemplateDoesNotExist** en runtime |
| **108** | 🟡 | Sin UUID PK en ningún modelo — todos AutoField int |
| **109** | 🟡 | `author`/`user` en vez de `created_by` — excepción al estándar del proyecto |
| **110** | 🟠 | `search_help` — busca el log por `query` text para actualizar stats — race condition si hay búsquedas simultáneas del mismo término |

---

## 8. Deuda técnica

### Alta prioridad

- **Bug #107** — Crear los 3 templates faltantes. Sin esto, `faq_list`, `video_tutorials` y `quick_start` son endpoints no funcionales. Los templates de `category_detail.html` pueden servir de base.
- **Bug #101** — Mover import de `courses.models` a imports lazy dentro de los métodos `_get_*_content()` para romper la dependencia de carga.
- **Bug #104** — Cambiar `article.save()` a `article.save(update_fields=['helpful_count'])` / `['not_helpful_count']`.

### Media prioridad

- **Bug #102** — Agregar `@login_required` a `article_feedback_stats`.
- **Bug #110** — Guardar la instancia de `HelpSearchLog` en una variable y actualizarla directamente en lugar de hacer `HelpSearchLog.objects.filter(query=query).last()`.
- **Bug #103** — Guardar los counts en variables antes de construir el contexto para evitar doble evaluación.
- **`FAQ.view_count` / `FAQ.helpful_count`** — Implementar endpoints para incrementarlos o eliminar los campos.

### Baja prioridad

- **Bug #105** — Implementar `UserGuideProgress` o eliminar el parámetro `user` de `mark_completed()`.
- **Bug #106** — Mejorar `get_related_articles()` para considerar tags comunes.
- **Bug #108** — Migrar a UUID PKs (breaking change — requiere migración y actualización de URLs).
- **Bug #100** — Mover `get_user_model()` dentro de los métodos o usar `settings.AUTH_USER_MODEL` en FKs.
- **`HelpFeedback`** — Agregar `unique_together = ('article', 'user')` para evitar feedback duplicado por usuario.
- **`setup_help.py`** — 1115 líneas de seed data. Documentar qué categorías/artículos crea para saber qué contenido de demo esperar.
