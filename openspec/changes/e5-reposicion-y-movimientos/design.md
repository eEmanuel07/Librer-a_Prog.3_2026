# Design: e5-reposicion-y-movimientos

## Context

`mover_stock` (E3) ya hace lo difícil: suma el stock, deja el movimiento, rechaza un libro dado de baja con `Conflicto` y hace `flush()` sin confirmar. E4 dejó el módulo con `get_usuario_actual` en las escrituras y la paginación de B5 en el listado. E5 sólo arma los dos endpoints encima.

## Goals / Non-Goals

**Goals**
- Reponer stock respetando RN-11 (por `mover_stock`) y RN-13 (409 si el libro está dado de baja).
- Consultar los movimientos de un libro, paginados.

**Non-Goals**
- El rol ADMIN (R2), los `.http` (E7) y corregir movimientos (RN-12: se compensan con otro, no se editan).

## Decisions

### 1. El cuerpo de la reposición: sólo `cantidad`

La consigna no da un ejemplo del cuerpo. Se pide `{"cantidad": n}` con `n` entero ≥ 1 y `extra="forbid"`. El motivo es fijo, «Reposición», igual que «Stock inicial» en el alta: así los motivos se pueden buscar y contar, y nadie escribe un motivo de venta desde la reposición. Una cantidad 0 o negativa da 422 en el contrato, antes del servicio (la tabla, además, tiene `CHECK cantidad <> 0`).

### 2. 404 para el inexistente y 409 para el dado de baja

Se busca el libro **incluyendo los dados de baja** (`get_by_id_including_deleted`):
- si no existe, 404 (el recurso de la ruta no existe);
- si existe pero está dado de baja, `mover_stock` lanza `Conflicto` y se responde 409, como pide RN-13 («no se vende ni se repone»).

Buscarlo sólo entre los vigentes daría 404 en los dos casos, y la consigna pide 409 para el dado de baja.

### 3. La respuesta de la reposición

200 con `{libro: {id, isbn, titulo, stock}, movimiento: {...}}`. El caso C-13 pide «reposición 200 con su movimiento», y el stock nuevo deja ver que la suma subió en la misma respuesta.

### 4. Movimientos: del más viejo al más nuevo, con los dados de baja

Orden por `cuando` y después por `id` (dos movimientos pueden tener el mismo instante), para que la paginación sea estable. Una sola consulta por página, sin relaciones: el movimiento trae `usuario_id` y `venta_id`, no los objetos, así que no hay riesgo de N+1. El libro dado de baja sigue mostrando sus movimientos, porque son su historia y no se borran (RN-12).

### 5. Un solo bloque `async with` para reponer

La búsqueda del libro y `mover_stock` van en el mismo bloque: si algo falla, el UoW revierte el stock y el movimiento juntos. La respuesta se arma con el libro y el movimiento ya cargados, sin otra lectura.

## Risks / Trade-offs

- **[Riesgo] Sin rol ADMIN hasta R2** → cualquier usuario con sesión puede reponer. Igual que en E4: se pide sesión desde ya y queda anotado.
- **[Trade-off] Rama sobre E4** → este PR muestra también los commits de E4 hasta que el #86 se mergee. Se abre recién después.
