# Diseño y Roadmap — App `campaigns`

> **Actualizado:** 2026-03-20 (Sesión Analista Doc)
> **Estado:** Funcional — dashboard + listados + detalle operativos. Sin integración `bots` aún.
> **Fase del proyecto:** Dependencia de `bots` BOT-3 (Sprint 9)
> **Migraciones:** `0001_initial` — aplicada

---

## Visión General

La app `campaigns` es el **repositorio de datos de campañas outbound** de Management360. Actúa como capa de almacenamiento para datos de proveedores externos y como origen del pipeline de distribución de leads de `bots`.

```
Proveedor externo
      │ upload
      ▼
ProviderRawData (campaña)
      │ 1:N
      ▼
ContactRecord (contactos)         ──► [BOT-3] bots.Lead
      │                                         │
      ▼                                         ▼
DiscadorLoad (1:1)                      bots.LeadCampaign
  │ export_file
  ▼
Discador telefónico (sistema externo)
```

---

## Estado de Implementación

| Componente | Estado | Notas |
|-----------|--------|-------|
| `ProviderRawData` | ✅ Funcional | UUID PK |
| `ContactRecord` | ✅ Funcional | Sin UUID PK |
| `DiscadorLoad` | ✅ Funcional | Sin UUID PK |
| Dashboard | ✅ Funcional | Estadísticas globales |
| Lista campañas | ✅ Funcional | Paginado + filtro status |
| Detalle campaña | ⚠️ Funcional con bug | `contacts[:50]` hardcoded (#94), `hasattr` frágil (#93) |
| Lista contactos | ✅ Funcional | Paginado + búsqueda + filtros |
| Lista DiscadorLoad | ✅ Funcional | Paginado + filtro status |
| Detalle DiscadorLoad | ✅ Funcional | — |
| Pipeline → `bots` (BOT-3) | ❌ No implementado | Sprint 9 |
| Upload de datos (crear campaña) | ❌ No implementado | Sin vista de creación |
| Tests | ❌ Sin tests | — |

---

## Arquitectura de Datos

```
ProviderRawData (UUID PK)
  └── ContactRecord (N) — int PK
  └── DiscadorLoad (1:1) — int PK
```

### Dependencias con otras apps

| Dependencia | Dirección | Estado |
|-------------|-----------|--------|
| `bots` | campaigns → bots | ⬜ BOT-3 pendiente — `ContactRecord → Lead`, `DiscadorLoad → LeadCampaign` |

Sin otras dependencias — app independiente actualmente.

---

## Roadmap — Sprint 9

| ID | Tarea | Prioridad | Notas |
|----|-------|-----------|-------|
| CMP-1 | Fix `hasattr` → `try/except` en `campaign_detail` (Bug #93) | 🟠 | — |
| CMP-2 | Paginar contactos en `campaign_detail` (Bug #94) | 🟠 | — |
| BOT-3 | Pipeline `ContactRecord → Lead` + `DiscadorLoad → LeadCampaign` | 🟠 | Ver `BOTS_DESIGN.md` |
| CMP-3 | Implementar vista de creación de campaña + upload de archivo | 🟡 | Sin vista actualmente |
| CMP-4 | UUID PK en `ContactRecord` y `DiscadorLoad` | 🟢 | Migración con datos existentes |

---

## Notas para Claude

- **Campañas son datos globales** — no hay `created_by` ni filtro por usuario. Todos los usuarios autenticados ven todas las campañas. Esto es diseño intencional del sistema de contact center.
- **`ProviderRawData` tiene UUID PK** — usar `<uuid:pk>` en URLs. `DiscadorLoad` tiene int PK — usar `<int:pk>`.
- **`campaign.discador_load`** puede lanzar `RelatedObjectDoesNotExist` — siempre acceder con `try/except` o `.filter().first()`.
- **`ContactRecord.campaign`** FK con `CASCADE` — al eliminar `ProviderRawData` se eliminan todos sus contactos.
- **`DiscadorLoad.campaign` es `OneToOneField`** — una campaña solo puede tener una carga al discador.
- **BOT-3 pendiente** — cuando se implemente, `campaigns` se convierte en dependencia de `bots`.
