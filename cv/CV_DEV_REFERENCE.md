# Referencia de Desarrollo — App `cv`

> **Actualizado:** 2026-03-20 (Sesión Analista Doc — documentación completa)
> **Audiencia:** Desarrolladores del proyecto y asistentes de IA (Claude)
> **Sprint:** S7.5 — Documentación completa generada.
> **Stats:** 32 archivos · models.py 286 L · views.py 873 L · forms.py 382 L · urls.py 32 L · 23 templates
> **Namespace:** `cv` ✅

---

## Índice

| # | Sección | Contenido |
|---|---------|-----------|
| 1 | Resumen | Qué hace la app, sus pilares |
| 2 | Modelos | 10 modelos — campo por campo |
| 3 | Formularios | Jerarquía de forms, validaciones |
| 4 | Vistas | 14 vistas organizadas por módulo |
| 5 | URLs | Mapa completo de endpoints |
| 6 | Mixins | `CorporateDataMixin`, `FileManagementMixin` |
| 7 | Template tags | `custom_filters.py` |
| 8 | Integración con otras apps | `courses`, `events` |
| 9 | Convenciones críticas y violaciones | Gotchas, bugs de convención |
| 10 | Bugs conocidos | Tabla con estado |
| 11 | Deuda técnica | Clasificada por prioridad |

---

## 1. Resumen

La app `cv` implementa el **Curriculum Vitae dinámico** de Management360. Cada usuario del sistema puede tener un único perfil profesional (`Curriculum` OneToOne con User) que agrupa su información personal, historial laboral, formación, habilidades y archivos adjuntos.

**Pilar 1 — Perfil profesional estructurado**
`Curriculum` + 6 modelos relacionados (Experience, Education, Skill, Language, Certification, y 3 modelos de archivo) con edición por secciones mediante formsets.

**Pilar 2 — Vista corporativa con datos de `events`**
`CurriculumDetailView` es la vista principal — muestra el perfil del usuario enriquecido con métricas de proyectos, tareas y eventos activos, usando los `EventManager`, `ProjectManager` y `TaskManager` de `events`.

**Pilar 3 — Dos formatos de visualización**
El CV puede verse en formato corporativo (`corporate_profile.html`) o en formato tradicional/Harvard (`traditional_profile.html`). Además existe una vista pública sin login (`PublicCurriculumView`).

**Dependencia crítica con `courses`:**
`courses/models.py` hace `from cv.models import Curriculum` en línea 9 — si `cv` no carga, `courses` tampoco. Verificar siempre que las migraciones de `cv` estén aplicadas antes que las de `courses`.

---

## 2. Modelos

### Convenciones de la app

⚠️ **Violaciones documentadas — no cambiar sin migración:**
- **Sin UUID PKs** — todos los modelos usan `AutoField` (int) por defecto.
- **Sin `created_by`** — el propietario es siempre `Curriculum.user` (OneToOne con AUTH_USER_MODEL). Los modelos relacionados heredan el propietario a través de la FK al `Curriculum`.
- **Import incorrecto en models.py** — `from django.contrib.auth.models import User` importado pero no usado como campo (todos los campos usan `settings.AUTH_USER_MODEL`). Import muerto que viola la convención del proyecto.

---

### 2.1 `RoleChoices` (TextChoices)

Definido a nivel de clase dentro de `models.py`.

| Valor | Código | Display |
|-------|--------|---------|
| `SU` | SUPERVISOR | Supervisor |
| `GE` | EVENT_MANAGER | Gestor de Eventos |
| `AD` | ADMIN | Administrador |
| `US` | STANDARD_USER | Usuario Estándar |

**Import correcto:**
```python
from cv.models import RoleChoices
# NO: Curriculum.RoleChoices — es una inner class de models.py, no de Curriculum
```

---

### 2.2 `Curriculum`

Modelo principal — OneToOne con User. Contiene toda la información del perfil profesional.

| Campo | Tipo | Notas |
|-------|------|-------|
| `user` | `OneToOneField(AUTH_USER_MODEL, CASCADE, related_name='cv')` | Propietario — acceder vía `user.cv` |
| `full_name` | `CharField(100)` | Nombre completo (puede diferir de `user.username`) |
| `profession` | `CharField(100)` | Título profesional |
| `bio` | `TextField` | Biografía profesional |
| `profile_picture` | `ImageField(upload_to='profile_pics/', null=True)` | Foto de perfil |
| `location` | `CharField(30, blank=True)` | Ciudad/región |
| `country` | `CharField(100, blank=True)` | País |
| `address` | `CharField(200, blank=True)` | Dirección completa |
| `phone` | `CharField(20, blank=True)` | Validado en form: 9–15 dígitos, solo `+` y números |
| `email` | `EmailField(100, blank=True)` | Email de contacto (≠ email de login) — validado único en form |
| `linkedin_url` | `URLField(blank=True)` | — |
| `github_url` | `URLField(blank=True)` | — |
| `twitter_url` | `URLField(blank=True)` | — |
| `facebook_url` | `URLField(blank=True)` | — |
| `instagram_url` | `URLField(blank=True)` | — |
| `role` | `CharField(2, choices=RoleChoices, default=STANDARD_USER)` | Rol dentro de la empresa |
| `company` | `CharField(100, blank=True)` | Empresa actual |
| `job_title` | `CharField(100, blank=True)` | Cargo actual (diferente de `profession`) |
| `department` | `CharField(100, blank=True)` | Departamento corporativo |
| `corporate_position` | `CharField(100, blank=True)` | Cargo corporativo formal |
| `employee_id` | `CharField(50, blank=True)` | ID de empleado |
| `manager` | `FK(AUTH_USER_MODEL, SET_NULL, null=True, related_name='subordinates')` | Supervisor directo — jerarquía organizacional |
| `hire_date` | `DateField(null=True, blank=True)` | Fecha de contratación |
| `office_location` | `CharField(100, blank=True)` | Oficina asignada |
| `created_at` | `DateTimeField(auto_now_add=True)` | ✅ |
| `updated_at` | `DateTimeField(auto_now=True)` | ✅ |

**Relaciones inversas (related names):**
- `cv.experiences` → `Experience`
- `cv.educations` → `Education`
- `cv.skills_list` → `Skill`
- `cv.languages` → `Language`
- `cv.certifications` → `Certification`
- `cv.documents` → `Document`
- `cv.images` → `Image`
- `cv.databases` → `Database`

**Acceso al CV de un usuario:**
```python
user.cv          # OneToOne reverse — lanza RelatedObjectDoesNotExist si no tiene CV
Curriculum.objects.get(user=user)  # más seguro en vistas
```

**Ordering:** `['-created_at']`

---

### 2.3 `Experience`

| Campo | Tipo | Notas |
|-------|------|-------|
| `cv` | `FK(Curriculum, CASCADE, related_name='experiences')` | — |
| `job_title` | `CharField(100)` | Cargo |
| `company_name` | `CharField(100)` | Empresa |
| `start_date` | `DateField` | — |
| `end_date` | `DateField(null=True, blank=True)` | `None` = trabajo actual |
| `description` | `TextField` | Responsabilidades y logros |

**Validación:** `clean()` verifica `end_date >= start_date`. Se llama **explícitamente en `save()`** — la validación aplica también desde admin y shell.  
**Ordering:** `['-start_date']`

---

### 2.4 `Education`

| Campo | Tipo | Notas |
|-------|------|-------|
| `cv` | `FK(Curriculum, CASCADE, related_name='educations')` | — |
| `institution_name` | `CharField(100)` | Institución |
| `degree` | `CharField(100)` | Título obtenido |
| `field_of_study` | `CharField(100)` | Campo de estudio |
| `start_date` | `DateField` | — |
| `end_date` | `DateField(null=True, blank=True)` | `None` = en curso |
| `description` | `TextField(blank=True)` | Descripción opcional |

**Validación:** misma que `Experience`. **Ordering:** `['-start_date']`

---

### 2.5 `Skill`

| Campo | Tipo | Notas |
|-------|------|-------|
| `cv` | `FK(Curriculum, CASCADE, related_name='skills_list')` | ⚠️ `skills_list`, NO `skills` |
| `skill_name` | `CharField(100)` | Capitalizado en `clean_skill_name()` del form |
| `proficiency_level` | `CharField(1, choices)` | `B`/`I`/`A` — ver tabla |

**`PROFICIENCY_CHOICES`:** definido como class attribute de `Skill` (no módulo-level):

| Código | Display |
|--------|---------|
| `B` | Básico |
| `I` | Intermedio |
| `A` | Avanzado |

**⚠️ related_name es `skills_list`**, no `skills` — en templates y queries usar `cv.skills_list.all()`.  
**Ordering:** `['skill_name']`

---

### 2.6 `Language`

| Campo | Tipo | Notas |
|-------|------|-------|
| `cv` | `FK(Curriculum, CASCADE, related_name='languages')` | — |
| `language_name` | `CharField(100)` | Capitalizado en form |
| `proficiency_level` | `CharField(1, choices)` | `B`/`C`/`F`/`N` |

**`PROFICIENCY_CHOICES`:** `B`=Básico, `C`=Conversacional, `F`=Fluido, `N`=Nativo.  
**Ordering:** `['language_name']`

---

### 2.7 `Certification`

| Campo | Tipo | Notas |
|-------|------|-------|
| `cv` | `FK(Curriculum, CASCADE, related_name='certifications')` | — |
| `certification_name` | `CharField(200)` | — |
| `issuing_organization` | `CharField(200)` | — |
| `issue_date` | `DateField` | — |
| `expiration_date` | `DateField(null=True, blank=True)` | `None` = no expira |
| `credential_id` | `CharField(100, blank=True)` | ID de credencial |
| `credential_url` | `URLField(blank=True)` | URL de verificación |

**Validación:** `expiration_date >= issue_date`. Explícita en `save()`.  
**Ordering:** `['-issue_date']`

---

### 2.8 `Document`, `Image`, `Database` (modelos de archivo)

Los tres modelos de archivo siguen el mismo patrón:

| Campo | Tipo | Notas |
|-------|------|-------|
| `cv` | `FK(Curriculum, CASCADE, related_name='documents'/'images'/'databases')` | — |
| `upload` | `FileField(upload_to=get_upload_path, validators=[FileExtensionValidator])` | — |
| `uploaded_at` | `DateTimeField(auto_now_add=True)` | ⚠️ NO es `created_at` — inconsistencia de nombre |

**Extensiones permitidas:**

| Modelo | Extensiones | `related_name` |
|--------|-------------|----------------|
| `Document` | `pdf`, `docx`, `ppt` | `documents` |
| `Image` | `jpg`, `jpeg`, `png`, `bmp` | `images` |
| `Database` | `csv`, `txt`, `xlsx`, `xlsm` | `databases` |

**`get_upload_path(instance, filename)`** — helper a nivel de módulo:
```python
# Si ext in ['pdf', 'docx', 'ppt'] → documents/{ext}/{filename}
# Else → images/{ext}/{filename}
# ⚠️ Bug: 'bmp', 'csv', 'xlsx', 'xlsm', 'txt', 'xlsm' van a images/ aunque no sean imágenes
```

---

## 3. Formularios

### Jerarquía

```
BaseModelForm (ModelForm)
    ├── CurriculumForm
    ├── ExperienceForm
    ├── EducationForm
    ├── SkillForm
    ├── LanguageForm
    └── CertificationForm

FileUploadForm (Form)
    ├── DocumentForm
    ├── ImageForm
    └── DatabaseForm
```

### 3.1 `BaseModelForm`

Clase base heredada por todos los ModelForms. Aplica en `__init__`:
- `class="form-control"` a todos los campos
- Placeholders descriptivos con indicador de requerido/opcional
- Mensajes de error personalizados en español
- Atributos especiales para `EmailField`, `URLField`, `DateField`
- `clean()` — strip de espacios en todos los campos de texto

### 3.2 `CurriculumForm`

```python
model = Curriculum
fields = '__all__'
exclude = ['user', 'created_at', 'updated_at']
```

**Validaciones custom:**
- `clean_email()` — verifica unicidad del email entre Curricula (excluye el propio)
- `clean_phone()` — elimina caracteres no numéricos salvo `+`, valida longitud 9–15

### 3.3 `ExperienceForm`, `EducationForm`, `CertificationForm`

Todos excluyen la FK al CV (`exclude = ['cv']`). Validan fechas en `clean()`. Usan `DateInput(type='date')` para el datepicker del navegador.

### 3.4 `SkillForm`, `LanguageForm`

Inyectan opción vacía `('', 'Seleccione nivel')` en los choices de `proficiency_level`. `clean_skill_name()` y `clean_language_name()` capitalizan el input.

### 3.5 `FileUploadForm` y subclases

Form base (no ModelForm) con:
- `file = FileField` con validación de extensión dinámica (pasada vía `valid_extensions` en `kwargs`)
- Límite de tamaño: **10 MB**
- Regex de nombre de archivo: solo `[\w\-. ]` (sin caracteres especiales)

| Form | Extensiones | `accept` HTML |
|------|-------------|---------------|
| `DocumentForm` | pdf, docx, ppt | `.pdf,.docx,.ppt` |
| `ImageForm` | jpg, jpeg, png, gif | `.jpg,.jpeg,.png,.gif` |
| `DatabaseForm` | csv, xlsx, xls | `.csv,.xlsx,.xls` |

⚠️ `ImageForm` acepta `.gif` pero `Image` model valida `['jpg','jpeg','png','bmp']` — discrepancia.

---

## 4. Vistas

Todas las vistas usan `LoginRequiredMixin` excepto `PublicCurriculumView` (pública por diseño).

### 4.1 `CurriculumDetailView` — Vista principal corporativa

**URL:** `GET /cv/`  
**Template:** `cv/corporate_profile.html`  
**Mixins:** `LoginRequiredMixin`, `DetailView`, `CorporateDataMixin`

Si el usuario no tiene CV → redirect a `cv:cv_create`.

**Contexto:**
- `cv` — objeto Curriculum
- `metrics` — dict de `get_user_metrics()`: tasks_completed, projects_active, events_attended, total_tasks, total_projects, total_events
- `active_projects` — lista de proyectos con progreso (max 5)
- `recent_activities` — actividades últimos 30 días (max 5)
- `certifications_count`, `education_count`, `experience_count`, `skills_count`, `languages_count`

---

### 4.2 `CurriculumCreateView`

**URL:** `GET|POST /cv/crear/`  
**Template:** `cv/curriculum_create.html`  
**Form:** `CurriculumForm`

`dispatch()` redirige a `cv:cv_detail` si el usuario ya tiene CV (OneToOne — solo uno por usuario).  
`form_valid()` inyecta `user=request.user` antes de guardar.

---

### 4.3 `CurriculumUpdateView`

**URL:** `GET|POST /cv/editar/`  
**Template:** `cv/curriculum_form.html`

Edición completa del CV con **5 formsets simultáneos** (experience, education, skill, language, certification), todos con `extra=0` (no muestra formularios vacíos). Usa `@transaction.atomic` en POST.

**Validación:** `form.is_valid() AND all(fs.is_valid() for fs in formsets.values())` — si cualquier formset falla, no se guarda nada.

---

### 4.4 `PublicCurriculumView`

**URL:** `GET /cv/ver/<int:user_id>/`  
**Template:** `cv/view_curriculum.html`  
**Sin `LoginRequiredMixin`** — acceso público

Muestra el CV de cualquier usuario por `user_id`. Si no existe → renderiza `cv/curriculum_not_found.html` con status 404.

⚠️ **Bug #79** — `pk_url_kwarg = 'user_id'` está seteado pero `get_object()` es sobreescrito y no lo usa — setting superfluo/confuso.

---

### 4.5 `EditPersonalInfoView`

**URL:** `GET|POST /cv/editar/personal/`  
**Template:** `cv/edit_section.html`  
Paso 1/5 del wizard de edición. Redirige a `cv:edit_experience` en éxito.

---

### 4.6 `EditExperienceView`, `EditEducationView`, `EditSkillsView`

**URLs:** `/cv/editar/experiencia/`, `/cv/editar/educacion/`, `/cv/editar/habilidades/`  
**Template:** `cv/edit_section.html` (compartido)  
Pasos 2/5, 3/5 y 4/5 del wizard. Cada uno usa un formset con `extra=0, can_delete=True`.

**Flujo del wizard:**
```
edit_personal (1/5, 20%)
  → edit_experience (2/5, 40%)
    → edit_education (3/5, 60%)
      → edit_skills (4/5, 80%)
        → cv_detail
```

⚠️ Las secciones de `Language` y `Certification` no tienen vistas propias en el wizard — solo se editan desde `CurriculumUpdateView` (edición completa).

---

### 4.7 `FileUploadView` y subclases

**URLs:** `/cv/documentos/subir/documento/`, `/cv/documentos/subir/imagen/`, `/cv/documentos/subir/base-datos/`  
**Template:** `cv/documents/upload.html`

Vista base con `dispatch()` que verifica existencia de CV. `form_valid()` crea el objeto de archivo con `cv=get_cv(user)`.

| Vista | Form | Modelo |
|-------|------|--------|
| `DocumentUploadView` | `DocumentForm` | `Document` |
| `ImageUploadView` | `ImageForm` | `Image` |
| `DatabaseUploadView` | `DatabaseForm` | `Database` |

---

### 4.8 `FileDeleteView`

**URL:** `POST /cv/documentos/eliminar/<str:file_type>/<int:file_id>/`

Elimina archivo verificando propietario: `get_object_or_404(model, id=file_id, cv__user=request.user)` ✅. `file_type` debe ser `'document'`, `'image'` o `'database'` — si no está en el `models_map`, devuelve error.

---

### 4.9 `DocumentListView`

**URL:** `GET /cv/documentos/`  
**Template:** `cv/documents/docsview.html`

Lista los 3 tipos de archivos del CV del usuario. Contexto: `documents`, `images`, `databases`.

---

### 4.10 `TraditionalProfileView`

**URL:** `GET /cv/view/<int:user_id>/tradicional/`  
**Template:** `cv/traditional_profile.html`  

CV en formato tradicional. Si se pasa `user_id` → busca por `Curriculum(user_id=user_id)`. Sin `user_id` → el propio usuario.

---

## 5. URLs

| Pattern | Name | Vista | Auth |
|---------|------|-------|------|
| `/cv/` | `cv:cv_detail` | `CurriculumDetailView` | ✅ login |
| `/cv/crear/` | `cv:cv_create` | `CurriculumCreateView` | ✅ login |
| `/cv/editar/` | `cv:cv_edit` | `CurriculumUpdateView` | ✅ login |
| `/cv/ver/<int:user_id>/` | `cv:view_cv` | `PublicCurriculumView` | ❌ público |
| `/cv/editar/personal/` | `cv:edit_personal` | `EditPersonalInfoView` | ✅ login |
| `/cv/editar/experiencia/` | `cv:edit_experience` | `EditExperienceView` | ✅ login |
| `/cv/editar/educacion/` | `cv:edit_education` | `EditEducationView` | ✅ login |
| `/cv/editar/habilidades/` | `cv:edit_skills` | `EditSkillsView` | ✅ login |
| `/cv/documentos/` | `cv:docsview` | `DocumentListView` | ✅ login |
| `/cv/documentos/subir/documento/` | `cv:document_upload` | `DocumentUploadView` | ✅ login |
| `/cv/documentos/subir/imagen/` | `cv:image_upload` | `ImageUploadView` | ✅ login |
| `/cv/documentos/subir/base-datos/` | `cv:upload_db` | `DatabaseUploadView` | ✅ login |
| `/cv/documentos/eliminar/<str:file_type>/<int:file_id>/` | `cv:delete_file` | `FileDeleteView` | ✅ login (mixin) |
| `/cv/view/<int:user_id>/tradicional/` | `cv:traditional_profile` | `TraditionalProfileView` | ✅ login |

**Namespace:** `app_name = 'cv'` ✅ declarado en `urls.py`.

---

## 6. Mixins

### 6.1 `CorporateDataMixin`

Mixin sin herencia propia. Provee 3 métodos usados por `CurriculumDetailView`:

**`get_user_metrics(user)`** — llama a los 3 managers de `events` y devuelve: `tasks_completed`, `projects_active`, `events_attended`, `total_tasks`, `total_projects`, `total_events`.

**`get_active_projects(user, limit=5)`** — devuelve lista de proyectos con: `id`, `name`, `description`, `role`, `start_date`, `status`, `status_color`, `progress` (% tareas done), `team_size`, `detail_url`, `edit_url`.

**`_get_user_project_role(user, project)`** — determina rol: `'Host'` si `project.host == user`, `'Responsable'` si `project.assigned_to == user`, `'Participante'` si está en attendees, `'Colaborador'` en otro caso.

**`get_recent_activities(user, limit=5, days=30)`** — mezcla hasta 3 tareas + 2 proyectos + 2 eventos recientes, ordenados por `updated_at` desc.

⚠️ **Bug #75** — Los managers de `events` se importan a **nivel de módulo** al tope de `views.py`:
```python
from events.management.event_manager import EventManager
from events.management.project_manager import ProjectManager
from events.management.task_manager import TaskManager
```
Si estos módulos no existen o tienen errores, **toda la app `cv` falla al cargar**.

⚠️ **Bug #76** — `get_active_projects` usa `reverse('project_detail', ...)` y `reverse('tasks_with_id', ...)` sin namespace — producen `NoReverseMatch` si los names no están registrados exactamente así.

### 6.2 `FileManagementMixin`

Hereda de `LoginRequiredMixin`. Provee:
- `models_map` — dict `{'document': Document, 'image': Image, 'database': Database}`
- `get_cv(user)` — `get_object_or_404(Curriculum, user=user)`
- `get_file_model(file_type)` — lookup en `models_map`, retorna `None` si no existe

---

## 7. Template Tags — `custom_filters.py`

Ubicado en `cv/templatetags/custom_filters.py` (57 líneas). No documentado en detalle en el código fuente. Registrado como librería de template tags para uso en los templates de `cv`.

---

## 8. Integración con Otras Apps

### Con `courses`

```python
# courses/models.py línea 9:
from cv.models import Curriculum
```

`Curriculum` es importado directamente en `courses/models.py`. Si `cv` falla al importar, `courses` no carga. Es la única dependencia directa.

### Con `events`

`CorporateDataMixin` en `views.py` importa a nivel de módulo:
```python
from events.management.event_manager import EventManager
from events.management.project_manager import ProjectManager
from events.management.task_manager import TaskManager
from events.models import Task, Project, Event, EventAttendee
```

Esta dependencia es **en tiempo de carga del módulo** — si `events` no está disponible, `cv.views` no importa.

---

## 9. Convenciones Críticas y Violaciones

| Convención | Estándar | Estado en `cv` |
|------------|----------|----------------|
| PK UUID | `UUIDField(primary_key=True)` | ❌ Todos los modelos usan AutoField int |
| `created_by` | `FK(AUTH_USER_MODEL)` | ❌ Ausente — propietario es `Curriculum.user` (OneToOne) |
| Timestamps | `created_at`/`updated_at` | ⚠️ Solo `Curriculum` los tiene; modelos de archivo usan `uploaded_at` |
| User import en models | `settings.AUTH_USER_MODEL` | ⚠️ `from django.contrib.auth.models import User` importado pero no usado como campo |
| Namespace | `app_name = 'cv'` | ✅ Correcto |
| `@login_required` | en todas las vistas | ✅ excepto `PublicCurriculumView` (intencional — vista pública) |

### Patrón de propietario

`cv` no usa `created_by` — el propietario siempre se obtiene a través de la cadena `objeto.cv.user`. Para acceso seguro:

```python
# Verificar propietario al eliminar archivos:
get_object_or_404(Document, id=pk, cv__user=request.user)  ✅

# Acceder al CV del usuario autenticado:
get_object_or_404(Curriculum, user=request.user)  ✅
```

### `clean()` explícito en `save()`

`Experience`, `Education` y `Certification` llaman `self.clean()` dentro de `save()`. Esto es intencional para garantizar validación de fechas aunque se cree el objeto desde admin o shell, sin pasar por el formulario.

---

## 10. Bugs Conocidos

| # | Estado | App | Descripción | Impacto |
|---|--------|-----|-------------|---------|
| #24 | ✅ | cv | Admin con campos inexistentes | — |
| #73 | ⬜ | cv | `from django.contrib.auth.models import User` importado sin uso en `models.py` — violación de convención | Bajo |
| #74 | ⬜ | cv | Sin UUID PK en ningún modelo | Bajo (deuda) |
| #75 | ⬜ | cv | `EventManager`, `ProjectManager`, `TaskManager` importados a nivel de módulo — si `events.management` falla, `cv` no carga | **Alto** |
| #76 | ⬜ | cv | `reverse('project_detail', ...)` y `reverse('tasks_with_id', ...)` sin namespace en `CorporateDataMixin` — probable `NoReverseMatch` | **Alto** |
| #77 | ⬜ | cv | `pk_url_kwarg = 'user_id'` en `PublicCurriculumView` superfluo — `get_object()` sobreescrito no lo usa | Bajo (code smell) |
| #78 | ⬜ | cv | `get_upload_path()` enruta `bmp`, `csv`, `xlsx`, `xlsm`, `txt` al path `images/` — path semánticamente incorrecto | Bajo |
| #79 | ⬜ | cv | `ImageForm` acepta `.gif` pero `Image` model valida solo `jpg`, `jpeg`, `png`, `bmp` — discrepancia de extensiones | Medio |
| #80 | ⬜ | cv | El wizard de edición no incluye vistas para `Language` ni `Certification` — solo editables desde `cv:cv_edit` (edición completa) | Bajo (UX) |

---

## 11. Deuda Técnica

### Alta prioridad

- **Bug #75 — Imports de managers a nivel de módulo** — convertir a imports lazy (dentro del método) para evitar que la app falle si `events.management` no está disponible.
- **Bug #76 — reverse sin namespace** — cambiar a `reverse('events:project_detail', ...)` o el nombre correcto según `events/urls.py`.

### Media prioridad

- **Bug #79 — Unificar extensiones** entre `ImageForm` y `Image` model (agregar `gif` al model o quitarlo del form).
- **Bug #73 — Limpiar import** `from django.contrib.auth.models import User` de `models.py`.
- **Agregar `created_by`** a `LeadCampaign` — `Curriculum` ya tiene propietario vía `user`, pero los modelos de archivo no tienen auditoría de quién subió cada archivo.
- **UUID PKs** — migración para convertir todos los modelos (bloquea interoperabilidad con otras apps que usan UUIDs).

### Baja prioridad

- **Bug #78 — Fix `get_upload_path()`** — usar paths semánticos por tipo de modelo, no por extensión.
- **Agregar vistas wizard** para `Language` y `Certification` (pasos 5 y 6).
- **`custom_filters.py`** — documentar qué filtros provee.
- **Tests** — sin tests reales.
- **`uploaded_at` → `created_at`** en modelos de archivo — consistencia con el resto del proyecto.
