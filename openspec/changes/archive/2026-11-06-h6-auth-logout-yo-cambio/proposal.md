# Proposal: h6-auth-logout-yo-cambio

> Issue: #42 ([H6] — POST /auth/logout, GET /auth/yo, POST /auth/cambiar-password). Consigna: `Parcial_Cap1a6_Consigna.pdf`, Ejercicio 4 (pág. 11), RN-06 y RN-16 (pág. 21).

## Why

Una vez autenticado o registrado un usuario, el sistema requiere endpoints para gestionar la sesión activa y la seguridad de la cuenta:
1. `POST /auth/logout`: Permite cerrar la sesión eliminando la cookie HttpOnly `access_token` de manera idempotente.
2. `GET /auth/yo`: Permite a un cliente o miembro del personal consultar su propia identidad, conociendo tanto los roles vigentes en la base de datos en tiempo real (RN-04) como los roles emitidos en el token JWT, y el estado de la bandera `debe_cambiar_password`.
3. `POST /auth/cambiar-password`: Permite a un usuario con sesión activa actualizar su propia contraseña (restringida a 72 bytes UTF-8 para bcrypt), quitando la obligación de cambio (`debe_cambiar_password = False`) y registrando atómicamente un evento de auditoría en `evento_seguridad` bajo la misma transacción (RN-16), sin invalidar sesiones existentes ni emitir un token nuevo.

## What Changes

- **Contratos de entrada y salida (`app/modules/usuarios/schemas.py`)**:
  - `YoResponse`: Devuelve `id`, `email`, `nombre`, `debe_cambiar_password`, `roles` (vigentes en BD) y `roles_token` (en el JWT).
  - `CambioPasswordRequest`: Contrato estricto (`extra="forbid"`) con `password_actual: PasswordBcrypt` y `password_nueva: PasswordBcrypt` (1 a 72 bytes UTF-8).
  - `MensajeResponse`: Contrato genérico de respuesta con `mensaje: str` para logout y cambio de contraseña.
- **Persistencia y Unit of Work (`app/modules/usuarios/repository.py` y `unit_of_work.py`)**:
  - `EventoSeguridadRepository`: Repositorio sobre `EventoSeguridad` heredando de `BaseRepository`.
  - `UsuarioUnitOfWork`: Composición de `self.eventos = EventoSeguridadRepository(session)`.
- **Dependencias de Autenticación (`app/core/dependencies.py`)**:
  - Dependencia `get_usuario_actual`: Extrae el token JWT de la cookie `access_token`, valida firma y expiración, y verifica que el usuario exista y esté activo en la base (401 si falta o es inválido).
- **Lógica de Servicio (`app/modules/usuarios/service.py`)**:
  - `obtener_perfil_yo(usuario, token_roles, uow)`: Consulta roles vigentes en la base y retorna `YoResponse`.
  - `cambiar_password(datos, usuario, uow, settings)`: Verifica `password_actual`, calcula el nuevo hash bcrypt antes de la transacción y, en un único bloque de UoW, actualiza `usuario.password_hash`, desmarca `debe_cambiar_password` y anota el evento en `evento_seguridad` con `actor=usuario.email` y `accion="Cambio de contraseña"`.
- **Rutas HTTP (`app/modules/usuarios/router.py`)**:
  - `POST /auth/logout`: Elimina la cookie `access_token` y responde 200 `{"mensaje": "Sesión cerrada"}`.
  - `GET /auth/yo`: Responde 200 con `YoResponse`.
  - `POST /auth/cambiar-password`: Responde 200 con `{"mensaje": "Contraseña actualizada exitosamente"}`.

## Capabilities

### New Capabilities

(ninguna nueva)

### Modified Capabilities

- `autenticacion`: Incorpora los requerimientos y escenarios para el cierre de sesión, la consulta del perfil propio (`GET /auth/yo`) y el cambio atómico de contraseña con auditoría en `evento_seguridad` (RN-16).

## Impact

- **Seguridad:** Cookie `access_token` eliminada en logout. El cambio de contraseña exige la clave actual, valida el límite de 72 bytes de bcrypt y persiste auditoría inmutable en `evento_seguridad`.
- **Transaccionalidad:** Cumplimiento de RN-16: el cambio de contraseña y la inserción del evento de seguridad se ejecutan en un único bloque transaccional del Unit of Work.
- **Compatibilidad:** No emite un nuevo token ni revoca sesiones al cambiar la clave (según consigna pág. 11).
