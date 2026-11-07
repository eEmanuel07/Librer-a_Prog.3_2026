# Proposal: j4-aviso-comprobante

> Issue: #57 ([J4] — Aviso del comprobante con BackgroundTasks). Consigna: `Parcial_Cap1a6_Consigna.pdf`, Ejercicio 8 (pág. 13), caso C-10 (pág. 22).

## Why

Al registrar una venta, la consigna pide agendar con `BackgroundTasks` el aviso del comprobante al cliente, simulado con `await asyncio.sleep(0.5)` y un mensaje en el registro. Tiene que correr **después** de enviar la respuesta, **sólo si** la venta se confirmó, y verse en la consola con el arranque normal de uvicorn. El aviso ya existía desde el TP; faltaba comprobar esas tres condiciones y dejarlas en la spec.

## What Changes

- **Tests (`tests/test_ventas_aviso_comprobante.py`)**:
  - Venta confirmada (201): el aviso corre una sola vez, con el id, el email del cliente y el total, y **después** de que termina de enviarse la respuesta.
  - Venta rechazada (409 por stock, libro o cliente inexistente) y cuerpo inválido (422): no hay aviso.
  - `avisar_comprobante` espera con `asyncio.sleep(0.5)` y escribe en el logger `uvicorn.error` en INFO.
- **Router (`app/modules/ventas/router.py`)**: sólo se aclara el comentario de por qué el aviso se agenda únicamente cuando la venta se confirmó. No cambia el comportamiento.

## Capabilities

### New Capabilities

(ninguna)

### Modified Capabilities

- `ventas`: agrega el requisito del aviso del comprobante.

## Impact

- **Comportamiento:** ninguno nuevo; queda probado y especificado.
- **Límite conocido:** el aviso vive en memoria del proceso; si el servidor se reinicia antes de que corra, se pierde (la consigna lo acepta; las colas de tareas son del capítulo 8).
