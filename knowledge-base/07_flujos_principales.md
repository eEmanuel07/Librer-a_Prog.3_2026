# Flujos Principales

## Flujo 1: Petición autenticada (cualquier ruta protegida)
**Disparador:** pedido a una ruta del grupo protegido. **Actor:** usuario con sesión.

1. FastAPI resuelve `get_session` **una sola vez**: una sesión por petición (pág. 9).
2. `get_usuario_actual` lee la cookie `access_token` y valida el token y el usuario. Si falla, responde 401 (pág. 11).
3. El control del cambio obligatorio, montado una vez en el grupo protegido, responde 403 si está pendiente (RN-06).
4. `requiere_rol` consulta los roles vigentes en la base con **la misma sesión**. Si no tiene el rol, responde 403 (RN-04).
5. El router construye el UoW del módulo con esa misma sesión y se lo pasa al servicio sin abrirlo.
6. El servicio abre el UoW con `async with`, aplica las reglas y, al salir del bloque, el UoW confirma o revierte.

Una sola conexión del pool por petición (pág. 12).

**Casos de error:** sin cookie, token vencido o usuario inactivo → 401. Rol faltante o cambio pendiente → 403. Choque con la base → 409 con mensaje propio (RN-15).

## Flujo 2: Login (RN-07, RN-08; págs. 7, 11-12)
**Disparador:** `POST /auth/login`. **Actor:** cualquiera.

1. Validar el contrato (contraseña de hasta 72 bytes, si no 422).
2. Contar los fallos de `(email, ip)` de los últimos 60 s en `intento_acceso`. Con 5 o más → 429 con `Retry-After`, **sin calcular ningún hash**.
3. Buscar el usuario y verificar la contraseña **fuera de la transacción**: contra su hash, o contra el hash ficticio si el correo no existe o el usuario está inactivo.
4. Anotar el intento (correcto o fallido) en `intento_acceso` con **sesión y transacción propias**, que se confirman siempre.
5. Si falló → 401 con el mismo mensaje y el mismo tiempo, exista o no el correo.
6. Si anduvo → JWT con los roles vigentes, en la cookie `HttpOnly`. El cuerpo trae `mensaje`, `debe_cambiar_password` y `expira_en_segundos` (pág. 19).

## Flujo 3: Auto-registro (RN-02; pág. 7)
**Disparador:** `POST /auth/registro`. **Actor:** visitante.

1. Calcular el hash de la contraseña **antes** de abrir la transacción (pág. 11).
2. En **un solo** bloque del UoW: crear el usuario, su rol CLIENTE y su ficha de cliente.
3. Si el correo ya es de un usuario o de un cliente → 409 con mensaje propio, sin dejar filas sueltas y sin apropiarse de la ficha existente (C-02).

## Flujo 4: Registrar una venta (RN-09, RN-10, RN-11; págs. 7, 12-13)
**Disparador:** `POST /ventas`. **Actor:** VENDEDOR o ADMIN.

1. El cuerpo trae `cliente_id` y renglones (`libro_id`, `cantidad`); nunca precio, total ni fecha (pág. 18).
2. En **un solo** bloque del UoW:
   - leer los libros vigentes y sus precios;
   - crear la venta con sus renglones, el precio copiado de cada libro y el total calculado por el servidor;
   - descontar el stock de cada libro **por el punto único de escritura** y dejar un movimiento por renglón.
3. Si un libro no alcanza, no existe o está dado de baja → 409, y no queda **ninguna** escritura (C-11, C-12).
4. Después de confirmar, el router agenda el aviso del comprobante con `BackgroundTasks`. Corre después de la respuesta y sólo si la venta se confirmó (pág. 13).

**Invariante:** después de cada venta, para cada libro, `stock` es igual a la suma de sus movimientos (pág. 6).

## Flujo 5: Alta, reposición y baja de un libro (RN-11, RN-13; págs. 7, 18-19, 22)
**Actor:** ADMIN.

- **Alta:** viaja `stock_inicial` (no `stock`), y el alta deja el movimiento "Stock inicial".
- **Reposición:** `POST /libros/{id}/reponer` deja un movimiento de entrada y responde 200.
- **Baja:** `DELETE /libros/{id}` escribe `borrado_en` y responde 204. El libro deja de aparecer en el catálogo, no se vende ni se repone (409), y las ventas viejas siguen mostrando su título.
- **Mismo ISBN:** una vez dado de baja, se puede volver a cargar (201). Un segundo libro vigente con ese ISBN da 409 (C-13).

## Flujo 6: Cambio de rol o alta de personal (RN-03, RN-05, RN-16)
**Actor:** ADMIN.

1. En **un solo** bloque: escribir la asignación, o la revocación con `revocada_en`, y la línea de `evento_seguridad`.
2. Revocarse el propio ADMIN, o dejar el sistema sin administradores → 409. Dos asignaciones abiertas del mismo rol → 409 (índice parcial).
3. La revocación corta el permiso de la sesión ya abierta en la petición siguiente (C-07).
