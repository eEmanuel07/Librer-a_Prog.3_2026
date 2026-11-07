# Design: r8-seed-en-la-raiz

## Context

El script `scripts/seed.py` del TP 1-4 no contempla las tablas nuevas de la migración 3 (`usuario`, `asignacion_rol`, `intento_acceso`, `evento_seguridad`, `movimiento_stock`), escribe `libro.stock` directamente sin generar movimientos y vive en `scripts/seed.py` en lugar de `seed.py` en la raíz (issue #52, R8).

## Goals / Non-Goals

**Goals:**
- Ubicar `seed.py` en la raíz del proyecto para que se ejecute con `python seed.py`.
- Permitir inyectar una fábrica de sesiones opcional en `sembrar(fabrica=None, settings=None)` para poder testearlo contra SQLite en memoria en la suite de `unittest` sin requerir PostgreSQL levantado, manteniendo el comportamiento por defecto contra `get_settings().database_url`.
- Utilizar `LibroRepository(session).mover_stock(...)` tanto para el `"Stock inicial"` como para las salidas de la venta 1, garantizando por construcción el invariante `libro.stock == sum(movimientos)` (RN-11).

**Non-Goals:**
- No modifica modelos ni migraciones.

## Decisions

### 1. Uso de `mover_stock` para el stock inicial y la venta 1
- **Decisión:** Crear los 5 libros con `stock=0`, hacer `flush()`, aplicar `mover_stock` con `"Stock inicial"` (`Rayuela` 11, `Antología` 5, `Ficciones` 10, `Respiración artificial` 3, `Bestiario` 1) a nombre de `admin@example.com`, y luego registrar la venta 1 de Lucía (`1 Rayuela` + `2 Ficciones`, total `69000.00`) descontando `-1` y `-2` con `mover_stock` a nombre de `vendedor@example.com` y con `venta_id=venta.id`.
- **Por qué:** Respeta RN-11 (punto único de escritura de stock) y deja los stocks finales exactos de la consigna (`10, 5, 8, 3, 1`) con `ids_con_stock_inconsistente() == []`.

### 2. Limpieza idempotente compatible con PostgreSQL y SQLite (tests)
- **Decisión:** En PostgreSQL usar `TRUNCATE TABLE ... RESTART IDENTITY CASCADE` (que no dispara el trigger por fila `trg_movimiento_stock_solo_agregado`). Si el dialecto es SQLite (usado en los tests unitarios), borrar las filas en orden inverso de dependencias.
- **Por qué:** Permite probar `sembrar()` dos veces seguidas en `unittest` con SQLite en memoria y a la vez usar `TRUNCATE ... RESTART IDENTITY CASCADE` en PostgreSQL real.
