# Proposal: j3-venta-con-stock

> Issue: #56 ([J3] — Registrar una venta: descuento de stock y movimientos). Consigna: `Parcial_Cap1a6_Consigna.pdf`, Ejercicio 6 (pág. 11), RN-09, RN-10 y RN-11 (pág. 7), casos C-10, C-11 y C-12 (pág. 22).

## Why

Hasta ahora `POST /ventas` crea la venta y sus renglones, pero no toca el stock: un libro se puede vender aunque no haya ejemplares y el stock deja de coincidir con la suma de sus movimientos. La consigna pide que registrar una venta descuente el stock de cada libro y deje un movimiento por renglón, todo en un solo bloque del Unit of Work, y que si algo falla no quede ninguna escritura (RN-10). El stock se escribe sólo por el punto único que dejó E3 (RN-11).

## What Changes

- **Servicio (`app/modules/ventas/service.py`)**:
  - `crear_venta(uow, datos, usuario_id)`: en un único `async with uow.con_mensajes(...)` lee los libros (bloqueados), crea la venta con sus renglones (precio copiado, total calculado), hace `add` (flush, para tener el id) y llama a `uow.libros.mover_stock(libro, -cantidad, "Venta", usuario_id, venta.id)` por cada renglón.
  - 409 con mensaje propio si un libro no existe, está dado de baja o no alcanza, o si el cliente no existe; el bloque revierte todo.
- **Repositorio de libros (`app/modules/libros/repository.py`)**:
  - `obtener_para_vender(libro_ids)`: trae los libros pedidos (incluidos los dados de baja, para que el 409 diga «dado de baja» y no «no existe») con `SELECT … FOR UPDATE`, ordenados por id.
- **Repositorio de ventas (`app/modules/ventas/repository.py`)**:
  - `VentaRepository` pasa a heredar de `BaseRepository[Venta]` (Ej. 6); el alta usa `add`, que hace flush. Se quita el `agregar` propio.
- **Router (`app/modules/ventas/router.py`)**:
  - `POST /ventas/` pide `get_usuario_actual` (401 sin sesión), que comparte la sesión con el Unit of Work, y le pasa `usuario.id` al servicio para que quede en cada movimiento.
- **Tests (`tests/test_ventas_registro_service.py`)**: C-10, C-11, C-12 (cliente, libro inexistente y libro dado de baja) y el invariante stock = suma de movimientos.

## Capabilities

### New Capabilities

- `ventas`: registro de una venta con descuento de stock y movimientos en una sola transacción (RN-09, RN-10, RN-11).

### Modified Capabilities

(ninguna)

## Impact

- **Transaccionalidad:** venta, renglones, descuentos y movimientos se confirman juntos o no se confirma nada (RN-10, C-11).
- **Concurrencia:** dos ventas simultáneas del mismo libro no pueden vender el mismo ejemplar: la segunda espera el bloqueo y lee el stock ya descontado.
- **Autorización:** registrar una venta exige sesión (401). La restricción a VENDEDOR y ADMIN queda para cuando esté `requiere_rol` (R2).
- **Fuera de alcance:** el aviso del comprobante (J4) y el `.http` con login (J8) siguen como están.
