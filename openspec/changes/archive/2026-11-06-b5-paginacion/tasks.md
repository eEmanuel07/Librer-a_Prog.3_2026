# Tasks: b5-paginacion

> Change retroactivo: todas las tareas se implementaron y verificaron en el PR #66 (commits `0e5f20e` y `d91aea8`), y las funciones puras se volvieron a verificar en memoria el 2026-11-06.

## 1. Envoltorio de paginación y manejador global de `PaginaInexistente`

- [x] 1.1 Crear `app/core/paginacion.py` con `ParametrosPagina`, `parametros_pagina`, `calcular_paginas`, `validar_pagina`, `paginar`, `Pagina[T]` y `PaginaInexistente`, y registrar el `@app.exception_handler(PaginaInexistente)` con `422` en `app/main.py`.
  - **Evidencia:** `app/core/paginacion.py` y `app/main.py` (commits `0e5f20e` y `d91aea8`, PR #66).

## 2. Verificación unitaria y por HTTP

- [x] 2.1 Verificar el cálculo de `offset`, `Pagina.armar` y `validar_pagina`.
  - **Evidencia (PR #66 y re-verificación 2026-11-06):**
    - `offset`: `(page 1, size 20)` → `0`; `(2, 20)` → `20`; `(3, 5)` → `10`.
    - `Pagina.armar`: `6` elementos de a `2` → `pages 3`; `6` de a `4` → `pages 2`; `0` elementos → `pages 1` (página vacía).
    - `validar_pagina`: página `3` de `3` → ok; página `1` sin resultados (`total = 0`) → ok; página `4` con `6` elementos de a `2` → lanza `PaginaInexistente("La página 4 no existe: hay 3")`.
- [x] 2.2 Verificar por HTTP con la consulta real de libros (incluyendo los casos de C-16).
  - **Evidencia (PR #66):**
    - `titulo=ficc&size=1` → `200`, `total 1`, `pages 1` (C-16);
    - `titulo=ficc&size=1&page=2` → `422` `"La página 2 no existe: hay 1"` (C-16);
    - `size=500` → `422` (C-16);
    - `page=0` → `422`;
    - `size=2` → `total 6`, `pages 3`;
    - `size=2&page=4` → `422`;
    - `titulo=noexiste` → `total 0`, `pages 1`, `items []`.
