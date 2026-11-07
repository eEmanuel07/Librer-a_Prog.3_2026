# Tasks: e5-reposicion-y-movimientos

TDD: cada tarea empieza con un test que falla (`tests/test_libros.py`, `unittest`, SQLite en memoria) y termina con la suite completa en verde.

## 1. Reposición

- [x] 1.1 `ReposicionCreate` con `cantidad` ≥ 1 y `extra="forbid"`; 0, negativa o un campo de más dan 422
- [x] 1.2 `reponer_libro`: en un solo bloque, busca el libro incluyendo los dados de baja y llama a `mover_stock` con «Reposición» y el id del usuario
- [x] 1.3 200 con el libro (stock nuevo) y el movimiento; el stock sigue siendo la suma de los movimientos
- [x] 1.4 Dado de baja: 409 sin movimiento nuevo; inexistente: 404

## 2. Movimientos

- [x] 2.1 `LibroRepository.listar_movimientos_pagina` ordenado por `cuando` e `id`, con `paginar`
- [x] 2.2 `GET /libros/{id}/movimientos` con el envoltorio; incluye los de un libro dado de baja
- [x] 2.3 Inexistente: 404; página inexistente: 422

## 3. Sesión

- [x] 3.1 Los dos endpoints con `Depends(get_usuario_actual)`: sin sesión, 401

## 4. Verificación

- [x] 4.1 Suite completa: `python -m unittest discover -s tests`
- [x] 4.2 Prueba manual contra PostgreSQL en una base temporal: reposición con su movimiento, 409 del dado de baja, movimientos en orden, stock = suma de movimientos
- [x] 4.3 `openspec validate --all --strict`
