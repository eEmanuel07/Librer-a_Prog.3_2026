# Proposal: j5-detalle-venta-dueno

> Issue: #58 ([J5] — Detalle de una venta para el personal o el cliente dueño). Consigna: `Parcial_Cap1a6_Consigna.pdf`, Ejercicio 8 (pág. 13), RN-04 y RN-14 (pág. 7), tabla de rutas y recuadro «El detalle de una venta no lleva requiere_rol» (pág. 18), casos C-06 y C-15 (pág. 22).

## Why

Hoy `GET /ventas/{id}` no pide sesión: cualquiera ve cualquier venta. La consigna pide que la vea el personal (VENDEDOR o ADMIN) o el cliente dueño, y nadie más (403). No puede resolverse con `requiere_rol`, porque el dueño no tiene un rol de personal: decide el servicio, primero quién es y qué relación tiene con la venta, y recién después qué se devuelve. El detalle tiene que salir con un número fijo de consultas, aunque tenga más renglones o algún libro esté dado de baja.

## What Changes

- **Errores (`app/core/errors.py`)**: nuevo `SinPermiso(ErrorDeDominio)`, que el router traduce a 403.
- **Unit of Work (`app/modules/ventas/unit_of_work.py`)**: compone `self.roles = AsignacionRolRepository(session)` para leer los roles vigentes en la misma sesión.
- **Repositorio (`app/modules/ventas/repository.py`)**: `obtener_dueno(venta_id)`: una consulta (venta JOIN cliente) que devuelve el `usuario_id` del cliente, o `None` si la venta no existe. `obtener_con_detalle` no cambia; se documenta que trae el libro aunque esté dado de baja.
- **Servicio (`app/modules/ventas/service.py`)**: `ver_venta(uow, venta_id, usuario)`: roles vigentes → si no es personal, comprueba que sea el dueño (404 / 403) → detalle. `obtener_venta` queda para el alta.
- **Router (`app/modules/ventas/router.py`)**: `GET /ventas/{id}` pide `get_usuario_actual` (401 sin sesión), sin `requiere_rol`, y traduce `SinPermiso` a 403.
- **Tests (`tests/test_ventas_detalle.py`)**: quién puede verla, roles revocados o vencidos, libro dado de baja, cantidad de consultas y códigos HTTP.

## Capabilities

### New Capabilities

(ninguna)

### Modified Capabilities

- `ventas`: agrega el requisito del detalle para el personal o el dueño.

## Impact

- **Autorización:** el detalle pasa a exigir sesión; un cliente sólo ve las suyas (RN-14). Los roles se leen de la base en cada petición (RN-04): un rol revocado o vencido deja de dar acceso aunque el token todavía lo nombre.
- **Consultas:** número fijo (C-15): para el personal, roles + venta con cliente + renglones con libro; para el dueño, una más (el dueño).
- **Fuera de alcance:** `GET /ventas` y `/mis-ventas` (J6); el 403 por cambio de contraseña pendiente lo pone el grupo protegido (R3).
