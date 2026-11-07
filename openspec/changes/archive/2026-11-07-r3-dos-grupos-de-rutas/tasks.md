# Tasks: r3-dos-grupos-de-rutas

- [x] 1. Escribir tests en `tests/test_dos_grupos_rutas.py` para el caso C-09 (bloqueo 403 con `debe_cambiar_password=True` en rutas protegidas, acceso permitido a `/auth` y rutas abiertas, y acceso 200 tras `POST /auth/cambiar-password`).
- [x] 2. Implementar `verificar_cambio_password_pendiente` en `app/core/dependencies.py`.
- [x] 3. Separar `router_publico` y `router_protegido` en `editoriales`, `generos`, `autores` y `libros`, y organizar `grupo_abierto` y `grupo_protegido` en `app/main.py`.
- [x] 4. Ejecutar la suite completa de tests con `python -m unittest discover -s tests`.
