# datos-iniciales Specification

## Purpose
Definir la carga repetible de los datos iniciales del sistema mediante `seed.py` en la raíz del proyecto, garantizando usuarios de prueba, catálogo, clientes, venta inicial con invariante de movimientos de stock y registro en el historial de seguridad.

## Requirements

### Requirement: Carga de datos iniciales en la raíz (`seed.py`)
El sistema SHALL proveer el script `seed.py` en la raíz del proyecto que vacíe todas las tablas y cargue los 5 usuarios iniciales con sus roles vigentes, el catálogo inicial (3 editoriales, 3 géneros, 6 autores y 5 libros con movimientos iniciales), los 3 clientes, la venta inicial con sus movimientos cumpliendo el invariante `stock = suma(movimientos)` (RN-11) y la fila en `evento_seguridad` con actor `SISTEMA` (RN-16).

#### Scenario: Invariante de stock y datos completos tras ejecutar el seed
- **WHEN** se ejecuta `sembrar()` de `seed.py`
- **THEN** quedan cargados los 5 usuarios con sus asignaciones de rol, las 3 editoriales, los 3 géneros, los 6 autores, los 5 libros con stocks 10, 5, 8, 3 y 1, los 3 clientes, la venta 1 con total `69000.00`, 7 movimientos de stock tales que `ids_con_stock_inconsistente()` devuelve `[]`, y 1 evento de seguridad con `actor="SISTEMA"` y `accion="Carga de los datos iniciales"`
