# Design: r7-proteger-catalogo

## Context

- En `main`, los módulos `editoriales`, `generos` y `autores` todavía importaban `app/core/pagination.py` (del TP anterior, basado en `limit` y `offset` devolviendo `list[...]`) y no exigían `requiere_rol("ADMIN")` en sus endpoints de escritura.
- Además, `listar_libros` en `editoriales` y `generos`, y `listar_autorias` en `autores`, no filtraban `Libro.borrado_en.is_(None)` (RN-13).

## Goals / Non-Goals

**Goals:**
- Proteger todas las escrituras (`POST`, `PATCH`) de `editoriales`, `generos` y `autores` con `Depends(requiere_rol("ADMIN"))`.
- Mantener públicas todas las lecturas (`GET`) del catálogo (`03_actores_y_roles.md` §Rutas públicas).
- Migrar todos los listados de esos tres módulos a `app/core/paginacion.py` (`Pagina[...]`, `ParametrosPagina`, `parametros_pagina`, `paginar`).
- Excluir libros con `borrado_en` no nulo en `/{id}/libros`.

**Non-Goals:**
- Borrar `app/core/pagination.py` si otro módulo aún lo importa en ramas paralelas.

## Decisions

1. **Filtrado de borrado lógico en `autores`:**
   En `AutorRepository.listar_autorias_pagina`, se hace `.join(Libro, Libro.id == LibroAutor.libro_id).where(LibroAutor.autor_id == autor_id, Libro.borrado_en.is_(None))` manteniendo `options(joinedload(LibroAutor.libro))` para que el conteo de `paginar` y la página excluyan los libros dados de baja sin N+1.
