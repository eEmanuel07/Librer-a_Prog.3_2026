# Proposal

## Why

El sistema de la librería requiere autenticar usuarios de manera segura y sin exponer secretos. La issue [H4] (Ejercicio 4 de la consigna) implementa `POST /auth/login` con protección anti-fuerza bruta (RN-07: máximo 5 fallos en 60 segundos por correo e IP, respondiendo 429 con cabecera `Retry-After`) y anti-enumeración de cuentas (RN-08: mismo mensaje de error y tiempo de respuesta uniforme comparando contra un hash ficticio si el correo no existe). El token de sesión viaja exclusivamente en una cookie `HttpOnly` y nunca en el cuerpo de la respuesta.

## What Changes

- **Contratos (schemas)**: Creación de `LoginRequest` con `extra="forbid"`, email normalizado y contraseña validada en 72 bytes UTF-8 (`PasswordBcrypt`), y `LoginResponse` con mensaje descriptivo, indicador `debe_cambiar_password` y `expira_en_segundos`.
- **Servicio de autenticación (`login`)**: Flujo secuencial estricto:
  1. Verificación del límite de intentos en `intento_acceso` (una sola consulta): si se superó, responde 429 con `Retry-After` sin calcular ningún hash bcrypt.
  2. Verificación de contraseña: si el usuario existe y está activo, contra su `password_hash`; si no existe o está inactivo, contra el `hash_ficticio` generado en el lifespan.
  3. Registro del intento en sesión y transacción propias con `registrar_intento_acceso`, para que los fallos persistan aún ante rollback de la petición.
  4. Si las credenciales no son válidas, lanza error de credenciales (traducido a 401). Si son válidas, genera el JWT con `sub`, `exp` y los roles vigentes del usuario.
- **Router HTTP (`POST /auth/login`)**:
  - Expone el endpoint en el grupo de rutas abiertas (`/auth/login`).
  - Fija la cookie `access_token` en la respuesta con atributos `HttpOnly`, `SameSite="lax"`, `max_age` derivado de `jwt_expira_minutos` y `secure` según la configuración de entorno (`COOKIE_SECURE`).
  - No incluye el token en el cuerpo de la respuesta.
- **Registro en `main.py`**: Montaje del router de autenticación en las rutas de la aplicación.

## Capabilities

### New Capabilities
- `autenticacion`: Autenticación de usuarios mediante credenciales seguras, prevención de enumeración y fuerza bruta, y emisión de cookie de sesión JWT.

### Modified Capabilities
*(Ninguna)*

## Impact

- `app/modules/usuarios/schemas.py`: incorporación de contratos estrictos de entrada y salida para login.
- `app/modules/usuarios/service.py`: lógica de autenticación con el orden de seguridad estricto.
- `app/modules/usuarios/router.py`: endpoint HTTP que traduce errores a 401 / 429 y adjunta la cookie `access_token`.
- `app/main.py`: inclusión del router de autenticación en las rutas públicas.
