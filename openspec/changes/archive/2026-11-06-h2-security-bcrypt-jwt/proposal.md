# Proposal: h2-security-bcrypt-jwt

> Issue: #38 ([H2] — app/core/security.py: bcrypt y JWT). Consigna: `Parcial_Cap1a6_Consigna.pdf`, Ejercicio 4 (págs. 11 y 20).

## Nota sobre el orden: change retroactivo

Este change se escribió **después** de la implementación. Las utilidades de criptografía y seguridad ya estaban desarrolladas, cubiertas con tests unitarios y mergeadas en `main` (PR #71) antes de la inicialización de OpenSpec. Este documento consolida la trazabilidad y especificaciones canónicas de seguridad del proyecto.

## Why

El Ejercicio 4 del parcial establece que las contraseñas deben guardarse con bcrypt, con un costo y concurrencia máxima declarados en `Settings` (nunca fijos en código). Además, las llamadas a bcrypt deben correr fuera del bucle de eventos (`asyncio.to_thread`) y bajo un semáforo para no saturar la CPU del proceso asincrónico. Se exige validar que las contraseñas no superen 72 bytes en UTF-8 (`PasswordBcrypt`) para responder 422 y no 500 (por ValueError de bcrypt 5.0). Los tokens JWT deben emitirse firmados con HS256 conteniendo claims obligatorios `sub`, `exp` y los roles vigentes (`roles`).

## What Changes

- **Nuevo módulo `app/core/security.py`**:
  - `PasswordBcrypt` / `PasswordBcryptStr`: validador Pydantic que restringe la longitud a 1-72 bytes UTF-8.
  - `obtener_semaforo_bcrypt(settings)`: semáforo por bucle de eventos (`WeakKeyDictionary`), con límite dado por `settings.bcrypt_concurrencia`.
  - `hashear_password(password, settings, semaforo)`: ejecuta `bcrypt.hashpw` fuera del bucle (`asyncio.to_thread`) y bajo semáforo con `settings.bcrypt_costo`.
  - `verificar_password(password, password_hash, semaforo, settings)`: ejecuta `bcrypt.checkpw` fuera del bucle bajo semáforo.
  - `calcular_hash_ficticio(settings, semaforo)`: calcula el hash de una clave aleatoria descartable durante el lifespan (RN-08).
  - `crear_access_token(usuario_id, roles, settings, ahora)`: genera un JWT con `sub`, `exp` y `roles` firmado con `settings.jwt_secret`.
  - `decodificar_access_token(token, settings)`: decodifica el token exigiendo `sub` y `exp`, traduciendo fallos o vencimiento a `TokenInvalidoError`.

## Capabilities

### New Capabilities

- `seguridad`: Operaciones criptográficas de hasheo/verificación de contraseñas bajo concurrencia controlada fuera del bucle de eventos, validación de contrato para passwords (<= 72 bytes) y emisión/validación de tokens JWT.

### Modified Capabilities

(ninguna previa)

## Impact

- **Seguridad:** Cero llamadas bloqueantes en el event loop; protección contra denegación de servicio por bcrypt masivo.
- **Robustez:** Evita 500 ante contraseñas mayores a 72 bytes (responde 422 en FastAPI).
- **Módulos:** Base para los endpoints de autenticación (`login`, `registro`, `cambiar-password`) y dependencias de autorización.
