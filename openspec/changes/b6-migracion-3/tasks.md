# Tasks: b6-migracion-3

> Change retroactivo: todas las tareas ya estaban hechas cuando se escribió este archivo (ver `proposal.md`). Cada una indica su evidencia.

## 1. Generar y leer la migración

- [x] 1.1 Generar la migración con `alembic revision --autogenerate` a partir de los modelos, revisando a `0efd84a6de03`.
  - **Evidencia:** `migrations/versions/4a775b04f730_acceso_movimientos_de_stock_y_borrado_.py` (`down_revision = '0efd84a6de03'`), commit `1409c5d` en `feat/b6-migracion-3`.
- [x] 1.2 Leer la migración antes de aplicarla y comprobar que trae lo que piden los requisitos de `specs/esquema-base-datos/spec.md`: tablas `usuario`, `asignacion_rol`, `intento_acceso`, `evento_seguridad` y `movimiento_stock`; columnas `cliente.usuario_id` y `libro.borrado_en`; ISBN con índice único parcial; un índice en cada FK.
  - **Evidencia:** el docstring de la migración ("LEÍDA ANTES DE APLICARLA (Ej. 2)") resume lo revisado.
- [x] 1.3 Corregir a mano la FK `cliente.usuario_id`, que venía sin nombre y rompía el downgrade, nombrándola `cliente_usuario_id_fkey`.
  - **Evidencia:** `op.create_foreign_key('cliente_usuario_id_fkey', ...)` en el `upgrade()` y `op.drop_constraint('cliente_usuario_id_fkey', ...)` en el `downgrade()`, con el comentario "Corrección manual", más la explicación en el docstring.
- [x] 1.4 Documentar en el docstring el riesgo del downgrade con ISBN duplicados.
  - **Evidencia:** el docstring de la migración ("Ojo en el downgrade: vuelve a crear el UNIQUE común del ISBN…").

## 2. Aplicar y verificar contra la base de desarrollo

- [x] 2.1 Aplicar la migración sobre la base `libreria` (contenedor `libreria-db`, puerto 5433) y verificar que queda en `head`.
  - **Evidencia:** `alembic upgrade head` → `Running upgrade 0efd84a6de03 -> 4a775b04f730, acceso, movimientos de stock y borrado logico`; `alembic current` → `4a775b04f730 (head)`.
- [x] 2.2 Verificar que el esquema coincide con los modelos (requisito "Migraciones reversibles y consistentes con los modelos", escenario "Sin diferencias con los modelos").
  - **Evidencia:** `alembic check` → `No new upgrade operations detected.` (código de salida 0). Las líneas `Detected sequence ... assuming SERIAL and omitting` son informativas y no son diferencias.

## 3. Prueba de ida y vuelta en base vacía

- [x] 3.1 En una base vacía aparte (`libreria_prueba`, creada con `createdb` dentro de `libreria-db` y apuntada con `POSTGRES_DB=libreria_prueba`), correr `upgrade head → downgrade base → upgrade head` (escenario "Ida y vuelta en base vacía").
  - **Evidencia:** antes de empezar, `alembic current` sobre `libreria_prueba` salió vacío, lo que confirmó que no apuntaba a `libreria`. Upgrade: `-> 24071e705bcf -> 0efd84a6de03 -> 4a775b04f730`. Downgrade: `4a775b04f730 -> 0efd84a6de03 -> 24071e705bcf -> (base)`. Segundo upgrade: igual que el primero. Todos con código de salida 0. `alembic current` → `4a775b04f730 (head)`.
- [x] 3.2 Borrar la base de prueba y confirmar que la base `libreria` no cambió.
  - **Evidencia:** `dropdb -U postgres libreria_prueba` (código de salida 0); `alembic current` sobre `libreria` → `4a775b04f730 (head)`.

## 4. Probar los escenarios de la spec con datos reales

Contra la base `libreria` (`docker exec -i libreria-db psql -U postgres -d libreria`), en **una sola transacción terminada en `ROLLBACK`**, con un `SAVEPOINT` antes de cada caso. Se usaron datos de prueba nuevos (prefijo `zz_prueba`), respetando las FK y los CHECK que ya existían (`precio > 0`, `stock >= 0`).

- [x] 4.1 Email repetido en `usuario` → falla (requisito "Email de usuario único").
  - **Evidencia:** `ERROR: 23505` (unique_violation) sobre `usuario_email_key`.
- [x] 4.2 Asignación con rol `'JEFE'` → falla (escenario "Rol inexistente").
  - **Evidencia:** `ERROR: 23514` (check_violation) sobre `ck_asignacion_rol_rol`.
- [x] 4.3 Dos asignaciones `VENDEDOR` vigentes del mismo usuario → falla; con la primera revocada (`revocada_en` con fecha), la segunda entra (escenarios "Mismo rol vigente dos veces" y "Volver a otorgar un rol revocado").
  - **Evidencia:** `ERROR: 23505` sobre `uq_asignacion_rol_vigente`; con la primera revocada, las dos filas entran (`INSERT 0 1` dos veces; consulta: `VENDEDOR | revocada t` y `VENDEDOR | revocada f`).
- [x] 4.4 Movimiento de stock con `cantidad = 0` → falla (escenario "Cantidad cero").
  - **Evidencia:** `ERROR: 23514` sobre `ck_movimiento_stock_cantidad_no_cero`. El insert usaba `venta_id` nulo y la única restricción violada fue el CHECK.
- [x] 4.5 Dos clientes con el mismo `usuario_id` → falla (escenario "Usuario compartido por dos clientes").
  - **Evidencia:** el primer cliente entra (`INSERT 0 1`) y el segundo da `ERROR: 23505` sobre `ix_cliente_usuario_id`.
- [x] 4.6 Dos libros vigentes con el mismo ISBN → falla; con el primero dado de baja (`borrado_en` con fecha), el segundo entra (escenarios "ISBN repetido entre libros vigentes" y "Volver a cargar un ISBN dado de baja").
  - **Evidencia:** `ERROR: 23505` sobre `uq_libro_isbn_vigente`; con el primero dado de baja, las dos filas entran (consulta: `Libro 1 (baja) | t` y `Libro 2 (vigente) | f`).
- [x] 4.7 Confirmar que la prueba no dejó datos en la base.
  - **Evidencia:** la transacción terminó en `ROLLBACK`. Después, un conteo de las filas de prueba (`zz_prueba%` en `usuario`, `editorial`, `libro` y `cliente`) y de `asignacion_rol` y `movimiento_stock` dio `0|0|0|0|0|0`.

## Notas de verificación

- Fuera de alcance: `scripts/seed.py` deja de funcionar con esta migración; el seed nuevo es la tarea R8.

## Workflow follow-up

- Revisar el change; después, `openspec validate b6-migracion-3` y archivar con `/opsx:archive` cuando la issue #35 esté aprobada.
