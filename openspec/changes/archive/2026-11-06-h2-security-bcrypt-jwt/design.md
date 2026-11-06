# Design: h2-security-bcrypt-jwt

## UI Mockups

Decision: no (no UI)

## Context & Architecture

Módulo central `app/core/security.py` para la gestión de criptografía de contraseñas y tokens de sesión.

## Technical Decisions

1. **Gestión de semáforos por Event Loop**:
   Para evitar problemas al instanciar semáforos al momento de importar módulos cuando no existe aún un loop corriendo, se usa `_SEMAFOROS_POR_LOOP: weakref.WeakKeyDictionary[asyncio.AbstractEventLoop, asyncio.Semaphore]`.
2. **Validación de 72 bytes UTF-8**:
   Se implementa con un validador `AfterValidator` en Pydantic (`PasswordBcrypt = Annotated[str, AfterValidator(validar_password_bcrypt)]`), midiendo `len(valor.encode('utf-8'))`.
3. **Costo y secretos dinámicos**:
   Todos los parámetros (`bcrypt_costo`, `bcrypt_concurrencia`, `jwt_secret`, `jwt_expira_minutos`) se obtienen de la instancia `Settings` leída del entorno.
4. **Traducción de excepciones de JWT**:
   `ExpiredSignatureError` y `PyJWTError` se envuelven en `TokenInvalidoError`, garantizando un contrato limpio para las capas superiores.
