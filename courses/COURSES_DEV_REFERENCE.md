# Referencia de Desarrollo — App `courses`

> **Actualizado:** 2026-03-19  
> **Audiencia:** Desarrolladores y asistentes IA  
> **Archivos:** 89 | **Vistas:** 2309 líneas | **Modelos:** 565 líneas | **Templates:** 77 | **Endpoints:** 59  
> **Namespace:** `courses` ✅ declarado en `urls.py`  
> **Migración activa:** `0001_initial`

---

## Índice

| Sección | Contenido |
|---------|-----------|
| 1. Resumen | Cuatro subsistemas |
| 2. Modelos | 10 modelos + 3 TextChoices + 2 signals |
| 3. Formularios | CourseForm, ModuleForm, LessonForm, ReviewForm, CategoryForm |
| 4. Vistas | Organizadas por subsistema |
| 5. URLs | Mapa completo con gotchas de routing |
| 6. Convenciones críticas | Tutor vs autor, propietario, slugs |
| 7. Bugs conocidos | Issues activos |
| 8. Deuda técnica | Clasificada por prioridad |

---

## 1. Resumen

`courses` es la app de **aprendizaje y gestión de contenido** de Management360. Cuatro subsistemas conviven en el mismo `views.py`:

**Subsistema 1 — LMS (Learning Management System)**
Cursos con módulos, lecciones, inscripciones, progreso y reseñas. Ciclo completo de aprendizaje: explorar → inscribirse → aprender → completar → reseñar.

**Subsistema 2 — Panel de tutor**
CRUD completo de cursos, módulos y lecciones para usuarios con perfil `cv`. Wizard de creación, analíticas, duplicación, reordenamiento y acciones masivas.

**Subsistema 3 — CMS (Content Management System)**
`ContentBlock` — bloques de contenido reutilizable en 20 tipos (HTML, Bootstrap, Markdown, JSON, video, código, tabla, etc.). Los tutores crean bloques que pueden insertar en lecciones.

**Subsistema 4 — Lecciones independientes**
`Lesson` con `module=None` — lecciones sueltas sin pertenecer a ningún curso. Tienen su propio ciclo de publicación y vista de detalle.

**Dependencia crítica con `cv`:**
- `Course.tutor` requiere que el usuario tenga `Curriculum` (app `cv`)
- Todas las vistas de tutor verifican `hasattr(request.user, 'cv')`
- `models.py` importa `from cv.models import Curriculum` en el nivel de módulo

---

## 2. Modelos

### TextChoices (módulo-level)

```python
CourseLevelChoices:       BEGINNER | INTERMEDIATE | ADVANCED
EnrollmentStatusChoices:  ACTIVE | COMPLETED | DROPPED
LessonTypeChoices:        VIDEO | TEXT | QUIZ | ASSIGNMENT
```

---

### `CourseCategory`

```python
class CourseCategory(models.Model):
    name        # CharField(100)
    description # TextField(blank)
    slug        # SlugField(unique) — autogenerado desde name en save()
```

`save()`: genera slug desde `name` si está vacío. No hay unicidad garantizada si el nombre cambia.

---

### `Course` — modelo principal del LMS

```python
class Course(models.Model):
    title             # CharField(200)
    slug              # SlugField(unique) — autogenerado
    description       # TextField
    short_description # CharField(300, blank)

    tutor             # FK → User (CASCADE, related: 'courses_taught')
                      # limit_choices_to={'cv__isnull': False}
    category          # FK → CourseCategory (SET_NULL, nullable)
    level             # CharField choices CourseLevelChoices
    price             # DecimalField(10,2, ≥0)
    duration_hours    # PositiveIntegerField
    thumbnail         # ImageField(upload_to='courses/thumbnails/')

    is_published      # BooleanField(default=False)
    is_featured       # BooleanField(default=False)
    students_count    # PositiveIntegerField(default=0) — contador denormalizado
    average_rating    # DecimalField(3,2, 0–5)

    created_at        # DateTimeField(auto_now_add)
    updated_at        # DateTimeField(auto_now)
    published_at      # DateTimeField(nullable) — se setea automáticamente al publicar
```

**`save()` override:**
1. Genera slug desde `title` si no existe
2. Si `is_published=True` y `published_at` es None → `published_at = now()`
3. **⚠️ Valida que el tutor tenga `cv`** — lanza `ValueError` si no. Esto significa que **no se puede crear un `Course` en tests sin un `Curriculum` asociado al tutor**.

**Métodos:** `get_tutor_profile()` → `getattr(self.tutor, 'cv', None)`

⚠️ **Propietario: `tutor`** — no es `created_by` ni `owner`. Es una FK específica del dominio.

⚠️ **Sin UUID** — PK es int (AutoField). Rutas del LMS usan `<slug:slug>`, no `<int:pk>`.

---

### `Module`

```python
class Module(models.Model):
    course      # FK → Course (CASCADE, related: 'modules')
    title       # CharField(200)
    description # TextField(blank)
    order       # PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']
```

Sin timestamps ni is_active. Simple contenedor ordenado de lecciones.

---

### `LessonAttachment`

```python
class LessonAttachment(models.Model):
    lesson      # FK → Lesson (CASCADE, related: 'attachments')
    title       # CharField(200)
    file        # FileField(upload_to='courses/lesson_attachments/')
                # validators: extensiones permitidas (pdf, doc, xlsx, mp4, etc.)
    file_type   # CharField(50, blank) — detectado automáticamente
    file_size   # PositiveIntegerField(bytes)
    uploaded_at # DateTimeField(auto_now_add)
    order       # PositiveIntegerField(default=0)
```

`save()`: detecta `file_type` via `get_file_type()` (mapa de extensiones) y captura `file_size`.

⚠️ **Bug en `get_file_size_display()`** — retorna el string de formato `".1f"` literal en lugar de `f"{size:.1f} {unit}"`. Ver B1.

---

### `Lesson` — modelo dual (de curso + independiente)

El modelo más complejo. Funciona en dos modos según el valor de `module`:

| Campo | Con módulo (curso) | Sin módulo (independiente) |
|-------|-------------------|--------------------------|
| `module` | FK → Module | NULL |
| `author` | NULL (usa tutor del curso) | FK → User (requerido) |
| `slug` | blank | Autogenerado (requerido) |
| `is_published` | N/A (usa Course.is_published) | Controla visibilidad propia |
| `is_featured` | N/A | Destacado en biblioteca |

```python
class Lesson(models.Model):
    module       # FK → Module (CASCADE, nullable) — NULL = lección independiente
    author       # FK → User (CASCADE, nullable) — requerido si module=None
    slug         # SlugField(blank) — autogenerado para lecciones independientes
    description  # TextField(blank)
    is_published # BooleanField(default=False)
    is_featured  # BooleanField(default=False)

    title           # CharField(200)
    lesson_type     # CharField choices LessonTypeChoices (default VIDEO)
    content         # TextField(blank) — texto simple
    structured_content # JSONField(default=list) — contenido estructurado con elementos
    video_url       # URLField(blank)
    duration_minutes# PositiveIntegerField(default=0)
    order           # PositiveIntegerField(default=0)
    is_free         # BooleanField(default=False) — preview sin inscripción

    # Quiz
    quiz_questions  # JSONField(default=list) — lista de {question, options, correct_answer}

    # Assignment
    assignment_instructions # TextField(blank)
    assignment_file         # FileField(nullable, .pdf/.docx/.txt)
    assignment_due_date     # DateTimeField(nullable)

    created_at # DateTimeField(auto_now_add)
    updated_at # DateTimeField(auto_now)

    class Meta:
        ordering = ['order']
```

**`save()` override:**
- Si `module is None` y `slug` vacío → genera slug único
- Si `module is None` y `author is None` → lanza `ValueError`

**Propiedad:** `is_standalone` → `self.module is None`

---

### `Enrollment` — Inscripción de estudiante

```python
class Enrollment(models.Model):
    student      # FK → User (CASCADE, related: 'course_enrollments')
    course       # FK → Course (CASCADE, related: 'enrollments')
    status       # CharField choices EnrollmentStatusChoices (default ACTIVE)
    enrolled_at  # DateTimeField(auto_now_add)
    completed_at # DateTimeField(nullable)
    updated_at   # DateTimeField(auto_now)

    class Meta:
        unique_together = ['student', 'course']
```

⚠️ Sin `created_by` — el propietario es `student`.

---

### `Progress` — Progreso de lección

```python
class Progress(models.Model):
    enrollment   # FK → Enrollment (CASCADE, related: 'progress')
    lesson       # FK → Lesson (CASCADE, related: 'progress')
    completed    # BooleanField(default=False)
    completed_at # DateTimeField(nullable)
    score        # DecimalField(5,2, 0–100, nullable)
    attempts     # PositiveIntegerField(default=0)
    max_attempts # PositiveIntegerField(default=3)
    retries_left # PositiveIntegerField(default=3)

    class Meta:
        unique_together = ['enrollment', 'lesson']
```

⚠️ `attempts` y `retries_left` no se sincronizan automáticamente — dependen del código de las vistas para mantenerse consistentes.

---

### `Review` — Reseña de curso

```python
class Review(models.Model):
    student    # FK → User (CASCADE, related: 'course_reviews')
    course     # FK → Course (CASCADE, related: 'reviews')
    rating     # PositiveIntegerField(1–5)
    comment    # TextField(blank)
    created_at # DateTimeField(auto_now_add)
    updated_at # DateTimeField(auto_now)

    class Meta:
        unique_together = ['student', 'course']
```

**`save()` override:** recalcula `course.average_rating` promediando todas las reseñas del curso. ⚠️ Esto puede ser costoso si un curso tiene muchas reseñas — hace `all()` y los itera en Python.

**Signals registrados en el mismo `models.py`:**
- `post_save(Review)` → `update_course_rating` — recalcula promedio
- `post_delete(Review)` → `update_course_rating_on_delete` — recalcula promedio
- `post_save(Enrollment)` → `update_student_count` — incrementa `students_count` en Course

⚠️ La lógica de `average_rating` está **duplicada**: una vez en `Review.save()` y otra vez en los signals. El signal siempre se ejecuta (incluso cuando llama `Review.save()`), causando **doble recálculo** en cada guardado.

---

### `ContentBlock` — CMS integrado

```python
class ContentBlock(models.Model):
    title         # CharField(200)
    slug          # SlugField(unique) — autogenerado con colisión-handling
    description   # TextField(blank)
    content_type  # CharField(20) choices: 20 tipos (html, bootstrap, markdown, json,
                  #   text, image, video, quote, code, list, table, card, alert,
                  #   button, form, divider, icon, progress, badge, timeline)

    # Contenido según tipo
    html_content     # TextField(blank)
    json_content     # JSONField(default=dict, blank)
    markdown_content # TextField(blank)

    author       # FK → User (CASCADE, related: 'content_blocks')
    category     # CharField(100, blank)
    tags         # CharField(500, blank) — separados por comas
    is_public    # BooleanField(default=True)
    is_featured  # BooleanField(default=False)
    usage_count  # PositiveIntegerField(default=0)

    created_at   # DateTimeField(auto_now_add)
    updated_at   # DateTimeField(auto_now)
```

**`save()` override:** genera slug único con sufijo numérico si hay colisión.

**Métodos:**
- `get_content()` → retorna el campo de contenido principal según `content_type`
- `increment_usage()` → `usage_count += 1`, save con `update_fields`
- `get_tags_list()` → lista de strings desde el campo `tags` separado por comas

⚠️ `author` usa FK directa — propietario del CMS es `author`, no `created_by`.

---

## 3. Formularios

### `CourseForm`

Acepta `user=` via `kwargs.pop`. Campos: `title`, `category`, `level`, `description`, `short_description`, `price`, `duration_hours`, `thumbnail`, `is_published`, `is_featured`. Excluye `tutor`, `slug`, `students_count`, `average_rating` — son manejados por las vistas.

**Validaciones custom:** título min 5 chars, descripción min 50, precio ≤ $10k, duración 1–500h, thumbnail ≤ 5MB.

**`clean()`:** valida que el usuario tenga `cv` y que si `is_featured=True` también sea `is_published=True`.

---

### `ModuleForm`

Mínimo: `title`, `description`, `order`. Sin lógica especial.

---

### `LessonForm`

Campo extra `structured_content_json` (Textarea) no en el modelo — recibe JSON serializado del `structured_content`. `save()` override: convierte el JSON a lista Python y asigna a `instance.structured_content`.

Campos: `title`, `lesson_type`, `content`, `structured_content_json`, `video_url`, `duration_minutes`, `order`, `is_free`, `quiz_questions`, `assignment_instructions`, `assignment_file`, `assignment_due_date`.

⚠️ No incluye `author`, `is_published`, `is_featured`, `slug` — se manejan en las vistas correspondientes.

---

### `ReviewForm`

Solo `rating` y `comment`. Sin lógica especial.

---

### `CategoryForm`

`clean_name()` valida duplicados (case insensitive) y aplica `.title()` al nombre. `clean_description()` aplica `.strip()`.

---

## 4. Vistas

### Vistas públicas (sin auth)

| Vista | URL | Descripción |
|-------|-----|-------------|
| `index` | `/courses/` | Landing con stats, featured, recientes, categorías |
| `course_list` | `/courses/courses/` | Lista filtrable (cat, level, search) |
| `course_list` | `/courses/category/<slug>/` | Alias con categoría preseleccionada |
| `course_detail` | `/courses/<slug>/` | Detalle del curso (solo `is_published=True`) |
| `courses_docs` | `/courses/docs/` | Lee `README.md` de la app y lo renderiza |

`course_list` y `course_detail` no requieren auth — cualquier visitante puede ver cursos publicados.

---

### Vistas de estudiante

| Vista | URL | Auth |
|-------|-----|------|
| `enroll` | `/courses/<int:course_id>/enroll/` | ✅ |
| `dashboard` | `/courses/dashboard/` | ✅ |
| `course_learning` | `/courses/<slug>/learn/` | ✅ |
| `course_learning` | `/courses/<slug>/learn/<int:lesson_id>/` | ✅ |
| `mark_lesson_complete` | `/courses/lesson/<int:lesson_id>/complete/` | ✅ POST |
| `add_review` | `/courses/<int:course_id>/review/` | ✅ |

**`course_learning`:** gestiona progreso, navegación prev/next, envíos de quiz y assignments. Delega en helpers `_handle_lesson_submission()`, `_handle_quiz_submission()`, `_handle_assignment_submission()`.

**`mark_lesson_complete`:** doble modo — si `X-Requested-With: XMLHttpRequest` retorna JSON `{status: 'success'}`, si no redirige a la lección.

⚠️ `mark_lesson_complete` asume que la lección pertenece a un módulo (`lesson.module.course`) — falla con `AttributeError` si se llama con una lección independiente (module=None).

---

### Vistas de tutor (requieren `hasattr(user, 'cv')`)

**Cursos:**

| Vista | URL | Descripción |
|-------|-----|-------------|
| `manage_courses` | `/courses/manage/` | Lista cursos propios con stats |
| `create_course` | `/courses/manage/create/` | Form simple |
| `create_course_wizard` | `/courses/manage/create/wizard/` | 2 pasos: curso + primer módulo |
| `edit_course` | `/courses/manage/<slug>/edit/` | Editar |
| `delete_course` | `/courses/manage/<slug>/delete/` | Con validación de dependencias |
| `course_analytics` | `/courses/manage/<slug>/analytics/` | Progreso de estudiantes |

**Módulos:**

| Vista | URL | Descripción |
|-------|-----|-------------|
| `manage_content` | `/courses/manage/<slug>/content/` | Vista principal de módulos + lecciones |
| `create_module` | `…/modules/create/` | Crear |
| `edit_module` | `…/modules/<id>/edit/` | Editar |
| `delete_module` | `…/modules/<id>/delete/` | Eliminar |
| `duplicate_module` | `…/modules/<id>/duplicate/` | Copia con lecciones |
| `module_statistics` | `…/modules/<id>/statistics/` | Tasa de compleción por lección |
| `module_progress` | `…/modules/<id>/progress/` | Progreso por estudiante |
| `bulk_module_actions` | `…/modules/bulk-actions/` | Eliminar/duplicar seleccionados |
| `reorder_modules` | `…/modules/reorder/` | AJAX — reordena por array de IDs |
| `modules_overview` | `/courses/modules/overview/` | Vista global de módulos del tutor |

**Lecciones:**

| Vista | URL | Descripción |
|-------|-----|-------------|
| `create_lesson` | `…/<module_id>/lessons/create/` | Soporta AJAX (X-Requested-With) |
| `edit_lesson` | `…/<module_id>/lessons/<lesson_id>/edit/` | Ídem |
| `preview_lesson` | `…/<module_id>/lessons/<lesson_id>/preview/` | Solo lectura para tutor |
| `delete_lesson` | `…/<module_id>/lessons/<lesson_id>/delete/` | — |

**Categorías (requieren `is_staff`):**

| Vista | URL |
|-------|-----|
| `manage_categories` | `/courses/manage/categories/` |
| `create_category` | `/courses/manage/categories/create/` (AJAX support) |
| `quick_create_category` | `/courses/manage/categories/quick-create/` |
| `edit_category` | `/courses/manage/categories/<id>/edit/` |
| `delete_category` | `/courses/manage/categories/<id>/delete/` |

**Admin (requieren `is_staff`):**

| Vista | URL |
|-------|-----|
| `admin_dashboard` | `/courses/admin/` |
| `admin_users` | `/courses/admin/users/` (paginado, 20/página) |
| `admin_user_detail` | `/courses/admin/users/<id>/` |
| `edit_user` | `/courses/admin/users/<id>/edit/` |

⚠️ `edit_user` modifica `first_name`, `last_name`, `email`, `is_active` directamente desde `request.POST` sin usar un Django Form — sin CSRF implícito en el form (depende del template), sin validación de email único, sin protección contra campos extra.

---

### Vistas del CMS (ContentBlock)

Todas `@login_required` + verifican `hasattr(user, 'cv')` (excepto toggle y preview).

| Vista | URL | Descripción |
|-------|-----|-------------|
| `content_manager` | `/courses/content/` | Panel principal |
| `create_content_block` | `/courses/content/create/<str:block_type>/` | Crea según tipo (20 tipos) |
| `create_content_block` | `/courses/content/create/` | Alias con type='html' |
| `edit_content_block` | `/courses/content/<slug>/edit/` | Edita — mismo switch de 20 tipos |
| `delete_content_block` | `/courses/content/<slug>/delete/` | Solo author puede borrar |
| `duplicate_content_block` | `/courses/content/<slug>/duplicate/` | Copia privada |
| `preview_content_block` | `/courses/content/<slug>/preview/` | Vista previa |
| `my_content_blocks` | `/courses/content/my-blocks/` | Bloques propios con filtros |
| `public_content_blocks` | `/courses/content/public/` | Biblioteca pública |
| `featured_content_blocks` | `/courses/content/featured/` | Destacados |
| `toggle_block_featured` | `/courses/content/<slug>/toggle-featured/` | POST → JSON |
| `toggle_block_public` | `/courses/content/<slug>/toggle-public/` | POST → JSON |

`create_content_block` y `edit_content_block` tienen un switch de 20 ramas `elif` para manejar cada tipo de contenido. El código es idéntico en ambas vistas — **alta deuda de duplicación**.

---

### Vistas de lecciones independientes

| Vista | URL | Auth |
|-------|-----|------|
| `standalone_lessons_list` | `/courses/content/` | ✅ — ⚠️ URL duplicada (ver B2) |
| `my_standalone_lessons` | `/courses/lessons/my-lessons/` | ✅ + cv |
| `create_standalone_lesson` | `/courses/lessons/create/` | ✅ + cv |
| `standalone_lesson_detail` | `/courses/lessons/<slug>/` | ✅ |
| `edit_standalone_lesson` | `/courses/lessons/<slug>/edit/` | ✅ |
| `delete_standalone_lesson` | `/courses/lessons/<slug>/delete/` | ✅ |
| `toggle_lesson_published` | `/courses/lessons/<slug>/toggle-published/` | ✅ POST → JSON |

---

## 5. URLs

> ✅ `app_name = 'courses'` declarado.

**⚠️ URL duplicada crítica:** dos patterns tienen el mismo path `'content/'`:

```python
path('content/', views.content_manager, name='content_manager'),
# ... 10 URLs más ...
path('content/', views.standalone_lessons_list, name='standalone_lessons_list'),
```

Django usará siempre `content_manager` (primer match). `standalone_lessons_list` es **inaccesible** como URL directa. Ver B2.

**⚠️ Orden de URLs sensible:** `manage/categories/` debe declararse antes de `manage/<slug:slug>/edit/` para no capturarse como slug. El orden actual lo maneja correctamente.

**⚠️ Colisión potencial de slugs:** `<slug:slug>/` al final del urlconf puede capturar `courses/`, `docs/`, `lessons/` si no están declaradas antes. El orden actual es correcto pero frágil — agregar nueva URL con slug puede romper el routing.

---

## 6. Convenciones Críticas

### Propietario varía por modelo

```python
# CORRECTO por modelo:
course  = get_object_or_404(Course, slug=slug, tutor=request.user)
lesson  = get_object_or_404(Lesson, slug=slug, author=request.user, module__isnull=True)
block   = get_object_or_404(ContentBlock, slug=slug)
# ContentBlock: verificar block.author == request.user por separado
enrollment = get_object_or_404(Enrollment, student=request.user, course=course)
```

| Modelo | Propietario | Campo |
|--------|-------------|-------|
| `Course` | Tutor | `tutor` |
| `Lesson` (independiente) | Autor | `author` |
| `ContentBlock` | Autor | `author` |
| `Enrollment` | Estudiante | `student` |
| `Review` | Estudiante | `student` |

### Acceso a funciones de tutor — verificar `cv` primero

```python
# CORRECTO — todas las vistas de tutor lo hacen así:
if not hasattr(request.user, 'cv'):
    messages.error(request, 'Necesitas un perfil de tutor')
    return redirect('cv:detail')
```

Si se omite, `Course.save()` lanzará `ValueError` al intentar crear el curso.

### Slugs — Course usa `<slug:slug>`, NO `<int:pk>`

```python
# CORRECTO
course = get_object_or_404(Course, slug=slug)
{% url 'courses:course_detail' slug=course.slug %}

# INCORRECTO — no existe pk UUID ni int en las URLs de Course
```

`enroll` y `add_review` sí usan `<int:course_id>` — son los únicos endpoints con int de Course.

### Lección de curso vs lección independiente

```python
# Verificar si es independiente:
if lesson.is_standalone:  # == lesson.module is None
    # usar lesson.author
else:
    # usar lesson.module.course.tutor
```

### `mark_lesson_complete` solo funciona para lecciones de curso

```python
# Falla si lesson.module es None:
enrollment = get_object_or_404(
    Enrollment,
    student=request.user,
    course=lesson.module.course,  # AttributeError si module=None
    ...
)
```

No llamar con lecciones independientes.

---

## 7. Bugs Conocidos

| # | Estado | Descripción |
|---|--------|-------------|
| B1 | ⬜ activo | `LessonAttachment.get_file_size_display()` retorna el string literal `".1f"` en lugar de `f"{size:.1f} {unit}"` — bug de sintaxis f-string |
| B2 | ⬜ activo | `path('content/', views.standalone_lessons_list, ...)` duplica el path de `content_manager` — `standalone_lessons_list` es inaccesible directamente |
| B3 | ⬜ activo | `Review.save()` y signal `update_course_rating` recalculan `average_rating` dos veces por cada guardado de reseña — doble query innecesaria |
| B4 | ⬜ activo | `mark_lesson_complete` llama `lesson.module.course` sin verificar que `lesson.module` no sea None — falla con lecciones independientes |
| B5 | ⬜ activo | `edit_user` procesa POST sin Django Form — sin validación de email, posible email duplicado, sin CSRF garantizado desde el código |
| B6 | ⬜ activo | `course_list` calcula `total_students` con un loop Python sobre todos los cursos — potencial N+1 sin paginación |
| B7 | ⬜ activo | Global bug #8 — editor de lecciones lento con muchos ContentBlocks (`available_content_blocks` sin límite de resultados) |
| B8 | ⬜ activo | `create_content_block` y `edit_content_block` tienen switch de 20 ramas `elif` duplicado — si se añade un nuevo tipo hay que actualizar ambas vistas |
| B9 | ⬜ activo | `modules_overview` calcula `total_lessons` con loops Python anidados sobre todos los cursos/módulos — N+N+1 sin `annotate` |
| B10 | ⬜ activo | `Course.save()` lanza `ValueError` (no `ValidationError`) al crear curso sin CV — los formularios Django no capturan `ValueError` automáticamente |

---

## 8. Deuda Técnica

**Alta prioridad:**
- **Fix B1** — `get_file_size_display()` retorna string literal, no formateado
- **Fix B2** — registrar `standalone_lessons_list` en una URL diferente a `content/`
- **Fix B4** — verificar `lesson.module` antes de acceder en `mark_lesson_complete`
- **Extraer switch de tipos** de `create_content_block` y `edit_content_block` a un helper compartido `_build_block_content(block, block_type, request.POST)` — elimina 200+ líneas duplicadas

**Media prioridad:**
- **Eliminar duplicación** en `Review.save()` — si hay signal, el `save()` no necesita recalcular también (o viceversa)
- **Fix `edit_user`** — usar un Django Form con validación apropiada
- **Paginación** en `course_list` y `standalone_lessons_list` — sin límite en datasets grandes
- **Reemplazar loops Python** por `annotate` en `course_list`, `modules_overview`, `dashboard`
- **`students_count` en `Course`** es un campo denormalizado que puede desincronizarse — considerar calcularlo con `annotate` en lugar de mantener un campo separado

**Baja prioridad:**
- `Course.save()` debería lanzar `ValidationError` en lugar de `ValueError` para integrar correctamente con Django Forms
- Agregar `created_by` / UUID en modelos si se requiere alinear con convenciones del proyecto (actualmente todos usan PKs int)
- Documentar `course_filters.py` y `lesson_tags.py` — no se revisaron en esta sesión
- `test_template.html` en la carpeta de templates — archivo de prueba que debería eliminarse
