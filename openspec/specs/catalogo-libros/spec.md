# catalogo-libros Specification

## Purpose
Define el contrato del catálogo de libros: el alta con su stock inicial convertido en movimiento (RN-11), el PATCH limitado a título y precio, la baja lógica que conserva la fila y libera el ISBN (RN-01, RN-13), las escrituras con sesión y el listado paginado con filtros.

## Requirements

### Requirement: Alta de un libro con stock inicial y su movimiento
`POST /libros/` SHALL recibir `stock_inicial` (entero mayor o igual a 0) en lugar de `stock`, y SHALL crear en una única transacción el libro, sus autorías y, si `stock_inicial` es mayor que 0, un movimiento de stock con motivo «Stock inicial», cantidad igual a `stock_inicial` y el id del usuario de la sesión. El `stock` del libro creado SHALL ser igual a la suma de sus movimientos (RN-11). Responde 201 con el detalle del libro.

#### Scenario: Alta con stock inicial positivo
- **WHEN** un usuario con sesión da de alta un libro con `stock_inicial` 4 y dos autores
- **THEN** la API responde 201 con el libro, `stock` 4 y sus dos autores en orden, y queda un único movimiento «Stock inicial» de cantidad 4 a nombre de ese usuario

#### Scenario: Alta con stock inicial cero
- **WHEN** se da de alta un libro con `stock_inicial` 0
- **THEN** la API responde 201 con `stock` 0 y no queda ningún movimiento para ese libro

#### Scenario: El alta no acepta stock
- **WHEN** el cuerpo del alta trae `stock` en lugar de `stock_inicial`, o un `stock_inicial` negativo
- **THEN** la API responde 422 y no escribe nada

### Requirement: Rechazo del alta por la base, con mensaje propio y sin escrituras
Si la base rechaza el alta (ISBN de un libro vigente, editorial, género o autor inexistente), la API SHALL responder 409 con un mensaje propio, sin texto de la base (RN-15), y SHALL revertir el libro, las autorías y el movimiento juntos.

#### Scenario: ISBN de un libro vigente
- **WHEN** se da de alta un libro con el ISBN de otro libro vigente
- **THEN** la API responde 409 y en la base sigue habiendo un único libro con ese ISBN y ningún movimiento nuevo

#### Scenario: Editorial inexistente
- **WHEN** se da de alta un libro con un `editorial_id` que no existe
- **THEN** la API responde 409 con un mensaje propio y no queda ni el libro ni su movimiento

### Requirement: PATCH sólo de título y precio
`PATCH /libros/{id}` SHALL aceptar únicamente `titulo` y `precio`, SHALL aplicar sólo los campos enviados y SHALL responder 422 si el cuerpo trae cualquier otro campo, `stock` incluido (RN-11). Responde 404 si el libro no existe o está dado de baja.

#### Scenario: PATCH parcial
- **WHEN** se envía un PATCH con sólo `precio`
- **THEN** la API responde 200, el precio cambia y el título, el stock y los autores quedan como estaban

#### Scenario: PATCH del stock
- **WHEN** se envía un PATCH con `stock`
- **THEN** la API responde 422 y el stock del libro no cambia

#### Scenario: PATCH de un libro inexistente
- **WHEN** se envía un PATCH a un id que no existe o a un libro dado de baja
- **THEN** la API responde 404

### Requirement: Baja lógica de un libro
`DELETE /libros/{id}` SHALL escribir `borrado_en` en lugar de borrar la fila, y SHALL responder 204. El libro dado de baja SHALL dejar de aparecer en el listado y en el detalle. Responde 404 si el libro no existe o ya estaba dado de baja (RN-13).

#### Scenario: Baja de un libro vigente
- **WHEN** se da de baja un libro vigente
- **THEN** la API responde 204, la fila sigue en la tabla con `borrado_en` escrito, y el libro ya no aparece en `GET /libros/` ni en `GET /libros/{id}` (404)

#### Scenario: Baja repetida
- **WHEN** se da de baja un libro que ya estaba dado de baja
- **THEN** la API responde 404

### Requirement: Reutilización del ISBN de un libro dado de baja
Una vez dado de baja un libro, su ISBN SHALL poder usarse en un alta nueva, y un segundo libro vigente con ese ISBN SHALL rechazarse con 409 (RN-01, C-13).

#### Scenario: Volver a cargar el ISBN
- **WHEN** se da de baja un libro y después se da de alta otro con el mismo ISBN
- **THEN** el alta responde 201

#### Scenario: Segundo vigente con el mismo ISBN
- **WHEN** ya hay un libro vigente con ese ISBN recargado y se intenta otro alta con el mismo ISBN
- **THEN** la API responde 409

### Requirement: Escrituras del catálogo con sesión
Alta, PATCH y baja SHALL exigir una sesión válida y el rol ADMIN vigente en la base (RN-04): sin sesión, la API SHALL responder 401, y con sesión pero sin el rol ADMIN, 403, en los dos casos sin escribir nada.

#### Scenario: Alta sin sesión
- **WHEN** se intenta un alta, un PATCH o una baja sin la cookie de sesión
- **THEN** la API responde 401 y no se escribe nada

#### Scenario: Usuario sin el rol ADMIN
- **WHEN** un usuario con sesión y rol VENDEDOR intenta un alta, un PATCH o una baja
- **THEN** la API responde 403 y no se escribe nada

#### Scenario: Usuario con el rol ADMIN
- **WHEN** un usuario con sesión y el rol ADMIN vigente da de alta un libro
- **THEN** la API responde 201 y el movimiento «Stock inicial» queda a su nombre

### Requirement: Listado de libros con envoltorio y filtros
`GET /libros/` SHALL responder con el envoltorio `{items, total, page, size, pages}` de la paginación común, con los filtros opcionales `titulo` (parámetro ligado, sin distinguir mayúsculas) y `genero_id`, sólo con libros vigentes. `total` SHALL contar con los mismos filtros, y una página más allá de la última SHALL dar 422.

#### Scenario: Búsqueda con inyección
- **WHEN** se busca `titulo=' OR '1'='1`
- **THEN** la API responde 200 con `items` vacío y `total` 0

#### Scenario: Paginación con filtro
- **WHEN** se busca un título que coincide con un solo libro con `size=1`, y después la misma búsqueda con `page=2`
- **THEN** la primera responde 200 con `total` 1 y `pages` 1, y la segunda responde 422
