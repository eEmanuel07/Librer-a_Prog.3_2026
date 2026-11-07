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
