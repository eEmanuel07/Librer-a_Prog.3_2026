# Proposal: b5-paginacion

> Issue: #34 (B5 — Paginación con envoltorio). PR: #66 (commits `0e5f20e` y `d91aea8`). Consigna: `Parcial_Cap1a6_Consigna.pdf`, Ejercicio 3 (págs. 8 y 10).

## Nota sobre el orden: change retroactivo

Este change se escribió **después** de la implementación. `app/core/paginacion.py` y el manejador global de `PaginaInexistente` en `app/main.py` ya estaban implementados, probados y mergeados en `main` (PR #66, commits `0e5f20e` y `d91aea8`) antes de que el grupo inicializara OpenSpec en el repositorio (PR #73). No se alteró el orden para aparentar un flujo distinto: OpenSpec todavía no existía cuando se hizo B5. Este documento deja asentado qué se construyó, por qué y cómo se verificó, sincronizando la spec `paginacion`.

## Why

En el TP los listados recibían `limit` y `offset` (`app/core/pagination.py`) y devolvían una lista suelta sin informar el total de registros ni la cantidad de páginas. El Ejercicio 3 del parcial pide un módulo `app/core/paginacion.py` con el envoltorio `{items, total, page, size, pages}`, `page` desde 1, `size` de 1 a 100 (20 por defecto), conteo con los mismos filtros de la consulta, una única página vacía cuando hay 0 resultados (`pages = 1`) y respuesta `422` cuando se pide una página más allá de la última.

## What Changes

- **Nuevo `app/core/paginacion.py`:**
  - `ParametrosPagina(page=1, size=20)` con propiedad `offset = (page - 1) * size` y dependencia `parametros_pagina` que valida `page >= 1` y `1 <= size <= 100` con `Query` (devolviendo 422 si no cumplen).
  - `calcular_paginas(total, size)`: devuelve `max(1, ceil(total / size))` (con 0 resultados hay 1 página vacía).
  - `PaginaInexistente(ErrorDeDominio)` y `validar_pagina(params, total)`: lanza `PaginaInexistente("La página X no existe: hay Y")` cuando `params.page > paginas`.
  - `paginar(session, consulta, params)`: calcula `total` sobre una subconsulta de `consulta.order_by(None)` (manteniendo exactamente los mismos filtros `WHERE`), valida la página pedida y ejecuta la consulta con `offset` y `limit`.
  - `Pagina[T](BaseModel, Generic[T])`: esquema genérico de salida con `{items, total, page, size, pages}` y constructor `Pagina.armar(items, total, params)`.
- **`app/main.py`:**
  - Manejador global `@app.exception_handler(PaginaInexistente)` que devuelve `422` con `{"detail": error.mensaje}`.

## Capabilities

### New Capabilities

- `paginacion`: validación de parámetros `page` y `size`, cálculo de páginas y desplazamiento, conteo consistente con los filtros aplicados, rechazo con 422 de páginas inexistentes y envoltorio `{items, total, page, size, pages}` para todos los listados.

### Modified Capabilities

(ninguna)

## Impact

- **Código:** `app/core/paginacion.py` y el `@app.exception_handler(PaginaInexistente)` en `app/main.py` (ya mergeados en el PR #66; este change no toca código).
- **Convivencia temporal:** `app/core/pagination.py` (el del TP) sigue en el repo mientras cada módulo migra su listado a `app/core/paginacion.py` en su propia issue (E4, J6, J7, R6, R7; ver IN-02 en `knowledge-base/10_preguntas_abiertas.md`).
