# Proposal: r5-roles-con-vigencia

> Issue: #49 ([R5] — Roles con vigencia: asignar y revocar). Consigna: `Parcial_Cap1a6_Consigna.pdf`, Ejercicio 5 (pág. 11), Ejercicio 6 (pág. 12), RN-03, RN-05, RN-16 y casos C-07 y C-08 (pág. 21).

## Why

El sistema necesita administrar los roles de los usuarios (`ADMIN`, `VENDEDOR`, `CLIENTE`) con vigencia opcional e historial completo de revocaciones. Las reglas RN-03, RN-05 y RN-16 exigen:
- A lo sumo una asignación abierta (`revocada_en IS NULL`) por usuario y rol (409 si ya tiene el rol vigente, pero si la asignación abierta ya venció, se cierra escribiendo `revocada_en` y se abre una fila nueva).
- Validar en el contrato que `vence_en` (si se envía) tenga zona horaria y esté en el futuro, respondiendo 422 (y nunca 409).
- Revocar escribiendo `revocada_en` sin borrar nunca la fila.
- Autoprotección (RN-05): un administrador no puede revocarse su propio rol `ADMIN` y el sistema nunca puede quedar sin administradores vigentes (409).
- Registrar cada asignación y revocación en `evento_seguridad` dentro del **mismo bloque** del Unit of Work (RN-16).

## What Changes

- **Índice único parcial en SQLite para tests (`app/modules/usuarios/models.py`)**:
  - Añadir `sqlite_where=text("revocada_en IS NULL")` al índice `uq_asignacion_rol_vigente` de `AsignacionRol` (igual que en `Libro`, ignorado por PostgreSQL) para que los tests en memoria validen el índice parcial y permitan reasignar roles revocados o cerrados por vencimiento.
- **Contratos de entrada y salida (`app/modules/usuarios/schemas.py`)**:
  - `AsignarRolRequest` (`extra="forbid"`): `rol` (`Literal["ADMIN", "VENDEDOR", "CLIENTE"]`) y `vence_en: datetime | None = None`, con validador que exige zona horaria (`tzinfo` con offset no nulo) y fecha futura (`vence_en > ahora_utc()`), devolviendo 422 en caso contrario.
  - `AsignacionRolRead`: contrato de salida con `id`, `usuario_id`, `rol`, `desde`, `vence_en`, `revocada_en`, `otorgada_por` y `vigente: bool`.
- **Consultas en `AsignacionRolRepository` (`app/modules/usuarios/repository.py`)**:
  - `obtener_abierta(usuario_id, rol)`: devuelve la fila con `revocada_en IS NULL` para ese usuario y rol, o `None`.
  - `listar_de_usuario(usuario_id)`: devuelve todas las asignaciones del usuario (vigentes, vencidas y revocadas) ordenadas por `id`.
  - `contar_admins_vigentes(ahora)`: cuenta cuántos usuarios activos tienen una asignación de `ADMIN` vigente (no revocada y sin vencer).
- **Lógica de negocio (`app/modules/usuarios/service.py`)**:
  - `asignar_rol(uow, usuario_id, datos, actor)`: en un solo bloque del UoW verifica que el usuario exista (404), si hay una asignación abierta vencida la cierra (`revocada_en = ahora`) antes de insertar la nueva (y si sigue vigente lanza `Conflicto` 409), inserta la nueva `AsignacionRol` con `otorgada_por=actor.id` y registra el `EventoSeguridad` (RN-16).
  - `listar_roles_usuario(uow, usuario_id)`: verifica que el usuario exista (404) y devuelve todas sus asignaciones.
  - `revocar_rol(uow, usuario_id, rol, actor)`: en un solo bloque verifica que el usuario exista (404) y tenga una asignación abierta vigente de ese rol (404 si no existe), aplica la autoprotección RN-05 (409 si `actor.id == usuario_id` y `rol == "ADMIN"`, o si `contar_admins_vigentes <= 1`), escribe `revocada_en = ahora` y registra el `EventoSeguridad` (RN-16).
- **Rutas HTTP (`app/modules/usuarios/router.py` y `app/main.py`)**:
  - `router_usuarios = APIRouter(prefix="/usuarios", tags=["usuarios"])` protegido con `Depends(requiere_rol("ADMIN"))`:
    - `POST /usuarios/{usuario_id}/roles` (201)
    - `GET /usuarios/{usuario_id}/roles` (200)
    - `DELETE /usuarios/{usuario_id}/roles/{rol}` (200)
  - Registrar `router_usuarios` en `app/main.py`.

## Capabilities

### New Capabilities

*(Ninguna)*

### Modified Capabilities

- `autorizacion`: Incorpora la asignación, consulta y revocación de roles con vigencia, reasignación de roles vencidos, autoprotección de administradores (RN-05) y auditoría en la misma transacción (RN-16).

## Impact

- `app/modules/usuarios/models.py`, `schemas.py`, `repository.py`, `service.py`, `router.py` y `app/main.py`.
- `tests/test_roles_vigencia.py`: suite completa de pruebas con `unittest`.
