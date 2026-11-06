# Design: b6-migracion-3

## Context

Ver `proposal.md` (Why y la nota sobre el orden retroactivo). La base estaba en `0efd84a6de03` (migración 2: género y `libro.genero_id`). Los modelos SQLModel ya describían el acceso, los movimientos de stock y el borrado lógico; faltaba llevarlos a la base. Las restricciones que debe cumplir el esquema están en `specs/esquema-base-datos/spec.md`.

## Goals / Non-Goals

**Goals:**
- Una sola migración (`4a775b04f730`) que lleve la base de `0efd84a6de03` a coincidir con los modelos.
- Que el downgrade deshaga todo lo que hace el upgrade, en orden inverso.

**Non-Goals:**
- Cambiar modelos o código de la aplicación.
- Migrar o adaptar datos existentes, incluido el seed (`scripts/seed.py`, tarea R8).

## Decisions

### 1. `--autogenerate` + lectura manual antes de aplicar
Se generó con `alembic revision --autogenerate` y se leyó línea por línea antes del `upgrade`; el docstring de la migración deja asentada esa lectura.
- **Por qué:** lo pide la consigna, y autogenerate no es confiable a ciegas (ver decisión 2).
- **Alternativa descartada:** escribir la migración a mano, que es más lenta y fácil de desalinear con los modelos.

### 2. Nombrar la FK `cliente_usuario_id_fkey`
Autogenerate dejó `op.create_foreign_key(None, 'cliente', ...)`. Con nombre `None`, el `drop_constraint` del downgrade no tiene qué borrar y falla. Se la nombró `cliente_usuario_id_fkey`, el mismo nombre que PostgreSQL le pondría automáticamente.
- **Por qué este nombre:** sigue la convención de PostgreSQL y de las otras FK, y la base queda igual que si la hubiera nombrado el motor.
- **Alternativa descartada:** configurar una `naming_convention` global en el `MetaData`; afecta a todas las migraciones y modelos, así que excede este change.

### 3. Unicidad del ISBN con índice único parcial
Se reemplaza `libro_isbn_key` (UNIQUE común) por `uq_libro_isbn_vigente` (`UNIQUE ... WHERE borrado_en IS NULL`).
- **Por qué:** con borrado lógico, un libro dado de baja sigue en la tabla. Un UNIQUE común impediría volver a cargar ese ISBN.
- **Alternativa descartada:** borrar físicamente el libro, lo que perdería el historial de movimientos y ventas que lo referencian.

### 4. Mismo patrón para roles vigentes
`uq_asignacion_rol_vigente` es un índice único parcial `(usuario_id, rol) WHERE revocada_en IS NULL`: se conserva el historial de asignaciones revocadas y se impide duplicar una vigente.

### 5. Índice en cada FK nueva
PostgreSQL no indexa las FK automáticamente. Se indexa cada una para que los joins y los borrados en la tabla padre no recorran la tabla entera.

## Risks / Trade-offs

- **[Riesgo] El downgrade vuelve a crear el UNIQUE común del ISBN** → si hay dos libros con el mismo ISBN (uno con `borrado_en`), `create_unique_constraint` falla y el downgrade se corta. **Mitigación:** queda advertido en el docstring de la migración; antes de un downgrade con datos reales hay que resolver los duplicados a mano. No se agregó limpieza automática, porque borrar o modificar libros en un downgrade es más peligroso que dejarlo fallar.
- **[Trade-off] El seed viejo deja de funcionar** → queda fuera de alcance y lo resuelve la tarea R8.

## Migration Plan

1. `alembic upgrade head` sobre la base de desarrollo (`0efd84a6de03 → 4a775b04f730`).
2. `alembic check` para confirmar que no quedan diferencias con los modelos.
3. Prueba de ida y vuelta en una base vacía aparte (`libreria_prueba`): `upgrade head → downgrade base → upgrade head`, y después se borra esa base.
4. **Rollback:** `alembic downgrade 0efd84a6de03`, teniendo en cuenta el riesgo del ISBN.

## UI Mockups

- Decision: no (no UI) — 2026-11-05. El change solo toca el esquema de la base.
