# Design: r4-alta-de-personal

## Context

- `router_usuarios` (`prefix="/usuarios"`) ya está registrado en `app/main.py` desde `[R5]`.
- La regla RN-16 exige que cada alta de personal deje una fila en `evento_seguridad` en el **mismo** bloque `async with` del `UnitOfWork`.
- El Ejercicio 4 exige que el cálculo de bcrypt (`hashear_password`) ocurra fuera del bloque transaccional para no retener una conexión del pool mientras corre el hash en el hilo trabajador.

## Goals / Non-Goals

**Goals:**
- Implementar `POST /usuarios` (201 Created) exclusivo para `ADMIN`.
- Garantizar `debe_cambiar_password = True` en el usuario creado y registrar `EventoSeguridad` en la misma transacción.
- Mantener la validación estricta (`extra="forbid"`, `PasswordBcrypt` hasta 72 bytes UTF-8) y no exponer `password_hash`.

**Non-Goals:**
- Bloquear el acceso a rutas protegidas cuando `debe_cambiar_password` es verdadero (eso corresponde a `[R3]` en `app/main.py` y `app/core/dependencies.py`).

## Decisions

1. **Hash fuera de la transacción y escritura única en UoW:**
   `crear_personal` llama primero a `await hashear_password(datos.password, settings=settings)` y luego abre `async with uow.con_mensajes(unique="El correo electrónico ya está registrado"):` donde hace `await uow.usuarios.add(usuario)` y `await uow.eventos.add(EventoSeguridad(...))`. Si `uow.usuarios.add` lanza `IntegrityError` por correo repetido, el UoW revierte toda la transacción (no queda evento de seguridad) y lanza `Conflicto` (409).
2. **Ruta sin barra final obligatoria:**
   En `router_usuarios` (`prefix="/usuarios"`), se declara `@router_usuarios.post("", response_model=UsuarioRead, status_code=status.HTTP_201_CREATED)` para responder directamente a `POST /usuarios`.
