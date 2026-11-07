# Design: r2-requiere-rol

## Context

Véase `proposal.md` y `specs/autorizacion/spec.md`. El módulo `app/core/dependencies.py` ya cuenta con `get_usuario_actual` (PR #85), y `app/modules/usuarios/repository.py` ya dispone de `AsignacionRolRepository.listar_roles_vigentes(usuario_id)` ([H1]/[H4]), que filtra `revocada_en IS NULL` y `(vence_en IS NULL OR vence_en > ahora)`.

## Goals / Non-Goals

**Goals:**
- Implementar `requiere_rol(*roles_permitidos: str)` en `app/core/dependencies.py`.
- Consultar siempre los roles vigentes en la base usando la misma sesión de `get_session` que `get_usuario_actual` y el Unit of Work.
- Responder 403 Forbidden cuando el usuario no tenga ninguno de los roles requeridos vigentes en la base.
- Devolver el objeto `Usuario` cuando la verificación sea exitosa.

**Non-Goals:**
- Modificar `get_usuario_actual` o `get_roles_token`.
- Endpoints de asignación y revocación de roles (`POST`/`GET`/`DELETE /usuarios/{id}/roles` corresponden a [R5]).
- Montaje de los dos grupos de rutas y control de cambio obligatorio de contraseña en `main.py` (corresponde a [R3]).

## UI Mockups

Decision: no (no UI)

## Decisions

### 1. Firma `requiere_rol(*roles_permitidos: str)` que devuelve `Usuario`
- **Decisión**: `requiere_rol` recibe uno o más nombres de rol (`"ADMIN"`, `"VENDEDOR"`, `"CLIENTE"`) y devuelve una corrutina dependencia de FastAPI cuyo valor de retorno es `Usuario`.
- **Alternativa descartada**: Recibir un único `rol: str` o no devolver el usuario. Varios endpoints del sistema admiten tanto `VENDEDOR` como `ADMIN` (ventas y clientes), y otros necesitan el `usuario.id` para auditoría o movimientos de stock usando una sola dependencia `usuario: Usuario = Depends(requiere_rol("ADMIN"))`.

### 2. Consulta en la base con la sesión compartida (RN-04)
- **Decisión**: La dependencia interna inyecta `usuario: Usuario = Depends(get_usuario_actual)` y `session: AsyncSession = Depends(get_session)`, e invoca `await AsignacionRolRepository(session).listar_roles_vigentes(usuario.id)`.
- **Alternativa descartada**: Leer `request.state.roles_token`. La regla RN-04 establece que los roles del token son solo informativos y que revocar un rol con la sesión abierta debe dar 403 en la petición siguiente (caso C-07).

## Risks / Trade-offs

- **[Llamada a `requiere_rol()` sin argumentos]** → Mitigación: validar que `roles_permitidos` no esté vacío al construir la dependencia (`ValueError`), evitando crear por error una ruta donde ningún rol pueda entrar.
