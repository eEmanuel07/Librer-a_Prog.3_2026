# Tasks: j3-venta-con-stock

## 1. Repositorios

- [x] 1.1 Agregar `obtener_para_vender` en `LibroRepository`: los libros pedidos (también los dados de baja) con `FOR UPDATE`, ordenados por id
- [x] 1.2 Hacer que `VentaRepository` herede de `BaseRepository[Venta]` y usar `add` en lugar de `agregar`

## 2. Servicio y router

- [x] 2.1 Reescribir `crear_venta` para que, en un solo bloque del Unit of Work, cree la venta y llame a `mover_stock` por renglón con motivo «Venta» (RN-10, RN-11)
- [x] 2.2 Pedir `get_usuario_actual` en `POST /ventas/` y pasar el id del usuario al servicio
- [ ] 2.3 Restringir `POST /ventas/` a VENDEDOR y ADMIN con `requiere_rol` (espera a R2)

## 3. Verificación

- [x] 3.1 Tests de servicio en `tests/test_ventas_registro_service.py`: C-10, C-11, C-12 (cliente, libro inexistente, libro dado de baja) e invariante stock = suma de movimientos
- [x] 3.2 Suite completa (`python -m unittest discover -s tests`): 79 tests OK
- [x] 3.3 Contra PostgreSQL con los datos del parcial: 401 sin cookie; C-10 201 con el aviso después de la respuesta; C-11, C-12 (los tres) 409 sin escrituras; stock = suma de movimientos en los cinco libros; `FOR UPDATE` en el SQL; cuatro ventas simultáneas del último ejemplar, una 201 y tres 409

## Workflow follow-up

- Abrir PR hacia `main` con título `feat(ventas): registrar la venta con descuento de stock y movimientos (RN-10)` y `Closes #56`.
- Cuando esté R2, agregar la tarea 2.3 en este mismo PR o en uno chico aparte.
