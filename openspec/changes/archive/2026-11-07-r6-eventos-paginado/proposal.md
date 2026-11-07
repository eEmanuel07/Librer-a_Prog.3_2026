# Proposal: r6-eventos-paginado

## Why

El Ejercicio 5 (Autorización) y el Ejercicio 3 (Contratos y CRUD) establecen que los administradores pueden consultar el historial de seguridad (`evento_seguridad`) a través del endpoint `GET /eventos`, restringido al rol `ADMIN` y con el envoltorio de paginación `{items, total, page, size, pages}` de `app/core/paginacion.py`.

## What Changes

- En `app/modules/usuarios/schemas.py`:
  - Agregar `EventoSeguridadRead(BaseModel)` con `id`, `cuando`, `actor` y `accion`.
- En `app/modules/usuarios/repository.py`:
  - Agregar `listar_pagina(self, params: ParametrosPagina)` en `EventoSeguridadRepository` usando `paginar(self.session, select(EventoSeguridad).order_by(EventoSeguridad.id), params)`.
- En `app/modules/usuarios/service.py`:
  - Agregar `listar_eventos(uow: UsuarioUnitOfWork, params: ParametrosPagina) -> Pagina[EventoSeguridadRead]`.
- En `app/modules/usuarios/router.py` y `app/main.py`:
  - Declarar `router_eventos = APIRouter(prefix="/eventos", tags=["eventos"])` con `GET /eventos` (`response_model=Pagina[EventoSeguridadRead]`, protegido con `Depends(requiere_rol("ADMIN"))`) y registrarlo en `app/main.py`.
- En `tests/test_eventos.py`:
  - Tests con `unittest` para el listado paginado de eventos (altas de personal, cambios de rol y contraseña, línea `SISTEMA`), 422 por página inexistente, y 403 para usuarios sin rol `ADMIN`.

## Capabilities

### New Capabilities

_(Ninguna capacidad nueva; amplía `autorizacion`)_

### Modified Capabilities

- `autorizacion`: Agrega el requerimiento de consulta paginada del historial de seguridad (`GET /eventos`).

## Impact

- `app/modules/usuarios/schemas.py`
- `app/modules/usuarios/repository.py`
- `app/modules/usuarios/service.py`
- `app/modules/usuarios/router.py`
- `app/main.py`
- `tests/test_eventos.py`
