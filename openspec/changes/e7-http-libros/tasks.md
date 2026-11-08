# Tasks: e7-http-libros

## 1. Archivo

- [x] 1.1 Cabecera: `python seed.py` antes de correrlo, usuarios y libros del seed que se usan
- [x] 1.2 Inicio de sesión de ADMIN y VENDEDOR con la convención de `test/seguridad.http`
- [x] 1.3 Catálogo público: listado con envoltorio, detalle y 404, sin sesión
- [x] 1.4 C-16: inyección, filtro con `size=1`, `page=2`, `size=500`, PATCH parcial y PATCH con `stock`
- [x] 1.5 C-13: reponer, movimientos, baja, fuera del catálogo, reponer el dado de baja, recarga del ISBN, segundo vigente y la venta 1 con el título
- [x] 1.6 Rechazos del alta: 401, 403, 409 y 422

## 2. Verificación

- [x] 2.1 Script descartable que corre el archivo contra PostgreSQL (base temporal, `alembic upgrade head`, `python seed.py`) y compara cada código con su `# Esperado:`
- [x] 2.2 Suite completa: `python -m unittest discover -s tests`
- [x] 2.3 `openspec validate e7-http-libros --strict`
