# ventas Specification

## Purpose
Registra las ventas de la librería con el descuento del stock de cada libro y un movimiento por renglón, en una sola transacción y escribiendo el stock sólo por el punto único (RN-09, RN-10, RN-11).

## Requirements

### Requirement: Venta con descuento de stock en una sola transacción
El sistema SHALL registrar en `POST /ventas` la venta, sus renglones con el precio copiado de cada libro, el total calculado por el servidor, el descuento del stock de cada libro y un `movimiento_stock` por renglón en un único bloque del Unit of Work (RN-09, RN-10). El stock MUST escribirse sólo a través del punto único de escritura (RN-11).

#### Scenario: Venta válida con dos renglones (C-10)
- **WHEN** un usuario autenticado registra una venta con Rayuela (2) y Ficciones (1) para un cliente existente
- **THEN** el sistema responde 201 con los precios copiados y el total 72000, el stock de cada libro baja en la cantidad vendida y queda un movimiento negativo por renglón con el id de la venta, el usuario que la registró y el motivo «Venta»

#### Scenario: Un libro no alcanza (C-11)
- **WHEN** se registra una venta con Rayuela (1, alcanza) y Bestiario (2, hay 1)
- **THEN** el sistema responde 409 con un mensaje que nombra a Bestiario y no queda venta, renglones, descuentos ni movimientos: Rayuela sigue en 10 y en cada libro el stock coincide con la suma de sus movimientos

### Requirement: Rechazo sin escrituras de cliente o libro inválido
El sistema SHALL responder 409 con un mensaje propio, sin dejar ninguna escritura, si el cliente no existe, si un libro no existe o si un libro está dado de baja (C-12).

#### Scenario: Cliente inexistente
- **WHEN** se registra una venta para un `cliente_id` que no existe
- **THEN** el sistema responde 409 «El cliente indicado no existe» y no escribe nada

#### Scenario: Libro inexistente
- **WHEN** un renglón pide un `libro_id` que no existe
- **THEN** el sistema responde 409 «No existe el libro con id N» y no escribe nada

#### Scenario: Libro dado de baja
- **WHEN** un renglón pide un libro con `borrado_en` cargado
- **THEN** el sistema responde 409 «El libro está dado de baja», no escribe nada y el stock de ese libro no cambia

### Requirement: Ventas simultáneas del mismo libro
El sistema SHALL bloquear los libros de la venta hasta el commit, de modo que dos ventas simultáneas no descuenten el mismo stock.

#### Scenario: Último ejemplar pedido a la vez
- **WHEN** llegan a la vez varias ventas de un libro con stock 1
- **THEN** una responde 201, las demás 409 por stock insuficiente, el stock queda en 0 y hay un solo movimiento de venta

### Requirement: Registrar una venta exige sesión
El sistema SHALL responder 401 a `POST /ventas` sin una cookie de sesión válida, y SHALL guardar en cada movimiento el id del usuario autenticado.

#### Scenario: Sin sesión
- **WHEN** se envía `POST /ventas` sin cookie `access_token`
- **THEN** el sistema responde 401 y no escribe nada

### Requirement: Aviso del comprobante después de confirmar la venta
El sistema SHALL agendar con `BackgroundTasks`, al registrar una venta, el aviso del comprobante al cliente, simulado con `await asyncio.sleep(0.5)` y una línea en el registro. El aviso MUST correr después de enviar la respuesta, sólo si la venta se confirmó, y MUST verse en la consola con el arranque normal de uvicorn.

#### Scenario: Venta confirmada
- **WHEN** se registra una venta válida y el sistema responde 201
- **THEN** después de enviar la respuesta se escribe una sola línea «Comprobante de la venta N enviado a <email> (total $T)» con el logger de uvicorn

#### Scenario: Venta rechazada
- **WHEN** una venta responde 409 (stock insuficiente, libro o cliente inexistente, libro dado de baja) o 422 (cuerpo inválido)
- **THEN** no se agenda ni se escribe ningún aviso

#### Scenario: El aviso no bloquea
- **WHEN** corre el aviso
- **THEN** espera con `asyncio.sleep(0.5)` (no con una llamada bloqueante) y el servidor sigue atendiendo otras peticiones

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
