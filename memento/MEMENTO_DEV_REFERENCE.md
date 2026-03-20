# Referencia de Desarrollo — App `memento`

> **Actualizado:** 2026-03-19  
> **Audiencia:** Desarrolladores y asistentes IA  
> **Archivos:** 17 | **Vistas:** 1 archivo (199 líneas) | **Templates:** 6 | **Endpoints:** 6  
> **Migraciones:** 7 aplicadas (`0001_initial` → `0007_alter_mementoconfig_death_date`)

---

## Índice

| Sección | Contenido |
|---------|-----------|
| 1. Resumen | Qué hace esta app |
| 2. Modelos | `MementoConfig` campo por campo |
| 3. Vistas | Función principal, helpers, CBVs |
| 4. Formularios | `MementoConfigForm` |
| 5. URLs | Mapa completo de endpoints |
| 6. Templatetags | `memento_filters` |
| 7. Convenciones críticas | Gotchas, flujos, patrones |
| 8. Bugs conocidos | Issues activos |
| 9. Deuda técnica | Clasificada por prioridad |

---

## 1. Resumen

`memento` es la app de **visualización de mortalidad** de Management360 — una implementación del concepto filosófico *Memento Mori* ("recuerda que vas a morir"). Permite al usuario configurar sus fechas de nacimiento y fallecimiento estimado para visualizar su vida como un calendario de unidades consumidas/restantes.

Sus responsabilidades son:

- **Configuración de fechas** — el usuario define `birth_date` y `death_date` estimada, guardadas en `MementoConfig`
- **Visualización trimodal** — tres vistas del mismo concepto: diaria (días), semanal (semanas), mensual (meses/años)
- **Modo temporal** — cualquier usuario (incluso anónimo) puede explorar la visualización sin guardar configuración
- **Cálculo de unidades de vida** — total / transcurridas / restantes en días, semanas y meses
- **Gestión de configuraciones múltiples** — un usuario puede tener varias configuraciones (distintas combinaciones de fechas)

La app tiene un CSS propio (`memento.css`) y templatetags propios (`memento_filters.py`), lo que la hace visualmente independiente del resto del proyecto.

---

## 2. Modelos

### `MementoConfig` — único modelo de la app

```python
class MementoConfig(models.Model):
    user               # FK → User (related: 'memento_configs')
    birth_date         # DateField — obligatorio
    death_date         # DateField — obligatorio, validado >= hoy
    preferred_frequency# CharField(10) — 'daily'|'weekly'|'monthly', default='monthly'
    created_at         # DateTimeField(auto_now_add=True)
    updated_at         # DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']
        unique_together = ('user', 'birth_date', 'death_date')
```

**Campos detallados:**

| Campo | Tipo | Obligatorio | Validación | Notas |
|-------|------|-------------|------------|-------|
| `user` | FK → User | Sí | CASCADE | Propietario de la configuración |
| `birth_date` | DateField | Sí | — | Fecha de nacimiento del usuario |
| `death_date` | DateField | Sí | `>= timezone.now().date()` | Fecha estimada de fallecimiento |
| `preferred_frequency` | CharField(10) | Sí | choices | `'daily'`, `'weekly'`, `'monthly'` |
| `created_at` | DateTimeField | Auto | auto_now_add | — |
| `updated_at` | DateTimeField | Auto | auto_now | Usado para obtener la config más reciente |

**Constraint `unique_together`:** un mismo usuario no puede tener dos configs con idénticas `birth_date` + `death_date`. Puede tener múltiples configs si varían las fechas (ej: distintos escenarios de expectativa de vida).

**⚠️ Violaciones de convención del proyecto:**
- Sin `id = UUIDField(primary_key=True)` — usa `BigAutoField` int. PKs referenciadas en URLs como `<int:pk>`
- Propietario en campo `user`, no `created_by` (excepción no documentada previamente en el proyecto)
- Sin `is_active` para soft delete

**⚠️ Bug en validador de `death_date`:**
```python
death_date = models.DateField(
    validators=[MinValueValidator(limit_value=timezone.now().date())]
)
```
`timezone.now().date()` se evalúa **en tiempo de importación del módulo**, no en tiempo de validación. El valor de "hoy" queda congelado en el momento en que Django carga la app. En un servidor de larga duración, este validador quedará desactualizado. Ver B1.

**Método `get_absolute_url()`:**
```python
def get_absolute_url(self):
    return reverse('memento', kwargs={
        'frequency': self.preferred_frequency,
        'birth_date': self.birth_date.strftime('%Y-%m-%d'),
        'death_date': self.death_date.strftime('%Y-%m-%d')
    })
```
Correcto — usa `reverse()` y el formato de fecha `'%Y-%m-%d'` que espera la URL.

**`__str__`:** `"Configuración de {username} (Nacimiento: {birth_date})"`

---

## 3. Vistas

### `memento(request, frequency, birth_date, death_date)` — Vista principal

La vista central de la app. Sin `@login_required` — funciona para usuarios autenticados y anónimos.

```python
def memento(request, frequency=None, birth_date=None, death_date=None):
```

**Flujo completo:**

```
1. Resolver parámetros
   ├── URL params (/<frequency>/<birth_date>/<death_date>/)
   └── GET params (?frequency=&birth_date=&death_date=)

2. ¿Faltan parámetros?
   ├── Usuario autenticado → busca última MementoConfig
   │     ├── Existe → redirect a 'memento' con sus fechas
   │     └── No existe → render date_selection.html (formulario vacío)
   └── Anónimo → render date_selection.html (formulario vacío)

3. Convertir y validar fechas
   ├── strptime('%Y-%m-%d') para birth_date y death_date
   ├── birth_date >= death_date → error en form
   ├── death_date <= date.today() → error en form
   └── Error → render date_selection.html con errores

4. ¿Guardar configuración?
   └── Solo si: request.user.is_authenticated AND POST.get('save_config') == 'true'
       → update_or_create(user, defaults={birth_date, death_date, frequency})

5. Calcular datos → calculate_memento_data()
6. Construir contexto → build_memento_context()
7. Render memento_mori.html
```

**Parámetros aceptados:**

| Parámetro | Fuente | Formato | Ejemplo |
|-----------|--------|---------|---------|
| `frequency` | URL o GET | string | `'daily'`, `'weekly'`, `'monthly'` |
| `birth_date` | URL o GET | `YYYY-MM-DD` | `'1990-05-15'` |
| `death_date` | URL o GET | `YYYY-MM-DD` | `'2070-05-15'` |

**`context['is_temporary']`:** `True` si el usuario no está autenticado o no envió `save_config=true`. Se usa en el template para mostrar avisos de modo temporal.

---

### `calculate_memento_data(birth_date, death_date)` → dict

Función helper pura (sin acceso a BD ni request). Calcula todas las métricas de vida.

```python
def calculate_memento_data(birth_date, death_date):
```

Usa `dateutil.relativedelta` para el cálculo de meses (maneja correctamente distintos largos de mes).

**Retorna:**

| Clave | Cálculo | Notas |
|-------|---------|-------|
| `total_days` | `(death_date - birth_date).days` | Días totales de vida |
| `passed_days` | `(today - birth_date).days` | Días vividos |
| `left_days` | `max(0, total - passed)` | Días restantes |
| `total_weeks` | `total_days // 7` | Semanas totales |
| `passed_weeks` | `passed_days // 7` | Semanas vividas |
| `left_weeks` | `max(0, total - passed)` | Semanas restantes |
| `total_months` | `years*12 + months` via relativedelta | Meses totales |
| `passed_months` | ídem desde birth a today | Meses vividos |
| `left_months` | `max(0, total - passed)` | Meses restantes |
| `total_years` | `relativedelta(death, birth).years` | Años totales de vida |

---

### `build_memento_context(frequency, birth_date, death_date, data)` → dict

Construye el contexto para `memento_mori.html` según la frecuencia. Incluye siempre un `base_context` y agrega las claves específicas de la frecuencia.

**Contexto base (todas las frecuencias):**

| Clave | Valor |
|-------|-------|
| `title` | `"Calendario de la Muerte"` (luego sobreescrito con prefijo de frecuencia) |
| `birth_date` | Fecha formateada `DD/MM/YYYY` |
| `death_date` | Fecha formateada `DD/MM/YYYY` |
| `total_years` | Int |
| `frequency` | `'daily'`/`'weekly'`/`'monthly'` |
| `current_date` | Hoy en `DD/MM/YYYY` |

**Claves adicionales por frecuencia:**

| Frecuencia | Claves extra |
|------------|-------------|
| `'daily'` | `total_days`, `passed_days`, `left_days` |
| `'weekly'` | `total_weeks`, `passed_weeks`, `left_weeks` |
| `'monthly'` | `total_months`, `passed_months`, `left_months`, `now: {year, month}` |

⚠️ Si `frequency` no es ninguno de los tres valores válidos, la función retorna solo el `base_context` sin claves de conteo. El template recibiría un contexto incompleto. Ver B2.

---

### `MementoConfigCreateView` — CBV de creación

```python
@method_decorator(login_required, name='dispatch')
class MementoConfigCreateView(CreateView):
    model = MementoConfig
    form_class = MementoConfigForm
    template_name = 'memento/date_selection.html'
    success_url = reverse_lazy('memento_default')
```

**Lógica custom en `form_valid`:**
- Verifica si ya existe una config con las mismas fechas para el usuario
- Si existe → redirige a `memento_update` (no crea duplicado)
- Si no → guarda y redirige a la visualización con las fechas recién guardadas

**`get_form_kwargs`:** pasa `user=request.user` al form para que `MementoConfigForm.clean()` pueda validar duplicados.

**`get_success_url`:** override que redirige a `'memento'` con las fechas del objeto recién creado, en lugar del `success_url` de clase (que iría a `memento_default`).

---

### `MementoConfigUpdateView` — CBV de edición

```python
@method_decorator(login_required, name='dispatch')
class MementoConfigUpdateView(UpdateView):
    model = MementoConfig
    form_class = MementoConfigForm
    template_name = 'memento/date_selection.html'
```

**⚠️ Sin verificación de propietario** — cualquier usuario autenticado que conozca el `pk` puede editar la config de otro usuario. No tiene `get_queryset` filtrado por `user=request.user`. Ver B3.

**`get_success_url`:** redirige a `'memento'` con las fechas actualizadas.

---

## 4. Formularios

### `MementoConfigForm`

```python
class MementoConfigForm(forms.ModelForm):
    save_config = forms.BooleanField(required=False, initial=True)

    class Meta:
        model  = MementoConfig
        fields = ['preferred_frequency', 'birth_date', 'death_date']
```

**Campo extra `save_config`:** checkbox no requerido. Cuando está desmarcado, el usuario puede explorar la visualización sin guardar la config en BD. Este campo no pertenece al modelo — se maneja en `memento()` vía `request.POST.get('save_config')`.

**`__init__`:** acepta `user=` via `kwargs.pop('user')` para la validación de duplicados en `clean()`. Si no se pasa `user`, la verificación de duplicados se omite silenciosamente.

**`clean()`:**
1. Valida que `death_date > birth_date`
2. Valida que `death_date > date.today()`
3. Si `user` fue pasado y no es instancia existente (`not self.instance.pk`) → verifica duplicados en BD

**Widgets:** `DateInput(type='date')` para ambas fechas — usa el selector nativo de HTML5. `form-control` y `form-select` de Bootstrap aplicados.

---

## 5. URLs

> **⚠️ Violación de convención:** `memento` **NO declara `app_name`** en `urls.py`. Sin namespace.

> **⚠️ Endpoint redundante:** `'memento_try'` (`/try/`) apunta exactamente a la misma vista y con los mismos parámetros que `'memento_default'` (`/`). Son idénticos funcionalmente. Ver B4.

> **⚠️ `LogoutView` propio:** la app registra su propio `logout` en `/memento/logout/`. Duplica la funcionalidad de `accounts:logout`. Ver B5.

| URL | Name | Vista | Auth | Método |
|-----|------|-------|------|--------|
| `/memento/` | `memento_default` | `memento` | ❌ | GET/POST |
| `/memento/try/` | `memento_try` | `memento` | ❌ | GET/POST |
| `/memento/config/create/` | `memento_create` | `MementoConfigCreateView` | ✅ | GET/POST |
| `/memento/config/update/<int:pk>/` | `memento_update` | `MementoConfigUpdateView` | ✅ | GET/POST |
| `/memento/view/<str:frequency>/<str:birth_date>/<str:death_date>/` | `memento` | `memento` | ❌ | GET |
| `/memento/logout/` | `memento_logout` | `LogoutView` | — | POST |

**Formato de parámetros en URL `memento`:**
- `frequency`: `daily` / `weekly` / `monthly`
- `birth_date`: `YYYY-MM-DD` (ej: `1990-05-15`)
- `death_date`: `YYYY-MM-DD` (ej: `2070-05-15`)

Ejemplo URL completa: `/memento/view/monthly/1990-05-15/2070-05-15/`

---

## 6. Templatetags — `memento_filters`

La app tiene su propio templatetag en `templatetags/memento_filters.py` (17 líneas). No se subió el archivo, pero por su tamaño y nombre probable contiene filtros de formato para los conteos (ej: formateo de números grandes, cálculo de porcentajes para barras de progreso).

Para usarlo en templates: `{% load memento_filters %}`.

---

## 7. Convenciones Críticas

### Formato de fechas en URL — siempre `YYYY-MM-DD`

```python
# CORRECTO — en toda la app
birth_date.strftime('%Y-%m-%d')   # para construir URLs
datetime.strptime(s, '%Y-%m-%d')  # para parsear desde URL

# El template debe construir URLs así:
{% url 'memento' frequency=config.preferred_frequency birth_date=config.birth_date|date:"Y-m-d" death_date=config.death_date|date:"Y-m-d" %}
```

### Fechas se muestran en `DD/MM/YYYY` en templates

```python
# build_memento_context formatea así para el template:
birth_date.strftime("%d/%m/%Y")  # display
```

### Propietario: `user`, no `created_by`

```python
# CORRECTO en memento
config = get_object_or_404(MementoConfig, pk=pk, user=request.user)

# INCORRECTO — no existe created_by en este modelo
```

### El campo `save_config` no es del modelo

Es un campo extra del form (`BooleanField` no requerido). Se lee desde `request.POST.get('save_config')` en la vista funcional, no desde `form.cleaned_data`. No confundir con campos del modelo.

### `update_or_create` en `memento()` — sin `birth_date`/`death_date` como lookup

```python
MementoConfig.objects.update_or_create(
    user=request.user,
    defaults={
        'birth_date': birth_date,
        'death_date': death_date,
        'preferred_frequency': frequency
    }
)
```

Este `update_or_create` busca por `user` solamente. Si el usuario ya tiene **cualquier** configuración, la sobreescribe con las nuevas fechas. No respeta el `unique_together`. Comportamiento diferente al de `MementoConfigCreateView` que sí verifica duplicados. Ver B6.

### Dependencia externa: `dateutil`

```python
from dateutil.relativedelta import relativedelta
```

`python-dateutil` debe estar en `requirements.txt`. Sin él, `calculate_memento_data()` falla con `ImportError`.

---

## 8. Bugs Conocidos

| # | Estado | Descripción |
|---|--------|-------------|
| B1 | ⬜ activo | `MinValueValidator(limit_value=timezone.now().date())` en `death_date` — valor de "hoy" congelado en tiempo de carga del módulo, no en tiempo de validación |
| B2 | ⬜ activo | `build_memento_context()` sin rama `else` — frecuencia inválida retorna contexto incompleto sin error; el template podría fallar |
| B3 | ⬜ activo | `MementoConfigUpdateView` sin filtro de propietario — cualquier usuario autenticado puede editar configs ajenas conociendo el `pk` |
| B4 | ⬜ activo | `'memento_try'` (`/try/`) es idéntico a `'memento_default'` (`/`) — endpoint redundante sin propósito diferenciado |
| B5 | ⬜ activo | `LogoutView` propio en `/memento/logout/` — duplica `accounts:logout`, potencialmente confuso y desincronizado |
| B6 | ⬜ activo | `update_or_create` en `memento()` busca solo por `user` — sobreescribe cualquier config existente del usuario en lugar de crear nueva entrada |
| B7 | ⬜ activo | `app_name` no declarado en `urls.py` — sin namespace propio |
| B8 | ⬜ activo | `MementoConfigUpdateView` no pasa `user` a `get_form_kwargs` — la validación de duplicados en `MementoConfigForm.clean()` se omite silenciosamente en edición |
| B9 | ⬜ activo | PKs int en URLs (`<int:pk>`) — fuera de convención UUID del proyecto |

---

## 9. Deuda Técnica

**Alta prioridad (seguridad y correctness):**
- **Proteger `MementoConfigUpdateView`** con `get_queryset` filtrado por `user=request.user` para evitar edición de configs ajenas (IDOR)
- **Corregir validador de `death_date`** — reemplazar `MinValueValidator` por validación en `clean()` del form o usar un callable: `validators=[MinValueValidator(limit_value=date.today)]` (sin paréntesis, pasa la función, no el valor)
- **Revisar comportamiento de `update_or_create`** en `memento()` — decidir si debe sobreescribir la última config o crear una nueva

**Media prioridad:**
- **Declarar `app_name = 'memento'`** en `urls.py`
- **Eliminar `'memento_try'`** o diferenciarlo con un propósito real
- **Eliminar `LogoutView`** propio — usar `accounts:logout`
- **Agregar rama `else`** en `build_memento_context()` con error explícito para frecuencias inválidas
- **Pasar `user` a `get_form_kwargs` en `MementoConfigUpdateView`** para activar validación de duplicados en edición

**Baja prioridad:**
- Migrar PK a UUID (alinear con convención del proyecto)
- Cambiar `user` → `created_by` (alinear con convención del proyecto)
- Agregar `is_active` para soft delete
- Verificar y documentar `memento_filters.py` — no se pudo revisar en esta sesión
- Documentar dependencia de `python-dateutil` en `requirements.txt`
