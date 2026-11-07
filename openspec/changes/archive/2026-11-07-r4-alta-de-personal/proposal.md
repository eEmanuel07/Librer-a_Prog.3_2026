# Proposal: r4-alta-de-personal

## Why

El Ejercicio 5 (Autorización) y la regla de negocio RN-16 establecen que el alta de cuentas del personal se realiza mediante `POST /usuarios`, restringido exclusivamente a usuarios con rol `ADMIN` vigente. A diferencia del auto-registro de clientes (`POST /auth/registro`), el alta de personal crea la cuenta con una contraseña provisoria (`debe_cambiar_password = True`), sin crear ficha de cliente ni asignar roles automáticamente (los roles se otorgan por `POST /usuarios/{id}/roles`), y deja obligatoriamente una línea en `evento_seguridad` dentro de la misma transacción (`async with uow`).

## What Changes

- En `app/modules/usuarios/schemas.py`:
  - Agregar `CrearPersonalRequest(StrictSchema)` con `nombre`, `email` (normalizado) y `password: PasswordBcrypt` (validación de 1 a 72 bytes UTF-8).
  - Agregar `UsuarioRead(BaseModel)` con `id`, `email`, `nombre`, `activo` y `debe_cambiar_password` (nunca expone `password_hash`).
- En `app/modules/usuarios/service.py`:
  - Implementar `crear_personal(uow, datos, actor, settings) -> UsuarioRead`: calcula el hash bcrypt **antes** de abrir el `UnitOfWork`, y dentro de un único bloque `async with uow.con_mensajes(unique="El correo electrónico ya está registrado"):` inserta el `Usuario` (`activo=True`, `debe_cambiar_password=True`) y el `EventoSeguridad` (`actor=actor.email`, `accion=f"Alta de personal {usuario.email}"`).
- En `app/modules/usuarios/router.py`:
  - Exponer `POST /usuarios` (`status_code=201`, `response_model=UsuarioRead`) protegido con `Depends(requiere_rol("ADMIN"))`, traduciendo `Conflicto` a HTTP 409.
- En `tests/test_alta_personal.py`:
  - Tests con `unittest` verificando el alta 201 con `debe_cambiar_password=True` y evento de seguridad en la misma transacción, rechazo 409 por email duplicado sin dejar evento huérfano, rechazo 422 por contraseña > 72 bytes o campos extra, y rechazo 403 para usuarios sin rol `ADMIN`.

## Capabilities

### New Capabilities

_(Ninguna capacidad nueva; amplía `autorizacion`)_

### Modified Capabilities

- `autorizacion`: Agrega el requerimiento de alta de personal (`POST /usuarios`) con contraseña provisoria y auditoría atómica en `evento_seguridad` (RN-16).

## Impact

- `app/modules/usuarios/schemas.py`
- `app/modules/usuarios/service.py`
- `app/modules/usuarios/router.py`
- `tests/test_alta_personal.py`
