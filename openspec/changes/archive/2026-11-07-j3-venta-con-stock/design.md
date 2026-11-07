# Design: j3-venta-con-stock

## UI Mockups

Decision: no (no UI)

## Context

`POST /ventas` ya valida el cuerpo (al menos un renglón, sin libros repetidos, sin precio ni total), copia el precio de cada libro y calcula el total en el servidor. E3 dejó `LibroRepository.mover_stock`, el único lugar que escribe el stock y anota el `movimiento_stock`; B4 dejó el Unit of Work con `con_mensajes` para traducir las violaciones de integridad a 409 con mensaje propio; H6 dejó `get_usuario_actual`.

## Goals / Non-Goals

**Goals:**
- Registrar la venta, sus renglones, el descuento de cada libro y un movimiento por renglón en un solo bloque del Unit of Work (RN-10).
- 409 sin ninguna escritura si un libro no alcanza (C-11) o si el cliente o un libro no existe o el libro está dado de baja (C-12).
- Escribir el stock sólo con `mover_stock` (RN-11).
- Que cada movimiento registre quién hizo la venta.

**Non-Goals:**
- No se restringe el endpoint a VENDEDOR y ADMIN: `requiere_rol` es de R2 y todavía no está en `main`. Cuando llegue es una dependencia más en el router.
- No se cambia el aviso del comprobante (J4) ni el `.http` (J8).

## Decisions

### 1. Un solo bloque y validación por la propia escritura
- **Decisión:** todo va en un `async with uow.con_mensajes(...)`. El cliente no se consulta antes: si no existe, la clave foránea falla en el flush de `add` y el Unit of Work la traduce a «El cliente indicado no existe». El libro dado de baja y el que no alcanza los rechaza `mover_stock`.
- **Por qué:** cualquier 409 que salga del bloque lo revierte entero, incluidos los descuentos de los renglones anteriores (C-11: Rayuela se descuenta y Bestiario falla; Rayuela vuelve a 10).

### 2. Libros bloqueados con `FOR UPDATE`
- **Decisión:** `LibroRepository.obtener_para_vender` lee los libros con `SELECT … FOR UPDATE`, ordenados por id y con `populate_existing`.
- **Por qué:** sin el bloqueo, dos ventas simultáneas del último ejemplar leen las dos `stock = 1` y las dos lo descuentan. Con el bloqueo, la segunda espera el commit de la primera, lee 0 y responde 409. Ordenar por id evita que dos ventas con libros en común se bloqueen en distinto orden y queden esperándose.
- **Alternativa descartada:** `UPDATE libro SET stock = stock - n WHERE stock >= n`. Resuelve la carrera, pero escribe el stock fuera de `mover_stock` y rompe el punto único (RN-11).

### 3. Los dados de baja se traen igual
- **Decisión:** `obtener_para_vender` no filtra `borrado_en`.
- **Por qué:** así el 409 dice «El libro está dado de baja» y no «No existe el libro», y el control lo hace `mover_stock`, el mismo que usa la reposición.

### 4. `VentaRepository` hereda de `BaseRepository`
- **Decisión:** se usa `add` (que hace flush) en lugar del `agregar` propio.
- **Por qué:** el Ej. 6 pide que cada entidad tenga su repositorio sobre la base, y el flush hace falta para tener el id de la venta antes de anotar los movimientos.

### 5. Quién vende
- **Decisión:** el router pide `get_usuario_actual` y pasa `usuario.id` al servicio. La dependencia usa la misma sesión que el Unit of Work.
- **Por qué:** `movimiento_stock.usuario_id` es obligatorio; además, sin sesión la venta responde 401.

## Risks / Trade-offs

- **[Riesgo] Una venta larga retiene el bloqueo de sus libros:** el bloque sólo hace inserts y updates de pocas filas, sin llamadas externas; el aviso corre después del commit.
- **[Riesgo] SQLite ignora `FOR UPDATE`:** los tests unitarios prueban la lógica; el bloqueo se verificó contra PostgreSQL (cuatro ventas simultáneas del último ejemplar: una 201 y tres 409).
- **[Trade-off] `LibroRepository.precios` queda sin uso:** no se borra en esta tarea porque el archivo es de otro integrante.
