# modelos-usuarios Specification

## Purpose

Define las entidades y restricciones de base de datos para la autenticación, roles con vigencia, auditoría y vinculación con clientes.

## ADDED Requirements

### Requirement: Entidad Usuario con unicidad de email
El sistema SHALL definir el modelo de tabla `Usuario` con `email` único, `password_hash`, banderas booleanas `activo` y `debe_cambiar_password`.

#### Scenario: Atributos y restricciones de Usuario
- **WHEN** se inspecciona la metadata de la tabla `usuario`
- **THEN** posee columnas `id` (PK), `email` (único), `nombre`, `password_hash`, `activo` y `debe_cambiar_password`

### Requirement: Asignación de rol con vigencia e índice único parcial
El sistema SHALL definir el modelo `AsignacionRol` restringido a los roles `ADMIN`, `VENDEDOR` y `CLIENTE`, y SHALL impedir que un usuario tenga más de una asignación abierta por rol mediante un índice único parcial.

#### Scenario: Restricción CHECK de rol
- **WHEN** se valida el rol en `AsignacionRol`
- **THEN** la tabla incluye el CheckConstraint `rol IN ('ADMIN', 'VENDEDOR', 'CLIENTE')`

#### Scenario: Índice único parcial de rol vigente
- **WHEN** se inspeccionan los índices de `asignacion_rol`
- **THEN** existe el índice único parcial `uq_asignacion_rol_vigente` sobre `(usuario_id, rol)` con filtro `revocada_en IS NULL`

### Requirement: Desambiguación de claves foráneas entre Usuario y AsignacionRol
La relación entre `Usuario` y `AsignacionRol` SHALL declarar explícitamente la clave foránea `usuario_id` para evitar ambigüedades con la columna `otorgada_por`.

#### Scenario: Mappers de SQLAlchemy sin ambigüedades
- **WHEN** SQLAlchemy inicializa la relación `Usuario.asignaciones`
- **THEN** se utiliza `foreign_keys=[AsignacionRol.usuario_id]` y no se genera `AmbiguousForeignKeysError`

### Requirement: Bitácora de intentos de acceso aislada
El sistema SHALL definir el modelo `IntentoAcceso` con índice sobre `(email, ip, cuando)` sin claves foráneas a otras tablas.

#### Scenario: Estructura de IntentoAcceso
- **WHEN** se inspecciona la tabla `intento_acceso`
- **THEN** incluye columnas `id`, `cuando`, `email`, `ip`, `exito` y el índice `ix_intento_acceso_email_ip_cuando`

### Requirement: Eventos de seguridad con actor textual
El sistema SHALL definir el modelo `EventoSeguridad` con columna `actor` de tipo texto para permitir actores que no correspondan a usuarios registrados (como 'SISTEMA').

#### Scenario: Estructura de EventoSeguridad
- **WHEN** se inspecciona la tabla `evento_seguridad`
- **THEN** incluye `id`, `cuando`, `actor` y `accion`

### Requirement: Relación uno a uno entre Cliente y Usuario
El modelo `Cliente` SHALL permitir un `usuario_id` nulo y único, y su relación de navegación SHALL devolver un objeto individual y no una lista.

#### Scenario: Asociación 1 a 1 Cliente-Usuario
- **WHEN** se navega desde `Cliente.usuario` o `Usuario.cliente`
- **THEN** la relación está configurada con `uselist=False` y `lazy="raise"`
