# Diseño y Roadmap — App `memento`

> **Actualizado:** 2026-03-19  
> **Estado:** Funcional en producción — documentación generada esta sesión  
> **Sprint actual:** 7 completado | Próximo: Sprint 8

---

## Visión General

`memento` es la app de **productividad existencial** de Management360. Implementa el concepto filosófico *Memento Mori* — una visualización de la vida como unidades de tiempo finitas para motivar el foco y la priorización.

Es la app más autocontenida del proyecto: tiene su propio CSS, sus propios templatetags, y puede funcionar completamente sin autenticación (modo temporal). Su rol dentro de M360 es complementar las apps de productividad personal (`bitacora`, `board`) con una perspectiva de horizonte de vida.

```
┌──────────────────────────────────────────────────────┐
│                    APP MEMENTO                       │
│                                                      │
│  ┌────────────────────────────────────────────────┐  │
│  │           Configuración de fechas              │  │
│  │   birth_date + death_date + frequency          │  │
│  │   Guardar (auth) o modo temporal (anónimo)     │  │
│  └────────────────────┬───────────────────────────┘  │
│                       │                              │
│          ┌────────────┼────────────┐                 │
│          ▼            ▼            ▼                 │
│       Diario       Semanal      Mensual              │
│      (días)       (semanas)   (meses/años)           │
│   ████░░░░░░    ████░░░░░░    ████░░░░░░             │
│   vividos  restantes                                 │
└──────────────────────────────────────────────────────┘
```

---

## Estado de Implementación

| Módulo | Estado | Observaciones |
|--------|--------|---------------|
| Modelo `MementoConfig` | ✅ Funcional | 7 migraciones — `death_date` fue ajustado múltiples veces |
| Vista principal `memento()` | ✅ Funcional | Dual mode: auth + anónimo |
| Cálculo de métricas (`calculate_memento_data`) | ✅ Completo | Usa `dateutil.relativedelta` para meses |
| Visualización diaria | ✅ Completo | Template `includes/memento_daily.html` |
| Visualización semanal | ✅ Completo | Template `includes/memento_weekly.html` |
| Visualización mensual | ✅ Completo | Template `includes/memento_monthly.html` |
| CRUD de configuraciones | ✅ Funcional | Create y Update — sin Delete |
| Modo temporal (anónimo) | ✅ Funcional | Sin guardar, con `save_config=false` |
| Validaciones de fechas | ⚠️ Parcial | Validador de modelo con bug (congelado en carga) |
| Control de acceso | ⚠️ Bug crítico | UpdateView sin verificación de propietario |
| CSS propio (`memento.css`) | ✅ Completo | 94 líneas, independiente del proyecto |
| Templatetags (`memento_filters`) | ✅ Existe | No revisado en esta sesión |
| Tests (`tests.py`) | ⚠️ Parcial | 68 líneas — cobertura no verificada |
| Admin | ⚠️ Mínimo | `admin.py` con solo 3 líneas (registro básico) |
| Documentación | ✅ Esta sesión | Primera documentación formal |

---

## Arquitectura de Datos

### Jerarquía y dependencias

```
accounts.User
    └── MementoConfig (FK: user)
            ├── birth_date    (DateField)
            ├── death_date    (DateField)
            └── preferred_frequency ('daily'|'weekly'|'monthly')

unique_together: (user, birth_date, death_date)
→ Un usuario puede tener múltiples configs con distintas fechas
→ No puede repetir la combinación (user, birth, death) exacta
```

`memento` no tiene dependencias de otras apps del proyecto (excepto `accounts.User`). Es una isla funcional.

### Historial de migraciones — señal de inestabilidad

```
0001_initial
0002_alter_mementoconfig_death_date
0003_alter_mementoconfig_death_date
0004_alter_mementoconfig_death_date
0005_alter_mementoconfig_death_date
0006_alter_mementoconfig_death_date
0007_alter_mementoconfig_death_date
```

`death_date` fue alterado **6 veces** post-initial. Indica iteración frecuente sobre la validación de este campo. El validador actual (`MinValueValidator` con valor congelado en carga) es el resultado de este proceso — y aún tiene un bug.

### Flujo de datos

```
Usuario ingresa fechas
    │
    ├── Anónimo / sin save_config
    │     └── calculate_memento_data() → build_memento_context()
    │                                         → render memento_mori.html
    │
    └── Autenticado + save_config=true
          └── MementoConfig.update_or_create()
                └── calculate_memento_data() → build_memento_context()
                                                    → render memento_mori.html
```

---

## Roadmap

### Deuda inmediata (pre-Sprint 8)

| ID | Tarea | Prioridad |
|----|-------|-----------|
| MEM-1 | Proteger `MementoConfigUpdateView` — agregar `get_queryset(user=request.user)` para evitar IDOR | 🔴 |
| MEM-2 | Corregir validador de `death_date` — usar callable `date.today` en lugar de valor congelado | 🔴 |
| MEM-3 | Declarar `app_name = 'memento'` en `urls.py` | 🟠 |
| MEM-4 | Revisar/documentar `memento_filters.py` | 🟠 |

### Sprint 8

| ID | Tarea | Prioridad |
|----|-------|-----------|
| MEM-5 | Eliminar `'memento_try'` o darle propósito diferenciado | 🟡 |
| MEM-6 | Eliminar `LogoutView` propio — usar `accounts:logout` | 🟠 |
| MEM-7 | Agregar `else` en `build_memento_context()` con error explícito | 🟠 |
| MEM-8 | Pasar `user` en `get_form_kwargs` de `MementoConfigUpdateView` | 🟠 |
| MEM-9 | Revisar comportamiento de `update_or_create` en `memento()` — ¿sobreescribir o crear nueva? | 🟠 |
| MEM-10 | Implementar vista de Delete para `MementoConfig` | 🟡 |
| MEM-11 | Mejorar `admin.py` con `MementoConfigAdmin` (list_display, search, filter) | 🟡 |

### Sprint 9

| ID | Tarea | Prioridad |
|----|-------|-----------|
| MEM-12 | Migrar PK a UUID | 🟡 |
| MEM-13 | Renombrar `user` → `created_by` para alinear con convención del proyecto | 🟡 |
| MEM-14 | Agregar `is_active` (soft delete) | 🟡 |
| MEM-15 | Considerar integración con `events` — relacionar config con expectativa de vida en proyectos/tareas | 🟡 |

---

## Notas para Claude

- **Sin `@login_required`** en `memento()` — es intencional. La app soporta modo anónimo (temporal). No agregar `@login_required` a esa vista
- **Fechas en URLs** siempre en formato `YYYY-MM-DD` — al construir URLs usar `date|date:"Y-m-d"` en templates o `.strftime('%Y-%m-%d')` en Python
- **Fechas en templates** se muestran como `DD/MM/YYYY` — `build_memento_context` ya las formatea así
- **Propietario es `user`**, no `created_by` — al hacer queries de seguridad: `get_object_or_404(MementoConfig, pk=pk, user=request.user)`
- **PKs son int** (`<int:pk>`) — no UUID. No usar `<uuid:pk>` en esta app
- **`save_config`** es un campo del form, no del modelo — no está en `form.cleaned_data` para uso en model; se lee como `request.POST.get('save_config')`
- **`update_or_create` en `memento()`** busca solo por `user` — sobreescribe la última config del usuario. Comportamiento diferente al de `MementoConfigCreateView`
- **`dateutil`** es dependencia requerida — si falla `from dateutil.relativedelta import relativedelta`, toda la app cae
- **`memento_filters.py`** existe pero no fue revisado — cargar con `{% load memento_filters %}` antes de usar sus filtros en templates
- **7 migraciones sobre `death_date`** — el campo tuvo iteración frecuente; si se modifica de nuevo, verificar que el validador sea un callable, no un valor estático
