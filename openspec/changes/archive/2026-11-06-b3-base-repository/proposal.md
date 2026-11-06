# Proposal: b3-base-repository

> Issue: #32 (B3 — BaseRepository). PR: #65 (commit `7e9e89c`). Consigna: `Parcial_Cap1a6_Consigna.pdf`, Ejercicio 6 (pág. 12) y estructura obligatoria (pág. 8).

## Nota sobre el orden: change retroactivo

Este change se escribió **después** de la implementación. `BaseRepository[T]` ya estaba implementado, probado y mergeado en `main` (PR #65, commit `7e9e89c`) antes de que el grupo inicializara OpenSpec en el repositorio (PR #73). No se cambió el orden para simular que pasó antes por `propose`: OpenSpec todavía no existía en el proyecto cuando se hizo B3. Este documento deja trazado qué se construyó, por qué y cómo se verificó, sincronizando la spec `repositorios`.

## Why

En el TP cada repositorio repetía a mano las operaciones básicas de lectura y escritura sobre su modelo. El Ejercicio 6 del parcial pide centralizar esas operaciones comunes en un `BaseRepository[T]` genérico en `app/core/repository.py` que reciba la sesión y la clase del modelo, exponga `get_by_id`, `get_all`, `count`, `add`, `update` y `delete`, y haga únicamente `flush()` sin llamar nunca a `commit()` (la confirmación es exclusiva del Unit of Work).

## What Changes

- **Nuevo `app/core/repository.py` con `BaseRepository[T]`:**
  - Recibe `session: AsyncSession` y `modelo: type[T]` en `__init__` (porque los parámetros genéricos `T` se borran en tiempo de ejecución en Python).
  - `get_by_id(id)`: busca por clave primaria con `session.get(self.modelo, id)`.
  - `get_all(*, offset=0, limit=None)`: devuelve las filas ordenadas por `id` con `offset` y `limit` opcional.
  - `count()`: cuenta las filas en la base con `SELECT count(*)` sin traer entidades a memoria.
  - `add(entidad)`: agrega la entidad a la sesión y ejecuta `await session.flush()` para obtener el `id` generado sin confirmar la transacción.
  - `update(entidad, datos)`: asigna los campos del diccionario `datos` sobre la entidad, la marca en la sesión y ejecuta `await session.flush()` sin confirmar.
  - `delete(entidad)`: elimina físicamente la fila con `await session.delete(entidad)` y ejecuta `await session.flush()` sin confirmar.

## Capabilities

### New Capabilities

- `repositorios`: operaciones genéricas de acceso a datos (`get_by_id`, `get_all`, `count`, `add`, `update`, `delete`) parametrizadas por modelo y sincronizadas con `flush()` sin confirmar la transacción.

### Modified Capabilities

(ninguna)

## Impact

- **Código:** `app/core/repository.py` (mergeado en el PR #65; posteriormente E2 sumó `SoftDeleteRepository[T]` en el mismo archivo). Este change no toca código.
- **Arquitectura:** habilitó `SoftDeleteRepository[T]` (E2) y el `UnitOfWork` (B4), garantizando la regla dura 12 (`ningún repositorio hace commit()`).
