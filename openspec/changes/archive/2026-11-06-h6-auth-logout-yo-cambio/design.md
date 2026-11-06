# Design: h6-auth-logout-yo-cambio

## UI Mockups

Decision: no (no UI)

## Context

El sistema ya cuenta con inicio de sesión (`POST /auth/login` — H4) y auto-registro (`POST /auth/registro` — H3) emitiendo o reconociendo tokens JWT firmados en la cookie HttpOnly `access_token`.
Para completar el ciclo de vida de la sesión (Ejercicio 4, RN-06 y RN-16), se requiere que los usuarios puedan cerrar sesión, inspeccionar su identidad y roles, y actualizar su propia contraseña registrando la auditoría correspondiente.

## Goals / Non-Goals

**Goals:**
- Implementar `POST /auth/logout` que elimina la cookie `access_token` de manera idempotente.
- Implementar `GET /auth/yo` mostrando `id`, `email`, `nombre`, `debe_cambiar_password`, `roles` (roles vigentes en la base según RN-04) y `roles_token` (los roles con los que se generó el JWT).
- Implementar `POST /auth/cambiar-password` con validación estricta de 72 bytes, cálculo de hash antes de la transacción, actualización de hash, desactivación de `debe_cambiar_password` y creación de `EventoSeguridad` en un solo bloque atómico del `UsuarioUnitOfWork` (RN-16).
- Proporcionar la dependencia `get_usuario_actual` en `app/core/dependencies.py` para resolver al usuario autenticado a partir de la cookie de la petición.

**Non-Goals:**
- No se implementa en esta tarea la restricción por roles de otras rutas (`requiere_rol` — R2).
- No se implementa la separación en dos grupos de rutas en `main.py` (R3).
- No se invalida la sesión ni se emite un nuevo token tras cambiar la contraseña (la consigna pág. 11 especifica que cambiar la contraseña no invalida sesiones ni emite token nuevo).

## Decisions

### 1. Dependencia de autenticación `get_usuario_actual`
- **Decisión:** Implementar `get_usuario_actual` en `app/core/dependencies.py` leyendo la cookie `access_token`, decodificando el JWT con `app.core.security.decodificar_access_token` y consultando el usuario activo en la sesión del UoW (`get_usuario_uow`).
- **Alternativas consideradas:** Requerir cabecera `Authorization: Bearer <token>`. Descartado porque la consigna prohíbe explícitamente tokens en encabezados o cuerpo; el token reside única y exclusivamente en la cookie HttpOnly.

### 2. Contraste de roles en `GET /auth/yo`
- **Decisión:** `GET /auth/yo` retorna dos listas de roles: `roles` (consultados en la tabla `asignacion_rol` en tiempo real para verificar vigencia, cumpliendo RN-04) y `roles_token` (los roles grabados en el payload del JWT emitido al loguearse).
- **Justificación:** Permite al cliente (y a las pruebas del caso) comprobar si los roles del usuario han cambiado o vencido desde que inició sesión sin obligarlo a reloguearse para saberlo.

### 3. Cambio de contraseña atómico con auditoría (RN-16)
- **Decisión:**
  1. Validar `password_actual` con `verificar_password(datos.password_actual, usuario.password_hash, settings)`.
  2. Calcular el hash de `password_nueva` **antes** de abrir la transacción con `await hashear_password(datos.password_nueva, settings)`.
  3. En un solo bloque `async with uow:`:
     - `usuario.password_hash = nuevo_hash`
     - `usuario.debe_cambiar_password = False`
     - `uow.usuarios.session.add(usuario)`
     - `await uow.eventos.add(EventoSeguridad(actor=usuario.email, accion="Cambio de contraseña", cuando=ahora))`
- **Justificación:** Cumple estrictamente con RN-16: el cambio de contraseña y la inserción del evento de seguridad persisten en la misma transacción o se revierten juntos.

### 4. Idempotencia en `POST /auth/logout`
- **Decisión:** `POST /auth/logout` borra la cookie `access_token` (`response.delete_cookie(key="access_token", httponly=True, samesite="lax")`) y responde 200 `{"mensaje": "Sesión cerrada"}` sin lanzar 401 si el cliente no tenía sesión previa.
- **Justificación:** Permite a cualquier cliente limpiar sus credenciales de manera segura e idempotente.

## Risks / Trade-offs

- **[Riesgo] Carga de CPU con dos operaciones bcrypt en cambio de contraseña:**
  - *Mitigación:* Se validan las contraseñas bajo el semáforo concurrente de `app/core/security.py` en hilos de trabajo independientes (`asyncio.to_thread`) y el nuevo hash se calcula antes de iniciar la transacción con la base de datos, evitando retener conexiones del pool.
- **[Riesgo] Contraseñas mayores a 72 bytes en UTF-8:**
  - *Mitigación:* Se utiliza `PasswordBcrypt` en el contrato Pydantic tanto para `password_actual` como para `password_nueva`, respondiendo 422 antes de invocar la librería nativa de bcrypt.
