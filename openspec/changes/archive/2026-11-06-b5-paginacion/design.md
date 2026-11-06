# Design: b5-paginacion

## Context

Ver `proposal.md` (Why y nota de change retroactivo). Implementado y mergeado en el PR #66 (commits `0e5f20e` y `d91aea8`).

## Goals / Non-Goals

**Goals:**
- Proveer `app/core/paginacion.py` con `ParametrosPagina`, `parametros_pagina`, `calcular_paginas`, `validar_pagina`, `paginar` y `Pagina[T]`, y registrar `PaginaInexistente` en `app/main.py` como `422`.
- Mantener `app/core/pagination.py` mientras los demás módulos migran en sus propias tareas para no romper `main`.

**Non-Goals:**
- Migrar los routers de libros, clientes, ventas, catálogo o eventos en este change (cada frente lo hace en E4, J6, J7, R6 y R7).

## Decisions

### 1. Contar sobre `consulta.order_by(None).subquery()` en `paginar`
`paginar(session, consulta, params)` recibe el `Select` ya armado con sus filtros (`WHERE`) y su `ORDER BY`. Para obtener `total`, quita el `ORDER BY` innecesario en el conteo y ejecuta `select(func.count()).select_from(subconsulta)`.
- **Por qué:** garantiza por construcción que `total` use siempre los mismos filtros que `items` (requisito del Ej. 3 y caso C-16), ejecutando siempre dos consultas fijas.

### 2. `PaginaInexistente` traducida en `app/main.py` a 422
`validar_pagina` lanza `PaginaInexistente(ErrorDeDominio)` y `app/main.py` la captura con `@app.exception_handler(PaginaInexistente)` devolviendo `422` con `{"detail": error.mensaje}`.
- **Por qué:** una página más allá de la última incumple el contrato de entrada igual que `size=500` o `page=0`, y centralizar el handler en `main.py` evita repetir `try / except PaginaInexistente` en cada router.

## Risks / Trade-offs

- **[Trade-off] Convivencia temporal con `app/core/pagination.py`** → permite que B5 se mergee sin tocar los módulos de otros integrantes (regla 4 de `AGENTS.md`). `pagination.py` se elimina cuando el último módulo pase a `paginacion.py` (IN-02).

## Migration Plan

Aplicado en `main` en el PR #66 (commits `0e5f20e` y `d91aea8`).

## UI Mockups

- Decision: no (no UI) — 2026-11-06. Contrato JSON de paginación de la API.
