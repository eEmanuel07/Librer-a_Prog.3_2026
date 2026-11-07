## MODIFIED Requirements

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
