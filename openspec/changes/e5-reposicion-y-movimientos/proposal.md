# Proposal: e5-reposicion-y-movimientos

> Issue: #24 (E5). Consigna: `Parcial_Cap1a6_Consigna.pdf`, Ejercicio 3, tabla de endpoints (pág. 18) y caso C-13. Reglas: RN-11, RN-12, RN-13, RN-15.
> Depende de E4 (`e4-libros-alta-patch-baja`, PR #86): se arma sobre esa rama porque toca los mismos archivos.

## Why

El ADMIN tiene que poder reponer stock y ver la historia de cada libro. Hoy la única forma de que entre stock es el alta (E4), y no hay forma de consultar los movimientos. La reposición tiene que pasar por `mover_stock` (E3), el único punto de escritura del stock, para que `stock` siga siendo la suma de los movimientos (RN-11). Un libro dado de baja no se puede reponer (RN-13).

## What Changes

- **Reposición** (`POST /libros/{id}/reponer`): el cuerpo trae `cantidad` (entero ≥ 1, `extra="forbid"`). En un solo bloque del Unit of Work se suma el stock y se deja el movimiento «Reposición» a nombre del usuario de la sesión. Responde 200 con el libro (id, ISBN, título, stock nuevo) y el movimiento creado. 404 si el libro no existe; 409 si está dado de baja; 422 si la cantidad no es un entero ≥ 1.
- **Movimientos** (`GET /libros/{id}/movimientos`): los movimientos del libro, del más viejo al más nuevo, con el envoltorio de B5 (`page`, `size`). Incluye los de un libro dado de baja, porque es su historia. 404 si el libro no existe; 422 si la página no existe o `size` está fuera de rango.
- **Sesión**: los dos piden `get_usuario_actual` (R1, PR #85): sin sesión, 401. El rol ADMIN se agrega con R2 (#46).

## Capabilities

### New Capabilities

- `movimientos-stock`: reposición de stock con su movimiento y consulta paginada de los movimientos de un libro.

### Modified Capabilities

(ninguna)

## Impact

- **Código:** sólo `app/modules/libros/` (`schemas`, `repository`, `service`, `router`) y tests nuevos en `tests/`.
- **Sin cambios:** `mover_stock` (ya rechaza el libro dado de baja con `Conflicto`), el modelo y la base (no hay migración).
- **Fuera de alcance:** el rol ADMIN (R2), los `.http` de C-13 (E7) y la reposición de varios libros a la vez.
