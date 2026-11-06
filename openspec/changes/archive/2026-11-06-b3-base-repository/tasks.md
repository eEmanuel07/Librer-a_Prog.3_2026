# Tasks: b3-base-repository

> Change retroactivo: todas las tareas se implementaron y verificaron en el PR #65 (commit `7e9e89c`), y se volvieron a verificar en memoria el 2026-11-06 sin tocar la base de datos.

## 1. Implementación de `BaseRepository[T]`

- [x] 1.1 Crear `app/core/repository.py` con `BaseRepository[T]`, recibiendo `session: AsyncSession` y `modelo: type[T]`, e implementar `get_by_id`, `get_all` (ordenado por `id` con `offset` y `limit`), `count` (`SELECT count(*)`), `add`, `update` y `delete` usando `flush()` y nunca `commit()`.
  - **Evidencia:** `app/core/repository.py` (commit `7e9e89c`, PR #65).

## 2. Verificación de operaciones y ausencia de `commit()`

- [x] 2.1 Probar `BaseRepository` con dos modelos (`Editorial` y `Genero`) dentro de una sesión que hace `rollback` al final, verificando altas, conteo, edición, paginación por `offset`/`limit`, borrado y que se envíen `0 COMMIT` a la base.
  - **Evidencia (PR #65 y re-verificación en memoria 2026-11-06):**
    - `add` asigna `id` (`id=4`) y `count()` pasa de `3` a `4`;
    - `update` + `get_by_id` devuelven el nombre editado (`Ed 4 editada`);
    - `get_all(limit=2)` → `[1, 2]` y `get_all(offset=1, limit=2)` → `[2, 3]`;
    - `delete` → `get_by_id` devuelve `None` y `count()` vuelve a `3`;
    - `0 COMMIT` enviados a la base (`commits=0`), y el `rollback` final deja la base intacta.
