# Zona de Pruebas de Navegación

## Descripción General

La **Zona de Pruebas de Navegación** es una estructura jerárquica de habitaciones interconectadas diseñada para testing y demostración del sistema de navegación del proyecto Management360. Esta zona incluye habitaciones organizadas en 4 niveles de profundidad con múltiples tipos de conexiones entre ellas.

## Arquitectura de la Estructura

### Jerarquía (4 niveles de profundidad)

```
Navigation Test Zone (Nivel 1 - Raíz)
├── Alpha Sector (Nivel 2)
│   ├── Alpha-1 (Nivel 3)
│   │   ├── Alpha-1A (Nivel 4)
│   │   └── Alpha-1B (Nivel 4)
│   ├── Alpha-2 (Nivel 3)
│   └── Alpha-3 (Nivel 3)
├── Beta Sector (Nivel 2)
│   ├── Beta-1 (Nivel 3)
│   └── Beta-2 (Nivel 3)
└── Gamma Sector (Nivel 2)
    ├── Gamma-1 (Nivel 3)
    ├── Gamma-2 (Nivel 3)
    ├── Gamma-3 (Nivel 3)
    │   ├── Gamma-3X (Nivel 4)
    │   └── Gamma-3Y (Nivel 4)
    └── Gamma-4 (Nivel 3)
```

### Tipos de Conexiones

#### 1. Puertas (EntranceExit)
- **Conexiones físicas** entre habitaciones del mismo nivel
- Requieren interacción manual del usuario
- Tienen costo de energía (5 unidades base)
- Ejemplos:
  - Alpha-1 ↔ Alpha-2
  - Beta-1 ↔ Beta-2
  - Gamma-3X ↔ Gamma-3Y

#### 2. Portales (Portal)
- **Teletransportación instantánea** entre niveles diferentes
- Tienen cooldown (60 segundos) y costo de energía (15 unidades)
- Conectan sectores principales con sub-sectores
- Ejemplos:
  - Alpha Sector → Beta-1
  - Beta Sector → Gamma-2
  - Gamma Sector → Alpha-1

#### 3. Objetos de Conexión (RoomObject)
- **Elementos interactivos** en habitaciones específicas
- Tipo DOOR o PORTAL
- Pueden teletransportar al usuario
- Ejemplos:
  - Cristal Dimensional en Alpha-1A (conecta a Gamma-3Y)

## Cómo Acceder

### Desde el Lobby
1. Ve al lobby principal: `/rooms/`
2. Busca la sección "Navigation Test Zone"
3. Haz clic en "Crear/Acceder a Zona de Pruebas"

### URL Directa
- **Vista de creación**: `/rooms/navigation-test-zone/`
- **Habitación raíz**: `/rooms/[ID]/` (ID se asigna dinámicamente)

## Características de las Habitaciones

### Propiedades Físicas
- **Dimensiones**: Varían por tipo de habitación
- **Colores**: Cada sector tiene colores distintivos
- **Materiales**: Concreto, Metal, Madera, Vidrio, etc.
- **Iluminación**: Intensidad variable (60-80%)
- **Temperatura**: 22°C promedio

### Tipos de Habitaciones
- **OFFICE**: Áreas de trabajo y desarrollo
- **MEETING**: Salas de reuniones y testing
- **LOUNGE**: Áreas administrativas

## Sistema de Navegación

### Movimiento del Jugador
- **Posición**: Se actualiza automáticamente al cambiar de habitación
- **Energía**: Se consume al usar conexiones
- **Historial**: Se registra el camino recorrido

### Estados del Jugador
- **AVAILABLE**: Listo para interactuar
- **WORKING**: En habitación de trabajo
- **SOCIALIZING**: En área social
- **RESTING**: Descansando

## Casos de Uso para Testing

### 1. Navegación Jerárquica
- Probar movimiento ascendente/descendente en la jerarquía
- Verificar que el historial de navegación se mantiene

### 2. Conexiones Horizontales
- Usar puertas para moverse entre habitaciones del mismo nivel
- Verificar costos de energía y restricciones

### 3. Teletransportación
- Usar portales para saltar entre niveles
- Probar cooldowns y límites de energía

### 4. Objetos Interactivos
- Encontrar y usar objetos de conexión
- Verificar teletransportación especial

### 5. Gestión de Estado
- Monitorear cambios de energía y productividad
- Probar diferentes estados del jugador

## API Endpoints Relacionados

### Creación y Gestión
- `POST /rooms/navigation-test-zone/` - Crear zona completa
- `GET /api/rooms/[id]/3d/data/` - Datos 3D de habitación
- `POST /api/3d/transition/` - Transición entre habitaciones

### Estado del Jugador
- `GET /api/3d/player/status/` - Estado completo del player
- `GET /api/navigation/history/` - Historial de navegación
- `POST /api/teleport/[room_id]/` - Teletransportación

## Comandos de Management

### Testing
```bash
# Probar creación básica
python manage.py test_navigation_zone

# Verificar estructura
python manage.py shell -c "from rooms.models import Room; print(Room.objects.filter(parent_room__isnull=False).count())"
```

### Debugging
```bash
# Ver habitaciones por nivel
python manage.py shell -c "
from rooms.models import Room
root = Room.objects.filter(name='Navigation Test Zone').first()
if root:
    print('Level 2:', Room.objects.filter(parent_room=root).count())
    for r in Room.objects.filter(parent_room=root):
        print('Level 3 under', r.name, ':', Room.objects.filter(parent_room=r).count())
"
```

## Notas Técnicas

### Creación Automática
- La zona se crea usando transacciones atómicas para garantizar integridad
- Las habitaciones se crean con `get_or_create` para evitar duplicados
- Las conexiones se validan antes de guardar

### Rendimiento
- Optimizado para recorridos frecuentes
- Cache de habitaciones activas
- Índices en campos de navegación

### Seguridad
- Solo usuarios autenticados pueden acceder
- Validación de permisos en cada transición
- Logging de movimientos para auditoría

## Próximas Mejoras

- [ ] Agregar más tipos de objetos interactivos
- [ ] Implementar quests o misiones en la zona
- [ ] Añadir NPCs con interacciones
- [ ] Sistema de logros por exploración
- [ ] Modo competitivo multijugador

---

**Estado**: ✅ Implementado y probado
**Última actualización**: 2025-10-03
**Versión**: 1.0