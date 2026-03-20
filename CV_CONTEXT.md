# Mapa de Contexto — App `cv`

> Generado por `m360_map.sh`  |  2026-03-20 09:36:45
> Ruta: `/data/data/com.termux/files/home/projects/Management360/cv`  |  Total archivos: **32**

---

## Índice

| # | Categoría | Archivos |
|---|-----------|----------|
| 1 | 👁 `views` | 1 |
| 2 | 🎨 `templates` | 23 |
| 3 | 🗃 `models` | 1 |
| 4 | 📝 `forms` | 1 |
| 5 | 🔗 `urls` | 1 |
| 6 | 🛡 `admin` | 1 |
| 7 | 📄 `other` | 4 |

---

## Archivos por Categoría


### VIEWS (1 archivos)

| Archivo | Líneas | Ruta relativa |
|---------|--------|---------------|
| `views.py` | 873 | `views.py` |

### TEMPLATES (23 archivos)

| Archivo | Líneas | Ruta relativa |
|---------|--------|---------------|
| `corporate_profile.html` | 34 | `templates/cv/corporate_profile.html` |
| `curriculum_create.html` | 610 | `templates/cv/curriculum_create.html` |
| `curriculum_form.html` | 513 | `templates/cv/curriculum_form.html` |
| `curriculum_not_found.html` | 39 | `templates/cv/curriculum_not_found.html` |
| `detail.html` | 103 | `templates/cv/detail.html` |
| `docsview.html` | 166 | `templates/cv/documents/docsview.html` |
| `upload.html` | 116 | `templates/cv/documents/upload.html` |
| `edit_section.html` | 577 | `templates/cv/edit_section.html` |
| `form_actions.html` | 21 | `templates/cv/includes/form_actions.html` |
| `formset_section.html` | 57 | `templates/cv/includes/formset_section.html` |
| `profile.html` | 18 | `templates/cv/includes/profile.html` |
| `profile_overview.html` | 73 | `templates/cv/includes/profile_overview.html` |
| `profile_sidebar.html` | 262 | `templates/cv/includes/profile_sidebar.html` |
| `profile_tabs.html` | 353 | `templates/cv/includes/profile_tabs.html` |
| `quick_actions.html` | 155 | `templates/cv/includes/quick_actions.html` |
| `single_form_section.html` | 27 | `templates/cv/includes/single_form_section.html` |
| `social_links.html` | 343 | `templates/cv/includes/social_links.html` |
| `corporate_info.html` | 317 | `templates/cv/includes/tabs/corporate_info.html` |
| `development.html` | 433 | `templates/cv/includes/tabs/development.html` |
| `performance.html` | 434 | `templates/cv/includes/tabs/performance.html` |
| `projects.html` | 477 | `templates/cv/includes/tabs/projects.html` |
| `traditional_profile.html` | 661 | `templates/cv/traditional_profile.html` |
| `view_curriculum.html` | 215 | `templates/cv/view_curriculum.html` |

### MODELS (1 archivos)

| Archivo | Líneas | Ruta relativa |
|---------|--------|---------------|
| `models.py` | 286 | `models.py` |

### FORMS (1 archivos)

| Archivo | Líneas | Ruta relativa |
|---------|--------|---------------|
| `forms.py` | 382 | `forms.py` |

### URLS (1 archivos)

| Archivo | Líneas | Ruta relativa |
|---------|--------|---------------|
| `urls.py` | 32 | `urls.py` |

### ADMIN (1 archivos)

| Archivo | Líneas | Ruta relativa |
|---------|--------|---------------|
| `admin.py` | 116 | `admin.py` |

### OTHER (4 archivos)

| Archivo | Líneas | Ruta relativa |
|---------|--------|---------------|
| `__init__.py` | 0 | `__init__.py` |
| `apps.py` | 6 | `apps.py` |
| `__init__.py` | 0 | `templatetags/__init__.py` |
| `custom_filters.py` | 57 | `templatetags/custom_filters.py` |

---

## Árbol de Directorios

```
cv/
├── templates
│   └── cv
│       ├── documents
│       │   ├── docsview.html
│       │   └── upload.html
│       ├── includes
│       │   ├── tabs
│       │   │   ├── corporate_info.html
│       │   │   ├── development.html
│       │   │   ├── performance.html
│       │   │   └── projects.html
│       │   ├── form_actions.html
│       │   ├── formset_section.html
│       │   ├── profile.html
│       │   ├── profile_overview.html
│       │   ├── profile_sidebar.html
│       │   ├── profile_tabs.html
│       │   ├── quick_actions.html
│       │   ├── single_form_section.html
│       │   └── social_links.html
│       ├── corporate_profile.html
│       ├── curriculum_create.html
│       ├── curriculum_form.html
│       ├── curriculum_not_found.html
│       ├── detail.html
│       ├── edit_section.html
│       ├── traditional_profile.html
│       └── view_curriculum.html
├── templatetags
│   ├── __init__.py
│   └── custom_filters.py
├── __init__.py
├── admin.py
├── apps.py
├── forms.py
├── models.py
├── urls.py
└── views.py
```

---

## Endpoints registrados

Fuente: `urls.py`  |  namespace: `cv`

```python
  path('', CurriculumDetailView.as_view(), name='cv_detail'),
  path('crear/', CurriculumCreateView.as_view(), name='cv_create'),
  path('editar/', CurriculumUpdateView.as_view(), name='cv_edit'),
  path('ver/<int:user_id>/', PublicCurriculumView.as_view(), name='view_cv'),
  path('editar/personal/', EditPersonalInfoView.as_view(), name='edit_personal'),
  path('editar/experiencia/', EditExperienceView.as_view(), name='edit_experience'),
  path('editar/educacion/', EditEducationView.as_view(), name='edit_education'),
  path('editar/habilidades/', EditSkillsView.as_view(), name='edit_skills'),
  path('documentos/', DocumentListView.as_view(), name='docsview'),
  path('documentos/subir/documento/', DocumentUploadView.as_view(), name='document_upload'),
  path('documentos/subir/imagen/', ImageUploadView.as_view(), name='image_upload'),
  path('documentos/subir/base-datos/', DatabaseUploadView.as_view(), name='upload_db'),
  path('documentos/eliminar/<str:file_type>/<int:file_id>/', FileDeleteView.as_view(), name='delete_file'),
  path('view/<int:user_id>/tradicional/', TraditionalProfileView.as_view(), name='traditional_profile'),
```

---

## Modelos detectados

**`models.py`**

- línea 21: `class RoleChoices(models.TextChoices):`
- línea 30: `class Curriculum(models.Model):`
- línea 100: `class Experience(models.Model):`
- línea 128: `class Education(models.Model):`
- línea 157: `class Skill(models.Model):`
- línea 183: `class Language(models.Model):`
- línea 210: `class Certification(models.Model):`
- línea 241: `class Document(models.Model):`
- línea 257: `class Image(models.Model):`
- línea 273: `class Database(models.Model):`


---

## Migraciones

| Archivo | Estado |
|---------|--------|
| `0001_initial` | aplicada |

---

## Funciones clave (views/ y services/)


---

## Compartir con Claude

```bash
cat /data/data/com.termux/files/home/projects/Management360/cv/views/mi_vista.py | termux-clipboard-set
```
