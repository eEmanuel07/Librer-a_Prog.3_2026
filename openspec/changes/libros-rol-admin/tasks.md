# Tasks: libros-rol-admin

TDD: el test del 403 se escribe primero (`tests/test_libros.py`) y tiene que fallar antes de cambiar el router.

## 1. Tests

- [ ] 1.1 El usuario de prueba recibe una asignación ADMIN; se agrega un usuario VENDEDOR
- [ ] 1.2 Con el VENDEDOR: alta, PATCH, baja, reponer y movimientos dan 403 y no escriben nada (falla antes del cambio)
- [ ] 1.3 Las lecturas públicas (`GET /libros/`, `GET /libros/{id}`) siguen respondiendo sin sesión

## 2. Router

- [ ] 2.1 Los cinco endpoints con `Depends(requiere_rol("ADMIN"))` en lugar de `Depends(get_usuario_actual)`

## 3. Verificación

- [ ] 3.1 Suite completa: `python -m unittest discover -s tests`
- [ ] 3.2 Prueba manual contra PostgreSQL con el seed de R8: `admin@example.com` 201 y `vendedor@example.com` 403, con login real por cookie
- [ ] 3.3 `openspec validate libros-rol-admin --strict`
