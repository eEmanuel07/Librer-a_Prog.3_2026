# Funcionalidades

Organizadas por **ejercicio de la consigna** (cada uno es una épica con su puntaje), con las issues del tablero que lo cubren. El estado de cada issue está en `CHANGES.md`.

## Ej. 1 · Proyecto, configuración y ciclo de vida — 6 pts (pág. 9) · B1, B2

- `Settings` con pydantic-settings, la URL de la base armada con un `@computed_field` y el tamaño del pool en la configuración.
- Motor y fábrica de sesiones creados en el **lifespan** y guardados en `app.state`, nunca al importar un módulo.
- `get_session`: una sesión por petición, `expire_on_commit=False`, cerrada al terminar.
- El lifespan calcula una vez el hash ficticio del login y al apagar hace `dispose()` del motor.
- `GET /health/live` no toca la base; `GET /health/ready` ejecuta `SELECT 1` y da 503 si la base no responde.

## Ej. 2 · Modelos, relaciones y migraciones — 10 pts (pág. 10) · E0, E1, H1, B6, E6

- Modelos nuevos, y `Cliente` y `Libro` modificados, con sus dos índices únicos parciales (`postgresql_where`).
- Migración 3 **autogenerada y leída** antes de aplicarla, con un comentario que lo diga y que explique cualquier corrección a mano.
- Migración 4 **a mano**: el disparador de sólo agregado (la comparación automática no ve funciones ni disparadores).
- `upgrade head` sobre una base vacía, `downgrade base` y otra vez `upgrade head` tienen que funcionar.

## Ej. 3 · Contratos y CRUD — 8 pts (pág. 10) · B5, E4, E5, J6, J7, R7

- Contratos separados de los modelos; los de entrada con `extra="forbid"` (nadie se registra con un rol ni edita el stock por PATCH).
- Ninguna respuesta incluye `password_hash`. Los PATCH aplican sólo lo enviado (`exclude_unset`).
- Códigos: 201 crear, 204 baja de libro, 404 recurso de la ruta inexistente, 409 choque con lo guardado, 422 contrato no cumplido.
- Listados con el envoltorio `{items, total, page, size, pages}`: `page` desde 1, `size` de 1 a 100 (20 por defecto), una página más allá de la última da 422, y `total` cuenta con los mismos filtros. Sin resultados hay una página vacía.

## Ej. 4 · Autenticación — 14 pts (pág. 11) · H2, H3, H4, H6, H7

- bcrypt con costo configurable, siempre fuera del bucle (`to_thread`) y bajo un semáforo. El hash se calcula **antes** de abrir la transacción.
- Todo campo que va a bcrypt acepta como máximo 72 **bytes** (422, no 500).
- Orden del login: primero el límite (RN-07, 429 con `Retry-After` sin calcular hash) y después la verificación, contra el hash real o el ficticio (RN-08).
- JWT con `sub`, `exp` y los roles vigentes al emitirlo, sólo en la cookie `access_token` (`HttpOnly`, `SameSite=Lax`, `Max-Age`, `Secure` configurable). El cuerpo del login no lo trae.
- Registro (RN-02), logout (borra la cookie), `GET /auth/yo` (usuario, roles vigentes y roles del token). Cambiar la contraseña no invalida sesiones ni emite un token nuevo.

## Ej. 5 · Autorización — 12 pts (pág. 11) · R1–R6, R9

- `get_usuario_actual` (401) y `requiere_rol` (403, roles vigentes en la base en cada petición, RN-04).
- Asignar roles con vencimiento opcional y revocarlos sin borrar la fila; reasignar un rol vencido cierra la fila anterior y abre otra. Un vencimiento sin zona horaria o en el pasado da 422, no 409.
- Autoprotección (RN-05). Cambio obligatorio de contraseña con dos grupos de rutas en `main.py` (RN-06). Lo propio (RN-14). Historial de seguridad (RN-16) con el actor `SISTEMA` en los datos iniciales.

## Ej. 6 · Repositorios y Unit of Work — 16 pts (pág. 12) · B3, B4, E2, E3

- `BaseRepository[T]` recibe la sesión **y la clase del modelo**, con `get_by_id`, `get_all`, `count`, `add`, `update` y `delete`. `SoftDeleteRepository[T]` filtra los dados de baja y suma `get_by_id_including_deleted` y `soft_delete`.
- `add` y `update` hacen `flush()`, nunca `commit()`. Los métodos se nombran por lo que traen, y la precarga va dentro del método.
- UoW base: confirma al salir, revierte ante una excepción, no cierra la sesión. Un UoW por módulo. El router lo construye y el servicio lo abre.
- RN-02, RN-10 y RN-16, cada una en un solo bloque. El usuario actual y la verificación de rol comparten la sesión del UoW (una conexión por petición).
- Un único punto de escritura del stock (RN-11).

## Ej. 7 · Integridad: sólo agregado e intento de acceso — 10 pts (pág. 12) · E6, E7, H5

- El disparador rechaza todo UPDATE o DELETE sobre `movimiento_stock` (RN-12).
- Cada intento de login se anota en `intento_acceso` con **sesión y transacción propias**, con un comentario que explique qué hace distinto, por qué no comparte la transacción y cuál es su costo.

## Ej. 8 · Lecturas sin N+1 y asincronía — 6 pts (pág. 13) · J3, J4, J5, J8

- Toda relación que se devuelve se precarga en el repositorio. El detalle de una venta usa un número fijo de consultas, aunque el libro esté dado de baja.
- Ninguna lectura depende de la carga perezosa; ninguna llamada bloqueante.
- El aviso del comprobante va con `BackgroundTasks`, corre después de la respuesta y **sólo si la operación se confirmó**. Tiene que verse con el arranque normal de uvicorn, así que no sirve un logger propio sin configurar.

## Ej. 9 · Contenedor: la imagen — 11 pts (págs. 14-15) · J1, J2

Sobre el **TP 1-4**, no sobre el parcial. El detalle está en [11](11_entrega_y_despliegue.md).

## Ej. 10 · Despliegue en el VPS — 7 pts (pág. 16) · E8, E9

El TP 1-4 en línea en la URL de `DEPLOY.md` hasta que se publiquen las notas. El detalle está en [11](11_entrega_y_despliegue.md).

## Cierre y entrega · B7, E10, H8, I1, R8, H7, R9, E7, J8

`seed.py`, archivos `.http` y evidencias, README, revisión de requisitos no funcionales, prueba de integración y armado del `.zip`.

## Casos de prueba mínimos (págs. 21-23)

| Caso | Qué demuestra | Dónde |
|---|---|---|
| C-01 a C-05 | Parámetro no entero, registro, cookie, login igual exista o no el correo, 429 | `test/auth.http` (H7) |
| C-06 a C-09 | 401 contra 403 y lo propio, revocar rol con sesión abierta, autoprotección, cambio obligatorio | `test/seguridad.http` (R9) |
| C-10 a C-12 | Venta válida, venta sin stock suficiente (nada escrito), cliente o libro inexistente o dado de baja | `test/ventas.http` (J8) |
| C-13, C-14 | Reponer, dar de baja y recargar un ISBN; UPDATE y DELETE rechazados por el disparador | `test/libros.http`, `test/solo_agregado.sql` (E7) |
| C-15 | Las mismas consultas para una venta de 2 y de 4 renglones | `evidencia/` (J8) |
| C-16 | Inyección en la búsqueda, paginación con filtro, PATCH parcial, PATCH del stock | `.http` de libros |
| D-01 a D-08 | Imagen, contenedor healthy, URL pública, reinicio, sin `DATABASE_URL`, sin secretos, usuario no root, aviso en los logs | `despliegue/evidencia/` (J2, E9) |

Antes de cada archivo `.http` se corre `python seed.py` (pág. 21).
