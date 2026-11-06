# Proposal: e6-disparador-solo-agregado

> Issues: #25 (E6 — migración 4) y #26 (E7, sólo la parte del caso C-14). Consigna: `Parcial_Cap1a6_Consigna.pdf`, Ejercicio 7 y caso C-14. Regla: RN-12.

## Nota sobre el orden: change retroactivo

Este change se escribió **después** de la implementación. La migración 4 ya estaba escrita, probada y mergeada (PR #79) cuando entró la regla 3 de `AGENTS.md` (PR #78), que pide arrancar cada tarea con `/opsx:propose`. El caso C-14 (PR #80) se armó en paralelo. Este documento deja registrado qué se hizo, por qué y cómo se verificó, igual que el change retroactivo de B6.

## Why

RN-12 pide que `movimiento_stock` sea de **sólo agregado**: nadie modifica ni borra sus filas, porque son el libro mayor del stock (`libro.stock` es la suma de sus movimientos, RN-11). La aplicación ya respeta eso, porque el único que escribe el stock es `LibroRepository.mover_stock`, que sólo inserta. Pero la consigna pide que lo garantice **la base**, venga el cambio de donde venga (la aplicación, psql u otra herramienta), y la comparación automática de Alembic no ve funciones ni disparadores. Por eso va una cuarta migración escrita a mano.

## What Changes

- **Migración 4, escrita a mano**: `migrations/versions/314ce2736bff_disparador_de_solo_agregado_en_.py` (revisa a `4a775b04f730`).
  - Función `movimiento_stock_solo_agregado()` en PL/pgSQL que lanza un error con SQLSTATE `23001` (`restrict_violation`) y una pista para compensar con otro movimiento.
  - Disparador `trg_movimiento_stock_solo_agregado`: `BEFORE UPDATE OR DELETE ON movimiento_stock FOR EACH ROW`.
  - El downgrade borra el disparador y después la función.
- **Caso C-14**: `test/solo_agregado.sql`, que corre en psql un UPDATE y un DELETE sobre `movimiento_stock` y muestra que la base los rechaza, y `evidencia/C-14_solo_agregado.txt` con la salida.
- **Corrección** en el comentario de la migración 4: la regla de "no termina en un 500" es RN-15, no RN-16.

## Capabilities

### New Capabilities

(ninguna)

### Modified Capabilities

- `esquema-base-datos`: se agrega el requisito de que `movimiento_stock` sea de sólo agregado, garantizado por la base.

## Impact

- **Base de datos:** una función y un disparador nuevos. Sin tablas ni columnas nuevas.
- **Código:** ninguno. `mover_stock` ya sólo insertaba.
- **seed.py:** sigue andando, porque vacía las tablas con `TRUNCATE`, que no dispara los disparadores por fila.
- **Fuera de alcance:** el segundo mecanismo de la sección 6.9 (quitarle al rol de la base el permiso de modificar la tabla); la consigna no lo pide porque el parcial usa un solo rol. Los casos C-13 y C-16 de E7 van en otro change, cuando estén E4 y E5.
