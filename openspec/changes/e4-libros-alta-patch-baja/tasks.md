# Tasks: e4-libros-alta-patch-baja

TDD: cada tarea empieza con un test que falla (`tests/test_libros_*.py`, `unittest`, SQLite en memoria) y termina con la suite completa en verde.

## 1. Contratos

- [ ] 1.1 `LibroCreate` con `stock_inicial` (≥ 0) en lugar de `stock`; `stock` da 422
- [ ] 1.2 `LibroUpdate` sólo con `titulo` y `precio`; `stock` u otro campo da 422; `null` explícito da 422

## 2. Alta con movimiento

- [ ] 2.1 `sqlite_where` en el índice único parcial del ISBN, para que los tests en SQLite lo traten como PostgreSQL
- [ ] 2.2 `crear_libro` recibe el id del usuario y, en un solo bloque, crea libro, autorías y el movimiento «Stock inicial» con `mover_stock`
- [ ] 2.3 `stock_inicial = 0` no deja movimiento
- [ ] 2.4 ISBN de un vigente y editorial inexistente: 409 y nada escrito

## 3. PATCH y baja

- [ ] 3.1 `actualizar_libro` sólo con título y precio; 404 si no existe o está dado de baja
- [ ] 3.2 `dar_de_baja_libro` con `soft_delete`; 204; 404 si no existe o ya estaba dado de baja
- [ ] 3.3 El libro dado de baja no aparece en el listado ni en el detalle, y su ISBN se puede volver a cargar (201); un segundo vigente, 409

## 4. Listado

- [ ] 4.1 `GET /libros/` con el envoltorio de B5 (`page`, `size`), filtros `titulo` y `genero_id`
- [ ] 4.2 Búsqueda con `' OR '1'='1` → 200 vacío; filtro con `size=1` → `total` 1, `pages` 1; `page=2` → 422

## 5. Router y sesión

- [ ] 5.1 Alta, PATCH y baja con `Depends(get_usuario_actual)`: sin sesión, 401
- [ ] 5.2 `DELETE /libros/{id}` con 204

## 6. Verificación

- [ ] 6.1 Suite completa: `python -m unittest discover -s tests`
- [ ] 6.2 Prueba manual contra PostgreSQL en una base temporal: alta con movimiento, 409 por ISBN y por editorial, baja y recarga del ISBN, `ids_con_stock_inconsistente` vacío
- [ ] 6.3 `alembic check` sin diferencias (el índice no cambia en PostgreSQL)
- [ ] 6.4 `openspec validate --all --strict`
