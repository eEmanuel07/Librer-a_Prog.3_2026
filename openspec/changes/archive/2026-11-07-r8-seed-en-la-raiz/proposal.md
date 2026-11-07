# Proposal: r8-seed-en-la-raiz

## Why

La consigna del Parcial (págs. 8, 19-21 y Ejercicio 5) exige que el script de carga inicial viva en la raíz del proyecto como `seed.py` (`python seed.py`), reemplazando a `scripts/seed.py` del TP. Además, después de la migración 3 el esquema exige usuarios, roles vigentes, movimientos de stock que respeten el invariante `stock = suma(movimientos)` para cada libro, y la fila inicial en `evento_seguridad` con actor `SISTEMA`.

## What Changes

- Se mueve y reemplaza `scripts/seed.py` por `seed.py` en la raíz del repositorio (y se elimina `scripts/`).
- `seed.py` vacía todas las tablas del proyecto con `TRUNCATE TABLE ... RESTART IDENTITY CASCADE` y carga:
  - **5 usuarios** con sus roles vigentes en `asignacion_rol`:
    - `admin@example.com` (`ADMIN`)
    - `admin2@example.com` (`ADMIN`)
    - `vendedor@example.com` (`VENDEDOR`)
    - `ana@example.com` (`CLIENTE`, vinculada a la clienta Ana Paz)
    - `nuevo@example.com` (`VENDEDOR`, con `debe_cambiar_password=True`)
  - **Catálogo:** 3 editoriales (`Sudamericana`, `Alfaguara`, `Emecé`), 3 géneros (`Novela`, `Cuento`, `Ensayo`), 6 autores (`Julio Cortázar`, `Ricardo Piglia`, `Silvina Ocampo`, `Adolfo Bioy Casares`, `Jorge Luis Borges`, `Ernesto Sabato`) y los 5 libros con su stock final (`Rayuela` 10, `Antología de la literatura fantástica` 5, `Ficciones` 8, `Respiración artificial` 3, `Bestiario` 1).
  - **Clientes:** `Lucía Fernández` (con `PerfilCliente`, sin usuario), `Tomás Ríos` (sin usuario) y `Ana Paz` (`usuario_id` vinculado a `ana@example.com`).
  - **Venta 1 y Movimientos de stock:** 5 movimientos de entrada `"Stock inicial"` (`Rayuela` +11, `Antología` +5, `Ficciones` +10, `Respiración artificial` +3, `Bestiario` +1) y la venta 1 de Lucía Fernández registrada por `vendedor@example.com` con 1 `Rayuela` ($25000.00) y 2 `Ficciones` ($22000.00 c/u, total $69000.00), con sus dos movimientos de salida (-1 y -2), cumpliendo `stock = suma(movimientos)` en los cinco libros.
  - **Historial de seguridad:** 1 fila en `evento_seguridad` con `actor="SISTEMA"` y `accion="Carga de los datos iniciales"`.
- Se agregan tests automáticos en `tests/test_seed.py`.

## Capabilities

### New Capabilities
- `datos-iniciales`: Carga idempotente del estado inicial del parcial desde `seed.py` en la raíz.

### Modified Capabilities
None.

## Impact

- Reemplaza `scripts/seed.py` por `seed.py` en la raíz (resuelve IN-01 / DD-08).
- Destraba la ejecución reproducible de `test/auth.http` (H7), `test/seguridad.http` (R9) y `test/ventas.http` (J8).
