# Spec Delta: repositorios

## Purpose

Define el contrato de los repositorios genéricos de acceso a datos que operan sobre una sesión asincrónica y delegan la confirmación de la transacción exclusivamente al Unit of Work.

## ADDED Requirements

### Requirement: Inicialización explícita con sesión y clase del modelo
El repositorio base SHALL recibir en su construcción la sesión asincrónica y la clase del modelo de dominio sobre la que ejecuta las consultas.

#### Scenario: Instanciación para distintos modelos
- **WHEN** se construye un `BaseRepository` para `Editorial` y otro para `Genero` sobre la misma sesión
- **THEN** cada instancia opera sobre la tabla de su propio modelo sin interferir con la otra

### Requirement: Operaciones de lectura y conteo estables
El repositorio base SHALL proveer búsqueda por identificador (`get_by_id`), listado ordenado por identificador con desplazamiento y límite opcionales (`get_all`) y conteo total en la base de datos (`count`).

#### Scenario: Listado paginado con offset y limit
- **WHEN** existen filas con identificadores `[1, 2, 3]` y se consulta `get_all(limit=2)` y luego `get_all(offset=1, limit=2)`
- **THEN** la primera consulta devuelve las filas `[1, 2]` y la segunda devuelve `[2, 3]`

#### Scenario: Búsqueda de un identificador inexistente
- **WHEN** se consulta `get_by_id` con un identificador que no existe (o que fue eliminado)
- **THEN** el repositorio devuelve `None`

### Requirement: Operaciones de escritura con flush y sin commit
Las operaciones de alta (`add`), modificación (`update`) y baja física (`delete`) del repositorio base SHALL sincronizar los cambios con la sesión mediante `flush()` (asignando el identificador en las altas y reflejando las modificaciones en lecturas posteriores dentro de la misma sesión) y SHALL NOT ejecutar `commit()` en ningún caso.

#### Scenario: Alta, edición y borrado revertibles en la misma sesión
- **WHEN** se agrega una entidad con `add`, se edita con `update`, se consulta con `get_by_id` y `count`, luego se elimina con `delete` y finalmente se revierte la sesión (`rollback`)
- **THEN** `add` asigna el `id` y sube el conteo, `update` refleja el cambio al leer por `id`, `delete` hace que `get_by_id` devuelva `None` y que el conteo vuelva al valor inicial, y se envían `0` sentencias `COMMIT` a la base de datos
