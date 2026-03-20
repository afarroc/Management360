# Referencia de Desarrollo — App `accounts`

> **Actualizado:** 2026-03-19  
> **Audiencia:** Desarrolladores y asistentes IA  
> **Archivos:** 19 | **Vistas:** 1 archivo (205 líneas) | **Templates:** 12 | **Endpoints:** 11  
> **Migración activa:** `0001_initial`

---

## Índice

| Sección | Contenido |
|---------|-----------|
| 1. Resumen | Qué hace esta app y sus pilares |
| 2. Modelos | `User` — campo por campo |
| 3. Vistas | Funciones, CBVs y decoradores |
| 4. Formularios | `SignUpForm` |
| 5. URLs | Mapa completo de endpoints |
| 6. Convenciones críticas | Gotchas, imports, patrones |
| 7. Bugs conocidos | Issues activos y resueltos |
| 8. Deuda técnica | Clasificada por prioridad |

---

## 1. Resumen

`accounts` es la **app de identidad** de Management360. Gestiona el ciclo completo de autenticación de usuarios y expone el modelo `User` custom del que dependen todas las demás apps del proyecto.

Sus responsabilidades son:

- **Autenticación** — registro, login, logout
- **Modelo User extendido** — hereda de `AbstractUser`, añade `phone`, `avatar`, `created_at`, `updated_at`
- **Gestión de contraseñas** — cambio (usuario autenticado) y recuperación por email (flujo completo con templates propios)
- **Dashboard de cuenta** — vista principal post-login diferenciada por `is_staff`
- **Reset administrativo** — endpoint para que staff resetee contraseña de cualquier usuario a un valor por defecto

---

## 2. Modelos

### `User` — único modelo de la app

Hereda de `django.contrib.auth.models.AbstractUser`. Todos los campos de AbstractUser están disponibles (`username`, `email`, `first_name`, `last_name`, `is_staff`, `is_active`, `date_joined`, etc.).

```python
class User(AbstractUser):
    # Contacto
    phone       = CharField(max_length=20, blank=True, null=True)
    
    # Perfil visual
    avatar      = ImageField(upload_to='avatars/', blank=True, null=True)
    
    # Timestamps propios (AbstractUser NO los tiene)
    created_at  = DateTimeField(auto_now_add=True)
    updated_at  = DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Usuario"
        verbose_name_plural = "Usuarios"

    def __str__(self):
        return self.get_full_name() or self.username
```

**Notas campo por campo:**

| Campo | Tipo | Obligatorio | Default | Notas |
|-------|------|-------------|---------|-------|
| `phone` | CharField(20) | No | NULL | Teléfono libre, sin validación de formato |
| `avatar` | ImageField | No | NULL | Sube a `MEDIA_ROOT/avatars/` |
| `created_at` | DateTimeField | Auto | auto_now_add | No editable — fecha de creación |
| `updated_at` | DateTimeField | Auto | auto_now | No editable — última modificación |

**Heredados de AbstractUser relevantes para M360:**

| Campo | Uso en el proyecto |
|-------|--------------------|
| `username` | Identificador único, usado en login y en `__str__` fallback |
| `email` | Requerido en registro (`SignUpForm`), único validado a nivel form |
| `is_staff` | Controla la rama del dashboard (`accounts_view`) |
| `is_active` | Soft-delete nativo de Django — convención del proyecto |
| `first_name` / `last_name` | Usados en `get_full_name()` para `__str__` |

**⚠️ Convención de proyecto cumplida:**
- `created_at` / `updated_at` ✅ (estándar del proyecto)
- `is_active` ✅ (heredado de AbstractUser)

**⚠️ Convención violada:**
- No tiene `id = UUIDField(primary_key=True)` — usa el `AutoField` int heredado de AbstractUser. Documentado como excepción aceptada (INC-001 fue causado por esto indirectamente).

**Configuración en `panel/settings.py`:**
```python
AUTH_USER_MODEL = 'accounts.User'
```

---

## 3. Vistas

### Decorador utilitario: `anonymous_required`

```python
def anonymous_required(function=None, redirect_url=None):
    """Redirige a usuarios ya autenticados. Inverso de @login_required."""
```

Implementado con `user_passes_test(lambda u: u.is_anonymous)`. Redirige a `"index"` por defecto.

**Uso:**
```python
@anonymous_required(redirect_url="index")
def login_view(request): ...
```

---

### Vistas funcionales

#### `accounts_view` — Dashboard principal

```python
@login_required
def accounts_view(request):
```

| Aspecto | Detalle |
|---------|---------|
| URL | `/accounts/` |
| Auth | `@login_required` |
| Template | `accounts/accounts_dashboard.html` |
| Contexto | `title`, `user` |
| Bifurcación | `is_staff` → título "Admin Dashboard" / "User Dashboard" |

⚠️ El contexto cambia el `title` según `is_staff`, pero ambas ramas renderizan el mismo template. La diferenciación visual real se hace en el template con `{% if user.is_staff %}`.

---

#### `signup_view` — Registro

```python
def signup_view(request):
```

| Aspecto | Detalle |
|---------|---------|
| URL | `/accounts/signup/` |
| Auth | Ninguna — redirige a `"index"` si ya autenticado |
| Form | `SignUpForm` |
| Éxito | Login automático + redirect a `"index"` |
| Template | `accounts/signup.html` |

Flujo: `POST válido → form.save() → auth_login() → redirect("index")`.

---

#### `login_view` — Login

```python
@anonymous_required(redirect_url="index")
def login_view(request):
```

| Aspecto | Detalle |
|---------|---------|
| URL | `/accounts/login/` |
| Auth | `@anonymous_required` — redirige autenticados a `"index"` |
| Template | `accounts/login.html` |
| Soporte `?next=` | Sí — `request.GET.get("next", "index")` |
| Logging | INFO en intento/éxito, WARNING en fallo |

**Gotcha:** el parámetro `next` recibe el valor crudo de la query string. Si es una URL relativa (ej. `/events/`) funciona. Si es un nombre de URL (ej. `"index"`) también funciona porque `redirect()` acepta ambos. No hay validación de `next` seguro (`url_has_allowed_host_and_scheme`) — deuda de seguridad.

---

#### `logout_view` — Logout

```python
def logout_view(request):
```

| Aspecto | Detalle |
|---------|---------|
| URL | `/accounts/logout/` |
| Auth | Ninguna (cualquiera puede llamarla, incluso anónimos) |
| Redirect | `reverse_lazy("login")` |

⚠️ No tiene `@require_POST` ni `@login_required`. Cualquier GET puede cerrar la sesión. Riesgo CSRF bajo en la práctica (logout no es destructivo), pero no sigue la convención del proyecto.

---

### Class-Based Views

#### `CustomPasswordChangeView`

```python
class CustomPasswordChangeView(PasswordChangeView):
    template_name = "accounts/password_change.html"
    success_url   = reverse_lazy("password_change_done")
    form_class    = PasswordChangeForm
```

Hereda de `django.contrib.auth.views.PasswordChangeView` (ya requiere login). Solo añade un `messages.success` en `form_valid`.

---

#### `CustomPasswordResetView`

```python
class CustomPasswordResetView(PasswordResetView):
    template_name          = "accounts/password_reset.html"
    email_template_name    = "accounts/password_reset_email.html"
    subject_template_name  = "accounts/password_reset_subject.txt"
    success_url            = reverse_lazy("password_reset_done")
    form_class             = PasswordResetForm
```

Dos overrides importantes:

**1. `form_valid` — Valida existencia del email antes de enviar:**
```python
if not User.objects.filter(email=email).exists():
    messages.error(...)
    return self.form_invalid(form)
```
⚠️ Esto viola una práctica de seguridad estándar: revelar si un email está registrado facilita enumeración de usuarios. Documentado como deuda técnica.

**2. `send_mail` — Modo debug:**
En `DEBUG=True`, el email NO se envía — solo se loguea con `logger.info`. En producción (`DEBUG=False`), llama al `super()` normal.

**Método adicional: `reset_to_default_password`:**
```python
def reset_to_default_password(self, request, username):
    """Solo staff. Resetea la contraseña de un usuario a 'DefaultPassword123'."""
```
⚠️ **Contraseña hardcodeada como string literal** `"DefaultPassword123"`. Gravísima deuda de seguridad — ver sección 8.

---

#### `CustomPasswordResetConfirmView`

```python
class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    template_name = "accounts/password_reset_confirm.html"
    success_url   = reverse_lazy("password_reset_complete")
    form_class    = SetPasswordForm
```

Solo añade `messages.success` en `form_valid`. Sin lógica adicional.

---

## 4. Formularios

### `SignUpForm`

```python
class SignUpForm(UserCreationForm):
    email = EmailField(max_length=254, required=True)

    class Meta:
        model  = User
        fields = ('username', 'email', 'password1', 'password2')

    def clean_email(self):
        """Valida unicidad de email a nivel form."""
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError("This email address is already in use.")
        return email
```

**Notas:**
- `email` es requerido pero **no tiene `unique=True` a nivel modelo** — la validación solo existe en el form. Un admin que cree usuarios vía Django Admin puede saltársela.
- No incluye `phone` ni `avatar` — son opcionales y se editan post-registro (no hay vista de edición de perfil aún).
- Hereda `password1` / `password2` con las validaciones por defecto de Django (`UserCreationForm`).

---

## 5. URLs

> **⚠️ Violación de convención:** `accounts` **NO declara `app_name`** en `urls.py`. El namespace `accounts` que aparece en el `PROJECT_CONTEXT.md` proviene del `include(..., namespace='accounts')` en el urls.py raíz — no de la app misma. Esto es frágil: si alguien cambia el include sin namespace, todos los `{% url 'accounts:...' %}` se rompen silenciosamente.

### Mapa completo

| URL | Name | Vista | Auth |
|-----|------|-------|------|
| `/accounts/` | `accounts` | `accounts_view` | `@login_required` |
| `/accounts/signup/` | `signup` | `signup_view` | Anónimo |
| `/accounts/login/` | `login` | `login_view` | `@anonymous_required` |
| `/accounts/logout/` | `logout` | `logout_view` | Ninguna |
| `/accounts/password-change/` | `password_change` | `CustomPasswordChangeView` | Django built-in |
| `/accounts/password-change/done/` | `password_change_done` | `PasswordChangeDoneView` | — |
| `/accounts/password-reset/` | `password_reset` | `CustomPasswordResetView` | Anónimo |
| `/accounts/password-reset/done/` | `password_reset_done` | `PasswordResetDoneView` | — |
| `/accounts/password-reset-confirm/<uidb64>/<token>/` | `password_reset_confirm` | `CustomPasswordResetConfirmView` | Token |
| `/accounts/password-reset-complete/` | `password_reset_complete` | `PasswordResetCompleteView` | — |
| `/accounts/password-reset/admin/<username>/` | `admin_password_reset` | `CustomPasswordResetView` | ⚠️ Solo valida `is_staff` dentro del método |

**Flujo de recuperación de contraseña (4 pasos):**

```
1. /password-reset/           → usuario ingresa email
2. /password-reset/done/      → confirmación de envío
3. /password-reset-confirm/   → usuario ingresa nueva contraseña (con token)
4. /password-reset-complete/  → éxito
```

---

## 6. Convenciones Críticas

### Import correcto de User

```python
# En models.py — accounts NO puede usar settings.AUTH_USER_MODEL para sí mismo
# (es el modelo que lo define). El import directo de AbstractUser es correcto aquí.
from django.contrib.auth.models import AbstractUser

# En views.py y forms.py — CORRECTO ✅
from django.contrib.auth import get_user_model
User = get_user_model()

# En OTRAS apps — referenciar a accounts.User así:
# models.py de otra app:
from django.conf import settings
created_by = models.ForeignKey(settings.AUTH_USER_MODEL, ...)

# views.py / forms.py de otra app:
from django.contrib.auth import get_user_model
User = get_user_model()
```

### `accounts` DEBE migrarse antes que el resto

```bash
# build.sh — orden crítico
python manage.py migrate auth
python manage.py migrate contenttypes
python manage.py migrate accounts   # ← PRIMERO — INC-001
python manage.py migrate --no-input
```

### El modelo User NO tiene UUID como PK

```python
# CORRECTO en accounts
user = get_object_or_404(User, pk=request.user.pk)  # pk es int
user = User.objects.get(id=1)                        # id es int

# INCORRECTO — no usar uuid aquí
```

### `DEBUG=True` suprime emails de password reset

En desarrollo, ningún email de recuperación de contraseña llega al destinatario. Se loguea en consola con `logger.info`. Para testear el flujo completo en dev, revisar los logs del servidor.

### Namespace declarado externamente

```python
# urls.py raíz (panel/urls.py o similar)
path('accounts/', include('accounts.urls', namespace='accounts'))

# En templates — funciona porque el namespace viene del include:
{% url 'accounts:login' %}
{% url 'accounts:signup' %}
```

---

## 7. Bugs Conocidos

| # | Estado | Descripción |
|---|--------|-------------|
| B1 | ⬜ activo | `app_name` no declarado en `urls.py` — namespace depende del `include()` externo |
| B2 | ⬜ activo | `logout_view` sin `@require_POST` ni `@login_required` — cualquier GET cierra sesión |
| B3 | ⬜ activo | `login_view`: `next` no validado con `url_has_allowed_host_and_scheme` — potencial open redirect |
| B4 | 🔴 crítico | `reset_to_default_password`: contraseña hardcodeada `"DefaultPassword123"` en código fuente |
| B5 | ⬜ activo | `CustomPasswordResetView.form_valid`: revela si un email está registrado (user enumeration) |
| B6 | ⬜ activo | `email` único solo validado en form, no a nivel de modelo (`unique=True` ausente en `User.email`) |
| B7 | ⬜ activo | Import `from analyst.views.file_views import file_tree_view` en `views.py` — importado pero nunca usado en este archivo |
| B8 | ✅ resuelto | `accounts_user` tabla inexistente en BD — INC-001 (2026-03-17), resuelto con `makemigrations` + commit de migrations |

---

## 8. Deuda Técnica

**Alta prioridad (seguridad):**
- **Eliminar `"DefaultPassword123"` hardcodeado** en `reset_to_default_password` — mover a `settings.py` o generar contraseña aleatoria con `get_random_string()`
- **Validar `next` en `login_view`** con `url_has_allowed_host_and_scheme(url=next_url, allowed_hosts=request.get_host())` para prevenir open redirect
- **Agregar `unique=True` a `User.email`** en el modelo (requiere migración) para que la unicidad no dependa solo del form
- **Proteger `logout_view`** con `@require_POST` o al menos `@login_required`

**Media prioridad:**
- **Declarar `app_name = 'accounts'`** directamente en `urls.py` para que el namespace sea autocontenido
- **Resolver user enumeration** en `CustomPasswordResetView.form_valid` — el comportamiento estándar de Django es no revelar si el email existe; revertir a `super().form_valid(form)` directamente
- **Eliminar import muerto** `from analyst.views.file_views import file_tree_view` en `views.py`
- **Vista de edición de perfil** — no existe forma de que el usuario edite `phone` o `avatar` post-registro
- **Admin custom** — no hay `admin.py`, el modelo `User` no está registrado con campos propios en Django Admin

**Baja prioridad:**
- **Tests** — `tests.py` existe (212 líneas según CONTEXT) pero no se subió; verificar cobertura real
- **Internacionalización** — mensajes de error en inglés; rest del proyecto en español
- **`anonymous_required` como decorador de app** — podría moverse a `core/decorators.py` para uso global
