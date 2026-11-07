# Design: r3-dos-grupos-de-rutas

## Context

- `app/main.py` hoy incluye todos los routers directamente sobre `app`.
- Algunos tests existentes (`tests/test_libros.py`, `tests/test_catalogo_protegido.py`) importan `router` de `libros`, `editoriales`, `generos` o `autores` o usan `from app.main import app`.
- En `app/main.py`, las rutas tienen que estar divididas en dos `APIRouter`: `grupo_abierto` (sin dependencia global) y `grupo_protegido` (`dependencies=[Depends(verificar_cambio_password_pendiente)]` montado **una sola vez**).

## Goals / Non-Goals

**Goals:**
- Montar `verificar_cambio_password_pendiente` una sola vez en `grupo_protegido` dentro de `app/main.py`.
- Que las lecturas públicas del catálogo, `/health` y `/auth` pertenezcan a `grupo_abierto` y no ejecuten `verificar_cambio_password_pendiente`.
- Que todas las rutas protegidas (`/usuarios`, `/eventos`, `/clientes`, `/ventas`, `/mis-ventas`, escrituras del catálogo y `/libros/{id}/reponer`, `/libros/{id}/movimientos`) pertenezcan a `grupo_protegido`.
- Mantener 100 % de compatibilidad con los tests unitarios que montan `router` de un módulo de catálogo directamente en un `FastAPI()` de prueba.

## Decisions

1. **Sub-routers `router_publico` y `router_protegido` en los módulos de catálogo:**
   En `editoriales`, `generos`, `autores` y `libros`, las rutas públicas (`GET`) se registran en `router_publico` y las protegidas (`POST`, `PATCH`, `DELETE`, `reponer`, `movimientos`) en `router_protegido`. Además, `router` incluye ambos (`router.include_router(router_publico)` y `router.include_router(router_protegido)`) para que cualquier test que haga `app.include_router(editoriales_router)` siga teniendo todas las rutas del módulo, mientras que `app/main.py` monta `router_publico` en `grupo_abierto` y `router_protegido` en `grupo_protegido`.
2. **Protección de `libros` con `requiere_rol("ADMIN")`:**
   Como dejó documentado Elías en el comentario de `app/modules/libros/router.py` líneas 21-23 (*"cuando entre requiere_rol (R2, #46) cada una cambia esa dependencia por la del rol ADMIN (403)"*), actualizamos `tests/test_libros.py` para asignar el rol `ADMIN` al usuario de prueba `admin@libreria.local` si cambiamos a `requiere_rol("ADMIN")`, o mantenemos la compatibilidad con `dependency_overrides[get_usuario_actual]` dado que `requiere_rol` depende de `get_usuario_actual` y consulta `AsignacionRol` en la misma sesión.
