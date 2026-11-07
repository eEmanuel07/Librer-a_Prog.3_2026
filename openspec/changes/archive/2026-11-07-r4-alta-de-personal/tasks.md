# Tasks: r4-alta-de-personal

- [x] 1. Escribir tests en `tests/test_alta_personal.py` para `POST /usuarios` (201 con `debe_cambiar_password=True` y `EventoSeguridad`, 409 por email duplicado sin evento huérfano, 422 por contraseña > 72 bytes o campo extra, 403 para no ADMIN).
- [x] 2. Agregar `CrearPersonalRequest` y `UsuarioRead` en `app/modules/usuarios/schemas.py`.
- [x] 3. Implementar `crear_personal` en `app/modules/usuarios/service.py` y el endpoint `POST /usuarios` en `app/modules/usuarios/router.py`.
- [x] 4. Ejecutar la suite completa de tests con `python -m unittest discover -s tests`.
