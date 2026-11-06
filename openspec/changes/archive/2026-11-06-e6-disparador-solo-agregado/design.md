# Design: e6-disparador-solo-agregado

## Context

Ver `proposal.md` (Why y la nota sobre el orden retroactivo). La base estaba en `4a775b04f730` (migración 3), que ya trae la tabla `movimiento_stock` con su CHECK `cantidad <> 0`. El requisito que debe cumplir el esquema está en `specs/esquema-base-datos/spec.md`.

## Goals / Non-Goals

**Goals:**
- Que la base rechace cualquier UPDATE o DELETE sobre `movimiento_stock`, sin importar quién lo intente.
- Que el rechazo nunca termine en un 500 si alguna vez lo dispara la aplicación (RN-15).
- Que el downgrade deje la base exactamente como estaba en la migración 3.

**Non-Goals:**
- Cambiar código de la aplicación.
- Quitarle permisos al rol de la base (segundo mecanismo de la sección 6.9, que no se pide).

## Decisions

### 1. Migración escrita a mano
Se creó con `alembic revision -m ...` (sin `--autogenerate`) y se escribió con `op.execute`.
- **Por qué:** autogenerate no compara funciones ni disparadores; nunca la habría generado, y `alembic check` no avisa si falta.

### 2. `BEFORE UPDATE OR DELETE ... FOR EACH ROW`
- **Por qué:** corta la operación antes de que toque la fila, y el mismo disparador cubre las dos operaciones prohibidas.
- **Consecuencia:** un UPDATE o DELETE que no encuentra filas no dispara nada y termina "bien" sin hacer cambios. Por eso `test/solo_agregado.sql` inserta un movimiento antes de intentarlo.

### 3. SQLSTATE `23001` (`restrict_violation`)
- **Por qué:** es de la clase 23 (violación de integridad). asyncpg la levanta como `IntegrityConstraintViolationError` y SQLAlchemy como `IntegrityError`, así que el `UnitOfWork` la traduce a `Conflicto` (409) con mensaje propio, sin texto de la base.
- **Alternativa descartada:** el `RAISE EXCEPTION` sin código (SQLSTATE `P0001`), que llegaría como un error genérico y terminaría en 500.

### 4. `TRUNCATE` no se bloquea
- **Por qué:** no es UPDATE ni DELETE, no dispara los disparadores por fila, y `seed.py` lo usa (`TRUNCATE ... RESTART IDENTITY CASCADE`) para dejar la base en su estado inicial.
- **Alternativa descartada:** un disparador `BEFORE TRUNCATE` a nivel sentencia, que rompería el seed.

### 5. El caso C-14 no deja rastros
`test/solo_agregado.sql` crea sus propios datos, corre en una transacción que termina en `ROLLBACK` y deshace cada rechazo con su `SAVEPOINT`.
- **Por qué:** se puede correr cuantas veces se quiera, sobre cualquier base migrada, sin alterar la igualdad entre `libro.stock` y la suma de sus movimientos.

## Risks / Trade-offs

- **[Riesgo] Un movimiento mal cargado no se puede corregir** → es lo que se busca. Se compensa con otro movimiento de signo contrario, y la pista del error lo dice.
- **[Trade-off] `TRUNCATE` sigue permitido** → quien tenga acceso a la base puede vaciar la tabla. Se acepta porque el seed lo necesita y porque la consigna sólo pide UPDATE y DELETE.

## Migration Plan

1. `alembic upgrade head` (`4a775b04f730 → 314ce2736bff`).
2. Prueba de ida y vuelta en una base vacía aparte: `upgrade head → downgrade -1 → downgrade base → upgrade head`, y después se borra esa base.
3. **Rollback:** `alembic downgrade 4a775b04f730`, que borra el disparador y la función sin tocar datos.

## UI Mockups

- Decision: no (no UI) — 2026-11-06. El change sólo toca la base.
