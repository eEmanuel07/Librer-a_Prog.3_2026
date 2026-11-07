## ADDED Requirements

### Requirement: Alta de personal con contraseña provisoria y evento de seguridad en la misma transacción (RN-16)
El sistema SHALL proveer el endpoint `POST /usuarios` (exclusivo para usuarios con rol `ADMIN` vigente) que cree una cuenta de personal con `activo = True` y `debe_cambiar_password = True`, calculando el hash bcrypt antes de abrir la transacción y registrando en el mismo bloque del Unit of Work una fila en `evento_seguridad` con el correo del administrador como `actor`, devolviendo HTTP 201 sin incluir `password_hash`.

#### Scenario: Administrador da de alta a un integrante del personal
- **WHEN** un administrador autenticado envía `POST /usuarios` con `nombre`, `email` y `password` válidos (hasta 72 bytes UTF-8)
- **THEN** el sistema crea el usuario con `debe_cambiar_password = True`, registra el evento en `evento_seguridad` en la misma transacción y responde HTTP 201 con los datos del usuario sin `password_hash`

#### Scenario: Alta de personal con correo duplicado responde 409 y no deja evento de seguridad (RN-01, RN-16)
- **WHEN** un administrador envía `POST /usuarios` con un `email` que ya pertenece a otro usuario
- **THEN** el sistema revierte la transacción, no deja registro en `evento_seguridad` y responde HTTP 409 Conflict con mensaje propio

#### Scenario: Usuario sin rol ADMIN recibe 403 al intentar dar de alta personal (C-06)
- **WHEN** un usuario autenticado sin rol `ADMIN` vigente envía `POST /usuarios`
- **THEN** el sistema responde HTTP 403 Forbidden
