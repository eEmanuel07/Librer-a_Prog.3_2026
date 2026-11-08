# Proposal: e7-http-libros

> Issue: #26 (E7), segunda parte. La primera (C-14: `test/solo_agregado.sql` y la captura de psql) entró en el PR #80. Consigna: `Parcial_Cap1a6_Consigna.pdf`, casos C-13 y C-16 (págs. 21-23).
> Se arma sobre `feat/libros-rol-admin` (PR #104): el caso del VENDEDOR espera 403, que recién da con ese cambio.

## Why

La consigna pide los casos C-13 y C-16 en el `.http` de libros, con la respuesta esperada de cada pedido en un comentario, corridos después de `python seed.py`. El `test/libros.http` actual es el del TP: manda `stock` en el alta, pagina con `limit` y `offset` y no inicia sesión, así que con E4, E5 y el rol ADMIN sus pedidos de escritura dan 422, 401 o 403.

## What Changes

- **`test/libros.http` reescrito** para el parcial, sobre los datos de `seed.py` (R8):
  - Inicio de sesión de `admin@example.com` y `vendedor@example.com` con la convención de `test/seguridad.http` (`# @name`, `# @no-cookie-jar` y la cookie en el encabezado).
  - **Catálogo público:** listado con el envoltorio, detalle y 404, sin sesión.
  - **C-16:** búsqueda con `' OR '1'='1` (lista vacía, total 0); `titulo=ficc&size=1` (total 1, pages 1) y `page=2` (422); `size=500` (422); PATCH parcial (sólo cambia lo enviado); PATCH con `stock` (422).
  - **C-13:** reposición 200 con su movimiento; movimientos del libro; baja 204; el libro deja de aparecer en el catálogo; reponer el dado de baja, 409; alta con el mismo ISBN, 201; un segundo vigente, 409; la venta 1 sigue mostrando el título del libro dado de baja.
  - **Rechazos del alta:** sin sesión 401, VENDEDOR 403, editorial inexistente 409, `stock` en lugar de `stock_inicial` 422.
- Cada pedido lleva su `# Esperado:` con el código y lo que tiene que mostrar.

## Capabilities

### New Capabilities

- `casos-de-prueba-libros`: los casos C-13 y C-16 del `.http` de libros, reproducibles sobre los datos iniciales.

### Modified Capabilities

(ninguna)

## Impact

- **Archivos:** sólo `test/libros.http`. No toca código.
- **Depende de:** `seed.py` (R8, en `main`) para los ids y las contraseñas de prueba, y del PR #104 para el 403 del VENDEDOR.
