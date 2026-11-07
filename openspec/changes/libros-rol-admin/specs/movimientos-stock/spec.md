## MODIFIED Requirements

### Requirement: Reposición y movimientos con sesión
La reposición y la consulta de movimientos SHALL exigir una sesión válida y el rol ADMIN vigente en la base (RN-04): sin sesión, la API SHALL responder 401, y con sesión pero sin el rol ADMIN, 403, en los dos casos sin escribir nada.

#### Scenario: Sin sesión
- **WHEN** se intenta reponer o consultar movimientos sin la cookie de sesión
- **THEN** la API responde 401 y el stock no cambia

#### Scenario: Usuario sin el rol ADMIN
- **WHEN** un usuario con sesión y rol VENDEDOR intenta reponer o consultar movimientos
- **THEN** la API responde 403 y el stock no cambia
