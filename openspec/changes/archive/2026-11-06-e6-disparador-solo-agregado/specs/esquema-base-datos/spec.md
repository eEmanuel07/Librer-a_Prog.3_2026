# Spec Delta: esquema-base-datos

## ADDED Requirements

### Requirement: Movimientos de stock de sólo agregado
La tabla `movimiento_stock` SHALL aceptar inserciones y SHALL rechazar cualquier UPDATE o DELETE sobre sus filas, venga de la aplicación o de una conexión directa a la base (RN-12). El rechazo SHALL usar un SQLSTATE de la clase 23 (violación de integridad), para que la aplicación lo traduzca a 409 y nunca a 500 (RN-15).

#### Scenario: Insertar un movimiento
- **WHEN** se inserta un movimiento válido en `movimiento_stock`
- **THEN** la base lo acepta

#### Scenario: Modificar un movimiento
- **WHEN** se corre un UPDATE sobre una fila existente de `movimiento_stock`
- **THEN** la base lo rechaza con SQLSTATE `23001` y la fila queda igual

#### Scenario: Borrar un movimiento
- **WHEN** se corre un DELETE sobre una fila existente de `movimiento_stock`
- **THEN** la base lo rechaza con SQLSTATE `23001` y la fila sigue en la tabla

#### Scenario: Rechazo desde la aplicación
- **WHEN** la aplicación intenta un UPDATE sobre `movimiento_stock` dentro de un bloque del Unit of Work
- **THEN** el Unit of Work revierte y levanta `Conflicto` (409) con un mensaje propio, sin texto de la base

#### Scenario: Vaciar la tabla para los datos iniciales
- **WHEN** `seed.py` vacía las tablas con `TRUNCATE ... RESTART IDENTITY CASCADE`
- **THEN** la base lo permite, porque TRUNCATE no es UPDATE ni DELETE

#### Scenario: Revertir la migración
- **WHEN** se corre `alembic downgrade` hasta la migración 3
- **THEN** la función y el disparador dejan de existir y la tabla vuelve a admitir UPDATE y DELETE
