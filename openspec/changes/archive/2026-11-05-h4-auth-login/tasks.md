# Tasks

## 1. Contratos de entrada y salida

- [x] 1.1 Crear `LoginRequest` (con `extra="forbid"`, email y contraseña validada en 72 bytes UTF-8 `PasswordBcrypt`) y `LoginResponse` en `app/modules/usuarios/schemas.py`, y verificar con tests unitarios
- [x] 1.2 Definir excepciones de dominio para login (`CredencialesInvalidasError` y `LimiteIntentosError` con `retry_after`) y verificar sus atributos

## 2. Lógica de servicio de autenticación

- [x] 2.1 Implementar en `app/modules/usuarios/service.py` el flujo de verificación de límite de intentos (5 fallos en 60s por email/ip) y verificar que responde `LimiteIntentosError` sin calcular bcrypt
- [x] 2.2 Implementar en `app/modules/usuarios/service.py` la verificación de contraseña con bcrypt (contra hash de usuario o hash ficticio) y el registro del intento en su propia sesión con `registrar_intento_acceso`
- [x] 2.3 Implementar en `app/modules/usuarios/service.py` la emisión del JWT con roles vigentes y verificar que el login exitoso devuelve el usuario y el token

## 3. Router HTTP y ciclo de vida

- [x] 3.1 En `app/main.py`, calcular una vez `app.state.hash_ficticio = await calcular_hash_ficticio(settings)` en el `lifespan` y asegurar su disponibilidad
- [x] 3.2 Crear `app/modules/usuarios/router.py` con `POST /auth/login`, adjuntando la cookie `access_token` (`HttpOnly`, `SameSite="lax"`, `max_age`, `secure=settings.cookie_secure`), traduciendo errores a 401 y 429 con `Retry-After`
- [x] 3.3 Registrar el router de autenticación en las rutas abiertas de `app/main.py` y verificar que el endpoint responde en `/auth/login`

## 4. Verificación y pruebas de integración

- [x] 4.1 Escribir suite de pruebas para `POST /auth/login` cubriendo los casos C-03 (cookie correcta, sin token en cuerpo), C-04 (mismo 401 para correo malo o contraseña mala) y C-05 (sexto intento 429 con Retry-After)
- [x] 4.2 Ejecutar la suite completa del proyecto y verificar que no existan regresiones

## Workflow follow-up

- Abrir PR de `[H4]` hacia `main` con `Closes #40` y evidencia de los tests.
- Archivar el change `h4-auth-login` tras el merge.
