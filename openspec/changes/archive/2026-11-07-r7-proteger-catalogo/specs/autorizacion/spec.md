## ADDED Requirements

### Requirement: Protección RBAC y paginación con envoltorio en editoriales, géneros y autores
El sistema SHALL exigir el rol `ADMIN` vigente (`Depends(requiere_rol("ADMIN"))`) en todas las operaciones de escritura (`POST` y `PATCH`) de `editoriales`, `generos` y `autores`, mantener públicas sus lecturas (`GET`), devolver todos sus listados con el envoltorio `{items, total, page, size, pages}` de `app/core/paginacion.py`, y excluir los libros dados de baja (`borrado_en IS NOT NULL`, RN-13) de los listados `/{id}/libros`.

#### Scenario: Vendedor intenta crear o modificar editorial, género o autor y recibe 403 (C-06)
- **WHEN** un usuario autenticado con rol `VENDEDOR` (sin rol `ADMIN` vigente) envía `POST` o `PATCH` a `/editoriales`, `/generos` o `/autores`
- **THEN** el sistema responde HTTP 403 Forbidden sin realizar cambios

#### Scenario: Visitante sin sesión consulta listados del catálogo y recibe el envoltorio de paginación
- **WHEN** un visitante sin sesión envía `GET /editoriales`, `GET /generos` o `GET /editoriales/{id}/libros`, `GET /generos/{id}/libros`, `GET /autores/{id}/libros`
- **THEN** el sistema responde HTTP 200 con `{items, total, page, size, pages}` excluyendo los libros dados de baja
