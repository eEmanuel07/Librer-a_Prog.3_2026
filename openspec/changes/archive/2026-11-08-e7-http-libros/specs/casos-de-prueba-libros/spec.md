## ADDED Requirements

### Requirement: Caso C-16 en el archivo .http de libros
`test/libros.http` SHALL incluir, sobre los datos de `seed.py`, la búsqueda con `' OR '1'='1` (200, lista vacía y total 0), la búsqueda `titulo=ficc&size=1` (total 1 y pages 1) y la misma con `page=2` (422), un listado con `size=500` (422), un PATCH parcial (sólo cambia lo enviado) y un PATCH con `stock` (422), cada pedido con su respuesta esperada en un comentario.

#### Scenario: Búsqueda con inyección y paginación con filtro
- **WHEN** se corren los pedidos de C-16 después de `python seed.py`
- **THEN** cada respuesta coincide con el código de su comentario `# Esperado:`

#### Scenario: PATCH parcial y PATCH del stock
- **WHEN** el ADMIN manda un PATCH con sólo el precio y otro con `stock`
- **THEN** el primero responde 200 sin cambiar título ni stock, y el segundo responde 422

### Requirement: Caso C-13 en el archivo .http de libros
`test/libros.http` SHALL incluir la reposición de un libro (200 con su movimiento), la baja de un libro vendido (204), que el libro deje de aparecer en el catálogo, la recarga de su ISBN (201), un segundo vigente con ese ISBN (409) y que la venta vieja siga mostrando el título, cada pedido con su respuesta esperada en un comentario.

#### Scenario: Reponer, dar de baja y recargar el ISBN
- **WHEN** se corren los pedidos de C-13 después de los de C-16
- **THEN** la reposición responde 200, la baja 204, el detalle del libro dado de baja 404, reponerlo 409, la recarga del ISBN 201 y el segundo vigente 409

#### Scenario: La venta vieja sigue mostrando el título
- **WHEN** después de dar de baja Rayuela se pide el detalle de la venta 1
- **THEN** la respuesta es 200 y su renglón sigue mostrando el título «Rayuela»

### Requirement: Rechazos del alta en el archivo .http de libros
`test/libros.http` SHALL mostrar que el alta sin sesión responde 401, con un VENDEDOR 403, con una editorial inexistente 409 y con `stock` en lugar de `stock_inicial` 422.

#### Scenario: Alta rechazada
- **WHEN** se corren los pedidos de rechazo del alta
- **THEN** cada respuesta coincide con el código de su comentario `# Esperado:` y no se crea ningún libro
