# Spec Delta: autenticacion

## ADDED Requirements

### Requirement: Cierre de sesión seguro e idempotente
El sistema SHALL proveer el endpoint `POST /auth/logout` que elimina la cookie `access_token` del cliente respondiendo HTTP 200 OK de forma idempotente, funcione o no exista una sesión previa.

#### Scenario: Cierre de sesión exitoso
- **WHEN** un cliente o usuario envía una petición `POST /auth/logout`
- **THEN** el sistema responde 200 OK con mensaje de sesión cerrada y fija la cookie `access_token` expirada o vacía para eliminarla del cliente

### Requirement: Consulta de identidad y roles de sesión
El sistema SHALL proveer el endpoint `GET /auth/yo` que requiere autenticación válida y retorna los datos del usuario autenticado, contrastando los roles vigentes consultados en la base de datos contra los roles presentes en el token JWT.

#### Scenario: Consulta de usuario autenticado
- **WHEN** un usuario autenticado envía `GET /auth/yo` con su cookie de sesión válida
- **THEN** el sistema responde 200 OK con su id, nombre, email, estado de `debe_cambiar_password`, la lista de roles vigentes leída de la base de datos y la lista de roles del token

#### Scenario: Intento de consulta sin sesión o con sesión inválida
- **WHEN** un cliente envía `GET /auth/yo` sin cookie `access_token` o con un token vencido o manipulado
- **THEN** el sistema responde 401 Unauthorized sin procesar la consulta

### Requirement: Cambio de contraseña con auditoría en la misma transacción
El sistema SHALL proveer el endpoint `POST /auth/cambiar-password` para que el usuario autenticado actualice su contraseña tras validar la actual, actualizando la clave, desactivando la obligación de cambio y registrando una fila en `evento_seguridad` en la misma transacción (RN-16), sin emitir un token nuevo ni invalidar la sesión existente.

#### Scenario: Cambio de contraseña exitoso
- **WHEN** un usuario autenticado envía `POST /auth/cambiar-password` con su contraseña actual correcta y una nueva contraseña válida de hasta 72 bytes UTF-8
- **THEN** el sistema actualiza la contraseña en la base de datos, fija `debe_cambiar_password` en False y añade un registro en `evento_seguridad` en el mismo bloque de Unit of Work, respondiendo 200 OK sin alterar la cookie de sesión

#### Scenario: Contraseña actual incorrecta
- **WHEN** un usuario envía `POST /auth/cambiar-password` con una contraseña actual errónea
- **THEN** el sistema responde 401 Unauthorized con mensaje de credenciales inválidas y no modifica la base de datos ni registra auditoría de cambio

#### Scenario: Nueva contraseña excede límite de 72 bytes
- **WHEN** un usuario envía una contraseña nueva que supera los 72 bytes en UTF-8 o incluye campos no permitidos
- **THEN** el sistema responde 422 Unprocessable Entity sin calcular hash bcrypt ni modificar la base
