# Tasks: j7-clientes-con-acceso

## 1. Clientes

- [x] 1.1 `requiere_rol("VENDEDOR", "ADMIN")` como dependencia del router de clientes
- [x] 1.2 `usuario_id` en `ClienteRead` (sólo lectura)
- [x] 1.3 `GET /clientes/{id}/ventas` con `parametros_pagina` y `Pagina[VentaRead]`; `listar_ventas_pagina` con `paginar`
- [x] 1.4 Borrar `app/core/pagination.py` (ya nadie lo importa)

## 2. Ventas

- [x] 2.1 `POST /ventas` con `requiere_rol("VENDEDOR", "ADMIN")` (tarea 2.3 de J3)
- [x] 2.2 `GET /ventas` con `requiere_rol("VENDEDOR", "ADMIN")` y sin el control del servicio (tarea 2.3 de J6)

## 3. Verificación

- [x] 3.1 `tests/test_clientes_protegido.py`: 401 y 403 en todas las rutas, el personal las usa, `usuario_id`, 422 al asignarlo, envoltorio, página vacía, 404, 422 y consultas fijas
- [x] 3.2 Tests de J4 y J6 ajustados al rol en el router, más 403 de `POST /ventas` para un cliente
- [x] 3.3 Suite completa (`python -m unittest discover -s tests`): 171 tests OK
- [x] 3.4 `test/clientes.http` contra PostgreSQL con `alembic upgrade head` y `python seed.py`: 33 de 33 con el código esperado; `test/seguridad.http` sigue dando todo OK

## Workflow follow-up

- Abrir PR hacia `main` con título `feat(clientes): módulo del personal con usuario_id y el envoltorio` y `Closes #60`.
