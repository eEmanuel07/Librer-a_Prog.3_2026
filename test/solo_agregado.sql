-- C-14 · movimiento_stock es de solo agregado (RN-12, Ej. 7)
--
-- Qué demuestra: un UPDATE y un DELETE sobre movimiento_stock, hechos directo
-- en psql (sin pasar por la aplicación), los rechaza el disparador de la
-- migración 4 (trg_movimiento_stock_solo_agregado).
--
-- Cómo se corre (después de `alembic upgrade head` y `python seed.py`):
--   psql -X -e -v ON_ERROR_STOP=0 -h localhost -U postgres -d libreria -f test/solo_agregado.sql
--   -e muestra cada sentencia antes de su resultado; ON_ERROR_STOP=0 hace que
--   psql siga después del primer rechazo, así se ven los dos.
--
-- No deja rastros: todo corre en una transacción que termina en ROLLBACK, y
-- cada rechazo se deshace con su SAVEPOINT. Por eso crea sus propios datos y
-- no toca los de seed.py.
--
-- Ojo: el disparador es por fila, así que un UPDATE o un DELETE que no
-- encuentra filas no lo dispara y "funciona" sin hacer nada. Por eso el script
-- primero inserta un movimiento y apunta a él.

\echo '--- 0. El disparador está instalado en la tabla'
-- Esperado: una fila, trg_movimiento_stock_solo_agregado, habilitado (O).
SELECT tgname, tgenabled
FROM pg_trigger
WHERE tgrelid = 'movimiento_stock'::regclass AND NOT tgisinternal;

BEGIN;

\echo '--- 1. Datos propios y un movimiento (INSERT: se permite)'
-- Esperado: INSERT 0 1 en cada sentencia. Agregar está permitido.
INSERT INTO editorial (nombre, pais) VALUES ('Editorial C-14', 'AR');
INSERT INTO usuario (email, nombre, password_hash, activo, debe_cambiar_password)
VALUES ('c14@prueba.local', 'Prueba C-14', 'no-es-un-hash', true, false);
INSERT INTO libro (isbn, titulo, precio, stock, editorial_id)
SELECT 'C14-0001', 'Libro de la prueba C-14', 100.00, 5, id
FROM editorial WHERE nombre = 'Editorial C-14';
INSERT INTO movimiento_stock (libro_id, usuario_id, cantidad, motivo, cuando)
SELECT l.id, u.id, 5, 'Stock inicial', now()
FROM libro l, usuario u
WHERE l.isbn = 'C14-0001' AND u.email = 'c14@prueba.local';

SAVEPOINT antes_del_update;

\echo '--- 2. UPDATE sobre movimiento_stock'
-- Esperado: ERROR: movimiento_stock es de solo agregado: no admite UPDATE
--           (SQLSTATE 23001), con la pista de registrar otro movimiento que lo compense.
UPDATE movimiento_stock SET cantidad = 500
WHERE libro_id = (SELECT id FROM libro WHERE isbn = 'C14-0001');

ROLLBACK TO SAVEPOINT antes_del_update;
SAVEPOINT antes_del_delete;

\echo '--- 3. DELETE sobre movimiento_stock'
-- Esperado: ERROR: movimiento_stock es de solo agregado: no admite DELETE (SQLSTATE 23001).
DELETE FROM movimiento_stock
WHERE libro_id = (SELECT id FROM libro WHERE isbn = 'C14-0001');

ROLLBACK TO SAVEPOINT antes_del_delete;

\echo '--- 4. El movimiento quedó como estaba'
-- Esperado: una fila con cantidad 5. Ni el UPDATE ni el DELETE lo tocaron.
SELECT m.cantidad, m.motivo
FROM movimiento_stock m JOIN libro l ON l.id = m.libro_id
WHERE l.isbn = 'C14-0001';

ROLLBACK;
-- Esperado: ROLLBACK. La base queda igual que antes de correr el script.
