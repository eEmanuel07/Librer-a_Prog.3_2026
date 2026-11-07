# datos-iniciales Specification

## Purpose
TBD - created by archiving change r8-seed-en-la-raiz. Update Purpose after archive.

## Requirements

### Requirement: Carga de datos iniciales en la raíz (`seed.py`)
El sistema SHALL proveer el script `seed.py` en la raíz del proyecto que vacíe todas las tablas y cargue los 5 usuarios iniciales con sus roles vigentes (`admin@example.com`, `admin2@example.com`, `vendedor@example.com`, `ana@example.com`, `nuevo@example.com` con `debe_cambiar_password=True`), 3 editoriales, 3 géneros, 6 autores, 5 libros (`Rayuela` stock 10, `Antología de la literatura fantástica` stock 5, `Ficciones` stock 8, `Respiración artificial` stock 3, `Bestiario` stock 1), 3 clientes (`Lucía Fernández` con perfil, `Tomás Ríos`, `Ana Paz` vinculada a `ana@example.com`), la venta 1 de Lucía por $69000.00 con sus movimientos de stock cumpliendo el invariante `stock = suma(movimientos)` para los cinco libros, y la fila en `evento_seguridad` con actor `SISTEMA` y acción `"Carga de los datos iniciales"`.

#### Scenario: Invariante de stock y datos completos tras ejecutar el seed
- **WHEN** se ejecuta `sembrar()` de `seed.py`
- **THEN** quedan cargados los 5 usuarios con sus asignaciones de rol, las 3 editoriales, los 3 géneros, los 6 autores, los 5 libros con stocks 10, 5, 8, 3 y 1, los 3 clientes, la venta 1 con total `69000.00`, 7 movimientos de stock tales que `ids_con_stock_inconsistente()` devuelve `[]`, y 1 evento de seguridad con `actor="SISTEMA"` y `accion="Carga de los datos iniciales"`
