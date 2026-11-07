## ADDED Requirements

### Requirement: Consulta paginada del historial de seguridad (RN-16)
El sistema SHALL proveer el endpoint `GET /eventos` (exclusivo para usuarios con rol `ADMIN` vigente) que devuelva las filas de `evento_seguridad` dentro del envoltorio de paginación `{items, total, page, size, pages}`, respondiendo HTTP 422 si se solicita una página inexistente y HTTP 403 si el usuario no posee el rol `ADMIN`.

#### Scenario: Administrador consulta el historial de seguridad paginado
- **WHEN** un administrador autenticado envía `GET /eventos?page=1&size=20`
- **THEN** el sistema responde HTTP 200 con `{items, total, page, size, pages}` listando las altas de personal, asignaciones/revocaciones de rol, cambios de contraseña y eventos del sistema

#### Scenario: Página más allá de la última en GET /eventos responde 422
- **WHEN** un administrador solicita una página mayor a `pages` en `GET /eventos`
- **THEN** el sistema responde HTTP 422 Unprocessable Entity

#### Scenario: Usuario sin rol ADMIN recibe 403 en GET /eventos
- **WHEN** un usuario autenticado sin rol `ADMIN` vigente envía `GET /eventos`
- **THEN** el sistema responde HTTP 403 Forbidden
