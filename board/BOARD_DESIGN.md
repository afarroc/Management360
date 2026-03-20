# Diseño y Roadmap — App `board`

> **Actualizado:** 2026-03-20 (Sesión Analista Doc)
> **Estado:** Funcional parcial — CRUD de cards operativo, Board CRUD incompleto, WebSocket sin activar
> **Fase del proyecto:** GTD Personal (Fase 1 base) — app satélite
> **Migraciones:** `0001_initial` — aplicada

---

## Visión General

Tablero visual tipo Pinterest/Kanban para organización personal. Cada usuario puede tener múltiples `Board` con layout configurable, y agregar `Card` de 5 tipos (nota, imagen, enlace, tarea, video). Las cards se manipulan sin recarga de página vía HTMX. Hay infraestructura WebSocket preparada para edición colaborativa en tiempo real, pendiente de activar.

```
Board (owner → User)
  ├── Card (N) — note / image / link / task / video
  │     └── HTMX CRUD sin recarga
  ├── Activity (N) — log de acciones
  └── BoardConsumer (WebSocket) — movimiento de cards [⚠️ no activado]

Board.collaborators (M2M → User) — acceso compartido [⚠️ no implementado en vistas]
```

---

## Estado de Implementación

| Componente | Estado | Notas |
|-----------|--------|-------|
| `Board` CRUD — crear | ✅ | `BoardCreateView` |
| `Board` CRUD — listar | ✅ | Solo boards propios |
| `Board` CRUD — ver detalle | ⚠️ Funcional con bug | Sin verificación de propietario (IDOR #84) |
| `Board` CRUD — editar | ❌ No implementado | Sin vista ni URL |
| `Board` CRUD — eliminar | ❌ No implementado | Sin vista ni URL |
| `Card` crear (HTMX) | ✅ | `create_card_htmx` + registro Activity |
| `Card` eliminar (HTMX) | ✅ | `delete_card_htmx` + registro Activity |
| `Card` toggle pin (HTMX) | ✅ | `toggle_pin_card` |
| `Card` infinite scroll | ✅ | `load_more_cards` |
| `Card` editar | ❌ No implementado | Sin vista ni URL |
| Colaboradores (`M2M`) | ❌ No implementado | Modelo existe, vistas no lo usan |
| WebSocket tiempo real | ⚠️ Infraestructura lista | `BoardConsumer` sin URL ASGI |
| `BOARD_CONFIG` en settings | ❓ Sin verificar | Posible KeyError en runtime (#85) |
| Tests | ❌ Stub | 3 líneas |
| Admin | ❌ Vacío | Sin registrar modelos |

---

## Arquitectura de Datos

```
User
├── boards (owned)     → Board (N)
└── shared_boards      → Board (M2M, via collaborators)

Board
├── cards              → Card (N)
└── activities         → Activity (N)
```

### Dependencias con otras apps
Ninguna — app independiente sin imports de otras apps del proyecto.

---

## Roadmap — Sprint 9

| ID | Tarea | Prioridad |
|----|-------|-----------|
| BOARD-1 | Fix IDOR en `BoardDetailView` — filtrar por propietario (Bug #84) | 🔴 |
| BOARD-2 | Verificar/agregar `BOARD_CONFIG` en settings | 🔴 |
| BOARD-3 | Implementar `BoardUpdateView` + `BoardDeleteView` | 🟠 |
| BOARD-4 | Registrar `BoardConsumer` en routing ASGI — activar tiempo real | 🟡 |
| BOARD-5 | Implementar lógica de colaboradores (acceso M2M en vistas) | 🟡 |
| BOARD-6 | Implementar `Card` editar (HTMX) | 🟡 |
| BOARD-7 | Tests básicos | 🟡 |

---

## Notas para Claude

- **`Board.owner`** es el propietario — no `created_by`. Queries de seguridad: `Board.objects.filter(owner=request.user)`.
- **`Card.created_by`** ✅ sí sigue la convención estándar.
- **`Activity.timestamp`** es el campo de fecha — no `created_at`.
- **`board.cards.all()`** ya viene ordenado por `['-is_pinned', '-created_at']` — cards fijadas primero.
- **`settings.BOARD_CONFIG['CARDS_PER_PAGE']`** — siempre verificar que exista antes de usar htmx_views.
- **`BoardConsumer`** requiere `CHANNEL_LAYERS` en settings (igual que `chat`) — actualmente sin activar.
- **Sin imports de otras apps** — app completamente independiente, no genera dependencias cruzadas.
