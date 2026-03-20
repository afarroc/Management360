# Mapa de Contexto — App `accounts`

> Generado por `m360_map.sh`  |  2026-03-19 18:09:09
> Ruta: `/data/data/com.termux/files/home/projects/Management360/accounts`  |  Total archivos: **19**

---

## Índice

| # | Categoría | Archivos |
|---|-----------|----------|
| 1 | 👁 `views` | 1 |
| 2 | 🎨 `templates` | 12 |
| 3 | 🗃 `models` | 1 |
| 4 | 📝 `forms` | 1 |
| 5 | 🔗 `urls` | 1 |
| 6 | 🧪 `tests` | 1 |
| 7 | 📄 `other` | 2 |

---

## Archivos por Categoría


### VIEWS (1 archivos)

| Archivo | Líneas | Ruta relativa |
|---------|--------|---------------|
| `views.py` | 205 | `views.py` |

### TEMPLATES (12 archivos)

| Archivo | Líneas | Ruta relativa |
|---------|--------|---------------|
| `accounts_dashboard.html` | 119 | `templates/accounts/accounts_dashboard.html` |
| `form.html` | 13 | `templates/accounts/includes/form.html` |
| `terms_conditions.html` | 54 | `templates/accounts/includes/terms_conditions.html` |
| `login.html` | 116 | `templates/accounts/login.html` |
| `password_change.html` | 134 | `templates/accounts/password_change.html` |
| `password_change_done.html` | 63 | `templates/accounts/password_change_done.html` |
| `password_reset.html` | 67 | `templates/accounts/password_reset.html` |
| `password_reset_complete.html` | 9 | `templates/accounts/password_reset_complete.html` |
| `password_reset_confirm.html` | 13 | `templates/accounts/password_reset_confirm.html` |
| `password_reset_done.html` | 40 | `templates/accounts/password_reset_done.html` |
| `password_reset_email.html` | 56 | `templates/accounts/password_reset_email.html` |
| `signup.html` | 112 | `templates/accounts/signup.html` |

### MODELS (1 archivos)

| Archivo | Líneas | Ruta relativa |
|---------|--------|---------------|
| `models.py` | 32 | `models.py` |

### FORMS (1 archivos)

| Archivo | Líneas | Ruta relativa |
|---------|--------|---------------|
| `forms.py` | 19 | `forms.py` |

### URLS (1 archivos)

| Archivo | Líneas | Ruta relativa |
|---------|--------|---------------|
| `urls.py` | 79 | `urls.py` |

### TESTS (1 archivos)

| Archivo | Líneas | Ruta relativa |
|---------|--------|---------------|
| `tests.py` | 212 | `tests.py` |

### OTHER (2 archivos)

| Archivo | Líneas | Ruta relativa |
|---------|--------|---------------|
| `__init__.py` | 0 | `__init__.py` |
| `apps.py` | 6 | `apps.py` |

---

## Árbol de Directorios

```
accounts/
├── templates
│   └── accounts
│       ├── includes
│       │   ├── form.html
│       │   └── terms_conditions.html
│       ├── accounts_dashboard.html
│       ├── login.html
│       ├── password_change.html
│       ├── password_change_done.html
│       ├── password_reset.html
│       ├── password_reset_complete.html
│       ├── password_reset_confirm.html
│       ├── password_reset_done.html
│       ├── password_reset_email.html
│       └── signup.html
├── __init__.py
├── apps.py
├── forms.py
├── models.py
├── tests.py
├── urls.py
└── views.py
```

---

## Endpoints registrados

Fuente: `urls.py`

```python
  path("", accounts_view, name="accounts"),
  path("signup/", signup_view, name="signup"),
  path("login/", login_view, name="login"),
  path("logout/", logout_view, name="logout"),
  path(
  path(
  path(
  path(
  path(
  path(
  re_path(
```

---

## Modelos detectados

**`models.py`**

- línea 4: `class User(AbstractUser):`


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
cat /data/data/com.termux/files/home/projects/Management360/accounts/views/mi_vista.py | termux-clipboard-set
```
