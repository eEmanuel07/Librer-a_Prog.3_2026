# Spec Delta: ventas

## ADDED Requirements

### Requirement: Detalle de una venta para el personal o el cliente dueño
El sistema SHALL responder `GET /ventas/{id}` con el detalle de la venta (cliente, renglones y título de cada libro) al personal (VENDEDOR o ADMIN según los roles vigentes en la base) o al cliente dueño de la venta (RN-14). La ruta MUST NOT usar `requiere_rol`: decide el servicio, primero quién pide y qué relación tiene con la venta, y después qué devuelve.

#### Scenario: Sin sesión
- **WHEN** se pide `GET /ventas/{id}` sin cookie `access_token`
- **THEN** el sistema responde 401

#### Scenario: El personal ve cualquier venta
- **WHEN** un usuario con rol vigente VENDEDOR o ADMIN pide el detalle de una venta existente
- **THEN** el sistema responde 200 con la venta, su cliente y sus renglones

#### Scenario: La cliente ve su venta y no la ajena (C-06)
- **WHEN** una usuaria sin rol de personal pide el detalle de una venta de su ficha de cliente, y después el de una venta de otro cliente
- **THEN** el sistema responde 200 a la suya y 403 «No tenés permiso para ver esta venta» a la ajena

#### Scenario: Rol revocado o vencido
- **WHEN** un usuario cuyo rol VENDEDOR está revocado o vencido en la base pide una venta que no es suya
- **THEN** el sistema responde 403, aunque el token todavía nombre ese rol

#### Scenario: Venta inexistente
- **WHEN** el personal o un cliente piden un id de venta que no existe
- **THEN** el sistema responde 404 «La venta no existe»

### Requirement: Detalle con un número fijo de consultas
El sistema SHALL armar el detalle de una venta con una cantidad de consultas que no depende de la cantidad de renglones (C-15), y SHALL mostrar el título de los libros aunque estén dados de baja.

#### Scenario: Dos y cuatro renglones (C-15)
- **WHEN** el personal pide el detalle de una venta con 2 renglones y el de otra con 4
- **THEN** las dos peticiones ejecutan la misma cantidad de consultas

#### Scenario: Libro dado de baja
- **WHEN** se pide el detalle de una venta que tiene un libro dado de baja
- **THEN** el renglón sigue mostrando su título y la cantidad de consultas no cambia
