# Tasks: j4-aviso-comprobante

## 1. Verificación del aviso

- [x] 1.1 Test HTTP: con una venta confirmada, el aviso corre una vez, con id, email y total, después de que se envía la respuesta
- [x] 1.2 Test HTTP: con 409 (stock, libro inexistente, cliente inexistente) y con 422, no hay aviso
- [x] 1.3 Test de `avisar_comprobante`: espera con `asyncio.sleep(0.5)` y escribe en `uvicorn.error` en INFO
- [x] 1.4 Comprobar que los tests fallan si el aviso se llama adentro del handler en lugar de agendarlo

## 2. Router

- [x] 2.1 Aclarar en el comentario del router por qué el aviso sólo se agenda si la venta se confirmó

## 3. Verificación final

- [x] 3.1 Suite completa (`python -m unittest discover -s tests`): 83 tests OK
- [x] 3.2 Contra PostgreSQL con `uvicorn app.main:app`: la venta respondió 201 en 0,1 s y la línea del aviso no estaba todavía en la consola; una petición hecha mientras el aviso esperaba respondió 200 en 2 ms; recién después apareció «Comprobante de la venta…»; la venta rechazada (409) no dejó aviso

## Workflow follow-up

- Abrir PR hacia `main` con título `test(ventas): aviso del comprobante después de confirmar la venta` y `Closes #57`.
