# Línea de base — b4-unit-of-work (tarea 0.2)

Referencia de "sin cambios": lo que devuelve la API **antes** de tocar el Unit of Work. Cada commit del change se compara contra esta tabla (mismos códigos y mismos mensajes).

## Cómo se obtuvo

- **Fecha:** 2026-11-05. **Rama:** `feat/b4-unit-of-work` en `d01f83f` (sin cambios de código).
- **Base:** copia `libreria_b4`, creada con `docker exec libreria-db createdb -U postgres -T libreria libreria_b4`. Se borra y se vuelve a crear **antes de cada archivo** `.http`, así cada uno parte de los mismos datos iniciales (como en `evidencia/integracion.txt`). La base `libreria` no se toca.
- **App:** `uvicorn app.main:app --port 8000` con `POSTGRES_DB=libreria_b4`. Se levanta y se apaga en cada archivo.
- **Peticiones:** las de los 7 archivos de `test/`, en orden (health, editoriales, generos, autores, libros, clientes, ventas), con un script fuera del repo (`correr_http.py`, en el scratchpad de la sesión) que entiende la sintaxis de REST Client (`@var`, `# @name`, `{{x.response.body.id}}`). El "esperado" sale del comentario `# Esperado:` de cada petición.
- **Ojo:** esta rama no tiene la migración 3 (entra con el PR #76 de B6). La copia ya está en `4a775b04f730` porque viene de `libreria`.

## Resumen

- **109 peticiones.** Las 109 dieron el código esperado y **ninguna dio 500**. El log de uvicorn no tiene errores ni trazas.

| Archivo | Peticiones | 200 | 201 | 404 | 405 | 409 | 422 |
|---|---|---|---|---|---|---|---|
| `health.http` | 2 | 2 | — | — | — | — | — |
| `editoriales.http` | 17 | 5 | 2 | 3 | — | 2 | 5 |
| `generos.http` | 10 | 3 | 1 | 1 | — | 1 | 4 |
| `autores.http` | 13 | 4 | 1 | 3 | — | — | 5 |
| `libros.http` | 28 | 9 | 2 | 2 | — | 7 | 8 |
| `clientes.http` | 24 | 7 | 2 | 4 | — | 4 | 7 |
| `ventas.http` | 15 | 2 | 1 | 1 | 1 | 2 | 8 |
| **Total** | **109** | **32** | **9** | **14** | **1** | **16** | **37** |

## Detalle por petición

El mensaje es el `detail` de la respuesta cuando es texto (los 409 y 404). En los 422 de validación, `detail` es una lista de FastAPI y no se transcribe.

### `health.http`

| # | Petición | Código | Mensaje |
|---|---|---|---|
| 1 | GET `/health/live` — Vivo (no toca la base) | 200 |  |
| 2 | GET `/health/ready` — Listo (ejecuta SELECT 1) | 200 |  |

### `editoriales.http`

| # | Petición | Código | Mensaje |
|---|---|---|---|
| 1 | POST `/editoriales/` — Alta de una editorial | 201 |  |
| 2 | POST `/editoriales/` — Nombre repetido | 409 | Ya existe una editorial con ese nombre |
| 3 | POST `/editoriales/` — El id no viaja en el alta | 422 |  |
| 4 | POST `/editoriales/` — Nombre vacio | 422 |  |
| 5 | GET `/editoriales/?limit=5&offset=0` — Listado paginado (RN-10) | 200 |  |
| 6 | GET `/editoriales/?limit=0` — Paginacion fuera de rango: limit 0 | 422 |  |
| 7 | GET `/editoriales/7` — Detalle de la editorial recien creada | 200 |  |
| 8 | GET `/editoriales/99999` — Detalle de una editorial que no existe | 404 | La editorial no existe |
| 9 | GET `/editoriales/abc` — C-01 · Id que no es un entero | 422 |  |
| 10 | PATCH `/editoriales/7` — PATCH parcial: solo el pais | 200 |  |
| 11 | POST `/editoriales/` — Segunda editorial, para probar el nombre repetido en el PATCH | 201 |  |
| 12 | PATCH `/editoriales/9` — PATCH con el nombre de otra editorial | 409 | Ya existe una editorial con ese nombre |
| 13 | PATCH `/editoriales/7` — PATCH con un campo en null | 422 |  |
| 14 | PATCH `/editoriales/99999` — PATCH de una editorial que no existe | 404 | La editorial no existe |
| 15 | GET `/editoriales/1/libros` — Libros de una editorial | 200 |  |
| 16 | GET `/editoriales/7/libros` — Libros de la editorial recien creada | 200 |  |
| 17 | GET `/editoriales/99999/libros` — Libros de una editorial que no existe | 404 | La editorial no existe |

### `generos.http`

| # | Petición | Código | Mensaje |
|---|---|---|---|
| 1 | POST `/generos/` — Alta de un genero | 201 |  |
| 2 | POST `/generos/` — Nombre repetido | 409 | Ya existe un género con ese nombre |
| 3 | POST `/generos/` — El id no viaja en el alta | 422 |  |
| 4 | POST `/generos/` — Nombre vacio | 422 |  |
| 5 | GET `/generos/?limit=5&offset=0` — Listado paginado (RN-10) | 200 |  |
| 6 | GET `/generos/?offset=-1` — Paginacion fuera de rango: offset negativo | 422 |  |
| 7 | GET `/generos/1/libros` — Libros de un genero | 200 |  |
| 8 | GET `/generos/5/libros` — Libros del genero recien creado | 200 |  |
| 9 | GET `/generos/99999/libros` — Libros de un genero que no existe | 404 | El género no existe |
| 10 | GET `/generos/abc/libros` — C-01 · Id que no es un entero | 422 |  |

### `autores.http`

| # | Petición | Código | Mensaje |
|---|---|---|---|
| 1 | POST `/autores/` — Alta de un autor | 201 |  |
| 2 | POST `/autores/` — El id no viaja en el alta | 422 |  |
| 3 | POST `/autores/` — Falta la nacionalidad | 422 |  |
| 4 | GET `/autores/6` — Detalle del autor recien creado | 200 |  |
| 5 | GET `/autores/99999` — Detalle de un autor que no existe | 404 | El autor no existe |
| 6 | GET `/autores/abc` — C-01 · Id que no es un entero | 422 |  |
| 7 | PATCH `/autores/6` — PATCH parcial: solo la nacionalidad | 200 |  |
| 8 | PATCH `/autores/6` — PATCH con un campo en null | 422 |  |
| 9 | PATCH `/autores/99999` — PATCH de un autor que no existe | 404 | El autor no existe |
| 10 | GET `/autores/1/libros` — Libros de un autor, con el rol y el orden de cada autoria | 200 |  |
| 11 | GET `/autores/6/libros` — Libros del autor recien creado | 200 |  |
| 12 | GET `/autores/99999/libros` — Libros de un autor que no existe | 404 | El autor no existe |
| 13 | GET `/autores/1/libros?limit=101` — Paginacion fuera de rango en los libros del autor | 422 |  |

### `libros.http`

| # | Petición | Código | Mensaje |
|---|---|---|---|
| 1 | POST `/libros/` — Alta de un libro con dos autores (rol y orden) | 201 |  |
| 2 | POST `/libros/` — C-02 · ISBN repetido | 409 | El ISBN ya existe o un autor figura dos veces en el libro |
| 3 | POST `/libros/` — C-04 · Libro con una editorial inexistente | 409 | La editorial, el género o algún autor indicado no existe |
| 4 | POST `/libros/` — C-04 · Libro con un autor inexistente | 409 | La editorial, el género o algún autor indicado no existe |
| 5 | POST `/libros/` — Alta de un libro con género (agregación opcional) | 201 |  |
| 6 | POST `/libros/` — Libro con un género inexistente | 409 | La editorial, el género o algún autor indicado no existe |
| 7 | POST `/libros/` — Un mismo autor dos veces en el mismo libro | 409 | El ISBN ya existe o un autor figura dos veces en el libro |
| 8 | POST `/libros/` — RN-03 · Precio en cero | 422 |  |
| 9 | POST `/libros/` — RN-03 · Stock negativo | 422 |  |
| 10 | POST `/libros/` — Rol que no está permitido | 422 |  |
| 11 | GET `/libros/12` — C-07 · Detalle del libro recién creado | 200 |  |
| 12 | GET `/libros/99999` — Detalle de un libro que no existe | 404 | El libro no existe |
| 13 | GET `/libros/abc` — C-01 · Id que no es un entero | 422 |  |
| 14 | GET `/libros/?limit=20&offset=0` — Listado paginado (RN-10) | 200 |  |
| 15 | GET `/libros/?limit=0` — Paginación fuera de rango: limit 0 | 422 |  |
| 16 | GET `/libros/?limit=101` — Paginación fuera de rango: limit 101 | 422 |  |
| 17 | GET `/libros/?genero_id=1` — Listado filtrado por género | 200 |  |
| 18 | GET `/libros/?genero_id=99999` — Listado filtrado por un género sin libros | 200 |  |
| 19 | GET `/libros/?titulo=PRUEBA` — RN-11 · Búsqueda por parte del título, sin distinguir mayúsculas | 200 |  |
| 20 | GET `/libros/?titulo=%27%20OR%20%271%27%3D%271` — C-08 · Búsqueda con intento de inyección SQL | 200 |  |
| 21 | PATCH `/libros/12` — PATCH parcial: sólo se cambia el título | 200 |  |
| 22 | PATCH `/libros/12` — PATCH: asignar un género a un libro | 200 |  |
| 23 | PATCH `/libros/12` — PATCH: quitar el género (es opcional) | 200 |  |
| 24 | PATCH `/libros/12` — PATCH a un género que no existe | 409 | La editorial, el género o algún autor indicado no existe |
| 25 | PATCH `/libros/12` — PATCH con un precio inválido | 422 |  |
| 26 | PATCH `/libros/12` — PATCH con un campo en null | 422 |  |
| 27 | PATCH `/libros/12` — PATCH a una editorial que no existe | 409 | La editorial, el género o algún autor indicado no existe |
| 28 | PATCH `/libros/99999` — PATCH de un libro que no existe | 404 | El libro no existe |

### `clientes.http`

| # | Petición | Código | Mensaje |
|---|---|---|---|
| 1 | GET `/clientes/abc` — C-01 · Parámetro de ruta que no es entero | 422 |  |
| 2 | POST `/clientes/` — C-02 · Email repetido (tomas@example.com ya existe en los datos iniciales) | 409 | El email ya está en uso |
| 3 | POST `/clientes/` — Email repetido en mayúsculas (el email se normaliza a minúsculas al entrar) | 409 | El email ya está en uso |
| 4 | POST `/clientes/` — Email inválido | 422 |  |
| 5 | POST `/clientes/` — El id no viaja en el alta | 422 |  |
| 6 | POST `/clientes/` — Nombre vacio | 422 |  |
| 7 | POST `/clientes/` — Alta de un cliente nuevo | 201 |  |
| 8 | GET `/clientes/8` — Detalle del cliente recién creado (sin perfil) | 200 |  |
| 9 | GET `/clientes/1` — Detalle del cliente 1 (con perfil) | 200 |  |
| 10 | GET `/clientes/99999` — Detalle de un cliente que no existe | 404 | El cliente no existe |
| 11 | PATCH `/clientes/8` — PATCH parcial: solo el nombre | 200 |  |
| 12 | PATCH `/clientes/8` — PATCH con email repetido | 409 | El email ya está en uso |
| 13 | PATCH `/clientes/8` — PATCH con un campo en null | 422 |  |
| 14 | PATCH `/clientes/99999` — PATCH de un cliente que no existe | 404 | El cliente no existe |
| 15 | POST `/clientes/1/perfil` — C-03 · El cliente 1 ya tiene perfil en los datos iniciales | 409 | El cliente ya tiene un perfil |
| 16 | POST `/clientes/2/perfil` — Perfil para el cliente 2 (que no tiene perfil) | 201 |  |
| 17 | POST `/clientes/99999/perfil` — El perfil de un cliente que no existe | 404 | El cliente no existe |
| 18 | GET `/clientes/2` — Detalle del cliente 2 con su perfil recién creado | 200 |  |
| 19 | GET `/clientes/1/ventas` — Ventas del cliente 1 (los datos iniciales cargan una venta con 2 renglones) | 200 |  |
| 20 | GET `/clientes/8/ventas` — Ventas de un cliente sin ventas | 200 |  |
| 21 | GET `/clientes/99999/ventas` — Ventas de un cliente que no existe | 404 | El cliente no existe |
| 22 | GET `/clientes/1/ventas?limit=1&offset=0` — Paginación de las ventas (RN-10) | 200 |  |
| 23 | GET `/clientes/1/ventas?limit=101` — limit fuera de rango | 422 |  |
| 24 | GET `/clientes/1/ventas?offset=-1` — offset negativo | 422 |  |

### `ventas.http`

| # | Petición | Código | Mensaje |
|---|---|---|---|
| 1 | POST `/ventas/` — C-06 · Venta válida con dos renglones | 201 |  |
| 2 | GET `/ventas/2` — C-07 · Detalle de la venta recién creada | 200 |  |
| 3 | GET `/ventas/?limit=20&offset=0` — Listado paginado (RN-10) | 200 |  |
| 4 | POST `/ventas/` — C-05 · Venta con un cliente inexistente | 409 | El cliente indicado no existe |
| 5 | POST `/ventas/` — C-05 · Venta con un libro inexistente | 409 | No existe el libro con id 9999 |
| 6 | POST `/ventas/` — RN-05 · Venta sin renglones | 422 |  |
| 7 | POST `/ventas/` — RN-05 · El mismo libro en dos renglones | 422 |  |
| 8 | POST `/ventas/` — RN-06 · El precio no viaja en el cuerpo | 422 |  |
| 9 | POST `/ventas/` — RN-07 · El total no viaja en el cuerpo | 422 |  |
| 10 | POST `/ventas/` — Cantidad no positiva | 422 |  |
| 11 | GET `/ventas/9999` — Detalle de una venta inexistente | 404 | La venta no existe |
| 12 | GET `/ventas/abc` — C-01 · Parámetro de ruta que no es entero | 422 |  |
| 13 | GET `/ventas/?limit=101` — RN-10 · limit fuera de rango | 422 |  |
| 14 | GET `/ventas/?offset=-1` — RN-10 · offset negativo | 422 |  |
| 15 | PATCH `/ventas/1` — RN-08 · Las ventas no se modifican | 405 | Method Not Allowed |
