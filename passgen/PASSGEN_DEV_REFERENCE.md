# Referencia de Desarrollo — App `passgen`

> **Actualizado:** 2026-03-20 (Sesión Analista Doc — documentación completa)
> **Audiencia:** Desarrolladores del proyecto y asistentes de IA (Claude)
> **Stats:** 12 archivos · generators.py 428 L · views.py 95 L · forms.py 49 L
> **Namespace:** ❌ NO declarado — violación de convención

---

## Índice

| # | Sección | Contenido |
|---|---------|-----------|
| 1 | Resumen | Qué hace la app |
| 2 | `PasswordGenerator` | Motor de generación — API completa |
| 3 | Formularios | `PasswordForm` |
| 4 | Vistas | `generate_password`, `password_help` |
| 5 | URLs | Mapa completo |
| 6 | Sistema de patrones | Sintaxis, predefinidos, componentes |
| 7 | Convenciones críticas y violaciones | Gotchas |
| 8 | Bugs conocidos | Tabla con estado |
| 9 | Deuda técnica | Clasificada por prioridad |

---

## 1. Resumen

La app `passgen` implementa un **generador de contraseñas seguras basado en patrones**. El núcleo es `PasswordGenerator` (428 líneas en `generators.py`) que usa `secrets.SystemRandom` (CSPRNG) para generar contraseñas compuestas de componentes configurables: letras minúsculas/mayúsculas (con acentos opcionales), números, símbolos, sílabas pronunciables y fechas.

Sin modelos. Sin base de datos. Las contraseñas se generan en memoria y no se almacenan.

---

## 2. `PasswordGenerator`

Clase principal — instanciada en cada request.

### Conjuntos de caracteres

| Atributo | Contenido |
|----------|-----------|
| `LOWERCASE` | `a-z` + `ñ` |
| `UPPERCASE` | `A-Z` + `Ñ` |
| `ACCENTED_LOWER` | `áéíóúñ` |
| `ACCENTED_UPPER` | `ÁÉÍÓÚÑ` |
| `SYMBOLS` | `!@#$%^&*()_+-=[]{}|;:,.<>?` |
| `NUMBERS` | `0-9` |
| `PRONOUNCEABLE_SYLLABLES` | 20 sílabas: `ba`, `be`, `bi`, ... `fu` |

### Componentes disponibles

| Símbolo | Método | Parámetros | Descripción |
|---------|--------|-----------|-------------|
| `a` | `_lowercase(length, accents)` | `length=4`, `accents=0` | Minúsculas + acentos opcionales |
| `A` | `_uppercase(length, accents)` | `length=4`, `accents=0` | Mayúsculas + acentos opcionales |
| `!` | `_symbols(length)` | `length=1` | Símbolos |
| `x` | `_numbers(length)` | `length=2` | Números |
| `d` | `_date(format)` | `format='ymd'` | Fecha actual (`ymd`/`dmy`/`mdy`) |
| `p` | `_pronounceable(length, complexity)` | `length=8`, `complexity=1` | Sílabas pronunciables |

### Métodos públicos

**`generate(pattern: str) → dict`**

Genera contraseña desde patrón. Retorna:
```python
{
    'password': str,
    'entropy': float,    # bits de entropía
    'strength': str,     # 'Baja'/'Media'/'Alta'/'Muy Alta'
    'length': int,
    'pattern': str
}
```
Lanza `ValueError` si el patrón es inválido, la contraseña es muy corta/larga, o tiene baja entropía.

**`generate_pronounceable(length, complexity) → dict`** — genera contraseña pronunciable directamente.

**`calculate_entropy(password) → float`** — entropía en bits basada en diversidad de caracteres × longitud.

**`estimate_strength(password) → str`** — scoring por longitud + diversidad + entropía - penalización por patrones comunes.

**`get_context_data() → dict`** — datos para templates: `demo_password`, `predefined_patterns` (lista con ejemplos generados), `categories`.

**`get_pattern_choices() → list[tuple]`** — opciones para select/radio: `[(key, descripción), ..., ('custom', 'Personalizado')]`.

### Patrones predefinidos

| Key | Pattern | Descripción | Fortaleza | Entropía estimada |
|-----|---------|-------------|-----------|-------------------|
| `basic` | `a:4|x:3|!:1` | Letras + números + símbolo | Media | 45 bits |
| `strong` | `A:3|a:3|!:2|x:2` | Mayús+minús+símbolos+núms | Alta | 60 bits |
| `pin` | `x:6` | PIN numérico | Baja | 20 bits |
| `phrase` | `p:3|x:2` | Pronunciable + números | Media | 35 bits |
| `secure` | `A:3:1|a:3:1|!:2|x:2|!:1` | Máx seguridad + acentos | Muy Alta | 75 bits |
| `date_based` | `a:2|d:ymd|!:1` | Fecha + letras + símbolo | Media | 40 bits |
| `accented` | `a:3:1|A:2:1|x:2` | Con acentos obligatorios | Alta | 55 bits |

⚠️ **Bug crítico #98**: `_validate_password()` exige `MIN_ENTROPY = 60 bits`. Los patrones `pin` (~20 bits), `phrase` (~35 bits), `basic` (~45 bits), `date_based` (~40 bits) y `accented` (~55 bits) **siempre fallan la validación** → `ValueError: Password entropy too low`.

### Seguridad

- **CSPRNG**: `secrets.SystemRandom()` — criptográficamente seguro.
- **`BANNED_CHARS`**: `'"\\`\`` — excluidos de cualquier contraseña.
- **`COMMON_PATTERNS`**: `['123', 'abc', 'qwe', 'asd', 'password', 'admin', 'qwerty']` — penalizados en strength, bloquean si `_has_common_patterns()` retorna True.
- **Límites**: longitud 8–64, entropía mínima 60 bits.

---

## 3. Formularios

### `PasswordForm`

Form dinámico — los choices de `pattern_type` se generan desde `PasswordGenerator().get_pattern_choices()` en `__init__`.

| Campo | Tipo | Widget | Notas |
|-------|------|--------|-------|
| `pattern_type` | `ChoiceField` | `RadioSelect` | Choices dinámicos desde `PREDEFINED_PATTERNS` + `'custom'` |
| `custom_pattern` | `CharField(required=False)` | `TextInput` | Patrón personalizado libre |
| `include_accents` | `BooleanField(required=False)` | `CheckboxInput` | Aplica acentos al patrón |
| `length` | `IntegerField(4–64, initial=12)` | — | ⚠️ **Definido pero nunca usado en views.py** |
| `exclude_ambiguous` | `BooleanField(required=False)` | — | ⚠️ **Definido pero nunca usado en views.py** |

⚠️ Los campos `length` y `exclude_ambiguous` están declarados a nivel de clase pero `generate_password` nunca los lee — son campos muertos.

---

## 4. Vistas

**Sin `@login_required`** — ambas vistas son públicas. ⚠️ Cualquier usuario no autenticado puede acceder.

### 4.1 `generate_password`

**URL:** `GET|POST /passgen/generate/`  
**Template:** `passgen/generar.html`

`GET` — renderiza el form vacío con `generator` en contexto.  
`POST` — valida form, obtiene el patrón (predefinido o custom), aplica acentos si `include_accents`, llama a `generator.generate(pattern)` y pasa resultado al template.

**Contexto:** `form`, `generator`, `generated_password` (dict o None), `pattern_used`, `pattern_name`.

**`apply_accents_to_pattern(pattern)`** — helper local en `views.py`. Transforma partes `a:N` → `a:N:1` y `A:N` → `A:N:1` para activar acentos.

---

### 4.2 `password_help`

**URL:** `GET /passgen/help/`  
**Template:** `passgen/info.html`

Llama a `generator.get_context_data()` y añade `modal_title` y `pattern_categories`.

⚠️ **Bug #96**: `get_context_data()` referencia `self.CATEGORIES` que **no está definido** en `PasswordGenerator` → `AttributeError` al acceder a esta vista.

---

## 5. URLs

| Pattern | Name | Vista | Auth |
|---------|------|-------|------|
| `/passgen/generate/` | `generate_password` | `generate_password` | ❌ Público |
| `/passgen/help/` | `password_help` | `password_help` | ❌ Público |

⚠️ **Sin `app_name`** en `urls.py` — namespace no declarado. Para referenciar URLs usar el nombre directo: `reverse('generate_password')`, no `reverse('passgen:generate_password')`.

---

## 6. Sistema de Patrones — Sintaxis

```
patron := componente ("|" componente)*
componente := simbolo ":" param1 (":" param2)?

Ejemplos:
  a:4         → 4 letras minúsculas sin acentos
  a:4:1       → 4 letras minúsculas, mínimo 1 acento
  A:3         → 3 letras mayúsculas
  A:3:2       → 3 mayúsculas, mínimo 2 con acento
  !:2         → 2 símbolos
  x:3         → 3 números
  d:ymd       → fecha en formato YYYYMMDD
  d:dmy       → fecha en formato DDMMYYYY
  p:6         → 6 caracteres pronunciables, complejidad 1
  p:6:2       → 6 caracteres pronunciables, complejidad 2

Patrón completo:
  A:3:1|a:3:1|!:2|x:2  → secure
```

**Complejidad en `p` (pronounceable):**
- `complexity=1` → capitaliza letra aleatoria
- `complexity=2` → + agrega un número
- `complexity=3` → + agrega un símbolo

---

## 7. Convenciones Críticas y Violaciones

| Convención | Estándar | Estado en `passgen` |
|------------|----------|---------------------|
| Namespace | `app_name = 'x'` | ❌ No declarado |
| `@login_required` | todas las vistas | ❌ Ninguna vista tiene auth |
| Modelos | — | N/A — sin modelos |
| UUID PK | — | N/A — sin modelos |

---

## 8. Bugs Conocidos

| # | Estado | Descripción | Impacto |
|---|--------|-------------|---------|
| **#95** | ⬜ | Sin `app_name` en `urls.py` — namespace no declarado | Bajo |
| **#96** | ⬜ | `get_context_data()` referencia `self.CATEGORIES` no definido → `AttributeError` en `password_help` | **Alto — runtime, rompe la vista** |
| **#97** | ⬜ | `PasswordForm.length` y `exclude_ambiguous` definidos pero nunca leídos en `generate_password` | Medio — funcionalidad prometida no implementada |
| **#98** | ⬜ | `_validate_password()` exige `MIN_ENTROPY=60` bits — los patrones `pin`, `phrase`, `basic`, `date_based`, `accented` siempre fallan → `ValueError` | **Alto — runtime, 5 de 7 patrones predefinidos no funcionan** |
| #99 | ⬜ | `generate_password` y `password_help` sin `@login_required` — acceso público no autenticado | Bajo (puede ser intencional) |

---

## 9. Deuda Técnica

### Alta prioridad (bloquea funcionalidad)
- **Bug #96** — definir `self.CATEGORIES` en `PasswordGenerator.__init__` o eliminar la referencia en `get_context_data()`.
- **Bug #98** — la solución más simple es bajar `MIN_ENTROPY` a un valor razonable por patrón, o eliminar la validación de entropía mínima global. Alternativa: ajustar los patrones `pin`, `phrase`, `basic` para que generen más entropía.

### Media prioridad
- **Bug #97** — implementar `length` y `exclude_ambiguous` en `generate_password`, o eliminar los campos del form.
- **Bug #95** — agregar `app_name = 'passgen'` en `urls.py`.
- **Bug #99** — decidir si la app debe ser pública o protegida y aplicar `@login_required` según corresponda.

### Baja prioridad
- Agregar más sílabas pronunciables (20 es muy limitado — genera contraseñas repetitivas).
- Implementar `exclude_ambiguous` real (eliminar `1`, `l`, `I`, `0`, `O` de los charsets).
- Tests — sin tests.
