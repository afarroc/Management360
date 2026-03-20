# Diseño y Roadmap — App `courses`

> **Actualizado:** 2026-03-19  
> **Estado:** Funcional — documentación generada esta sesión  
> **Sprint actual:** 7 completado | Próximo: Sprint 8

---

## Visión General

`courses` es la app de **aprendizaje y gestión de contenido** de Management360. Integra cuatro sistemas en un solo package: un LMS completo, un panel de gestión para tutores, un CMS de bloques reutilizables y una biblioteca de lecciones independientes.

```
┌────────────────────────────────────────────────────────────────┐
│                        APP COURSES                             │
│                                                                │
│  ┌─────────────────────┐  ┌─────────────────────────────────┐  │
│  │  LMS (estudiantes)  │  │  PANEL TUTOR                    │  │
│  │                     │  │                                 │  │
│  │  Catálogo de cursos │  │  CRUD cursos/módulos/lecciones  │  │
│  │  Inscripción        │  │  Analíticas de estudiantes      │  │
│  │  Aprendizaje        │  │  Wizard de creación             │  │
│  │  Progreso + Quiz    │  │  Duplicación + Reordenamiento   │  │
│  │  Reseñas            │  │  Acciones masivas               │  │
│  └─────────────────────┘  └─────────────────────────────────┘  │
│                                                                │
│  ┌─────────────────────┐  ┌─────────────────────────────────┐  │
│  │  CMS (ContentBlock) │  │  LECCIONES INDEPENDIENTES       │  │
│  │  20 tipos de bloque │  │  Lesson sin módulo              │  │
│  │  Biblioteca pública │  │  Publicación propia             │  │
│  │  Inserción en lecs. │  │  Biblioteca libre               │  │
│  └─────────────────────┘  └─────────────────────────────────┘  │
│                                                                │
│  Requiere: cv.Curriculum para crear cursos y bloques           │
└────────────────────────────────────────────────────────────────┘
         │
         ├── cv (import directo de Curriculum en models.py)
         ├── accounts.User (FK en Course.tutor, Lesson.author, etc.)
         └── bitacora ← courses.ContentBlock (structured_content)
```

---

## Estado de Implementación

| Módulo | Estado | Observaciones |
|--------|--------|---------------|
| Catálogo público de cursos | ✅ Completo | Filtros por cat, nivel, búsqueda |
| Inscripción de estudiantes | ✅ Completo | Idempotente via get_or_create |
| Vista de aprendizaje | ✅ Completo | Quiz, assignments, progreso, prev/next |
| Dashboard de estudiante | ✅ Completo | Progreso % por curso |
| Sistema de reseñas | ✅ Completo | Con recálculo automático de rating |
| Panel de tutor | ✅ Completo | CRUD, wizard, analytics |
| Gestión de módulos | ✅ Completo | CRUD, duplicate, reorder, bulk, stats |
| Gestión de lecciones | ✅ Completo | CRUD, preview, AJAX support |
| CMS ContentBlock | ✅ Completo | 20 tipos, biblioteca pública |
| Lecciones independientes | ✅ Completo | CRUD, toggle publicación |
| Panel de administración | ✅ Funcional | Usuarios, cursos — sin paginación en cursos |
| `mark_lesson_complete` con lecciones independientes | 🔴 Bug | Falla con `module=None` |
| `standalone_lessons_list` URL | 🔴 Bug | Path duplicado — inaccesible |
| `get_file_size_display` | ⬜ Bug menor | Retorna string literal |
| Tests | ⚠️ Management commands | `create_test_course.py` (387 líneas) — no tests unitarios |
| Documentación | ✅ Esta sesión | Primera documentación formal |

---

## Arquitectura de Datos

### Jerarquía del LMS

```
CourseCategory
  └── Course (tutor=User con cv)
        └── Module (ordered)
              └── Lesson (de curso, ordered)
                    ├── LessonAttachment (ordered)
                    └── Progress (via Enrollment)

Course
  ├── Enrollment (student=User)
  │     └── Progress (enrollment × lesson, unique)
  └── Review (student=User, unique per student)

ContentBlock (author=User)
  └── Lesson.structured_content (JSONField — referencia por contenido)

Lesson (module=None) — lección independiente
  └── author=User (requerido)
```

### Dependencias cross-app

```
courses → cv (import directo en models.py: from cv.models import Curriculum)
courses → accounts.User (FK en Course.tutor, Lesson.author, ContentBlock.author, etc.)
courses ← bitacora (bitacora.BitacoraEntry.structured_content usa courses.ContentBlock)
courses ← PROJECT_DESIGN.md: "cursos → analyst (análisis de progreso) + cv (certificaciones)"
```

⚠️ `from cv.models import Curriculum` en el nivel de módulo de `models.py` crea un **acoplamiento de importación** — si `cv` falla al cargar, `courses` también falla.

### Datos denormalizados en `Course`

```python
Course.students_count  # PositiveIntegerField — mantenido por signal
Course.average_rating  # DecimalField — mantenido por Review.save() + signal
```

Ambos pueden desincronizarse si se crean/eliminan inscripciones o reseñas fuera del flujo normal (admin, scripts de seeding, etc.).

---

## Roadmap

### Deuda inmediata (pre-Sprint 8)

| ID | Tarea | Prioridad |
|----|-------|-----------|
| CRS-1 | Fix URL duplicada `content/` — registrar `standalone_lessons_list` en `/lessons/` o similar | 🔴 |
| CRS-2 | Fix `mark_lesson_complete` — verificar `lesson.module` antes de acceder | 🔴 |
| CRS-3 | Fix `LessonAttachment.get_file_size_display()` — sintaxis de f-string | 🟠 |
| CRS-4 | Extraer switch de 20 tipos de `create_content_block` y `edit_content_block` a helper compartido | 🟠 |
| CRS-5 | Eliminar recálculo duplicado de `average_rating` en `Review.save()` (ya lo hace el signal) | 🟠 |

### Sprint 8

| ID | Tarea | Prioridad |
|----|-------|-----------|
| CRS-6 | Fix `edit_user` — reemplazar lectura cruda de `request.POST` por un Django Form | 🟠 |
| CRS-7 | Paginación en `course_list` y `standalone_lessons_list` | 🟠 |
| CRS-8 | Reemplazar loops Python en `dashboard`, `course_list`, `modules_overview` por `annotate` | 🟠 |
| CRS-9 | `available_content_blocks` en create/edit lección — agregar límite (ej. 50) para evitar B7 | 🟠 |
| CRS-10 | Documentar `course_filters.py` y `lesson_tags.py` | 🟡 |

### Sprint 9

| ID | Tarea | Prioridad |
|----|-------|-----------|
| CRS-11 | Evaluar `students_count` calculado via `annotate` en lugar de campo denormalizado | 🟡 |
| CRS-12 | Tests unitarios reales para flujo LMS (enroll → learn → complete → review) | 🟡 |
| CRS-13 | Integración `courses → analyst` para análisis de progreso de estudiantes | 🟡 |
| CRS-14 | Integración `courses → cv` para generar certificaciones al completar cursos | 🟡 |
| CRS-15 | Eliminar `test_template.html` del directorio de templates | 🟡 |

---

## Notas para Claude

- **Propietario varía por modelo** — `Course.tutor`, `Lesson.author`, `ContentBlock.author`, `Enrollment.student` — nunca usar `created_by`
- **Requiere `cv` para tutores** — siempre verificar `hasattr(request.user, 'cv')` antes de operaciones de tutor; `Course.save()` lanzará `ValueError` sin CV
- **`Course.save()` lanza `ValueError`** (no `ValidationError`) — los forms no lo capturan automáticamente; manejar en vistas con try/except si es necesario
- **`Lesson` dual** — `module=None` es lección independiente; `module=algo` es lección de curso. Siempre verificar con `lesson.is_standalone` o `lesson.module is None`
- **`mark_lesson_complete` solo para lecciones de curso** — no llamar con `module=None`
- **`standalone_lessons_list` está roto** — la URL `/courses/content/` siempre sirve `content_manager`; usar `my_standalone_lessons` o `standalone_lesson_detail` como alternativa
- **URLs usan `<slug:slug>` para cursos** — no hay `<int:pk>` en Course; solo `enroll` y `add_review` usan `<int:course_id>`
- **CMS: 20 tipos de ContentBlock** — el campo que se usa depende del tipo: `html_content` para html/bootstrap/text, `markdown_content` para markdown, `json_content` para el resto
- **Signals en `models.py`** — `update_course_rating` (post_save/post_delete de Review) y `update_student_count` (post_save de Enrollment) están definidos al final del archivo, no en `signals.py`. No hay `apps.py ready()` separado
- **`import from cv.models import Curriculum`** en la línea 9 de `models.py` — si la app `cv` no está disponible, `courses` no carga en absoluto
- **Bug global #8** (editor lento con muchos bloques): `available_content_blocks` sin límite — en instancias con cientos de bloques, la vista de crear/editar lección puede ser muy lenta
