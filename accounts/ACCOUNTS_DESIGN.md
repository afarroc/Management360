# Diseño y Roadmap — App `accounts`

> **Actualizado:** 2026-03-19  
> **Estado:** Funcional en producción — documentación generada esta sesión  
> **Sprint actual:** 7 completado | Próximo: Sprint 8

---

## Visión General

`accounts` es la **app fundacional** de Management360. Es la primera en migrarse, la única que define `AUTH_USER_MODEL`, y de la que dependen directamente las 19 apps restantes del proyecto.

Su alcance es deliberadamente estrecho: autenticación + modelo User. No gestiona perfiles complejos, roles de equipo ni permisos por objeto — eso lo hacen apps específicas (`cv`, `events`, `rooms`).

```
┌─────────────────────────────────────────────────────┐
│                   APP ACCOUNTS                      │
│                                                     │
│   ┌──────────────┐     ┌──────────────────────────┐ │
│   │  User model  │     │    Autenticación         │ │
│   │              │     │                          │ │
│   │  AbstractUser│     │  signup  → login         │ │
│   │  + phone     │     │  logout                  │ │
│   │  + avatar    │     │  password change         │ │
│   │  + created_at│     │  password reset (email)  │ │
│   │  + updated_at│     │  admin reset (staff)     │ │
│   └──────┬───────┘     └──────────────────────────┘ │
│          │ AUTH_USER_MODEL                           │
│          ▼                                           │
│   ← todas las demás apps del proyecto →              │
└─────────────────────────────────────────────────────┘
```

---

## Estado de Implementación

| Módulo | Estado | Observaciones |
|--------|--------|---------------|
| Modelo `User` (AbstractUser extendido) | ✅ Completo | phone, avatar, timestamps |
| Registro (`signup`) | ✅ Completo | Email único (a nivel form) |
| Login / Logout | ✅ Completo | Soporte `?next=`, logging |
| Dashboard de cuenta | ✅ Funcional | Bifurcación staff / usuario — template único |
| Password change | ✅ Completo | CBV custom con mensaje de éxito |
| Password reset por email | ✅ Completo | 4 pasos, simulado en DEBUG |
| Password reset por admin | ⚠️ Funcional con bug crítico | Contraseña hardcodeada — ver B4 |
| Edición de perfil (phone, avatar) | ❌ No implementado | Sin vista ni form de edición post-registro |
| Admin Django (`admin.py`) | ❌ No registrado | Sin fieldsets propios para User |
| Tests | ⚠️ Parcial | `tests.py` existe (212 líneas) — cobertura real por verificar |
| Documentación | ✅ Esta sesión | Primera documentación formal |

---

## Arquitectura de Datos

### Jerarquía y dependencias

```
AbstractUser (Django built-in)
    └── accounts.User
            ├── + phone       (CharField)
            ├── + avatar      (ImageField → MEDIA_ROOT/avatars/)
            ├── + created_at  (DateTimeField auto)
            └── + updated_at  (DateTimeField auto)

AUTH_USER_MODEL = 'accounts.User'
    │
    ├── events.Project.host         (FK)
    ├── events.Task.host            (FK)
    ├── events.Event.host           (FK)
    ├── events.InboxItem.created_by (FK)
    ├── analyst.StoredDataset.created_by (FK)
    ├── analyst.Report.created_by   (FK)
    ├── sim.SimAccount.created_by   (FK)
    ├── kpis.CallRecord.created_by  (FK)
    ├── bitacora.BitacoraEntry.created_by (FK)
    ├── courses.Course.created_by   (FK)
    ├── cv.Curriculum.created_by    (FK)
    ├── rooms.Room.owner            (FK)
    ├── simcity.Game.created_by     (FK)
    └── ... (todas las apps del proyecto)
```

### Convenciones de PK

`accounts.User` hereda el `AutoField` int de `AbstractUser`. **No tiene UUID.** Esta es la única excepción aceptada a nivel de Django — no se puede cambiar sin reescribir todas las FKs del proyecto.

---

## Roadmap

### Deuda inmediata (pre-Sprint 8)

| ID | Tarea | Prioridad |
|----|-------|-----------|
| ACC-1 | Eliminar `"DefaultPassword123"` hardcodeado — usar `get_random_string(12)` o variable de entorno | 🔴 |
| ACC-2 | Validar `next` en `login_view` con `url_has_allowed_host_and_scheme` | 🔴 |
| ACC-3 | Declarar `app_name = 'accounts'` en `urls.py` | 🟠 |
| ACC-4 | Eliminar import muerto `file_tree_view` en `views.py` | 🟠 |
| ACC-5 | Agregar `@login_required` o `@require_POST` a `logout_view` | 🟠 |

### Sprint 8 — Funcionalidades faltantes

| ID | Tarea | Prioridad |
|----|-------|-----------|
| ACC-6 | Implementar vista de edición de perfil (phone, avatar) | 🟠 |
| ACC-7 | Registrar `User` en Django Admin con fieldsets custom | 🟡 |
| ACC-8 | Resolver user enumeration en `CustomPasswordResetView` | 🟠 |
| ACC-9 | Agregar `unique=True` a `User.email` + migración | 🟠 |

### Sprint 9 — Optimización y seguridad

| ID | Tarea | Prioridad |
|----|-------|-----------|
| ACC-10 | Mover `anonymous_required` a `core/decorators.py` | 🟡 |
| ACC-11 | Internacionalizar mensajes de error (actualmente en inglés) | 🟡 |
| ACC-12 | Verificar y completar cobertura de `tests.py` | 🟡 |
| ACC-13 | Considerar campos adicionales al User para WFM: `role`, `department`, `team` | 🟡 |

---

## Notas para Claude

- **`accounts.User` tiene PK int** (AutoField heredado) — NO usar `<uuid:pk>` en ningún contexto de esta app
- **`AUTH_USER_MODEL = 'accounts.User'`** — todas las FK a User en otras apps DEBEN usar `settings.AUTH_USER_MODEL` en models.py
- **`accounts` migra PRIMERO** — siempre antes que cualquier otra app; si falla, todo el proyecto falla
- **`DEBUG=True` suprime emails** — el password reset solo loguea en consola en desarrollo; no hay email real
- **`app_name` no está en `urls.py`** — el namespace `accounts:` viene del `include()` en el urls.py raíz; no cambiar ese include sin verificar todos los `{% url 'accounts:...' %}`
- **`reset_to_default_password` es un método de instancia de CBV**, no un endpoint independiente — se llama vía `admin_password_reset` con `re_path`, pero la vista base es `CustomPasswordResetView`, no esta función específica; el routing es confuso
- **No hay `admin.py`** — si se crea, usar `UserAdmin` de `django.contrib.auth.admin` como base para no perder funcionalidades nativas
- **`file_tree_view`** importado en `views.py` pero nunca usado — ignorarlo, no llamarlo
