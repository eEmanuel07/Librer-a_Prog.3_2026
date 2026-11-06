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

### Requirement: Aislamiento transaccional en registro de intentos de acceso
El sistema SHALL registrar cada intento de acceso en una sesión y transacción propias e independientes que se confirman inmediatamente con `commit()`, asegurando que el intento persista aunque la petición principal sea rechazada o revertida.

#### Scenario: Persistencia del intento ante rollback de la petición
- **WHEN** un intento de acceso falla o una transacción de petición revierte con ROLLBACK
- **THEN** la fila correspondiente en `intento_acceso` permanece confirmada en la base de datos

#### Scenario: Documentación de aislamiento en el código
- **WHEN** se inspecciona la función `registrar_intento_acceso`
- **THEN** incluye el comentario obligatorio que explica qué hace distinto, por qué no puede compartir la transacción y cuál es su costo

### Requirement: Conteo de fallos vigentes en una única consulta SQL
El método `contar_fallos_vigentes_y_primer_fallo` de `IntentoAccesoRepository` SHALL evaluar la cantidad de fallos y el instante del primer fallo en una sola consulta SQL utilizando una subconsulta escalar para el último intento exitoso.

#### Scenario: Conteo posterior al último éxito en una sola consulta
- **WHEN** se invoca `contar_fallos_vigentes_y_primer_fallo` para un correo e IP dados
- **THEN** la base ejecuta una única sentencia SELECT devolviendo el recuento de fallos posteriores al último éxito dentro de la ventana

### Requirement: Auto-registro de cliente y usuario en un solo bloque
El sistema SHALL proveer el endpoint `POST /auth/registro` para registrar visitantes, creando atómicamente el usuario, su rol `CLIENTE` y su ficha de cliente en un único Unit of Work, respondiendo HTTP 201 Created.

#### Scenario: Registro exitoso
- **WHEN** un visitante envía `POST /auth/registro` con nombre, correo válido y contraseña válida
- **THEN** el sistema crea el usuario activo, la asignación del rol CLIENTE y el cliente vinculado, respondiendo 201 Created con los datos registrados y sin incluir password_hash

### Requirement: Atomicidad y prevención de apropiación de fichas
Si el correo electrónico ya pertenece a un usuario o a un cliente existente, el sistema SHALL rechazar el registro con HTTP 409 y revertir cualquier cambio, asegurando que no queden filas creadas ni se modifique la ficha de cliente existente.

#### Scenario: Correo ya registrado como cliente
- **WHEN** se intenta registrar un usuario con un correo que ya existe en la tabla de clientes
- **THEN** el sistema responde 409 con mensaje propio y no crea el usuario, el rol ni altera el cliente existente

#### Scenario: Correo ya registrado como usuario
- **WHEN** se intenta registrar un usuario con un correo que ya existe en la tabla de usuarios
- **THEN** el sistema responde 409 con mensaje propio y no deja registros huérfanos

### Requirement: Validación estricta y restricción de campos en registro
El contrato de `POST /auth/registro` SHALL rechazar campos adicionales (`extra="forbid"`) y validar que la contraseña no exceda los 72 bytes en UTF-8, respondiendo HTTP 422 ante cualquier violación.

#### Scenario: Intento de auto-asignación de roles
- **WHEN** un cliente envía campos no contemplados en el contrato como un rol
- **THEN** el sistema responde 422 Unprocessable Entity sin procesar el registro

#### Scenario: Contraseña que excede 72 bytes en registro
- **WHEN** se envía una contraseña de más de 72 bytes en UTF-8
- **THEN** el sistema responde 422 sin ejecutar el algoritmo de hash ni provocar un error 500
