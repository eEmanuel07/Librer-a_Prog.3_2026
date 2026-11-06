# Proposal: b6-migracion-3

> Issue: #35 (B6 — migración 3). Consigna: `Parcial_Cap1a6_Consigna.pdf`, Ejercicio 2 (páginas 5 y 6).

## Nota sobre el orden: change retroactivo

Este change se escribió **después** de la implementación. La migración ya estaba generada, leída, corregida, aplicada y probada cuando se inicializó OpenSpec en el repo (rama `chore/openspec-init`, PR #73). No se cambió el orden a propósito para "aparentar" un flujo prolijo: OpenSpec todavía no existía en el proyecto cuando se hizo el trabajo. Este documento deja registrado qué se hizo, por qué y cómo se verificó, para que quede trazable igual que los cambios siguientes, que sí van a pasar primero por `propose`.

## Why

Los modelos del proyecto ya incluían el acceso de usuarios (usuario, roles, intentos de acceso, eventos de seguridad), los movimientos de stock y el borrado lógico de libros, pero la base de datos no tenía esas tablas ni columnas. El Ejercicio 2 pide llevar esos cambios a la base con una migración de Alembic generada con `--autogenerate`, **leída antes de aplicarla**, y probada en ambos sentidos (upgrade y downgrade).

## What Changes

Una sola migración nueva: `migrations/versions/4a775b04f730_acceso_movimientos_de_stock_y_borrado_.py` (revisa a `0efd84a6de03`). Trae:

- **Tabla `usuario`** con `email` UNIQUE.
- **Tabla `asignacion_rol`** con CHECK del rol (`ADMIN`, `VENDEDOR`, `CLIENTE`) e índice único parcial `(usuario_id, rol) WHERE revocada_en IS NULL` (un usuario no puede tener dos veces el mismo rol vigente).
- **Tabla `intento_acceso`** con índice `(email, ip, cuando)`.
- **Tabla `evento_seguridad`**.
- **Tabla `movimiento_stock`** con CHECK `cantidad <> 0` y `venta_id` que admite nulo (movimientos que no vienen de una venta).
- **`cliente.usuario_id`**: columna nueva, nula, con índice UNIQUE y FK a `usuario.id`.
- **`libro.borrado_en`**: columna nueva `timestamptz`, nula (borrado lógico).
- **BREAKING (esquema):** el UNIQUE común de `libro.isbn` se reemplaza por un índice único parcial `WHERE borrado_en IS NULL`, para que un ISBN dado de baja se pueda volver a cargar.
- Cada FK nueva tiene su índice.
- **Corrección manual** sobre lo autogenerado: la FK `cliente.usuario_id` venía sin nombre y el downgrade fallaba al no poder borrarla; se la nombró `cliente_usuario_id_fkey`.

## Capabilities

### New Capabilities

- `esquema-base-datos`: estado del esquema de PostgreSQL que gestionan las migraciones de Alembic (tablas, restricciones e índices) y la garantía de que se puede aplicar y revertir.

### Modified Capabilities

(ninguna — no hay specs previas en `openspec/specs/`)

## Impact

- **Base de datos:** 5 tablas nuevas, 2 columnas nuevas, cambio de la unicidad del ISBN.
- **Código:** ninguno en este change. Los modelos ya existían; solo se agregó el archivo de migración.
- **Riesgo conocido:** el downgrade vuelve a crear el UNIQUE común del ISBN, y falla si quedaron dos libros con el mismo ISBN (uno dado de baja y otro vigente).
- **Fuera de alcance:** el seed viejo (`scripts/seed.py`) deja de funcionar con esta migración. El seed nuevo es la tarea **R8** (de Bruno) y no se toca acá.
