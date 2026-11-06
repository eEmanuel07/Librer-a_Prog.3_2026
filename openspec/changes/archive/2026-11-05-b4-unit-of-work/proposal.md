# Proposal: b4-unit-of-work

> Issue: #33 (B4 — UnitOfWork). Consigna: `Parcial_Cap1a6_Consigna.pdf`, Ejercicio 6 y estructura obligatoria (pág. 8).
> Este change se escribe **antes** del código: no se implementa nada hasta que se apruebe el plan.

## Why

Hoy el proyecto tiene un único `UnitOfWork` en `app/core/uow.py`, que compone los repositorios de los seis módulos. La dependencia `get_uow` lo abre con `async with`, y cada service confirma a mano con `await uow.commit(...)` (10 llamadas). Eso no cumple el Ejercicio 6 en cuatro puntos:

- el base confirma por un método explícito y no al salir del bloque;
- no hay un Unit of Work por módulo;
- el UoW lo abre la dependencia y no el service;
- el archivo no está en la ruta que pide la estructura obligatoria (`app/core/unit_of_work.py`).

Además, la issue #33 pide que una petición autenticada use **una sola conexión del pool**: el usuario actual y el UoW tienen que compartir la sesión.

## What Changes

- **Nuevo** `app/core/unit_of_work.py` con el `UnitOfWork` base:
  - solo guarda la sesión;
  - al salir del bloque confirma si no hubo error y revierte si lo hubo;
  - traduce `IntegrityError` a `Conflicto` (409) con mensajes propios, tanto si salta dentro del bloque (por un flush) como en el commit;
  - no cierra la sesión;
  - se puede abrir más de una vez.
  - Los mensajes del 409 se pasan con `uow.con_mensajes(...)`, que devuelve el mismo UoW.
- **Nuevo** `app/modules/<módulo>/unit_of_work.py` en editoriales, géneros, autores, libros, clientes y ventas. Cada uno tiene su clase con los repositorios que el módulo necesita (ventas también tiene el de libros) y su dependencia `get_<módulo>_uow`, que lo construye sin abrirlo.
- **Services:** las 10 llamadas `await uow.commit(...)` se reemplazan por bloques `async with`. El service abre el UoW pero nunca lo construye.
- **Routers:** cada uno usa la dependencia de su módulo y le pasa el UoW al service sin abrirlo. La traducción de errores a 404/409 no cambia.
- **Usuarios:** solo cambia el import de `UsuarioUnitOfWork` a `app.core.unit_of_work`. `registrar_intento_acceso`, con su sesión propia (Ej. 7), no se toca.
- **BREAKING (interno):** se borran `app/core/uow.py`, `get_uow` y `UnitOfWork.commit(...)`. Los contratos HTTP no cambian (mismos códigos y mismos mensajes).

## Capabilities

### New Capabilities

- `transacciones`: cómo se confirma, revierte y traduce a 409 la escritura de cada petición, y la garantía de que cada petición usa una sola sesión (y una sola conexión) compartida entre el Unit of Work y las dependencias de autenticación.

### Modified Capabilities

(ninguna — `autenticacion` no cambia de comportamiento: el login sigue usando la sesión propia de `registrar_intento_acceso` a propósito)

## Impact

- **Código:**
  - `app/core/` (nuevo `unit_of_work.py`; se borra `uow.py`; se actualizan los docstrings de `errors.py` y `pagination.py`);
  - `service.py`, `router.py` y el nuevo `unit_of_work.py` de 6 módulos;
  - un import en `app/modules/usuarios/unit_of_work.py`;
  - tests nuevos en `tests/`.
- **API:** sin cambios visibles. Los `.http` de `test/` tienen que dar lo mismo que antes.
- **Tests:** los 12 tests de Hernán (`python -m unittest discover -s tests`) tienen que seguir pasando.
- **Fuera de alcance:** `get_usuario_actual` y la verificación de rol son la tarea **R1** (Bruno). Este change solo deja preparado y probado que una dependencia que usa `get_session` recibe la misma sesión que el UoW. No se toca la base de datos ni las migraciones.
