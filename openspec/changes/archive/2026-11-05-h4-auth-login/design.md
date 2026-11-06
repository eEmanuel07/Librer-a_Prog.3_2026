# Design

## Context

Véase `proposal.md` y `specs/autenticacion/spec.md`. El sistema ya cuenta con `Usuario` y `AsignacionRol` ([H1]), las primitivas de `bcrypt` y JWT en `app/core/security.py` ([H2]), y el repositorio `IntentoAccesoRepository` junto con la función `registrar_intento_acceso` en sesión propia ([H5]).

## Goals / Non-Goals

**Goals:**
- Implementar el contrato `LoginRequest` y `LoginResponse` en `app/modules/usuarios/schemas.py`.
- Implementar la función de servicio `login(...)` en `app/modules/usuarios/service.py` respetando el orden de seguridad estricto.
- Exponer la ruta `POST /auth/login` en `app/modules/usuarios/router.py`, devolviendo 200 con la cookie `access_token` en `Set-Cookie`.
- Registrar el router en el grupo de rutas públicas en `app/main.py`.

**Non-Goals:**
- Registro de nuevos usuarios (`POST /auth/registro` corresponde a [H3]).
- Logout y consulta de identidad (`/auth/yo` y `/auth/logout` corresponden a [H6]).
- Control de cambio obligatorio de contraseña en rutas protegidas (corresponde a [R3]).

## UI Mockups

Decision: no (no UI)

## Decisions

### 1. Secuencia estricta de seguridad en `login`
- **Decisión**: El flujo ejecuta en este orden exacto:
  1. Contar fallos vigentes en `intento_acceso` (`contar_fallos_vigentes_y_primer_fallo`). Si `cantidad >= 5`, calcula segundos restantes y lanza `LimiteIntentosError` (429 con cabecera `Retry-After`).
  2. Buscar usuario por email en la sesión de la petición. Si existe y está activo, verificar la contraseña contra su `password_hash`; si no existe o está inactivo, verificar contra el hash ficticio del lifespan.
  3. Registrar el intento con `registrar_intento_acceso` en su sesión y transacción independientes.
  4. Si la verificación falló, lanzar `CredencialesInvalidasError` (401).
  5. Si fue exitosa, listar roles vigentes del usuario y emitir el JWT con `crear_access_token`.
- **Alternativa descartada**: Verificar la contraseña antes de chequear el límite de intentos. Descartada porque permitiría ataques DoS por consumo de CPU en bcrypt.

### 2. Cookie `access_token` en el Router
- **Decisión**: El router utiliza `response.set_cookie(key="access_token", value=token, httponly=True, samesite="lax", max_age=segundos, secure=settings.cookie_secure)`.
- **Alternativa descartada**: Enviar el token en el cuerpo JSON o cabecera `Authorization`. La consigna (Ej. 4 y RN-03) prohíbe explícitamente tokens en el cuerpo y exige autenticación por cookie HttpOnly.

### 3. Hash ficticio en `lifespan`
- **Decisión**: El `lifespan` en `app/main.py` calcula una sola vez `app.state.hash_ficticio = await calcular_hash_ficticio(settings, semaforo)` al arrancar el servidor, y el servicio lo recibe o toma de `request.app.state`.
- **Alternativa descartada**: Calcular un hash aleatorio en cada petición donde no exista el usuario. Duplicaría el costo de cómputo inútilmente.

## Risks / Trade-offs

- **[Conexión extra del pool al registrar el intento]** → Mitigación: la sesión propia de `registrar_intento_acceso` hace `flush()` + `commit()` y se cierra de inmediato en su propio bloque `async with`.
- **[Saturación de CPU por llamadas concurrentes a bcrypt]** → Mitigación: gobernado por `asyncio.to_thread` y el semáforo `_SEMAFOROS_POR_LOOP` basado en `settings.bcrypt_concurrencia`.
