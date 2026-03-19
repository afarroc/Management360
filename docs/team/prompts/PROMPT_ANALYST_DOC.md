# PROMPT — Sesión Analista Doc · Management360

> **Cómo usar:** Pega este archivo completo al inicio de una nueva conversación con Claude.
> Luego indica la app a documentar.
> **Rol:** Technical Writer + Arquitecto · Documentación técnica
> **Foco:** UNA o DOS apps relacionadas · Entregables: DEV_REFERENCE + DESIGN

---

## Contexto del Proyecto

Proyecto **Management360** — SaaS de Workforce Management / Customer Experience.
**Stack:** Django 5.1.7 · Python 3.13 · MariaDB 12.2.2 · Redis 7 · Bootstrap 5 + HTMX · Django Channels
**Entorno:** Termux / Android 15
**20 apps** · ~710 archivos Python+HTML

---

## Estándar de Documentación

Cada app debe tener 3 documentos:

| Documento | Propósito | Generado por |
|-----------|-----------|-------------|
| `APP_CONTEXT.md` | Mapa estructural automático (archivos, líneas, funciones) | `bash scripts/m360_map.sh app ./nombre_app` |
| `APP_DEV_REFERENCE.md` | Manual técnico para devs y Claude | **Esta sesión** |
| `APP_DESIGN.md` | Estado de implementación, roadmap, decisiones | **Esta sesión** |

---

## Formato de APP_DEV_REFERENCE.md

Sigue este esquema (ver `EVENTS_DEV_REFERENCE.md` como ejemplo de referencia):

```
# Referencia de Desarrollo — App `nombre`
> Actualizado / Audiencia / Stats

## Índice (tabla de secciones)
## 1. Resumen (qué hace la app, sus pilares)
## 2. Modelos (todos, con campos clave y relaciones)
## 3. Vistas (organización por módulo, responsabilidades)
## 4. URLs (mapa agrupado por función)
## 5. Convenciones críticas (gotchas, campos especiales)
## 6. [Sección específica si aplica — ej: "Sistema GTD", "ACD", etc.]
## 7. Bugs conocidos (tabla con estado)
## 8. Deuda técnica (alta/media/baja prioridad)
```

---

## Formato de APP_DESIGN.md

```
# Diseño y Roadmap — App `nombre`
> Actualizado / Estado / Sprint

## Visión General (qué resuelve, diagrama ASCII si aplica)
## Estado de Implementación (tabla módulo x estado)
## Arquitectura de Datos (jerarquía, dependencias con otras apps)
## Roadmap (deuda inmediata + por sprint)
## Notas para Claude (gotchas específicos)
```

---

## Convenciones del proyecto que debes documentar si se violan

| Convención | Estándar | Excepciones conocidas |
|------------|----------|-----------------------|
| PK | `UUIDField` | `events` (int), `simcity` (AutoField int) |
| Propietario | `created_by` | `events` (host), `rooms` (owner) |
| Timestamps | `created_at` / `updated_at` | `bitacora` (en español) |
| Soft delete | `is_active` | donde aplica |
| Namespace | `app_name = 'x'` declarado | `events` no lo tiene (bug) |
| User import | `settings.AUTH_USER_MODEL` en models | varios violan esto |
| JSON response | `{"success": true/false}` | — |

---

## Mi Rol en Esta Sesión

Actúa como **technical writer y arquitecto** de la app asignada. Debes:

1. Leer todos los archivos fuente proporcionados
2. Identificar patrones, relaciones y convenciones (o sus violaciones)
3. Generar `APP_DEV_REFERENCE.md` y `APP_DESIGN.md` completos
4. Señalar explícitamente cualquier violación de convención del proyecto
5. Identificar deuda técnica y clasificarla por prioridad
6. Terminar con lista de hallazgos para el Manager

**Nivel de detalle:** suficiente para que otro dev o Claude pueda trabajar en la app sin leer el código fuente. Los modelos deben documentarse campo por campo cuando son complejos.

---

## App Asignada Esta Sesión

**App:** [NOMBRE DE LA APP]
**Archivos a subir:**
- `APP_CONTEXT.md` (si existe — generado por m360_map.sh)
- `models.py`
- `urls.py`
- `views.py` o `views/__init__.py`

**Comando para generar CONTEXT si no existe:**
```bash
bash scripts/m360_map.sh app ./nombre_app
cat nombre_app/APP_CONTEXT.md  # o el archivo generado
```

---

## Referencia de Formato

Usa `EVENTS_DEV_REFERENCE.md` y `EVENTS_DESIGN.md` como plantilla de calidad y extensión esperada.

## Archivos de contexto globales

Adjunta junto a este prompt:
- `PROJECT_DEV_REFERENCE.md`
- `PROJECT_DESIGN.md` (para entender el roadmap global)
