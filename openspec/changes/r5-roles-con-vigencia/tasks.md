# Tasks

## 1. Modelo, contratos y repositorio de roles

- [x] 1.1 Agregar `sqlite_where=text("revocada_en IS NULL")` al índice `uq_asignacion_rol_vigente` en `app/modules/usuarios/models.py`.
- [x] 1.2 Agregar `RolNombre`, `AsignarRolRequest` (con validación 422 de `vence_en` con zona horaria y en el futuro) y `AsignacionRolRead` en `app/modules/usuarios/schemas.py`.
- [x] 1.3 Agregar `obtener_abierta`, `listar_de_usuario` y `contar_admins_vigentes` en `AsignacionRolRepository` (`app/modules/usuarios/repository.py`).

## 2. Servicio y rutas de roles con vigencia

- [x] 2.1 Implementar `asignar_rol`, `listar_roles_usuario` y `revocar_rol` en `app/modules/usuarios/service.py` cumpliendo RN-03, RN-05 y RN-16 en un único bloque del Unit of Work.
- [x] 2.2 Exponer `POST /usuarios/{usuario_id}/roles`, `GET /usuarios/{usuario_id}/roles` y `DELETE /usuarios/{usuario_id}/roles/{rol}` en `router_usuarios` (`app/modules/usuarios/router.py`) protegidos con `Depends(requiere_rol("ADMIN"))`, y montarlo en `app/main.py`.

## 3. Pruebas unitarias y de integración

- [x] 3.1 Crear `tests/test_roles_vigencia.py` verificando: alta de rol sin vencimiento y con vencimiento futuro (201 + evento RN-16), rechazo 422 por vencimiento en el pasado o sin zona horaria (C-07/C-08), rechazo 409 por rol vigente duplicado (RN-03), reasignación de rol vencido cerrando la fila anterior y abriendo una nueva, revocación escribiendo `revocada_en` sin borrar la fila y cortando el permiso de la sesión abierta en la petición siguiente (C-07), autoprotección 409 cuando un ADMIN intenta revocarse su propio ADMIN (C-08 / RN-05) y listado de roles.
- [x] 3.2 Ejecutar la suite completa con `python -m unittest discover -s tests` y verificar que todos los tests pasan sin regresiones.
