# autenticacion Specification

## Purpose
Permite autenticar usuarios en el sistema mediante credenciales verificadas contra bcrypt, emitiendo una cookie de sesión JWT segura y protegiendo el acceso contra ataques de fuerza bruta y enumeración de usuarios.

## Requirements

### Requirement: Autenticación con credenciales válidas y emisión de cookie
El sistema SHALL (DEBE) verificar las credenciales del usuario en `POST /auth/login` y, si son correctas, responder 200 con información de vigencia y fijar la cookie `access_token` con HttpOnly, SameSite=Lax y Max-Age igual a la expiración del token. El cuerpo de la respuesta MUST NOT contener el token.

#### Scenario: Login exitoso
- **WHEN** un cliente envía `POST /auth/login` con correo y contraseña válidos
- **THEN** el servidor responde 200 con `{ "mensaje": "Sesión iniciada", "debe_cambiar_password": false, "expira_en_segundos": 1800 }` y encabezado `Set-Cookie` con la cookie `access_token` (`HttpOnly`, `SameSite=Lax`, `Max-Age=1800`), sin incluir el token en el JSON

### Requirement: Prevención de enumeración de cuentas
El sistema SHALL (DEBE) responder 401 con el mismo mensaje genérico y registrar el intento fallido tanto si el correo no existe como si la contraseña es incorrecta. Si el correo no existe, DEBE verificar contra un hash ficticio para mantener uniforme el tiempo de respuesta.

#### Scenario: Contraseña incorrecta para usuario existente
- **WHEN** un cliente envía `POST /auth/login` con un correo existente pero contraseña errónea
- **THEN** el servidor responde 401 con mensaje genérico ("Credenciales inválidas") y anota el intento fallido en `intento_acceso`

#### Scenario: Correo inexistente
- **WHEN** un cliente envía `POST /auth/login` con un correo que no existe en el sistema
- **THEN** el servidor responde 401 con el mismo mensaje genérico, ejecuta la verificación contra el hash ficticio y anota el intento fallido en `intento_acceso`

### Requirement: Límite de intentos fallidos por correo e IP
El sistema SHALL (DEBE) contar los intentos fallidos de los últimos 60 segundos para la combinación de correo e IP. Si se superan 5 intentos fallidos consecutivos, MUST responder 429 con la cabecera `Retry-After` sin verificar la contraseña ni calcular ningún hash. Un login exitoso reinicia el conteo.

#### Scenario: Bloqueo tras 5 intentos fallidos consecutivos
- **WHEN** se realiza un sexto intento de login tras 5 fallos dentro de la ventana de 60 segundos
- **THEN** el servidor responde 429 con la cabecera `Retry-After` en segundos restantes, sin calcular hash de contraseña

#### Scenario: Reinicio del conteo tras login exitoso
- **WHEN** un usuario con fallos previos dentro de la ventana realiza un login exitoso
- **THEN** el servidor autentica con 200 y reinicia la cuenta de fallos para los intentos posteriores

### Requirement: Validación estricta de contrato y límite de contraseña
El contrato de entrada de login SHALL (DEBE) rechazar campos extra (`extra="forbid"`) y validar que la contraseña no supere los 72 bytes en UTF-8, respondiendo 422 ante violaciones.

#### Scenario: Contraseña que supera 72 bytes UTF-8
- **WHEN** un cliente envía un login con una contraseña de más de 72 bytes UTF-8
- **THEN** el servidor responde 422 sin invocar el algoritmo de hash ni provocar un error interno 500
