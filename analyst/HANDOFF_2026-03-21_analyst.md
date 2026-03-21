# HANDOFF — 2026-03-21 · App `analyst`
> Tarea: EVENTS-AI-3 — Completar integración Events/GTD (backend ya existía, fixes de bugs + UI dashboard)

---

## Qué se hizo

### Bugs corregidos (6/6)

| # | Archivo | Descripción | Tipo |
|---|---------|-------------|------|
| B-1 | `views/dashboard.py` L215-216 | `_load_df._EVENTS_MAP`: `start_date`→`created_at` (Project), `start_time`→`created_at` (Event). Causaba `FieldError` en runtime al renderizar cualquier widget events:projects o events:events | 🔴 Runtime crash |
| B-2 | `views/etl_manager.py` `_source_row()` | Añadido `"events_model": getattr(src,'events_model','') or ''`. Sin esto el JS no podía identificar fuentes events ni activar el tab correcto al editar | 🔴 Data loss |
| T-1 | `templates/analyst/etl_manager.html` `_EVENTS_DATE_HINTS` | Los 4 hints apuntaban a campos incorrectos o inexistentes. Corregidos a: `inbox→due_date`, `tasks/projects/events→created_at` con nota explicativa | 🟠 UI falsa |
| T-2 | `templates/analyst/etl_manager.html` L470 | `get_events_model_display` llamado sobre CharField sin `choices` → probable `AttributeError`. Reemplazado por lookup inline con if/elif | 🟠 Probable crash |
| T-3 | `templates/analyst/etl_manager.html` sim section | Labels y texto de ayuda decían "started_at" → corregidos a "fecha" (campo real de `sim.Interaction`) | 🟡 UI falsa |
| T-4 | `templates/analyst/dashboard.html` | Fuente `events` completamente ausente del modal de widgets. Añadidos: `<option value="events">` en select, `events_sources` en `SOURCES`, branch `events` en `onSrcTypeChange()` y `onSrcRefChange()` | 🔴 Feature ausente |

---

## Archivos entregados

```
analyst/views/dashboard.py
analyst/views/etl_manager.py
analyst/templates/analyst/etl_manager.html
analyst/templates/analyst/dashboard.html
```

Copiar con:
```bash
cp ~/HANDOFF_outputs/dashboard.py     analyst/views/dashboard.py
cp ~/HANDOFF_outputs/etl_manager.py   analyst/views/etl_manager.py
cp ~/HANDOFF_outputs/etl_manager.html analyst/templates/analyst/etl_manager.html
cp ~/HANDOFF_outputs/dashboard.html   analyst/templates/analyst/dashboard.html
```

---

## Estado de EVENTS-AI-3

| Capa | Estado |
|------|--------|
| `_extract_events_items()` — pipeline de extracción | ✅ |
| `_events_item_fields()` — introspección | ✅ |
| `_run_extraction()` dispatch | ✅ |
| `etl_source_save()` — guardar fuente events | ✅ |
| `etl_source_run()` — ejecutar con runtime_params | ✅ |
| `etl_models_api()` — expone `events_models` con fields | ✅ |
| `_source_row()` — serializa `events_model` | ✅ (fix B-2) |
| `_load_df()` fuente `events` en dashboard | ✅ (fix B-1) |
| Modal widget dashboard — selector fuente events | ✅ (fix T-4) |
| Template ETL — tab Events/GTD, hints, labels | ✅ (fixes T-1,T-2,T-3) |

**EVENTS-AI-3 completo end-to-end.**

---

## Bugs conocidos preexistentes (NO tocados esta sesión)

| # | Archivo | Descripción |
|---|---------|-------------|
| 1 | `forms.py` | `clean_file()` definido dos veces — Python usa la segunda. Eliminar la primera |
| 2 | `services/file_processor_service.py` | `process_excel()` referencia `ExcelProcessor._read_with_range()` posiblemente fuera de scope |

---

## Próximo paso sugerido

**EVENTS-AI-3 (parte 3)** — "GTD Overview" dashboard:
- Crear en UI un dashboard predefinido con widgets events (inbox pendiente, tasks backlog, projects activos)
- Requiere: `dashboard.html` + `dashboard.py`

O bien escalar a **Dashboard ACD widget** (ya tiene backend en `dashboard.py` branch `acd`, template ya tiene `acd_sessions_json`).

---

## Comando de commit

```bash
git add analyst/views/dashboard.py \
        analyst/views/etl_manager.py \
        analyst/templates/analyst/etl_manager.html \
        analyst/templates/analyst/dashboard.html

git commit -m "fix(analyst): EVENTS-AI-3 — 6 bugs corrección UI+backend

- dashboard.py: _load_df Project/Event usaban start_date/start_time inexistentes → created_at
- etl_manager.py: _source_row faltaba events_model → JS no podía editar fuentes events
- etl_manager.html: _EVENTS_DATE_HINTS con campos incorrectos, get_events_model_display sin choices,
  sim section con started_at en lugar de fecha
- dashboard.html: fuente events completamente ausente del modal de widgets (select, SOURCES, handlers)

Sprint 9 · EVENTS-AI-3 end-to-end completado"
```
