# Changelog — Management360

## [Unreleased] — Estado actual (2026-06-27)

### Agregado
- Endpoint AI test en `chat/views.py` (útil para validar orquestación)
- Endpoint `publish_content` en `api/views.py`
- Plantillas públicas de cursos (preview público, bloques, detalle)
- Handoffs de MementoBloom integrados en `docs/` (arquitecto, creador, complete, vault)

### Modificado
- `api/urls.py`: rutas nuevas para `content/publish/`
- `api/views.py`: vista `publish_content`
- `chat/ollama_api.py`: ajustes en integración Ollama
- `chat/templates/chat/assistant.html`: actualizaciones UI
- `chat/urls.py`: ruta `ai_test`
- `courses/views.py`: soporte para plantillas público
- `courses/templates/*`: actualizaciones CMS y preview
- `panel/asgi.py`: ajustes de configuración

### Pendiente
- Eliminar `runserver.pid` (ignorar/limpiar)
- Revisar `static/informe_bitacora.html` (ignorar en git)
- Confirmar si los templates públicos se versionan o se excluyen
- API genérica `/api/v1/` (M360-1 a M360-4)

---

## 2026-06-27 — `4f07189d`
docs: estado del proyecto Management360

## 2026-06-27 — `e2cd70d6`
refactor: mover ALLOWED_HOSTS a .env

## 2026-03-22 — `81ecef7a`
docs: DEV_REFERENCEs y context actualizados — Sprint 9 cierre

## 2026-03-22 — `f56138db`
fix(events): evitar GenericForeignKey reverse en signal create_inbox_item_for_task
