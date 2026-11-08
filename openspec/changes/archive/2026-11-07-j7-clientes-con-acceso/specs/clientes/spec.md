# Spec Delta: clientes

## ADDED Requirements

### Requirement: Módulo clientes del personal
El sistema SHALL exigir rol vigente VENDEDOR o ADMIN en la base para `POST /clientes`, `GET /clientes/{id}`, `PATCH /clientes/{id}`, `POST /clientes/{id}/perfil` y `GET /clientes/{id}/ventas`.

#### Scenario: Sin sesión
- **WHEN** se pide cualquiera de esas rutas sin cookie `access_token`
- **THEN** el sistema responde 401

#### Scenario: Un cliente o un rol revocado
- **WHEN** las pide un usuario sin rol vigente VENDEDOR ni ADMIN (por ejemplo, Ana Paz, CLIENTE)
- **THEN** el sistema responde 403 «No tiene permisos para realizar esta acción»

#### Scenario: El personal
- **WHEN** las pide un VENDEDOR o un ADMIN
- **THEN** el sistema responde como en el TP (201, 200, 404, 409 o 422 según el caso)

### Requirement: usuario_id en la ficha, sólo de lectura
El sistema SHALL mostrar en la ficha del cliente su `usuario_id` (nulo si no tiene acceso web) y SHALL rechazar con 422 un alta o un PATCH que lo envíe.

#### Scenario: Cliente con y sin acceso web
- **WHEN** el personal pide la ficha de Ana Paz y la de Lucía Fernández
- **THEN** la de Ana trae el id de su usuario y la de Lucía `usuario_id` null

#### Scenario: El personal intenta vincular un usuario
- **WHEN** un alta o un PATCH incluyen `usuario_id`
- **THEN** el sistema responde 422

### Requirement: Ventas de un cliente con el envoltorio
El sistema SHALL responder `GET /clientes/{id}/ventas` con `{items, total, page, size, pages}`, donde cada ítem es la venta con su cliente y sus renglones, con consultas fijas.

#### Scenario: Página de ventas
- **WHEN** el personal pide las ventas de un cliente con `size=1` y el cliente tiene 2 ventas
- **THEN** el sistema responde 200 con 1 ítem, `total` 2 y `pages` 2

#### Scenario: Sin ventas, cliente inexistente y página de más
- **WHEN** se piden las ventas de un cliente sin ventas, de uno que no existe o una página más allá de la última
- **THEN** el sistema responde 200 con página vacía, 404 «El cliente no existe» y 422, respectivamente
