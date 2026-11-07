# Spec Delta: ventas

## ADDED Requirements

### Requirement: Casos manuales de ventas y evidencia de C-15
El proyecto SHALL incluir `test/ventas.http` con C-10, C-11 y C-12 sobre los datos de `seed.py`, cada pedido con su respuesta esperada en un comentario, y `evidencia/` SHALL incluir la salida de la consola de C-15.

#### Scenario: Correr el archivo sobre una base recién cargada
- **WHEN** se corre `test/ventas.http` de arriba abajo después de `alembic upgrade head` y `python seed.py`
- **THEN** cada pedido responde el código que dice su comentario `Esperado`

#### Scenario: C-15 en la consola
- **WHEN** con `SQL_ECHO=true` se piden el detalle de una venta de 2 renglones y el de una de 4
- **THEN** la consola muestra la misma cantidad de SELECT en las dos peticiones
