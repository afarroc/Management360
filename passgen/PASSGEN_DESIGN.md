# Diseño y Roadmap — App `passgen`

> **Actualizado:** 2026-03-20 (Sesión Analista Doc)
> **Estado:** Parcialmente roto — 5 de 7 patrones predefinidos fallan en runtime
> **Fase del proyecto:** Utilidad independiente
> **Migraciones:** N/A — sin modelos

---

## Visión General

Generador de contraseñas basado en patrones configurables. Sin persistencia — las contraseñas se generan en memoria y se muestran al usuario. El corazón de la app es `PasswordGenerator` en `generators.py` (428 líneas), que implementa un parser de patrones y múltiples métodos de generación con CSPRNG (`secrets`).

```
Usuario
  │ POST pattern_type + custom_pattern + include_accents
  ▼
generate_password (view)
  │
  ▼
PasswordGenerator.generate(pattern)
  ├── _parse_pattern()  → tokens
  ├── [_lowercase / _uppercase / _symbols / _numbers / _date / _pronounceable]
  ├── _validate_password()  ← ⚠️ MIN_ENTROPY=60 bloquea 5/7 patrones
  └── {'password', 'entropy', 'strength', 'length'}
  │
  ▼
Template: contraseña + métricas
```

---

## Estado de Implementación

| Componente | Estado | Notas |
|-----------|--------|-------|
| `PasswordGenerator` — motor | ✅ Funcional | CSPRNG · parser de patrones · métricas |
| Patrón `strong` | ✅ Funciona | Entropía suficiente |
| Patrón `secure` | ✅ Funciona | — |
| Patrón `pin` | ❌ Roto | Entropía ~20 bits < MIN_ENTROPY 60 (#98) |
| Patrón `phrase` | ❌ Roto | Entropía ~35 bits (#98) |
| Patrón `basic` | ❌ Roto | Entropía ~45 bits (#98) |
| Patrón `date_based` | ❌ Roto | Entropía ~40 bits (#98) |
| Patrón `accented` | ❌ Roto | Entropía ~55 bits (#98) |
| Patrón custom | ✅ Funciona | Si entropía ≥ 60 bits |
| Vista `generate_password` | ✅ Funcional | POST genera correctamente si patrón no falla |
| Vista `password_help` | ❌ Rota | `AttributeError: CATEGORIES` (#96) |
| Campo `length` del form | ❌ Sin uso | Definido, nunca leído (#97) |
| Campo `exclude_ambiguous` | ❌ Sin uso | Definido, nunca leído (#97) |
| Namespace | ❌ No declarado | (#95) |
| `@login_required` | ❌ Ausente | Vistas públicas (#99) |
| Tests | ❌ Sin tests | — |

---

## Arquitectura

Sin modelos. Sin dependencias de otras apps. App completamente autónoma.

```
passgen/
  generators.py    ← PasswordGenerator (motor completo)
  forms.py         ← PasswordForm (dinámico desde generator)
  views.py         ← 2 vistas funcionales
  urls.py          ← 2 URLs (sin namespace)
```

---

## Roadmap — Sprint 9

| ID | Tarea | Prioridad | Notas |
|----|-------|-----------|-------|
| PG-1 | Fix `CATEGORIES` en `PasswordGenerator` (Bug #96) — desbloquea `password_help` | 🔴 | 1 línea de fix |
| PG-2 | Fix `MIN_ENTROPY` — bajar a 20 o validar por patrón (Bug #98) — desbloquea 5 patrones | 🔴 | — |
| PG-3 | Implementar `length` y `exclude_ambiguous` en `generate_password` (Bug #97) | 🟠 | — |
| PG-4 | Agregar `app_name = 'passgen'` en `urls.py` (Bug #95) | 🟡 | 1 línea |
| PG-5 | Decidir y aplicar política de auth (`@login_required` o público) (Bug #99) | 🟡 | — |

### Fixes rápidos (< 5 min cada uno)

```python
# Fix #95 — urls.py
app_name = 'passgen'

# Fix #96 — generators.py __init__
self.CATEGORIES = {
    'Básico': ['basic', 'pin', 'phrase'],
    'Seguro': ['strong', 'secure'],
    'Especiales': ['accented', 'date_based'],
}

# Fix #98 — generators.py
self.MIN_ENTROPY = 20  # o eliminar la validación global de entropía
```

---

## Notas para Claude

- **Sin modelos** — `models.py` tiene solo 3 líneas (stub). No hay migraciones necesarias.
- **`PasswordGenerator()` se instancia en cada request** — no es singleton, es stateless. Correcto para una app sin BD.
- **Solo `strong` y `secure` funcionan** actualmente — los demás patrones fallan por `MIN_ENTROPY=60`.
- **`generate()` retorna un dict**, no solo la contraseña — acceder como `result['password']`.
- **Sin namespace** — usar `reverse('generate_password')`, no `reverse('passgen:generate_password')`.
- **`apply_accents_to_pattern()`** está en `views.py`, no en `generators.py` — si se refactoriza, mover al generador.
- **`_safe_generate()`** en `generators.py` nunca lanza excepción — usarlo para ejemplos/demos, no para producción.
