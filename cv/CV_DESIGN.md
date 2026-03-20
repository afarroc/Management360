# Diseño y Roadmap — App `cv`

> **Actualizado:** 2026-03-20 (Sesión Analista Doc — documentación completa)
> **Estado:** Funcional — 14 vistas, 10 modelos, wizard de edición operativo
> **Fase del proyecto:** Fase 6 (dependencia de `courses`) — documentada en S7.5
> **Migraciones:** `0001_initial` — aplicada

---

## Visión General

La app `cv` implementa el **Curriculum Vitae dinámico** de cada usuario de Management360. Es la capa de identidad profesional del sistema: centraliza el perfil personal, el historial de carrera y los archivos, y los expone tanto en formato corporativo (con métricas de `events`) como en formato público/tradicional.

```
                    accounts.User
                          │ OneToOne
                    ┌─────▼──────┐
                    │ Curriculum  │   ← propietario de todo
                    └──────┬──────┘
            ┌──────┬───────┼───────┬──────┬────────┐
            │      │       │       │      │        │
       Experience Education Skill Language Certif.  Files
                                               (Doc/Img/DB)

  Vista corporativa (cv_detail)          Vista pública (view_cv)
  ┌────────────────────────────┐         ┌──────────────────┐
  │ Curriculum + events data   │         │ Curriculum only  │
  │ (managers: Task/Proj/Event)│         │ (no auth needed) │
  └────────────────────────────┘         └──────────────────┘

  Vista tradicional (traditional_profile)
  ┌────────────────────────────┐
  │ Formato Harvard/clásico    │
  │ (todos los modelos)        │
  └────────────────────────────┘
```

---

## Estado de Implementación

| Módulo | Componente | Estado | Notas |
|--------|-----------|--------|-------|
| **Modelos** | `Curriculum` | ✅ Funcional | Sin UUID · `user` OneToOne · manager FK para jerarquía |
| **Modelos** | `Experience` | ✅ Funcional | Validación fechas en `save()` |
| **Modelos** | `Education` | ✅ Funcional | Validación fechas en `save()` |
| **Modelos** | `Skill` | ✅ Funcional | `related_name='skills_list'` |
| **Modelos** | `Language` | ✅ Funcional | 4 niveles de competencia |
| **Modelos** | `Certification` | ✅ Funcional | Validación fechas en `save()` |
| **Modelos** | `Document` / `Image` / `Database` | ✅ Funcional | Upload con validación extensión + tamaño 10MB |
| **Vista** | `CurriculumDetailView` | ✅ Funcional | ⚠️ `reverse()` sin namespace (Bug #76) |
| **Vista** | `CurriculumCreateView` | ✅ Funcional | Guard anti-duplicado en `dispatch()` |
| **Vista** | `CurriculumUpdateView` | ✅ Funcional | 5 formsets simultáneos · `extra=0` · atomic |
| **Vista** | `PublicCurriculumView` | ✅ Funcional | Sin login · 404 elegante si no existe CV |
| **Vista** | Wizard de edición (4 pasos) | ✅ Funcional | ⚠️ Sin pasos para Language/Certification |
| **Vista** | `TraditionalProfileView` | ✅ Funcional | Formato Harvard |
| **Archivos** | Upload Document/Image/Database | ✅ Funcional | ⚠️ Discrepancia `.gif` form vs model (Bug #79) |
| **Archivos** | `FileDeleteView` | ✅ Funcional | ✅ Verificación de propietario via `cv__user` |
| **Formularios** | `BaseModelForm` | ✅ Funcional | Estilos + mensajes en español |
| **Formularios** | `CurriculumForm` | ✅ Funcional | Validación email único + phone |
| **Formularios** | `FileUploadForm` | ✅ Funcional | 10MB límite · regex nombre |
| **Admin** | `admin.py` | ✅ Registrado | 116 líneas |
| **Template tags** | `custom_filters.py` | ✅ Existe | 57 líneas — no analizado |
| **Tests** | `tests.py` | ❌ Sin tests | — |

---

## Arquitectura de Datos

### Jerarquía de modelos

```
accounts.User (OneToOne)
└── Curriculum
      ├── experiences       → Experience (N)
      ├── educations        → Education (N)
      ├── skills_list       → Skill (N)        ← ojo: skills_list, NO skills
      ├── languages         → Language (N)
      ├── certifications    → Certification (N)
      ├── documents         → Document (N)
      ├── images            → Image (N)
      └── databases         → Database (N)
```

### Dependencias con otras apps

| Dependencia | Dirección | Punto de integración | Riesgo |
|-------------|-----------|---------------------|--------|
| `accounts.User` | cv → accounts | `Curriculum.user` (OneToOne) + `Curriculum.manager` (FK) | ✅ Estable |
| `courses` | courses → cv | `from cv.models import Curriculum` en `courses/models.py:9` | ⚠️ Si `cv` falla, `courses` no carga |
| `events` | cv → events | Managers importados en `cv/views.py` a nivel de módulo | ⚠️ Bug #75 — import frágil |

---

## Roadmap

### Completado

| Tarea | Sprint | Estado |
|-------|--------|--------|
| Modelos base (Curriculum + related) | S6 | ✅ |
| CRUD de CV con formsets | S6 | ✅ |
| Vista pública | S6 | ✅ |
| Vista corporativa con datos de events | S6 | ✅ |
| Gestión de archivos (Document/Image/Database) | S6 | ✅ |
| Wizard de edición por secciones | S6 | ✅ |
| Vista formato tradicional | S6 | ✅ |
| Documentación completa | S7.5 | ✅ |

### Pendiente — Sprint 9

| ID | Tarea | Prioridad | Notas |
|----|-------|-----------|-------|
| CV-1 | Fix `reverse()` sin namespace en `CorporateDataMixin` (Bug #76) | 🔴 | Probable `NoReverseMatch` en producción |
| CV-2 | Convertir imports de `events.management.*` a lazy (Bug #75) | 🔴 | Import a nivel de módulo → falla de carga |
| CV-3 | Unificar extensiones `ImageForm` vs `Image` model (Bug #79) | 🟠 | `.gif` aceptado en form pero rechazado por model |
| CV-4 | Agregar pasos wizard para `Language` y `Certification` | 🟡 | UX incompleta (Bug #80) |
| CV-5 | Limpiar import `from django.contrib.auth.models import User` (Bug #73) | 🟡 | Code smell |
| CV-6 | Fix `get_upload_path()` — paths semánticos por tipo (Bug #78) | 🟡 | Archivos CSV en carpeta `images/` |
| CV-7 | Agregar tests | 🟡 | 0% cobertura actual |
| CV-8 | UUID PKs en todos los modelos | 🟢 | Migración coordinada con `courses` |

---

## Notas para Claude

- **`Curriculum` es OneToOne con User** — acceder siempre como `get_object_or_404(Curriculum, user=request.user)`. Nunca asumir que el usuario tiene CV — verificar antes con `Curriculum.objects.filter(user=request.user).exists()`.

- **`related_name='skills_list'`** en `Skill` — es `cv.skills_list.all()`, NO `cv.skills.all()` (que daría `AttributeError`).

- **Propietario implícito** — `cv` no usa `created_by`. El propietario de cualquier objeto se resuelve como `objeto.cv.user`. Para filtros de seguridad: `get_object_or_404(Document, id=pk, cv__user=request.user)`.

- **`clean()` en `save()`** — `Experience`, `Education`, `Certification` validan fechas en `save()`. No hacer `save(update_fields=['campo'])` para saltarse la validación — el `clean()` se ejecuta igualmente.

- **Imports de eventos son frágiles** — `views.py` importa `EventManager`, `ProjectManager`, `TaskManager` a nivel de módulo. Si los archivos no existen o tienen errores de sintaxis, **ninguna vista de `cv` carga**. Fix: mover los imports dentro del método `get_context_data`.

- **`RoleChoices` es una TextChoices independiente** — no es inner class de `Curriculum`. Importar como `from cv.models import RoleChoices`.

- **Vista pública sin auth** — `PublicCurriculumView` no requiere login. Si se necesita restricción futura, agregar `LoginRequiredMixin`.

- **`uploaded_at` en modelos de archivo** — los modelos `Document`, `Image`, `Database` usan `uploaded_at` (no `created_at`). Tenerlo en cuenta en queries de ordenación.

- **`courses` depende de `cv`** — el orden de migraciones es `cv` → `courses`. Si se agrega una migración a `cv`, asegurarse que `courses` siga cargando.

- **`CurriculumForm` usa `fields='__all__'` con `exclude`** — esto incluye todos los campos del modelo menos los excluidos. Si se agregan nuevos campos al modelo, aparecerán automáticamente en el form (puede ser no deseado).
