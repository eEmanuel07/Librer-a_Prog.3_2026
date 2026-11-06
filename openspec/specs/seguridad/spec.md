# seguridad Specification

## Purpose
Define las reglas técnicas y garantías de seguridad para el tratamiento de contraseñas con bcrypt y la generación/validación de tokens JWT.

## Requirements

### Requirement: Validación de longitud de contraseña en contratos
Toda contraseña que termine en bcrypt SHALL tener una longitud de entre 1 y 72 bytes medidos en UTF-8, rechazando longitudes mayores con error de validación (422) y nunca con 500.

#### Scenario: Contraseña de más de 72 bytes
- **WHEN** un contrato recibe una contraseña que supera los 72 bytes en UTF-8
- **THEN** la validación de Pydantic lanza `ValueError` produciendo una respuesta HTTP 422

#### Scenario: Contraseña válida con caracteres multibyte
- **WHEN** se envía una contraseña con caracteres acentuados o símbolos que ocupan hasta 72 bytes en UTF-8
- **THEN** la validación es exitosa

### Requirement: Hasheo y verificación no bloqueante bajo semáforo
Toda operación con bcrypt SHALL ejecutarse en un hilo secundario mediante `asyncio.to_thread` y bajo un semáforo asincrónico que limite la concurrencia a `settings.bcrypt_concurrencia`.

#### Scenario: Concurrencia controlada de bcrypt
- **WHEN** se ejecutan múltiples operaciones de hasheo o verificación simultáneas
- **THEN** nunca corren más de `bcrypt_concurrencia` hilos de bcrypt al mismo tiempo y el bucle de eventos no se bloquea

### Requirement: Hash ficticio para prevención de timing attacks
El sistema SHALL proveer la función `calcular_hash_ficticio` para generar en el arranque un hash con el costo configurado de bcrypt a partir de una clave descartable.

#### Scenario: Hash ficticio con costo uniforme
- **WHEN** se ejecuta `calcular_hash_ficticio` con la configuración del sistema
- **THEN** devuelve un hash bcrypt válido con el costo `settings.bcrypt_costo`

### Requirement: Emisión y decodificación estricta de JWT
El sistema SHALL emitir tokens JWT con algoritmo HS256 firmados con `settings.jwt_secret`, conteniendo `sub` (identificador como texto), `exp` y la lista de `roles`, y SHALL rechazar tokens vencidos o con firma inválida arrojando `TokenInvalidoError`.

#### Scenario: Token JWT con claims obligatorios
- **WHEN** se genera un token con `crear_access_token`
- **THEN** el payload contiene `sub`, `exp` y `roles`

#### Scenario: Token expirado o alterado
- **WHEN** se decodifica un token expirado o con firma alterada
- **THEN** `decodificar_access_token` lanza `TokenInvalidoError`
