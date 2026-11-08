# Design: j8-ventas-http-c15

## UI Mockups

Decision: no (no UI)

## Context

R8 dejó `seed.py` en la raíz con los datos de la consigna (ids fijos porque hace `TRUNCATE ... RESTART IDENTITY`). R9 fijó el patrón de sesiones en los `.http`: un `# @name loginX` por usuario y `Cookie: {{loginX.response.headers.Set-Cookie}}` con `# @no-cookie-jar`. J3 a J7 dejaron las rutas de ventas protegidas y con el envoltorio.

## Goals / Non-Goals

**Goals:**
- Que `test/ventas.http`, corrido de arriba abajo sobre una base recién cargada, dé el código esperado en cada pedido.
- Mostrar en el mismo archivo que C-11 y C-12 no dejan escrituras (stock antes y después).
- Dejar la evidencia de C-15 con la salida real de la consola.

**Non-Goals:**
- No se duplican los casos de C-06 que ya están en `seguridad.http` (R9); sólo uno de venta ajena.

## Decisions

### 1. Comprobar «sin escrituras» con el stock y los movimientos
- **Decisión:** después de cada 409 se pide `GET /libros/1` (stock 8) y, en C-11, `GET /libros/1/movimientos`.
- **Por qué:** es lo que ve quien corrige sin entrar a psql: si el bloque no revirtiera, Rayuela quedaría en 7.

### 2. El libro dado de baja se crea en el mismo archivo
- **Decisión:** el ADMIN da de alta un libro con stock 2 y lo da de baja antes de venderlo.
- **Por qué:** no se toca ningún libro de `seed.py` que usen otros `.http`.

### 3. C-15 con `SQL_ECHO=true`
- **Decisión:** el archivo crea una venta de 4 renglones y pide el detalle de la venta 1 (2 renglones) y el de esa. La evidencia es el fragmento de consola de esas dos peticiones.
- **Por qué:** la consigna pide ver las consultas en la consola; contar los SELECT de cada petición alcanza para comparar.

## Risks / Trade-offs

- **[Riesgo] Ids que dependen del orden:** la venta de 4 renglones no tiene un id fijo (las ventas rechazadas consumen la secuencia); se usa `{{ventaCuatro.response.body.$.id}}`.
- **[Trade-off] El archivo modifica datos:** correrlo dos veces sin volver a correr `seed.py` cambia stocks y totales esperados.
