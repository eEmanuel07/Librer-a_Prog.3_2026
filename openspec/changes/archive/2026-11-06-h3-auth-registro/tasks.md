# Tasks: h3-auth-registro

## 1. Contratos de entrada y salida

- [x] 1.1 Definir `RegistroRequest` (con `extra="forbid"`, email normalizado en minúsculas y `password: PasswordBcrypt` de hasta 72 bytes UTF-8) y `RegistroResponse` en `app/modules/usuarios/schemas.py`, y verificar con tests unitarios
- [x] 1.2 Verificar el rechazo de campos adicionales (422) y contraseñas de más de 72 bytes (422) en los contratos

## 2. Unit of Work y Servicio

- [x] 2.1 Componer `ClienteRepository` en `UsuarioUnitOfWork` (`app/modules/usuarios/unit_of_work.py`) como `self.clientes`
- [x] 2.2 Implementar la función `registrar` en `app/modules/usuarios/service.py` calculando bcrypt antes de la transacción y creando usuario, rol CLIENTE y cliente en un solo bloque `async with uow.con_mensajes(unique="...")`
- [x] 2.3 Verificar con tests unitarios la creación de las tres entidades y la propagación de `Conflicto` (409) con rollback si el correo ya existe

## 3. Router HTTP y Caso C-02

- [x] 3.1 Implementar el endpoint `POST /auth/registro` en `app/modules/usuarios/router.py` respondiendo 201 Created y traduciendo `Conflicto` a 409
- [x] 3.2 Escribir suite de integración `tests/test_auth_registro.py` verificando el caso C-02 (201 registro exitoso, 409 por correo de cliente repetido, 409 por correo de usuario repetido y comprobación de que no quedan filas huérfanas)
- [x] 3.3 Ejecutar la suite completa del proyecto (`python -m unittest discover -s tests`) y verificar que no existan regresiones

## Workflow follow-up

- Abrir PR hacia `main` con título `feat(auth): auto-registro de clientes en un solo Unit of Work (RN-02)` y descripción con `Closes #39`.
- Archivar el change `h3-auth-registro` tras el merge y marcar la tarea en `CHANGES.md`.
