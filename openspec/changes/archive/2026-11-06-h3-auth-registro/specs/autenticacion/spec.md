# Spec Delta: autenticacion

## ADDED Requirements

### Requirement: Auto-registro de cliente y usuario en un solo bloque
El sistema SHALL proveer el endpoint `POST /auth/registro` para registrar visitantes, creando atómicamente el usuario, su rol `CLIENTE` y su ficha de cliente en un único Unit of Work, respondiendo HTTP 201 Created.

#### Scenario: Registro exitoso
- **WHEN** un visitante envía `POST /auth/registro` con nombre, correo válido y contraseña válida
- **THEN** el sistema crea el usuario activo, la asignación del rol CLIENTE y el cliente vinculado, respondiendo 201 Created con los datos registrados y sin incluir password_hash

### Requirement: Atomicidad y prevención de apropiación de fichas
Si el correo electrónico ya pertenece a un usuario o a un cliente existente, el sistema SHALL rechazar el registro con HTTP 409 y revertir cualquier cambio, asegurando que no queden filas creadas ni se modifique la ficha de cliente existente.

#### Scenario: Correo ya registrado como cliente
- **WHEN** se intenta registrar un usuario con un correo que ya existe en la tabla de clientes
- **THEN** el sistema responde 409 con mensaje propio y no crea el usuario, el rol ni altera el cliente existente

#### Scenario: Correo ya registrado como usuario
- **WHEN** se intenta registrar un usuario con un correo que ya existe en la tabla de usuarios
- **THEN** el sistema responde 409 con mensaje propio y no deja registros huérfanos

### Requirement: Validación estricta y restricción de campos en registro
El contrato de `POST /auth/registro` SHALL rechazar campos adicionales (`extra="forbid"`) y validar que la contraseña no exceda los 72 bytes en UTF-8, respondiendo HTTP 422 ante cualquier violación.

#### Scenario: Intento de auto-asignación de roles
- **WHEN** un cliente envía campos no contemplados en el contrato como un rol
- **THEN** el sistema responde 422 Unprocessable Entity sin procesar el registro

#### Scenario: Contraseña que excede 72 bytes en registro
- **WHEN** se envía una contraseña de más de 72 bytes en UTF-8
- **THEN** el sistema responde 422 sin ejecutar el algoritmo de hash ni provocar un error 500
