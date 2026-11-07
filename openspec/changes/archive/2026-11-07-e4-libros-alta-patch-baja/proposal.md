# Proposal: e4-libros-alta-patch-baja

> Issue: #23 (E4). Consigna: `Parcial_Cap1a6_Consigna.pdf`, Ejercicio 3, tabla de endpoints (págs. 16-18) y casos C-13 y C-16. Reglas: RN-01, RN-11, RN-13, RN-15.

## Why

El módulo `libros` viene del TP 1-4 y no cumple el contrato del parcial:

- El alta recibe `stock` y lo escribe directo en `libro.stock`, sin movimiento. Rompe RN-11: el stock sólo cambia con movimientos, y `stock` tiene que ser la suma de los movimientos del libro.
- El PATCH acepta `stock`, `isbn`, `editorial_id` y `genero_id`. La consigna pide sólo título y precio, y que mandar el stock dé 422.
- No hay baja: falta `DELETE /libros/{id}` con borrado lógico (RN-13).
- El listado devuelve una lista con `limit` y `offset`, no el envoltorio `{items, total, page, size, pages}` de B5.
- Las escrituras no piden sesión, y la consigna las pone en el grupo protegido.

## What Changes

- **Alta** (`POST /libros/`): el cuerpo trae `stock_inicial` en lugar de `stock`. En un solo bloque del Unit of Work se crea el libro con stock 0, sus autorías y, si `stock_inicial` es mayor que 0, el movimiento «Stock inicial» por `mover_stock` (E3), a nombre del usuario de la sesión. 201; 409 con mensaje propio si el ISBN ya está en un libro vigente o si la editorial, el género o un autor no existe; 422 si el contrato no se cumple.
- **PATCH** (`PATCH /libros/{id}`): sólo `titulo` y `precio`. Cualquier otro campo, `stock` incluido, da 422 (`extra="forbid"`). Se aplica sólo lo enviado (`exclude_unset`). 404 si el libro no existe o está dado de baja.
- **Baja** (`DELETE /libros/{id}`): escribe `borrado_en` con `soft_delete` (E2) y responde 204. 404 si no existe o ya estaba dado de baja. El ISBN queda libre para otro alta (índice único parcial de E1).
- **Listado** (`GET /libros/`): pasa al envoltorio de B5 (`page`, `size`), con los filtros `titulo` (parámetro ligado, sin distinguir mayúsculas) y `genero_id`. `total` cuenta con los mismos filtros; una página más allá de la última da 422.
- **Sesión**: alta, PATCH y baja piden `get_usuario_actual` (R1, entró con el PR #85): sin sesión, 401. El alta usa su id para el movimiento.
- **Modelo**: el índice único parcial del ISBN declara también `sqlite_where`, para que los tests en SQLite en memoria tengan el mismo comportamiento que PostgreSQL. En PostgreSQL no cambia nada (no hay migración).

## Capabilities

### New Capabilities

- `catalogo-libros`: alta con stock inicial, PATCH de título y precio, baja lógica, reutilización del ISBN y listado paginado de libros.

### Modified Capabilities

(ninguna)

## Impact

- **Código:** sólo el módulo `app/modules/libros/` (`schemas`, `repository`, `service`, `router` y el índice de `models`) y tests nuevos en `tests/`.
- **Sin cambios:** `mover_stock` (lo usa la venta de J3), `precios` y `ids_con_stock_inconsistente`. Tampoco `app/core/`, `app/main.py`, `seed.py` ni los módulos de otros integrantes.
- **Base de datos:** sin migración. `sqlite_where` es una opción que PostgreSQL ignora, así que `alembic check` no ve diferencias.
- **Contrato:** cambia la forma del alta (`stock_inicial`), del PATCH y del listado (envoltorio). Ningún otro módulo los usa.
- **Fuera de alcance:** el control de rol ADMIN (`requiere_rol`, R2 de Bruno, #46). Se agrega cuando R2 esté en `main`: una línea por endpoint. La reposición y los movimientos son E5 (#24); los `.http` de C-13 y C-16, E7 (#26).
