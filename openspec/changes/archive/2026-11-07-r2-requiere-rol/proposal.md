# Proposal: r2-requiere-rol

> Issue: #46 ([R2] — requiere_rol (403) con roles vigentes en la base). Consigna: `Parcial_Cap1a6_Consigna.pdf`, Ejercicio 5 (pág. 11), Ejercicio 6 (pág. 12), RN-04 y casos C-06 y C-07 (pág. 21).

## Why

Con `get_usuario_actual` ya en `app/core/dependencies.py` (cubierta en PR #85), las rutas protegidas necesitan verificar qué roles tiene el usuario autenticado antes de permitirle ejecutar una operación. La regla RN-04 exige que los permisos se decidan consultando los roles vigentes (no revocados y sin vencer) **en la base de datos en cada petición**, usando la misma sesión del Unit of Work, porque los roles incluidos en el JWT son únicamente informativos. Así, si a un usuario con sesión abierta se le revoca un rol o ese rol vence, la petición siguiente recibe HTTP 403 Forbidden (caso C-07).

## What Changes

- **Dependencia de autorización por rol (`app/core/dependencies.py`)**:
  - Implementar la fábrica de dependencias `requiere_rol(*roles_permitidos: str)`:
    - Devuelve una dependencia asincrónica que recibe `usuario: Usuario = Depends(get_usuario_actual)` y `session: AsyncSession = Depends(get_session)`.
    - Consulta los roles vigentes del usuario en la base mediante `AsignacionRolRepository(session).listar_roles_vigentes(usuario.id)`.
    - Si el usuario no posee al menos uno de los `roles_permitidos` vigente en la base (aunque el rol figure en el claim `roles` del JWT), lanza `HTTPException(status_code=403, detail=...)`.
    - Devuelve la instancia de `Usuario` autenticado para que los endpoints puedan usar `usuario: Usuario = Depends(requiere_rol("ADMIN"))` o `Depends(requiere_rol("VENDEDOR", "ADMIN"))` como única dependencia.

## Capabilities

### New Capabilities

- `autorizacion`: Control de acceso basado en roles vigentes consultados en la base de datos en cada petición (RN-04), respondiendo HTTP 403 cuando el usuario autenticado carece del rol requerido.

### Modified Capabilities

*(Ninguna)*

## Impact

- `app/core/dependencies.py`: se agrega `requiere_rol` junto a `get_usuario_actual` sin alterar la firma ni el comportamiento de las funciones existentes.
- `tests/test_auth_dependencies.py`: se amplía con las pruebas unitarias y de integración de `requiere_rol` (acceso con rol vigente, rechazo 403 sin rol aunque figure en el token, revocación o vencimiento con sesión abierta C-07, soporte de múltiples roles permitidos y sesión compartida con el Unit of Work).
