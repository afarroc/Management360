# Diseño y Roadmap — App `help`

> **Actualizado:** 2026-03-20
> **Estado:** Parcialmente funcional — 7/10 endpoints con template, 5/5 templates core OK
> **Sprint:** Lote 4 documentación

---

## Visión General

`help` es el Centro de Ayuda integrado de Management360. Funciona como un CMS de solo lectura para usuarios finales, con contenido gestionado via Django Admin y el comando `setup_help.py`.

```
┌─────────────────────────────────────────────────┐
│              Centro de Ayuda (help)             │
├─────────────────────────────────────────────────┤
│  help_home    → portada con stats y destacados  │
│  categories   → árbol de categorías             │
│  articles     → documentación detallada         │
│  faq          → preguntas frecuentes ❌ NO TEMPLATE│
│  videos       → tutoriales ❌ NO TEMPLATE        │
│  quick_start  → guías ❌ NO TEMPLATE             │
│  search       → búsqueda cross-model            │
│  feedback     → rating por artículo             │
└────────────────────────┬────────────────────────┘
                         │ FK referencias opcionales
                         ▼
              ┌──────────────────┐
              │   App courses    │
              │  Course, Lesson  │
              │  ContentBlock    │
              └──────────────────┘
```

---

## Estado de Implementación

| Módulo | Estado | Notas |
|--------|--------|-------|
| Modelos (7) | ✅ Completo | AutoField int PK en todos |
| Migración 0001 | ✅ Aplicada | |
| Admin | ⚠️ Stub | `admin.py` tiene 3 líneas — sin registros |
| `help_home` | ✅ Funcional | Template OK |
| `category_list` | ✅ Funcional | Template OK |
| `category_detail` | ✅ Funcional | Template OK, paginación 12/página |
| `article_detail` | ✅ Funcional | Template OK, maneja `requires_auth` |
| `search_help` | ✅ Funcional | Template OK, log analítico |
| `submit_feedback` | ✅ Funcional | `@login_required`, POST JSON |
| `article_feedback_stats` | ⚠️ Parcial | Sin `@login_required` (bug #102) |
| `faq_list` | ❌ Template faltante | TemplateDoesNotExist (bug #107) |
| `video_tutorials` | ❌ Template faltante | TemplateDoesNotExist (bug #107) |
| `quick_start` | ❌ Template faltante | TemplateDoesNotExist (bug #107) |
| Tests | ❌ Stub 3 líneas | Sin cobertura real |
| `setup_help.py` | ✅ Implementado | 1115 líneas de seed data |

---

## Arquitectura de Datos

### Jerarquía de modelos

```
HelpCategory (1)
├── HelpArticle (N)      → author (User, nullable)
│   └── HelpFeedback (N) → user (User, nullable)
├── FAQ (N)
└── VideoTutorial (N)    → author (User, nullable)

QuickStartGuide          → sin FK a HelpCategory

HelpSearchLog            → user (User, nullable) — telemetría
```

### Dependencias con otras apps

| App | Tipo | Detalle |
|-----|------|---------|
| `courses` | Dependencia fuerte | FK a `Course`, `Lesson`, `ContentBlock` en `HelpArticle` y `VideoTutorial` |
| `courses` | Import a nivel de módulo | ⚠️ Si `courses` falla → `help` no carga (bug #101) |
| `accounts` | Implícita via User | FKs a `settings.AUTH_USER_MODEL` |

### Cadena de fallo

```
events.management.* falla
    → cv no carga (bug #75)
        → courses no carga (import de cv)
            → help no carga (import de courses) ← BUG #101
```

`help` está al final de la cadena de dependencias más frágil del proyecto.

---

## Roadmap

### Deuda inmediata (bloquea funcionalidad)

| ID | Tarea | Impacto | Esfuerzo |
|----|-------|---------|---------|
| HELP-1 | Crear `faq_list.html` | 🔴 Endpoint crashea | 30 min |
| HELP-2 | Crear `video_tutorials.html` | 🔴 Endpoint crashea | 30 min |
| HELP-3 | Crear `quick_start.html` | 🔴 Endpoint crashea | 20 min |
| HELP-4 | `article.save(update_fields=...)` en `submit_feedback` | 🟠 Sobrescritura | 5 min |
| HELP-5 | `@login_required` en `article_feedback_stats` | 🟠 Seguridad | 5 min |

### Sprint 9 — mejoras

| ID | Tarea | Prioridad |
|----|-------|-----------|
| HELP-6 | Registrar `help` en `admin.py` — al menos `HelpArticle`, `HelpCategory`, `FAQ` | 🟠 |
| HELP-7 | Mover imports de `courses` a lazy (dentro de métodos) | 🟠 |
| HELP-8 | Fix race condition `HelpSearchLog` (bug #110) | 🟡 |
| HELP-9 | Implementar `FAQ.view_count` / `FAQ.helpful_count` o eliminarlos | 🟡 |
| HELP-10 | Tests básicos para vistas públicas | 🟡 |

### Futuro (no urgente)

| Tarea | Nota |
|-------|------|
| Migrar PKs a UUID | Breaking change — evaluar cuando haya más integraciones |
| `UserGuideProgress` model | Completar `mark_completed(user)` |
| Feedback único por (article, user) | `unique_together` en `HelpFeedback` |
| Búsqueda con ranking por relevancia | Actualmente `icontains` simple |
| Panel de analytics para admin | `HelpSearchLog` ya guarda datos — explotar para insights |

---

## Notas para Claude

- **`help` NO tiene `created_by`** en ningún modelo — `author`/`user` son los campos de propietario
- **3 templates faltan** — `faq_list`, `video_tutorials`, `quick_start` dan 500 al visitarlos
- **Dependencia de `courses` en import** — no trabajar en `help` si `courses` tiene errores de sintaxis
- **`get_content()`** resuelve: propio > curso > lección > content_block — si FK es NULL, retorna `""`
- **`referenced_course`/`referenced_lesson`/`referenced_content_block`** son mutuamente excluyentes por convención, no por constraint
- **`submit_feedback`** actualiza contadores del artículo directamente (`helpful_count` ++) — no usar `F()` expressions actualmente (deuda)
- **`article_feedback_stats`** retorna JSON — usar `is_staff` check, no `@staff_member_required`
- **`search_help`** crea `HelpSearchLog` en cada búsqueda, incluyendo anónimos — puede crecer rápido
- **`setup_help.py`** popula la BD con categorías y artículos demo — correr antes de probar la app en dev
- **`QuickStartGuide`** no tiene FK a `HelpCategory` — es independiente del árbol de categorías
- **Namespace `help:`** — ✅ declarado correctamente, usar `{% url 'help:article_detail' slug=article.slug %}`
