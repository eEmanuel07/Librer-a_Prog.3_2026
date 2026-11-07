# Tasks: j8-ventas-http-c15

## 1. test/ventas.http

- [x] 1.1 Logins de VENDEDOR, ADMIN y Ana con `# @name` y `# @no-cookie-jar`
- [x] 1.2 Acceso: 401 sin sesión, 403 para un CLIENTE
- [x] 1.3 C-10, C-11 y C-12 con el stock y los movimientos antes y después
- [x] 1.4 Contrato del TP, detalle (J5) y listados con el envoltorio (J6)
- [x] 1.5 C-15: venta de 4 renglones y los dos detalles

## 2. Evidencia

- [x] 2.1 `evidencia/C-15_consultas_detalle.txt` con la consola de `GET /ventas/1` (2 renglones) y `GET /ventas/6` (4 renglones): 4 SELECT en cada uno

## 3. Verificación

- [x] 3.1 Base nueva con `alembic upgrade head` + `python seed.py` y servidor con `SQL_ECHO=true`: `test/ventas.http` 36 de 36 con el código esperado; los avisos de C-10 y C-15 aparecen en la consola después de la respuesta

## Workflow follow-up

- Abrir PR hacia `main` con título `test(ventas): ventas.http con C-10 a C-12 y evidencia de C-15` y `Closes #61`. Va después del PR de J7.
