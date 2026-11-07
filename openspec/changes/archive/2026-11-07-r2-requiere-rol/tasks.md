# Tasks

## 1. Dependencia `requiere_rol`

- [x] 1.1 Agregar `requiere_rol(*roles_permitidos: str)` en `app/core/dependencies.py` que reciba `usuario: Usuario = Depends(get_usuario_actual)` y `session: AsyncSession = Depends(get_session)`, consulte `AsignacionRolRepository(session).listar_roles_vigentes(usuario.id)`, responda 403 si el usuario no posee ninguno de los roles permitidos y devuelva el `Usuario` en caso contrario.

## 2. Pruebas unitarias y de integración

- [x] 2.1 Ampliar `tests/test_auth_dependencies.py` con casos de prueba para `requiere_rol`: acceso 200 con rol vigente devolviendo `Usuario`, rechazo 403 cuando falta el rol (C-06), rechazo 403 en la petición siguiente tras revocar el rol en la base con la sesión abierta (C-07), rechazo 403 cuando el rol venció aunque siga en el JWT, soporte de múltiples roles (`requiere_rol("VENDEDOR", "ADMIN")`) y verificación de sesión compartida con el Unit of Work.
- [x] 2.2 Ejecutar la suite completa con `python -m unittest discover -s tests` y verificar que todos los tests pasan sin regresiones.
