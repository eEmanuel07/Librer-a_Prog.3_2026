# Design: j4-aviso-comprobante

## UI Mockups

Decision: no (no UI)

## Context

`POST /ventas/` llama a `service.crear_venta`, que confirma la venta al cerrar el bloque del Unit of Work (J3). Si algo falla, el servicio lanza `Conflicto` y el router responde 409. Después de un alta correcta, el router agenda `service.avisar_comprobante(venta_id, email, total)` con `BackgroundTasks`; esa función espera con `asyncio.sleep(0.5)` y escribe una línea con el logger `uvicorn.error`.

## Goals / Non-Goals

**Goals:**
- Probar que el aviso corre después de la respuesta, una sola vez y con los datos de la venta confirmada.
- Probar que una venta rechazada (409) o un cuerpo inválido (422) no generan aviso.
- Probar que el mensaje sale por el logger de uvicorn, visible con el arranque normal.

**Non-Goals:**
- No se manda un correo real ni se usa una cola de tareas.
- No se reintenta el aviso si el proceso se cae.

## Decisions

### 1. Agendar después de que el servicio devuelve
- **Decisión:** `tareas.add_task(...)` va después de `await service.crear_venta(...)`, fuera del `try`. Si el servicio lanza `Conflicto`, el 409 sale antes y la tarea nunca se agenda.
- **Por qué:** que el servicio devuelva quiere decir que el commit ya se hizo, así que el aviso no puede salir por una venta que no quedó guardada.

### 2. Datos simples, no objetos del ORM
- **Decisión:** la tarea recibe `venta.id`, `venta.cliente.email` y `venta.total`, no la venta ni la sesión.
- **Por qué:** la tarea corre cuando la petición ya terminó y la sesión está cerrada; un objeto del ORM podría intentar una carga perezosa sobre una sesión que ya no existe.

### 3. Logger `uvicorn.error`
- **Decisión:** el mensaje se escribe con `logging.getLogger("uvicorn.error")`.
- **Por qué:** uvicorn deja ese logger configurado en INFO con su propio handler, así que el mensaje sale con `uvicorn app.main:app` sin tocar la configuración global. Un logger propio sin configurar no se vería, y configurar `logging.basicConfig` duplicaría las líneas de `SQL_ECHO`.

### 4. Cómo se prueba el "después"
- **Decisión:** el test envuelve la app con un ASGI mínimo que anota cuándo se envía el último fragmento del cuerpo de la respuesta, y reemplaza el aviso por uno que también anota. Se compara el orden de las anotaciones.
- **Por qué:** `TestClient` espera a que terminen las tareas antes de devolver, así que medir desde el cliente no alcanza; mirar los mensajes ASGI muestra el orden real.

## Risks / Trade-offs

- **[Riesgo] El aviso se pierde si el proceso se reinicia:** aceptado por la consigna; se anota como límite.
- **[Trade-off] Los tests reemplazan el aviso:** el test de orden no espera los 0,5 s; el `sleep` y el mensaje se prueban aparte, directamente sobre `avisar_comprobante`. Contra PostgreSQL y con el arranque normal, la respuesta volvió en 0,1 s y la línea del aviso apareció en la consola después.
