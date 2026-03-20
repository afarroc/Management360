# Referencia de Desarrollo — App `campaigns`

> **Actualizado:** 2026-03-20 (Sesión Analista Doc — documentación completa)
> **Audiencia:** Desarrolladores del proyecto y asistentes de IA (Claude)
> **Stats:** 6 archivos · models.py 69 L · views.py 157 L · urls.py 19 L
> **Namespace:** `campaigns` ✅

---

## Índice

| # | Sección | Contenido |
|---|---------|-----------|
| 1 | Resumen | Qué hace la app |
| 2 | Modelos | ProviderRawData, ContactRecord, DiscadorLoad |
| 3 | Vistas | 6 vistas organizadas por función |
| 4 | URLs | Mapa completo |
| 5 | Integración con `bots` | Pipeline bots → campaigns |
| 6 | Convenciones críticas y violaciones | Gotchas |
| 7 | Bugs conocidos | Tabla con estado |
| 8 | Deuda técnica | Clasificada por prioridad |

---

## 1. Resumen

La app `campaigns` gestiona **campañas de outbound** para contact center. Almacena datos brutos de proveedores (`ProviderRawData`), registros de contactos asociados a campañas (`ContactRecord`), y el estado de carga al discador (`DiscadorLoad`). Es el origen de datos que alimenta el pipeline de distribución de leads de la app `bots` (via `BOT-3`).

**Flujo de datos:**
```
Proveedor externo → ProviderRawData (carga de archivo)
                        └── ContactRecord (N contactos)
                              └── bots.LeadCampaign / bots.Lead (BOT-3, pendiente)
ProviderRawData → DiscadorLoad (OneToOne) → exportación al discador
```

---

## 2. Modelos

### 2.1 `ProviderRawData`

Campaña de datos brutos recibida de un proveedor.

| Campo | Tipo | Notas |
|-------|------|-------|
| `id` | `UUIDField(primary_key=True)` | ✅ Convención del proyecto |
| `campaign_name` | `CharField(255)` | Nombre de la campaña |
| `upload_date` | `DateTimeField(default=timezone.now)` | ⚠️ NO es `created_at` — usa `default`, no `auto_now_add` |
| `status` | `CharField(20, choices=CAMPAIGN_STATUS)` | `pending`/`processing`/`loaded`/`completed` |
| `source_file` | `FileField(upload_to='campaigns/raw_data/', null=True)` | Archivo fuente del proveedor |
| `records_count` | `IntegerField(default=0)` | Conteo de registros — actualizado manualmente |

⚠️ **Sin `created_by`** — las campañas son globales, no por usuario.  
⚠️ **`upload_date` con `default=timezone.now`** (no `auto_now_add`) — puede ser sobreescrito al crear instancias.

---

### 2.2 `ContactRecord`

Registro individual de un contacto dentro de una campaña.

| Campo | Tipo | Notas |
|-------|------|-------|
| `id` | `AutoField` | ⚠️ Sin UUID — inconsistencia con `ProviderRawData` |
| `campaign` | `FK(ProviderRawData, CASCADE, related_name='contacts')` | — |
| `ani` | `CharField(20)` | Número de teléfono |
| `dni` | `CharField(20, null=True, blank=True)` | Documento de identidad |
| `full_name` | `CharField(255)` | Nombre completo |
| `current_product` | `CharField(100)` | Producto actual del cliente |
| `offered_product` | `CharField(100)` | Producto ofrecido en la campaña |
| `contact_type` | `CharField(20, choices=CONTACT_TYPE, default='mobile')` | `mobile`/`landline`/`whatsapp` |
| `segment` | `CharField(50, null=True, blank=True)` | Segmento de marketing |
| `propensity_score` | `IntegerField(default=0)` | Score de propensión (0–100) |
| `created_at` | `DateTimeField(auto_now_add=True)` | ✅ |

**Índices:** `[ani]` · `[dni]` · `[campaign]`

---

### 2.3 `DiscadorLoad`

Estado de la carga de una campaña al discador telefónico. OneToOne con `ProviderRawData`.

| Campo | Tipo | Notas |
|-------|------|-------|
| `id` | `AutoField` | ⚠️ Sin UUID |
| `campaign` | `OneToOneField(ProviderRawData, CASCADE, related_name='discador_load')` | — |
| `load_date` | `DateTimeField(default=timezone.now)` | ⚠️ No es `created_at` |
| `status` | `CharField(20, choices=STATUS_CHOICES, default='pending')` | `pending`/`loading`/`loaded`/`in_progress`/`completed` |
| `records_loaded` | `IntegerField(default=0)` | Registros enviados al discador |
| `records_processed` | `IntegerField(default=0)` | Registros ya procesados |
| `success_rate` | `FloatField(default=0.0)` | Tasa de éxito (0.0–1.0) |
| `export_file` | `FileField(upload_to='campaigns/discador_exports/', null=True)` | Archivo exportado al discador |

**Acceso al DiscadorLoad desde una campaña:**
```python
# CORRECTO — OneToOne con related_name
campaign.discador_load  # lanza RelatedObjectDoesNotExist si no existe

# SEGURO — para verificar existencia
try:
    discador_load = campaign.discador_load
except DiscadorLoad.DoesNotExist:
    discador_load = None

# O bien:
DiscadorLoad.objects.filter(campaign=campaign).first()
```
⚠️ Las vistas usan `hasattr(campaign, 'discador_load')` — patrón frágil (Bug #93).

---

## 3. Vistas

Todas las vistas tienen `@login_required`. No hay `@csrf_exempt`.

⚠️ **Dato importante:** Ninguna vista filtra por usuario — las campañas son **datos globales** del sistema. Cualquier usuario autenticado ve todas las campañas y todos los contactos.

### 3.1 `dashboard`

**URL:** `GET /campaigns/`  
**Template:** `campaigns/dashboard.html`

Estadísticas generales: total de campañas, campañas activas (status=`processing`), total de contactos, últimas 5 campañas, distribución por estado y por tipo de contacto.

---

### 3.2 `campaign_list`

**URL:** `GET /campaigns/campaigns/?status=<filter>&page=<n>`  
**Template:** `campaigns/campaign_list.html`

Lista paginada (10 por página) de `ProviderRawData`. Filtra por `status`. Pasa `status_choices` y `current_status` al contexto.

---

### 3.3 `campaign_detail`

**URL:** `GET /campaigns/campaigns/<uuid:pk>/`  
**Template:** `campaigns/campaign_detail.html`

Detalle de una campaña con estadísticas: total de contactos, distribución por tipo (`contacts_by_type`), y objeto `DiscadorLoad` si existe.

⚠️ Muestra solo `contacts[:50]` — hardcodeado, sin paginación.

---

### 3.4 `contact_list`

**URL:** `GET /campaigns/campaigns/<uuid:campaign_id>/contacts/?contact_type=&segment=&search=&page=<n>`  
**Template:** `campaigns/contact_list.html`

Lista paginada (25 por página) con filtros por `contact_type`, `segment` y búsqueda fulltext en `full_name`, `ani`, `dni` via `Q`.

---

### 3.5 `discador_loads`

**URL:** `GET /campaigns/discador/?status=<filter>&page=<n>`  
**Template:** `campaigns/discador_loads.html`

Lista paginada (10 por página) de `DiscadorLoad` con `select_related('campaign')`. Filtra por status.

---

### 3.6 `discador_load_detail`

**URL:** `GET /campaigns/discador/<int:pk>/`  
**Template:** `campaigns/discador_load_detail.html`

Detalle de una carga al discador. Contexto: `load` y `load.campaign`.

⚠️ Usa `<int:pk>` — `DiscadorLoad` tiene AutoField int, correcto por ahora.

---

## 4. URLs

| Pattern | Name | Vista | Notas |
|---------|------|-------|-------|
| `/campaigns/` | `campaigns:dashboard` | `dashboard` | — |
| `/campaigns/campaigns/` | `campaigns:campaign_list` | `campaign_list` | Paginado, filtro status |
| `/campaigns/campaigns/<uuid:pk>/` | `campaigns:campaign_detail` | `campaign_detail` | UUID PK |
| `/campaigns/campaigns/<uuid:campaign_id>/contacts/` | `campaigns:contact_list` | `contact_list` | UUID, búsqueda |
| `/campaigns/discador/` | `campaigns:discador_loads` | `discador_loads` | Paginado |
| `/campaigns/discador/<int:pk>/` | `campaigns:discador_load_detail` | `discador_load_detail` | int PK |

**Namespace:** `app_name = 'campaigns'` ✅

---

## 5. Integración con `bots`

La app `campaigns` es el **origen de datos** del pipeline BOT-3 (pendiente de implementar). La relación diseñada es:

```
campaigns.ProviderRawData  → bots.LeadCampaign (a crear en BOT-3)
campaigns.ContactRecord    → bots.Lead (a crear en BOT-3)
campaigns.DiscadorLoad     → trigger del pipeline de distribución
```

El `BOTS_DESIGN.md` documenta BOT-3 como tarea de Sprint 9: `DiscadorLoad → genera LeadCampaign automáticamente` y `ContactRecord → genera Lead asociado`.

---

## 6. Convenciones Críticas y Violaciones

| Convención | Estándar | Estado en `campaigns` |
|------------|----------|-----------------------|
| PK UUID | `UUIDField(primary_key=True)` | ⚠️ Solo `ProviderRawData` ✅; `ContactRecord` y `DiscadorLoad` usan AutoField |
| `created_by` | `FK(AUTH_USER_MODEL)` | ❌ Ausente en todos los modelos — campañas son datos globales |
| Timestamps | `created_at`/`updated_at` | ⚠️ `ProviderRawData` y `DiscadorLoad` usan `upload_date`/`load_date` con `default=timezone.now`, no `auto_now_add`; solo `ContactRecord` tiene `created_at` ✅ |
| Namespace | `app_name = 'campaigns'` | ✅ |
| `@login_required` | todas las vistas | ✅ |
| User import | `settings.AUTH_USER_MODEL` | N/A — no hay FK a User |

---

## 7. Bugs Conocidos

| # | Estado | Descripción | Impacto |
|---|--------|-------------|---------|
| #90 | ⬜ | Sin `created_by` en ningún modelo — campañas son globales, cualquier usuario las ve | Bajo (diseño intencional) |
| #91 | ⬜ | `ContactRecord` y `DiscadorLoad` sin UUID PK — inconsistencia con `ProviderRawData` | Bajo |
| #92 | ⬜ | `upload_date`/`load_date` con `default=timezone.now` en lugar de `auto_now_add` — pueden ser sobreescritos | Bajo |
| **#93** | ⬜ | `hasattr(campaign, 'discador_load')` en `campaign_detail` — patrón frágil para OneToOne reverse | Medio |
| #94 | ⬜ | `contacts[:50]` hardcodeado en `campaign_detail` — sin paginación para campañas con muchos contactos | Medio |

---

## 8. Deuda Técnica

### Media prioridad
- **Bug #93** — reemplazar `hasattr` por `try/except DiscadorLoad.DoesNotExist` o `.filter().first()`
- **Bug #94** — paginar contactos en `campaign_detail` (actualmente limitado a 50)
- **BOT-3** — implementar el pipeline `ContactRecord → Lead` y `DiscadorLoad → LeadCampaign` (Sprint 9)

### Baja prioridad
- UUID PK en `ContactRecord` y `DiscadorLoad`
- Estandarizar timestamps a `created_at` con `auto_now_add`
- Tests — sin tests
- Admin vacío — registrar modelos
- Considerar scoping por usuario si las campañas dejan de ser datos globales
