# Tasks: e6-disparador-solo-agregado

> Change retroactivo: todas las tareas ya estaban hechas cuando se escribió este archivo (ver `proposal.md`). Cada una indica su evidencia. Las pruebas se escribieron antes que la migración: primero se corrieron contra la migración vacía y fallaron, y después pasaron con la migración escrita.

## 1. Escribir la migración 4 a mano

- [x] 1.1 Crear la migración sin `--autogenerate`, revisando a `4a775b04f730`.
  - **Evidencia:** `migrations/versions/314ce2736bff_disparador_de_solo_agregado_en_.py` (`down_revision = '4a775b04f730'`), commit `047a1f8`, PR #79.
- [x] 1.2 Escribir la función `movimiento_stock_solo_agregado()` (SQLSTATE `23001`, con pista) y el disparador `trg_movimiento_stock_solo_agregado` (`BEFORE UPDATE OR DELETE ... FOR EACH ROW`); en el downgrade, borrar el disparador y después la función.
  - **Evidencia:** `upgrade()` y `downgrade()` de la migración.
- [x] 1.3 Dejar en el docstring que se leyó, por qué va a mano y las decisiones (`FOR EACH ROW`, SQLSTATE, `TRUNCATE`, orden del downgrade).
  - **Evidencia:** docstring "LEÍDA ANTES DE APLICARLA (Ej. 2). ESCRITA A MANO…".
- [x] 1.4 Corregir la regla citada en el docstring: "no termina en un 500" es RN-15, no RN-16 (observación de Belén en la revisión).
  - **Evidencia:** commit `docs(migraciones)` en el PR #80.

## 2. Verificar en una base vacía aparte

Script de prueba descartable, sobre una base temporal (`libreria_scratch_e6`) que se borra al terminar.

- [x] 2.1 RED: con la migración vacía, la prueba falla (escenarios "Modificar un movimiento" y "Borrar un movimiento").
  - **Evidencia:** 5 fallas: el disparador no existe y la base acepta el UPDATE y el DELETE.
- [x] 2.2 GREEN: con la migración escrita, pasan los 14 chequeos.
  - **Evidencia:** `upgrade head` desde una base vacía; el disparador existe; el INSERT se acepta; UPDATE y DELETE se rechazan con `sqlstate=23001` y el movimiento queda igual; el `TRUNCATE ... RESTART IDENTITY CASCADE` del seed anda; `downgrade -1` borra el disparador y la función; `downgrade base`, `upgrade head` otra vez y `alembic check` (`No new upgrade operations detected.`) andan.
- [x] 2.3 Escenario "Rechazo desde la aplicación": un UPDATE dentro de un `UnitOfWork` termina en `Conflicto`.
  - **Evidencia:** `Conflicto (409): No se pudo completar la escritura.`
- [x] 2.4 La suite existente sigue pasando.
  - **Evidencia:** `python -m unittest discover -s tests` → 27 tests OK.

## 3. Caso C-14 (parte de E7)

- [x] 3.1 Escribir `test/solo_agregado.sql`: muestra el disparador instalado, inserta un movimiento propio, intenta UPDATE y DELETE (cada uno con su `SAVEPOINT`), muestra que el movimiento quedó igual y termina en `ROLLBACK`. Cada paso con la respuesta esperada en un comentario.
  - **Evidencia:** `test/solo_agregado.sql`, PR #80.
- [x] 3.2 Correrlo en psql sobre una base nueva migrada y guardar la salida.
  - **Evidencia:** `evidencia/C-14_solo_agregado.txt` (psql 17.11): `ERROR: movimiento_stock es de solo agregado: no admite UPDATE` y `... no admite DELETE`; el movimiento sigue con cantidad 5; después del script, `movimiento_stock`, `libro` y `usuario` quedan vacíos.

## Notas de verificación

- Fuera de alcance: C-13 y C-16 en `test/libros.http` (resto de E7), que dependen de E4 y E5.
- Si al cierre hace falta una captura en imagen del C-14, se saca corriendo el mismo script sobre la base con `seed.py`.
