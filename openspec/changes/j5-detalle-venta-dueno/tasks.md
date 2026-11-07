# Tasks: j5-detalle-venta-dueno

## 1. Errores, Unit of Work y repositorio

- [x] 1.1 Agregar `SinPermiso` en `app/core/errors.py` (→ 403)
- [x] 1.2 Componer `AsignacionRolRepository` como `self.roles` en `VentaUnitOfWork`
- [x] 1.3 Agregar `VentaRepository.obtener_dueno(venta_id)`: una consulta, venta JOIN cliente

## 2. Servicio y router

- [x] 2.1 `ver_venta(uow, venta_id, usuario)`: roles vigentes → dueño (404 / 403) → detalle, en un bloque del Unit of Work
- [x] 2.2 `GET /ventas/{id}` con `get_usuario_actual`, sin `requiere_rol`, y `SinPermiso` → 403

## 3. Verificación

- [x] 3.1 Tests en `tests/test_ventas_detalle.py`: personal, dueña, cliente ajeno, rol revocado y vencido, venta inexistente, libro dado de baja, consultas con 2 y 4 renglones, y códigos 401/403/404/200 por HTTP
- [x] 3.2 Suite completa (`python -m unittest discover -s tests`): 95 tests OK
- [x] 3.3 Contra PostgreSQL con los datos del parcial: sin cookie 401; Ana ve su venta (200) y no la de Lucía (403); 9999 da 404 a Ana y al vendedor; el vendedor ve la de Lucía (200); con `SQL_ECHO`, 4 consultas en el detalle con 2 renglones, con 4 y con un libro dado de baja (que sigue mostrando su título)

## Workflow follow-up

- Abrir PR hacia `main` con título `feat(ventas): detalle de una venta para el personal o el cliente dueño (RN-14)` y `Closes #58`.
