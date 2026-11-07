# Design: j7-clientes-con-acceso

## UI Mockups

Decision: no (no UI)

## Context

R2 dejó `requiere_rol(*roles)` en `app/core/dependencies.py`: lee los roles vigentes en la base con la sesión de la petición y responde 403 «No tiene permisos para realizar esta acción». R3 montó dos grupos de rutas; clientes y ventas ya están en el protegido. B5 dejó `paginacion.py`. El modelo `Cliente` ya tiene `usuario_id` (migración 3).

## Goals / Non-Goals

**Goals:**
- Todas las rutas de `/clientes` para VENDEDOR o ADMIN.
- `usuario_id` visible en la ficha, sin que el personal pueda asignarlo.
- Ventas de un cliente con el envoltorio y consultas fijas.
- Cerrar lo que J3 y J6 dejaron esperando a R2.

**Non-Goals:**
- No se agrega `GET /clientes` (listado de todos): no está en la tabla de rutas.
- No se cambia el detalle de una venta: sigue sin `requiere_rol` (J5).

## Decisions

### 1. El rol en el router, no en cada ruta
- **Decisión:** `APIRouter(prefix="/clientes", dependencies=[Depends(requiere_rol("VENDEDOR", "ADMIN"))])`.
- **Por qué:** las cinco rutas piden lo mismo; una ruta nueva queda protegida sin acordarse de agregarlo.

### 2. `usuario_id` sólo de lectura
- **Decisión:** se agrega a `ClienteRead`, no a `ClienteCreate` ni a `ClienteUpdate`.
- **Por qué:** el vínculo cliente-usuario lo crea el auto-registro (RN-02). Si el personal pudiera ponerlo, podría darle a un usuario acceso a las ventas de otro cliente (RN-14).

### 3. `Pagina[VentaRead]` en las ventas de un cliente
- **Decisión:** se mantiene el ítem del TP (la venta con sus renglones) y se envuelve en la página.
- **Por qué:** no cambia lo que ve el personal en cada venta; sólo el envoltorio. Las consultas siguen fijas (conteo + venta JOIN cliente + renglones JOIN libro).

### 4. `requiere_rol` en ventas
- **Decisión:** `POST /ventas` recibe el usuario de `requiere_rol("VENDEDOR", "ADMIN")` (lo necesita para los movimientos); `GET /ventas` lo pide como `_personal`. `listar_ventas` ya no recibe el usuario.
- **Por qué:** es el mismo control que pedía J6, pero en la ruta, como el resto del grupo. `_es_personal` queda sólo para el detalle (J5), que no puede usar `requiere_rol`.

## Risks / Trade-offs

- **[Riesgo] Cambia el mensaje del 403 de `GET /ventas`:** pasa al de `requiere_rol`. Nadie dependía del anterior fuera de los tests de J6, que se ajustan.
- **[Trade-off] `test/clientes.http` se reescribe entero:** todas las peticiones necesitan la cookie; se mantienen los casos del TP y se agregan los de acceso.
