# esquema-base-datos Specification

## Purpose

Define el esquema de PostgreSQL que las migraciones de Alembic dejan en la base de la librería y garantiza que esas migraciones se pueden aplicar, revertir y volver a aplicar sin errores.

## Requirements

### Requirement: Email de usuario único
La base SHALL tener una tabla `usuario` donde el `email` sea único.

#### Scenario: Email repetido
- **WHEN** se inserta un usuario con un email que ya existe
- **THEN** la base rechaza la inserción por violar la unicidad del email

### Requirement: Rol válido y vigente una sola vez
La tabla `asignacion_rol` SHALL aceptar solo los roles `ADMIN`, `VENDEDOR` y `CLIENTE`, y SHALL impedir que un usuario tenga dos asignaciones vigentes (sin `revocada_en`) del mismo rol.

#### Scenario: Rol inexistente
- **WHEN** se inserta una asignación con un rol fuera de `ADMIN`, `VENDEDOR` o `CLIENTE`
- **THEN** la base la rechaza por la restricción CHECK del rol

#### Scenario: Mismo rol vigente dos veces
- **WHEN** un usuario ya tiene el rol `VENDEDOR` sin revocar y se le inserta otra asignación `VENDEDOR` sin revocar
- **THEN** la base rechaza la inserción por el índice único parcial

#### Scenario: Volver a otorgar un rol revocado
- **WHEN** la asignación anterior del rol tiene `revocada_en` cargado y se inserta una nueva asignación vigente del mismo rol
- **THEN** la base la acepta

### Requirement: Registro de intentos de acceso y eventos de seguridad
La base SHALL tener las tablas `intento_acceso`, con un índice sobre `(email, ip, cuando)` para consultar intentos recientes, y `evento_seguridad`.

#### Scenario: Tablas de acceso presentes
- **WHEN** se aplica la migración hasta `head`
- **THEN** existen `intento_acceso` (con el índice `(email, ip, cuando)`) y `evento_seguridad`

### Requirement: Movimientos de stock distintos de cero
La tabla `movimiento_stock` SHALL rechazar movimientos con `cantidad` igual a cero y SHALL permitir que `venta_id` sea nulo para movimientos que no vienen de una venta.

#### Scenario: Cantidad cero
- **WHEN** se inserta un movimiento con `cantidad = 0`
- **THEN** la base lo rechaza por la restricción CHECK

#### Scenario: Movimiento sin venta
- **WHEN** se inserta un movimiento válido con `venta_id` nulo
- **THEN** la base lo acepta

### Requirement: Cliente vinculado a lo sumo a un usuario
La tabla `cliente` SHALL tener una columna `usuario_id` nula, con FK a `usuario.id`, y un mismo usuario SHALL NOT quedar vinculado a más de un cliente.

#### Scenario: Cliente sin usuario
- **WHEN** existe un cliente con `usuario_id` nulo
- **THEN** la base lo acepta

#### Scenario: Usuario compartido por dos clientes
- **WHEN** se asigna a un segundo cliente un `usuario_id` que ya usa otro cliente
- **THEN** la base lo rechaza por el índice UNIQUE

### Requirement: ISBN único solo entre libros vigentes
La tabla `libro` SHALL tener `borrado_en` (fecha con zona horaria, nula) y SHALL exigir ISBN único solo entre los libros con `borrado_en` nulo.

#### Scenario: ISBN repetido entre libros vigentes
- **WHEN** se inserta un libro vigente con el ISBN de otro libro vigente
- **THEN** la base lo rechaza

#### Scenario: Volver a cargar un ISBN dado de baja
- **WHEN** el libro con ese ISBN tiene `borrado_en` cargado y se inserta otro libro vigente con el mismo ISBN
- **THEN** la base lo acepta

### Requirement: Claves foráneas indexadas
Cada clave foránea nueva de esta migración SHALL tener un índice sobre su columna.

#### Scenario: Índices de las FK
- **WHEN** se aplica la migración hasta `head`
- **THEN** existen índices sobre `asignacion_rol.usuario_id`, `asignacion_rol.otorgada_por`, `movimiento_stock.libro_id`, `movimiento_stock.usuario_id`, `movimiento_stock.venta_id` y `cliente.usuario_id`

### Requirement: Migraciones reversibles y consistentes con los modelos
Las migraciones SHALL poder aplicarse y revertirse por completo en una base vacía, y después de `upgrade head` el esquema SHALL coincidir con los modelos.

#### Scenario: Ida y vuelta en base vacía
- **WHEN** en una base vacía se corre `upgrade head`, `downgrade base` y otra vez `upgrade head`
- **THEN** los tres comandos terminan sin errores y la base queda en la revisión `head`

#### Scenario: Sin diferencias con los modelos
- **WHEN** la base está en `head` y se corre `alembic check`
- **THEN** informa que no hay operaciones de upgrade nuevas
