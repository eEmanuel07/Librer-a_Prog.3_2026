# Tasks: h6-auth-logout-yo-cambio

## 1. Contratos, Repositorio y Dependencia de Autenticación

- [x] 1.1 Definir contratos `YoResponse`, `CambioPasswordRequest` (con `extra="forbid"` y `PasswordBcrypt`) y `MensajeResponse` en `app/modules/usuarios/schemas.py`, y verificar con tests unitarios
- [x] 1.2 Implementar `EventoSeguridadRepository` en `app/modules/usuarios/repository.py` y componerlo como `self.eventos` en `UsuarioUnitOfWork` (`app/modules/usuarios/unit_of_work.py`)
- [x] 1.3 Implementar la dependencia `get_usuario_actual` en `app/core/dependencies.py` resolviendo el usuario desde la cookie `access_token` y validando existencia y estado activo (401 si falta o no es válido)

## 2. Lógica de Servicio y Auditoría Atómica (RN-16)

- [x] 2.1 Implementar la función `obtener_yo` en `app/modules/usuarios/service.py` obteniendo roles vigentes en la base y roles del token
- [x] 2.2 Implementar la función `cambiar_password` en `app/modules/usuarios/service.py` calculando el nuevo hash antes de la transacción y actualizando la contraseña, reseteando `debe_cambiar_password=False` y creando `EventoSeguridad` en un único bloque atómico del Unit of Work (RN-16)
- [x] 2.3 Escribir tests unitarios de servicio en `tests/test_auth_service.py` o módulo de pruebas dedicado, verificando el flujo exitoso, el rechazo de contraseña actual incorrecta y la persistencia de auditoría

## 3. Rutas HTTP y Verificación Integral

- [x] 3.1 Implementar endpoints `POST /auth/logout`, `GET /auth/yo` y `POST /auth/cambiar-password` en `app/modules/usuarios/router.py`
- [x] 3.2 Escribir suite de integración `tests/test_auth_logout_yo_cambio.py` verificando el comportamiento de los tres endpoints con `TestClient`
- [x] 3.3 Ejecutar la suite completa del proyecto (`python -m unittest discover -s tests`) y verificar 100% de tests passing sin regresiones

## Workflow follow-up

- Abrir PR hacia `main` con título `feat(auth): logout, /auth/yo y cambio de contraseña con auditoría (RN-16)` y descripción con `Closes #42`.
- Archivar el change `h6-auth-logout-yo-cambio` con `openspec archive` tras la verificación y merge, y actualizar `CHANGES.md`.
