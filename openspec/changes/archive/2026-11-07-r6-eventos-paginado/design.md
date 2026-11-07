# Design: r6-eventos-paginado

## Context

- `EventoSeguridad` y `EventoSeguridadRepository` ya viven en `app/modules/usuarios/`.
- `app/core/paginacion.py` provee `Pagina[T]`, `ParametrosPagina`, `parametros_pagina` y `paginar(session, consulta, params)`.
- `app/main.py` ya tiene el manejador global de `PaginaInexistente` que devuelve HTTP 422 cuando se pide una página posterior a la última.

## Goals / Non-Goals

**Goals:**
- Exponer `GET /eventos` solo para `ADMIN` con el envoltorio `Pagina[EventoSeguridadRead]`.
- Ordenar los eventos de forma determinística (`order_by(EventoSeguridad.id)`).

**Non-Goals:**
- Agregar filtros no pedidos en la consigna.

## Decisions

1. **Router dedicado `router_eventos` en `app/modules/usuarios/router.py`:**
   Como `/eventos` cuelga de la raíz (igual que `/mis-ventas` en el módulo `ventas`), se define `router_eventos = APIRouter(prefix="/eventos", tags=["eventos"])` en `app/modules/usuarios/router.py` y se monta en `app/main.py`.
