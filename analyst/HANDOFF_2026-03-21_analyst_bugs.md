# HANDOFF — 2026-03-21 · App `analyst`
> Sesión completa: Bugs #1, #2, #3 — forms.py · file_processor_service.py · excel_processor.py · data_upload.py (verificación)

---

## Commits aplicados

| Hash | Mensaje |
|------|---------|
| `ef3678e7` | fix(analyst): Bugs #1 y #2 — process_excel firma rota + comentarios huérfanos |
| `4b7a0219` | fix(analyst): Bugs #1 #2 #3 — no_header huérfano + excel_processor limpieza |

---

## Qué se hizo

### Bug #1 — `forms.py` (cosmético)
El `clean_file()` duplicado ya no existía en esta versión.
Eliminados dos comentarios huérfanos `# analyst/forms.py` (líneas 38 y 201) producto de copypastes previos. Sin impacto funcional.

### Bug #2 — `file_processor_service.py` (crítico)
`process_excel()` había sido pegado desde `ExcelProcessor` sin adaptar. Tres bugs encadenados:

| Sub-bug | Problema | Fix |
|---------|----------|-----|
| 2a | `@staticmethod` — no podía llamar `cls._create_instances_*` | → `@classmethod` |
| 2b | Firma `(file, sheet_name, cell_range)` — `model` se asignaba a `sheet_name` en runtime | → firma completa con `model`, `column_mapping`, `no_header` |
| 2c | Retornaba `(df, metadata)` — `process_file()` esperaba `(records, preview_data, columns)` | → mismo pipeline que `process_csv` |

**Todo upload Excel fallaba silenciosamente desde el inicio del feature.**

### Bug #3 — `no_header` huérfano (feature nunca funcionó vía FileProcessorService)
`DataUploadForm` tiene `no_header = BooleanField` y `ExcelProcessor._read_with_range` lo soporta, pero el parámetro no se propagaba por la cadena de `FileProcessorService`.

Cadena corregida:
```
process_file(... no_header=False)        ← añadido
    → process_excel(... no_header=False)  ← añadido
        ├── con cell_range → _read_with_range(... no_header)   ✅ ya existía
        └── sin cell_range → pd.read_excel(header=None)        ✅ añadido
                              df.columns = ["Columna1", ...]
```

`excel_processor.py`: eliminado comentario huérfano `# analyst/services/excel_processor.py` dentro del cuerpo de la clase.

### Verificación `data_upload.py` (sin cambios)
La vista principal usa `ExcelProcessor.process_excel()` directamente — no pasa por `FileProcessorService`. El parámetro `no_header` ya estaba correctamente propagado en líneas 297, 299, 307, 312 y 350. **No requirió modificación.**

---

## Nota de arquitectura

`analyst` tiene dos rutas de procesamiento Excel paralelas:

| Ruta | Usada por | Retorna |
|------|-----------|---------|
| `ExcelProcessor.process_excel()` | `_handle_preview()` en `data_upload.py` | `(df, metadata)` |
| `FileProcessorService.process_excel()` | `process_file()` — entrada programática | `(records, preview, columns)` |

Ambas rutas tienen `no_header` propagado correctamente tras esta sesión.

---

## Archivos modificados

```
analyst/forms.py                            ← comentarios huérfanos eliminados
analyst/services/file_processor_service.py  ← process_excel reescrito
analyst/services/excel_processor.py         ← comentario huérfano eliminado
```

`data_upload.py` — revisado, sin cambios necesarios.

---

## Bugs analyst abiertos

**Ninguno.** App limpia para el sprint.

---

## Próximo paso sugerido

**REFACTOR-1** — `chat/views.py` 2017 líneas → dividir en módulos (sesión separada).
Archivos necesarios: `chat/views.py` · `CHAT_DEV_REFERENCE.md`.
