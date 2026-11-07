# Design: libros-rol-admin

## Context

`requiere_rol(*roles)` (R2) depende de `get_usuario_actual`, consulta los roles vigentes en la base con la misma sesión de la petición (RN-04, regla 14) y devuelve el `Usuario`. Desde R3, el router protegido de libros está montado en el grupo protegido, que además controla el cambio obligatorio de contraseña.

## Decisions

### 1. Cambiar la dependencia en el router, sin tocar el service

Cada endpoint de escritura reemplaza `usuario: Usuario = Depends(get_usuario_actual)` por `usuario: Usuario = Depends(requiere_rol("ADMIN"))`. Como las dos devuelven el `Usuario`, el alta y la reposición siguen pasando `usuario.id` al service para el movimiento. La autorización queda en la capa HTTP, como en los demás módulos.

### 2. `GET /libros/{id}/movimientos` también es de ADMIN

La tabla de endpoints de la consigna lo pone en el grupo protegido con rol ADMIN: es el historial del stock, no parte del catálogo público.

### 3. Tests: el usuario de prueba pasa a tener el rol ADMIN

Los tests reemplazan `get_usuario_actual` por el usuario de prueba. `requiere_rol` depende de `get_usuario_actual`, así que ese reemplazo también le llega a él, y la consulta de roles corre sobre la base de prueba. Por eso el usuario de prueba recibe una asignación ADMIN, y se agrega un VENDEDOR para probar el 403.

## Risks / Trade-offs

- **[Riesgo] Clientes de la API que hoy escriben con un usuario sin ADMIN** → pasan a recibir 403. Es lo que pide la consigna; el seed (R8) le da ADMIN a `admin@example.com` y `admin2@example.com`.
