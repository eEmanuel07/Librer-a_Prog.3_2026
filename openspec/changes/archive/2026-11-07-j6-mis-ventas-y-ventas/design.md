# Design: j6-mis-ventas-y-ventas

## UI Mockups

Decision: no (no UI)

## Context

B5 dejó `app/core/paginacion.py`: la dependencia `parametros_pagina` (page desde 1, size de 1 a 100, 20 por defecto), `paginar(session, consulta, params)` (conteo + página, `PaginaInexistente` si page pasa de la última, que `main.py` responde con 422) y `Pagina[T]` con `armar`. Ningún módulo lo usaba todavía. J5 dejó en el servicio de ventas el control «es personal» con los roles vigentes, y el repositorio de roles en el Unit of Work.

## Goals / Non-Goals

**Goals:**
- `GET /ventas` sólo para el personal, con el envoltorio.
- `GET /mis-ventas` para cualquier usuario autenticado, con sus ventas y el envoltorio.
- Consultas fijas y `total` contado con el mismo filtro que la página.

**Non-Goals:**
- No se pasan a `paginacion.py` los listados de otros módulos.
- No se agrega `requiere_rol`: es de R2.

## Decisions

### 1. Un solo método de repositorio para los dos listados
- **Decisión:** `listar_pagina(params, usuario_id=None)` arma `select(Venta)` con `joinedload(Venta.cliente)`, ordenado por id; con `usuario_id` agrega `JOIN cliente WHERE cliente.usuario_id = …`. La página y el conteo los hace `paginar`.
- **Por qué:** el conteo sale de la misma consulta que la página (sin el orden), así que `total` siempre usa el mismo filtro.

### 2. `/mis-ventas` en un router aparte del mismo módulo
- **Decisión:** `router_mis_ventas = APIRouter(tags=["ventas"])` en `app/modules/ventas/router.py`, registrado en `main.py`.
- **Por qué:** la ruta cuelga de la raíz y no de `/ventas`; sigue siendo del módulo ventas.

### 3. El rol de `GET /ventas` lo controla el servicio, por ahora
- **Decisión:** `listar_ventas` llama a `_es_personal` (roles vigentes en la base) y lanza `SinPermiso` (403).
- **Por qué:** sin `requiere_rol` en `main`, dejar la ruta sólo con sesión le mostraría todas las ventas a cualquier cliente. El comportamiento es el mismo que pide el Ej. 5 (403, roles de la base en cada petición).
- **Cuando llegue R2:** se agrega `Depends(requiere_rol("VENDEDOR", "ADMIN"))` en el router y se quita la comprobación del servicio.

### 4. Sin ficha de cliente, página vacía
- **Decisión:** `/mis-ventas` de un usuario sin ficha (por ejemplo, del personal) responde 200 con `items: []`, `total: 0`, `pages: 1`.
- **Por qué:** lo propio sólo pide estar autenticado, y la consigna dice que sin resultados hay una página vacía.

## Risks / Trade-offs

- **[Riesgo] Cambia el contrato de `GET /ventas`:** quien use `limit`/`offset` recibe la página 1 por defecto. Lo usan sólo `test/ventas.http` (J8) y la colección del TP.
- **[Trade-off] Doble control cuando llegue R2:** si no se quita la comprobación del servicio, se consultan los roles dos veces; no cambia el resultado.
