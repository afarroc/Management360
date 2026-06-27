# Estado del proyecto Management360

**Fecha:** 2026-06-27T00:11-05:00  
**Rama:** `main`  
**Último commit:** `e2cd70d6` refactor: mover ALLOWED_HOSTS a .env

---

## Cambios pendientes (working tree)

| Archivo | Tipo | Estado | Notas |
|---------|------|--------|-------|
| `panel/settings.py` | Modificado | **Commiteado** | ALLOWED_HOSTS movido a .env |
| `.env` | Modificado | Sin commit (ignorado) | ALLOWED_HOSTS agregado |
| `api/views.py` | Modificado | Pendiente | Agrega publish_content |
| `api/urls.py` | Modificado | Pendiente | Agrega content/publish/ |
| `chat/views.py` | Modificado | Pendiente | Agrega ai_test endpoint |
| `chat/ollama_api.py` | Modificado | Pendiente | Cambios en integración Ollama |
| `courses/views.py` | Modificado | Pendiente | Plantillas público |
| `docs/HANDOFF_*.md` | Nuevos (4) | Pendiente | Documentación histórica |

## Hardcodeos eliminados

| Antes | Después |
|-------|---------|
| `ALLOWED_HOSTS` con IPs en `panel/settings.py` | `localhost,127.0.0.1,testserver` (default) |
| | IPs movidas a `.env` como `ALLOWED_HOSTS` |

## Hardcodeos restantes en .env (pendientes)

| Variable | Valor actual | Acción |
|----------|--------------|--------|
| `DATABASE_HOST` | `192.168.18.59` | Pendiente mover a variable de entorno |
| `OLLAMA_HOST` | `192.168.18.59` | Pendiente mover a variable de entorno |
| `OLLAMA_BASE_URL` | `http://192.168.18.59:11434` | Pendiente mover a variable de entorno |

## Acceso

- **Django check:** `python manage.py check` → OK (0 issues)
- **Servidor:** `python manage.py runserver` (puerto 8000)
- **Panel:** http://127.0.0.1:8000/
- **Proyecto M360 ID:** 60 (MementoBloom)
