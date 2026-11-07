# Design: r5-roles-con-vigencia

## Context

Véase `proposal.md` y `specs/autorizacion/spec.md`. El módulo `usuarios` ya cuenta con `AsignacionRol` y `EventoSeguridad` ([H1]), `UsuarioUnitOfWork` con `self.asignaciones_rol` y `self.eventos` ([H6]), y `requiere_rol("ADMIN")` en `app/core/dependencies.py` ([R2]).

## Goals / Non-Goals

**Goals:**
- Implementar `POST /usuarios/{usuario_id}/roles`, `GET /usuarios/{usuario_id}/roles` y `DELETE /usuarios/{usuario_id}/roles/{rol}` solo para `ADMIN`.
- Validar en el contrato que `vence_en` tenga zona horaria y esté en el futuro (422).
- Cerrar la fila anterior (`revocada_en = ahora`) al reasignar un rol cuya asignación abierta ya venció, y rechazar con 409 si el rol ya está vigente (RN-03).
- Impedir que un `ADMIN` se revoque su propio `ADMIN` o que el sistema quede sin administradores vigentes (RN-05, 409).
- Anotar cada asignación y revocación en `evento_seguridad` en el mismo bloque `async with uow` (RN-16).

**Non-Goals:**
- Alta de personal `POST /usuarios` (corresponde a [R4]).
- Listado paginado `GET /eventos` (corresponde a [R6]).

## UI Mockups

Decision: no (no UI)

## Decisions

### 1. Reasignación de un rol vencido en el mismo bloque
- **Decisión**: Antes de insertar la nueva `AsignacionRol`, se consulta si existe una fila con `revocada_en IS NULL` para `(usuario_id, rol)`. Si existe y `vence_en <= ahora` (ya venció), se escribe `revocada_en = ahora` y se hace `flush()` para liberar el índice único parcial `uq_asignacion_rol_vigente` antes de agregar la nueva fila. Si existe y sigue vigente (`vence_en IS NULL` o `vence_en > ahora`), se lanza `Conflicto` (409).
- **Alternativa descartada**: Borrar la fila vencida con `DELETE`. La consigna prohíbe borrar filas de `asignacion_rol` para conservar el historial.

### 2. Validación de `vence_en` en el schema (422)
- **Decisión**: `AsignarRolRequest` valida en Pydantic (`field_validator`) que `vence_en` (cuando no es `None`) tenga `tzinfo is not None` y `utcoffset() is not None`, y que sea estrictamente mayor a `datetime.now(timezone.utc)`. Así FastAPI responde 422 Unprocessable Entity sin tocar la base de datos.

### 3. Autoprotección en `revocar_rol` (RN-05)
- **Decisión**: Si `rol == "ADMIN"` y `actor.id == usuario_id`, se lanza `Conflicto("Un administrador no puede revocarse su propio rol ADMIN")` (409). Además, si `rol == "ADMIN"` y `await uow.asignaciones_rol.contar_admins_vigentes(ahora) <= 1`, se lanza `Conflicto("El sistema no puede quedar sin administradores vigentes")` (409).

## Risks / Trade-offs

- **[Comparación de fechas naive vs aware en SQLite durante tests]** → Mitigación: normalizar a UTC cualquier fecha leída de SQLite antes de compararla con `ahora` en Python.
