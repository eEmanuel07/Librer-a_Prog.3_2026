# Design: b3-base-repository

## Context

Ver `proposal.md` (Why y nota de change retroactivo). Implementado y mergeado en el PR #65 (commit `7e9e89c`).

## Goals / Non-Goals

**Goals:**
- Proveer `BaseRepository[T]` en `app/core/repository.py` con las 6 operaciones que pide el Ejercicio 6 (pág. 12).
- Garantizar que toda escritura del repositorio haga `flush()` y nunca `commit()`.

**Non-Goals:**
- Implementar el borrado lógico (`SoftDeleteRepository[T]`, cubierto por E2 en el PR #69).
- Migrar todos los métodos específicos de cada repositorio de módulo en este change.

## Decisions

### 1. Pasar `modelo: type[T]` en `__init__`
En Python, `Generic[T]` se borra en tiempo de ejecución (`type erasure`), por lo que `select(T)` o `session.get(T, id)` no pueden conocer la tabla sin recibir la clase `modelo: type[T]` explícitamente en `__init__(self, session: AsyncSession, modelo: type[T])`.

### 2. Ordenamiento por `self.modelo.id` en `get_all`
PostgreSQL no garantiza el orden de las filas si la consulta no incluye `ORDER BY`. `get_all` ordena siempre por `self.modelo.id` para que `offset` y `limit` produzcan páginas determinísticas y sin solapamientos.

### 3. `flush()` en `add`, `update` y `delete`, nunca `commit()`
`flush()` envía el `INSERT`/`UPDATE`/`DELETE` a la transacción abierta de la sesión: así la entidad ya tiene su `id` asignado después de `add` y cualquier restricción de integridad salta dentro del bloque del Unit of Work, mientras que la decisión de confirmar (`commit`) o revertir (`rollback`) queda exclusivamente en el Unit of Work al salir del bloque `async with`.

## Risks / Trade-offs

- **[Trade-off] `update` recibe un `dict[str, Any]`** → quien llama a `update` en un `PATCH` debe construir el diccionario con `schema.model_dump(exclude_unset=True)` para no pisar campos no enviados (se documenta en el docstring de `update`).

## Migration Plan

Aplicado en `main` en el PR #65 (commit `7e9e89c`).

## UI Mockups

- Decision: no (no UI) — 2026-11-06. Capa interna de persistencia.
