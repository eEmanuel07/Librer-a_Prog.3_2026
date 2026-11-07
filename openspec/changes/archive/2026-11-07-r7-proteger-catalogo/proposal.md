# Proposal: r7-proteger-catalogo

## Why

El Ejercicio 3 (Contratos y CRUD) y el Ejercicio 5 (Autorización, caso C-06) exigen que los módulos `editoriales`, `generos` y `autores`:
1. Protejan todas sus operaciones de escritura (`POST` y `PATCH`) con `Depends(requiere_rol("ADMIN"))`, manteniendo públicas todas las lecturas (`GET`) del catálogo (`knowledge-base/02_descripcion_general.md` §API y `03_actores_y_roles.md` §Rutas públicas).
2. Devuelvan todos sus listados con el envoltorio `{items, total, page, size, pages}` de `app/core/paginacion.py` (reemplazando `app/core/pagination.py`, IN-02).
3. Excluyan los libros dados de baja (`Libro.borrado_en.is_(None)`, RN-13) al listar los libros de una editorial, género o autor.

## What Changes

- En `app/modules/editoriales/` (`repository.py`, `service.py`, `router.py`):
  - Proteger `POST /editoriales/` y `PATCH /editoriales/{editorial_id}` con `Depends(requiere_rol("ADMIN"))`.
  - Migrar `GET /editoriales/` y `GET /editoriales/{editorial_id}/libros` al envoltorio `Pagina[...]` con `ParametrosPagina`, `parametros_pagina` y `paginar`.
  - Filtrar `Libro.borrado_en.is_(None)` en `listar_libros_pagina`.
- En `app/modules/generos/` (`repository.py`, `service.py`, `router.py`):
  - Proteger `POST /generos/` con `Depends(requiere_rol("ADMIN"))`.
  - Migrar `GET /generos/` y `GET /generos/{genero_id}/libros` al envoltorio `Pagina[...]`.
  - Filtrar `Libro.borrado_en.is_(None)` en `listar_libros_pagina`.
- En `app/modules/autores/` (`repository.py`, `service.py`, `router.py`):
  - Proteger `POST /autores/` y `PATCH /autores/{autor_id}` con `Depends(requiere_rol("ADMIN"))`.
  - Migrar `GET /autores/{autor_id}/libros` al envoltorio `Pagina[LibroDeAutor]`.
  - Filtrar `Libro.borrado_en.is_(None)` en `listar_autorias_pagina`.
- En `tests/test_catalogo_protegido.py`:
  - Tests con `unittest` verificando C-06 (401 sin sesión y 403 con rol `VENDEDOR` en escrituras de editoriales, géneros y autores; 201/200 con `ADMIN`), lecturas públicas con envoltorio `Pagina`, 422 en páginas inexistentes o campos extra/null, 409 por unicidad, y exclusión de libros dados de baja.

## Capabilities

### New Capabilities

_(Ninguna capacidad nueva; amplía `autorizacion`)_

### Modified Capabilities

- `autorizacion`: Agrega los requerimientos de protección RBAC (`ADMIN`) y paginación con envoltorio para `editoriales`, `generos` y `autores`.

## Impact

- `app/modules/editoriales/repository.py`, `service.py`, `router.py`
- `app/modules/generos/repository.py`, `service.py`, `router.py`
- `app/modules/autores/repository.py`, `service.py`, `router.py`
- `tests/test_catalogo_protegido.py`
