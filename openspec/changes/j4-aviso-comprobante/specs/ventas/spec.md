# Spec Delta: ventas

## ADDED Requirements

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
