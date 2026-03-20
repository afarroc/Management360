# PROMPT — Sesión Analista Doc · Management360

> **Cómo usar:** Pega este archivo completo al inicio de una nueva conversación con Claude.
> Luego indica la app a documentar y sube los archivos fuente.
> **Rol:** Technical Writer + Arquitecto · Documentación técnica
> **Foco:** UNA o DOS apps relacionadas · Entregables: DEV_REFERENCE + DESIGN

---

## Contexto del Proyecto

Proyecto **Management360** — SaaS de Workforce Management / Customer Experience.
**Stack:** Django 5.1.7 · Python 3.13 · MariaDB 12.2.2 · Redis 7 · Bootstrap 5 + HTMX · Django Channels · Centrifugo · Ollama (IA local)
**Entorno:** Termux / Android 15
**20 apps** · ~710 archivos Python+HTML
**Documentadas:** 11/20 — `analyst`, `sim`, `bitacora`, `simcity`, `events`, `accounts`, `core`, `memento`, `chat`, `rooms`, `courses`

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

Sigue este esquema (ver `ACCOUNTS_DEV_REFERENCE.md` o `CHAT_DEV_REFERENCE.md` como referencias de calidad):

```
# Referencia de Desarrollo — App `nombre`
> Actualizado / Audiencia / Stats

## Índice (tabla de secciones)
## 1. Resumen (qué hace la app, sus pilares)
## 2. Modelos (todos, con campos clave y relaciones)
## 3. Formularios (si existen)
## 4. Vistas (organización por módulo, responsabilidades)
## 5. URLs (mapa agrupado por función)
## 6. Convenciones críticas (gotchas, campos especiales)
## 7. [Sección específica si aplica — ej: "Sistema GTD", "CMS", "Navegación 3D", etc.]
## 8. Bugs conocidos (tabla con estado)
## 9. Deuda técnica (alta/media/baja prioridad)
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

## Convenciones del proyecto — verificar siempre

| Convención | Estándar | Excepciones conocidas (todas auditadas) |
|------------|----------|----------------------------------------|
| PK | `UUIDField(primary_key=True)` | `events` (int), `simcity` (AutoField int) |
| Propietario | `created_by` | ver tabla completa abajo |
| Timestamps | `created_at` / `updated_at` | `bitacora` (en español) |
| Soft delete | `is_active` | donde aplica |
| Namespace | `app_name = 'x'` en `urls.py` | `core`, `events`, `memento` no lo declaran (vienen del include externo) |
| User import en models | `settings.AUTH_USER_MODEL` | varios violan esto |
| JSON response | `{"success": true/false}` | — |
| `@csrf_exempt` | PROHIBIDO en POST con datos de usuario | `chat` (20+ endpoints), `core` — activo |

### Excepciones de propietario por app (tabla completa)

| App | Modelo(s) | Campo propietario | Nota |
|-----|-----------|-------------------|------|
| `events` | `Project`, `Task`, `Event` | `host` | NO `created_by` |
| `events` | `InboxItem` | `created_by` ✅ | Excepción dentro de la excepción |
| `rooms` | `Room` | `owner` + `creator` | `owner` = propietario real |
| `courses` | `Course` | `tutor` | NO `created_by` |
| `courses` | `Lesson` (standalone), `ContentBlock` | `author` | NO `created_by` |
| `courses` | `Enrollment` | `student` | NO `created_by` |
| `chat` | `Conversation`, `CommandLog`, `AssistantConfiguration` | `user` | NO `created_by` |
| `memento` | `MementoConfig` | `user` | NO `created_by` |
| `rooms` | `RoomNotification` | `created_by` ✅ | Sí cumple convención |

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

**Al finalizar cada app**, actualizar la tabla de bugs globales numerando desde el #68 (los #1–#67 ya están registrados en `PROJECT_DEV_REFERENCE.md`).

---

## App Asignada Esta Sesión

**App:** [NOMBRE DE LA APP]
**Archivos a subir:**
- `APP_CONTEXT.md` (generado por m360_map.sh — **obligatorio**)
- `models.py`
- `urls.py`
- `views.py` o `views/__init__.py`
- `forms.py` (si existe)

**Comando para generar CONTEXT:**
```bash
bash scripts/m360_map.sh app ./nombre_app
```

---

## Apps pendientes (prioridad sugerida)

| App | Prioridad | Motivo |
|-----|-----------|--------|
| `kpis` | 🔴 | DEV_REFERENCE parcial — completar |
| `cv` | 🔴 | Dependencia directa de `courses` |
| `bots` | 🔴 | Target Sprint 8 |
| `board` | 🟠 | Simple — 3 modelos |
| `campaigns` | 🟠 | Simple — 3 modelos |
| `help` | 🟡 | 7 modelos |
| `api` | 🟡 | 0 modelos, 4 endpoints |
| `passgen` | 🟡 | Muy simple |
| `panel` | 🟡 | 0 modelos, configuración |

---

## Archivos de contexto globales

Adjunta junto a este prompt:
- `PROJECT_DEV_REFERENCE.md` ← contiene bugs #1–#67, convenciones, patrones
- `PROJECT_DESIGN.md` ← roadmap global, sprints, dependencias entre apps
