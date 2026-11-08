# Proposal: libros-rol-admin

> Completa E4 (#23, PR #86) y E5 (#24, PR #92), que quedaron pidiendo sólo sesión hasta que existiera `requiere_rol` (R2). Consigna: `Parcial_Cap1a6_Consigna.pdf`, Ej. 5 y tabla de endpoints (págs. 16-18). Reglas: RN-04.
> El requisito de reposición y movimientos vive en la spec `movimientos-stock`, que crea el archivo de E5 (PR #102): este change se archiva después de ese.

## Why

La consigna pone el alta, el PATCH y la baja de libros, la reposición y la consulta de movimientos en el grupo protegido **para ADMIN**. E4 y E5 se hicieron antes de que existiera `requiere_rol` (R2), así que hoy piden sólo sesión con `get_usuario_actual`: cualquier usuario con sesión (un VENDEDOR, un CLIENTE) puede dar de alta, editar o dar de baja libros y reponer stock. Con R2 y R3 en `main`, falta cambiar esa dependencia.

## What Changes

- `POST /libros/`, `PATCH /libros/{id}`, `DELETE /libros/{id}`, `POST /libros/{id}/reponer` y `GET /libros/{id}/movimientos` pasan de `Depends(get_usuario_actual)` a `Depends(requiere_rol("ADMIN"))`.
  - Sin sesión, siguen respondiendo 401.
  - Con sesión y sin el rol ADMIN vigente **en la base** (RN-04), responden 403 sin escribir nada.
- Las lecturas públicas (`GET /libros/` y `GET /libros/{id}`) no cambian.
- `requiere_rol` devuelve el mismo `Usuario`, así que el service no cambia: el alta y la reposición siguen usando su id para el movimiento.

## Capabilities

### New Capabilities

(ninguna)

### Modified Capabilities

- `catalogo-libros`: las escrituras del catálogo exigen el rol ADMIN.
- `movimientos-stock`: la reposición y la consulta de movimientos exigen el rol ADMIN.

## Impact

- **Código:** sólo `app/modules/libros/router.py` y `tests/test_libros.py`.
- **Sin cambios:** el service, el repositorio, `app/core/dependencies.py` y `app/main.py` (el router protegido de libros ya está en el grupo protegido desde R3).
