# Tasks: j6-mis-ventas-y-ventas

## 1. Repositorio y servicio

- [x] 1.1 `VentaRepository.listar_pagina(params, usuario_id=None)` con `paginar` (reemplaza a `listar`)
- [x] 1.2 `listar_ventas(uow, params, usuario)`: 403 si no es personal
- [x] 1.3 `listar_mis_ventas(uow, params, usuario)`
- [x] 1.4 `_es_personal` compartido con `ver_venta`

## 2. Router y app

- [x] 2.1 `GET /ventas/` con `parametros_pagina`, `get_usuario_actual` y `Pagina[VentaResumen]`
- [x] 2.2 `router_mis_ventas` con `GET /mis-ventas`, registrado en `app/main.py`
- [ ] 2.3 Pasar el rol de `GET /ventas` a `requiere_rol("VENDEDOR", "ADMIN")` (espera a R2)

## 3. Verificación

- [x] 3.1 Tests en `tests/test_ventas_listados.py`: personal y cliente, rol revocado, envoltorio, páginas, página de más, sin ficha, consultas fijas, 401/403/422 por HTTP y la ruta registrada en la app
- [x] 3.2 Suite completa (`python -m unittest discover -s tests`): 108 tests OK
- [x] 3.3 Contra PostgreSQL con los datos del parcial: sin cookie 401 en los dos; Ana en `/ventas` 403 y en `/mis-ventas` sólo las suyas; vendedor y admin paginan `/ventas`; página de más y `size=500` 422; vendedor sin ficha en `/mis-ventas`, página vacía; con `SQL_ECHO`, las mismas consultas con `size` 1 y 4

## Workflow follow-up

- Abrir PR hacia `main` con título `feat(ventas): GET /ventas y GET /mis-ventas con el envoltorio (RN-14)` y `Closes #59`.
