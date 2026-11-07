# Spec Delta: ventas

## ADDED Requirements

### Requirement: Listado de todas las ventas para el personal
El sistema SHALL responder `GET /ventas` sólo al personal (VENDEDOR o ADMIN según los roles vigentes en la base) con el envoltorio `{items, total, page, size, pages}`, ordenado por id, donde cada ítem trae la venta y su cliente.

#### Scenario: Sin sesión
- **WHEN** se pide `GET /ventas` sin cookie `access_token`
- **THEN** el sistema responde 401

#### Scenario: Un cliente o un rol revocado
- **WHEN** lo pide un usuario sin rol vigente de personal
- **THEN** el sistema responde 403 «No tenés permiso para ver todas las ventas»

#### Scenario: Página de ventas
- **WHEN** el personal pide `GET /ventas?size=2` y hay 5 ventas
- **THEN** el sistema responde 200 con 2 ítems, `total` 5, `page` 1, `size` 2 y `pages` 3

#### Scenario: Página de más o tamaño inválido
- **WHEN** se pide una página más allá de la última, o `size` fuera de 1 a 100
- **THEN** el sistema responde 422 (por ejemplo «La página 4 no existe: hay 3»)

### Requirement: Mis ventas
El sistema SHALL responder `GET /mis-ventas` a cualquier usuario autenticado con las ventas del cliente asociado a ese usuario, con el mismo envoltorio (RN-14).

#### Scenario: La cliente ve sólo las suyas
- **WHEN** una usuaria con ficha de cliente pide `GET /mis-ventas`
- **THEN** el sistema responde 200 sólo con sus ventas y `total` cuenta sólo las suyas

#### Scenario: Usuario sin ficha de cliente
- **WHEN** lo pide un usuario sin ficha de cliente
- **THEN** el sistema responde 200 con `items` vacío, `total` 0 y `pages` 1

#### Scenario: Sin sesión
- **WHEN** se pide `GET /mis-ventas` sin cookie `access_token`
- **THEN** el sistema responde 401

### Requirement: Listados con consultas fijas
El sistema SHALL armar cada listado con una cantidad de consultas que no depende del tamaño de la página: el conteo y la página (venta JOIN cliente), más la de roles en `GET /ventas`.

#### Scenario: Distintos tamaños de página
- **WHEN** se pide el mismo listado con `size` 1 y con `size` 4
- **THEN** las dos peticiones ejecutan la misma cantidad de consultas
