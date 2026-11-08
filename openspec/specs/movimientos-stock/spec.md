# movimientos-stock Specification

## Purpose
Define cómo entra stock a un libro después del alta y cómo se consulta su historia: la reposición pasa por el único punto de escritura del stock y deja su movimiento (RN-11), un libro dado de baja no se repone (RN-13), y los movimientos de cada libro se listan paginados, del más viejo al más nuevo, incluso después de la baja.

## Requirements

### Requirement: Reposición de stock con su movimiento
`POST /libros/{id}/reponer` SHALL recibir `cantidad` (entero mayor o igual a 1) y SHALL sumar esa cantidad al stock del libro y dejar un movimiento con motivo «Reposición», esa cantidad y el id del usuario de la sesión, en una única transacción (RN-11). Responde 200 con el libro (con su stock nuevo) y el movimiento creado.

#### Scenario: Reposición de un libro vigente
- **WHEN** un usuario con sesión repone 3 ejemplares de un libro con stock 4
- **THEN** la API responde 200 con el libro en stock 7 y un movimiento «Reposición» de cantidad 3 a nombre de ese usuario, y el stock sigue siendo la suma de los movimientos del libro

#### Scenario: Cantidad inválida
- **WHEN** se repone con `cantidad` 0, negativa o con un campo de más
- **THEN** la API responde 422 y el stock no cambia

### Requirement: Rechazo de la reposición de un libro dado de baja o inexistente
La reposición SHALL responder 409 si el libro está dado de baja (RN-13) y 404 si no existe, sin dejar movimiento en ninguno de los dos casos.

#### Scenario: Libro dado de baja
- **WHEN** se repone un libro dado de baja
- **THEN** la API responde 409 con un mensaje propio y no queda ningún movimiento nuevo

#### Scenario: Libro inexistente
- **WHEN** se repone un id que no existe
- **THEN** la API responde 404

### Requirement: Consulta paginada de los movimientos de un libro
`GET /libros/{id}/movimientos` SHALL devolver los movimientos del libro del más viejo al más nuevo, con el envoltorio `{items, total, page, size, pages}`, incluidos los de un libro dado de baja. Responde 404 si el libro no existe y 422 si la página pedida no existe.

#### Scenario: Movimientos en orden
- **WHEN** un libro tiene el movimiento «Stock inicial» y después dos reposiciones
- **THEN** la API responde 200 con `total` 3 y los tres movimientos en ese orden

#### Scenario: Movimientos de un libro dado de baja
- **WHEN** se piden los movimientos de un libro dado de baja
- **THEN** la API responde 200 con sus movimientos

#### Scenario: Libro inexistente o página inexistente
- **WHEN** se piden los movimientos de un id que no existe, o una página más allá de la última
- **THEN** la API responde 404 en el primer caso y 422 en el segundo

### Requirement: Reposición y movimientos con sesión
La reposición y la consulta de movimientos SHALL exigir una sesión válida y el rol ADMIN vigente en la base (RN-04): sin sesión, la API SHALL responder 401, y con sesión pero sin el rol ADMIN, 403, en los dos casos sin escribir nada.

#### Scenario: Sin sesión
- **WHEN** se intenta reponer o consultar movimientos sin la cookie de sesión
- **THEN** la API responde 401 y el stock no cambia

#### Scenario: Usuario sin el rol ADMIN
- **WHEN** un usuario con sesión y rol VENDEDOR intenta reponer o consultar movimientos
- **THEN** la API responde 403 y el stock no cambia
