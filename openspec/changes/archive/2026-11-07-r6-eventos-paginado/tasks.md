# Tasks: r6-eventos-paginado

- [x] 1. Escribir tests en `tests/test_eventos.py` para `GET /eventos` (envoltorio `Pagina`, paginación real, 422 por página más allá de la última, 403 sin rol ADMIN, 401 sin sesión).
- [x] 2. Agregar `EventoSeguridadRead` en `app/modules/usuarios/schemas.py` y `listar_pagina` en `EventoSeguridadRepository` (`app/modules/usuarios/repository.py`).
- [x] 3. Implementar `listar_eventos` en `app/modules/usuarios/service.py`, `router_eventos` en `app/modules/usuarios/router.py` y registrarlo en `app/main.py`.
- [x] 4. Ejecutar la suite completa de tests con `python -m unittest discover -s tests`.
