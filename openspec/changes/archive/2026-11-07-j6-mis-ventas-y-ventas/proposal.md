# Proposal: j6-mis-ventas-y-ventas

> Issue: #59 ([J6] — GET /mis-ventas y GET /ventas con el envoltorio). Consigna: `Parcial_Cap1a6_Consigna.pdf`, Ejercicio 3 (pág. 10), RN-04 y RN-14 (pág. 7), tabla de rutas (pág. 18).

## Why

`GET /ventas` hoy no pide sesión, devuelve una lista suelta y se pagina con `limit`/`offset` del TP. La consigna pide que lo use sólo el personal (VENDEDOR o ADMIN) y que todos los listados devuelvan el envoltorio `{items, total, page, size, pages}` (B5). Además falta `GET /mis-ventas`: las ventas del cliente asociado al usuario, que sólo pide estar autenticado (RN-14).

## What Changes

- **Repositorio (`app/modules/ventas/repository.py`)**: `listar_pagina(params, usuario_id=None)` reemplaza a `listar(limit, offset)`. Usa `paginar` de B5 (conteo + página, venta JOIN cliente); con `usuario_id` filtra por el cliente de ese usuario.
- **Servicio (`app/modules/ventas/service.py`)**:
  - `listar_ventas(uow, params, usuario)`: 403 si no es personal; si no, la página.
  - `listar_mis_ventas(uow, params, usuario)`: la página de las ventas propias.
  - `_es_personal(uow, usuario)`: el control de roles vigentes, compartido con `ver_venta` (J5).
- **Router (`app/modules/ventas/router.py`)**: `GET /ventas/` devuelve `Pagina[VentaResumen]` con `page`/`size` y pide sesión; nuevo `router_mis_ventas` con `GET /mis-ventas`.
- **`app/main.py`**: registra `router_mis_ventas`.
- **Tests (`tests/test_ventas_listados.py`)**: quién ve cada listado, envoltorio, paginación, página de más, sin ficha de cliente, cantidad de consultas y códigos HTTP.

## Capabilities

### New Capabilities

(ninguna)

### Modified Capabilities

- `ventas`: agrega los requisitos de los dos listados.

## Impact

- **Contrato:** `GET /ventas` pasa de lista con `limit`/`offset` al envoltorio con `page`/`size`. `test/ventas.http` se actualiza en J8.
- **Autorización:** mientras no esté `requiere_rol` (R2), el rol de `GET /ventas` lo controla el servicio con los roles vigentes en la base. Cuando llegue R2 se pasa a la dependencia del router.
- **Consultas:** fijas, no dependen del tamaño de la página.
