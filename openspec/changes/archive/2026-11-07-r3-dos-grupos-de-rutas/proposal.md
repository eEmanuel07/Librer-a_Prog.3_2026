# Proposal: r3-dos-grupos-de-rutas

## Why

El Ejercicio 5 (Autorización), la regla de negocio RN-06 y el caso C-09 establecen que los routers se montan en dos grupos en `app/main.py`:
1. **Grupo abierto:** `GET /health/live`, `GET /health/ready`, `/auth` (`registro`, `login`, `logout`, `yo`, `cambiar-password`) y todas las lecturas (`GET`) públicas del catálogo (`/libros`, `/libros/{id}`, `/editoriales`, `/editoriales/{id}`, `/editoriales/{id}/libros`, `/generos`, `/generos/{id}/libros`, `/autores/{id}`, `/autores/{id}/libros`).
2. **Grupo protegido:** lleva montado **una sola vez** el control del cambio obligatorio de contraseña (`verificar_cambio_password_pendiente`, RN-06). Cuando `usuario.debe_cambiar_password` es verdadero, toda ruta del grupo protegido responde HTTP 403 Forbidden (salvo `/auth` y las rutas abiertas). Una vez cambiada la contraseña mediante `POST /auth/cambiar-password`, el usuario accede normalmente (200). Además, lo propio (`/mis-ventas`) solo pide estar autenticado dentro del grupo protegido (RN-14).

## What Changes

- En `app/core/dependencies.py`:
  - Agregar `verificar_cambio_password_pendiente(usuario: Usuario = Depends(get_usuario_actual)) -> Usuario` que lanza HTTP 403 (`"Debe cambiar su contraseña provisoria antes de continuar"`) si `usuario.debe_cambiar_password` es verdadero.
- En `app/modules/editoriales/router.py`, `app/modules/generos/router.py`, `app/modules/autores/router.py` y `app/modules/libros/router.py`:
  - Separar las lecturas públicas (`router`, grupo abierto) de las rutas protegidas (`router_protegido`, grupo protegido) manteniendo `router` con todas las rutas cuando un test unitario de módulo incluye `router` de forma aislada, o exportando `router_publico` y `router_protegido` para `app/main.py`.
- En `app/main.py`:
  - Declarar `grupo_abierto = APIRouter()` y `grupo_protegido = APIRouter(dependencies=[Depends(verificar_cambio_password_pendiente)])`, montando cada sub-router en el grupo correspondiente y registrando ambos grupos en `app`.
- En `tests/test_dos_grupos_rutas.py`:
  - Tests con `unittest` verificando el caso C-09 completo (usuario con `debe_cambiar_password=True` recibe 403 en rutas del grupo protegido, puede usar `/auth/yo`, `/auth/cambiar-password` y lecturas del grupo abierto, y tras cambiar su contraseña recibe 200 en el grupo protegido) y RN-14 (`/mis-ventas` accesible para cualquier usuario autenticado sin cambio pendiente).

## Capabilities

### New Capabilities

_(Ninguna capacidad nueva; amplía `autorizacion`)_

### Modified Capabilities

- `autorizacion`: Agrega el requerimiento de dos grupos de rutas en `main.py` y el bloqueo por cambio obligatorio de contraseña (RN-06, C-09).

## Impact

- `app/core/dependencies.py`
- `app/modules/editoriales/router.py`
- `app/modules/generos/router.py`
- `app/modules/autores/router.py`
- `app/modules/libros/router.py`
- `app/main.py`
- `tests/test_dos_grupos_rutas.py`
