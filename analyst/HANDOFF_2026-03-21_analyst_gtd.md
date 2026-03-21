# HANDOFF — 2026-03-21 · App `analyst`
> Sesión completa: EVENTS-AI-3 Parte 3 + Dashboard ACD widget UI

---

## Qué se hizo

### Bug corregido

| # | Archivo | Descripción | Tipo |
|---|---------|-------------|------|
| B-NEW | `views/dashboard.py` L214 | `_EVENTS_MAP['tasks']` order_field `due_date` → `created_at`. Task NO tiene due_date. FieldError en todo widget `events:tasks`. | 🔴 Runtime crash |

---

### EVENTS-AI-3 Parte 3 — GTD Overview (modal con preset editable)

**`dashboard.py`** — endpoint `POST /analyst/dashboards/gtd-overview/`:
- Lee `name`/`description` del body JSON (fallback a valores por defecto)
- Crea `Dashboard` + 6 `DashboardWidget` con layout predefinido (3 KPI fila 0, 2 tablas fila 1, 1 tabla fila 2)

**`dashboard.html`** — 4 cambios:
1. Botón toolbar `GTD` con `tip-teal` + `bi-kanban`
2. Modal `#modal-gtd` con tabla preview de los 6 widgets (sistema modal custom, no Bootstrap)
3. `URLS.gtdOverview` en el objeto constante
4. `openGtdOverviewModal()` + `submitGtdOverview()` — mismo patrón de re-render que `submitDashboard()`

---

### Dashboard ACD widget — UI completa

**`dashboard.html`** — 5 cambios adicionales:

| Cambio | Descripción |
|--------|-------------|
| `<div id="w-src-hint">` | Div hint contextual en el modal de widget (debajo del selector de referencia) |
| `_srcOptionLabel(type, s)` | Helper — labels ricos para ACD (`name [canal] · status`), genérico para el resto |
| `_SRC_TYPE_HINTS` | Objeto con hints estáticos para `acd`, `sim`, `events` |
| `onSrcTypeChange()` | Usa helper para labels + muestra hint estático + aviso si no hay fuentes |
| `onSrcRefChange()` | Para ACD: enriquece el hint con nombre, canal, status y preview de columnas |
| `openAddWidgetModal()` | Reset de `w-src-hint` al abrir el modal |

**Comportamiento resultante:**
- Al seleccionar tipo "Sesión ACD": dropdown muestra `Nombre [canal] · status` (distinguible)
- Hint: "📞 Sesión ACD — filas de ACDInteraction … Campo de fecha: routed_at"
- Al seleccionar una sesión específica: hint se actualiza con canal, status y preview de columnas
- Si no hay sesiones disponibles: aviso claro en lugar de dropdown vacío silencioso
- Mismo comportamiento de hints para `sim` y `events`

---

## Archivos entregados

```
analyst/views/dashboard.py          ← fix task due_date + endpoint GTD Overview
analyst/templates/analyst/dashboard.html  ← GTD modal + ACD widget UI
```

Solo falta añadir la ruta en `urls.py`:
```python
path('dashboards/gtd-overview/', dashboard.dashboard_gtd_overview, name='dashboard_gtd_overview'),
```

---

## Estado features

| Feature | Estado |
|---------|--------|
| EVENTS-AI-3 end-to-end | ✅ completo |
| Dashboard ACD widget — backend | ✅ (existente) |
| Dashboard ACD widget — UI | ✅ (esta sesión) |

---

## Bugs preexistentes abiertos (NO tocados)

| # | Archivo | Descripción |
|---|---------|-------------|
| 1 | `forms.py` | `clean_file()` definido dos veces — eliminar la primera. |
| 2 | `services/file_processor_service.py` | `process_excel()` referencia `ExcelProcessor._read_with_range()` fuera de scope. |

---

## Próximo paso sugerido

- **Bugs #1 y #2** — quick wins, <30 min combinados (no requieren archivos extra)
- **REFACTOR-1** — `chat/views.py` 2017 líneas → dividir en módulos

---

## Comando de commit

```bash
git add analyst/views/dashboard.py \
        analyst/templates/analyst/dashboard.html \
        analyst/urls.py

git commit -m "fix+feat(analyst): GTD Overview modal + ACD widget UI + task due_date fix

- dashboard.py: _EVENTS_MAP['tasks'] due_date → created_at (FieldError)
- dashboard.py: dashboard_gtd_overview() lee name/desc del body JSON
- dashboard.html: modal GTD Overview con preset editable (6 widgets)
- dashboard.html: _srcOptionLabel() — labels ricos para ACD [canal · status]
- dashboard.html: _SRC_TYPE_HINTS — hints contextuales acd/sim/events
- dashboard.html: onSrcTypeChange/onSrcRefChange enriquecidos para ACD
- urls.py: ruta dashboards/gtd-overview/

Sprint 9 · EVENTS-AI-3 completo · Dashboard ACD widget UI completo"
```
