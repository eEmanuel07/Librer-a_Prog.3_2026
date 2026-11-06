# Spec Delta: paginacion

## Purpose

Define el contrato de paginación de los listados de la API: validación de los parámetros `page` y `size`, cálculo del total y de la cantidad de páginas bajo los mismos filtros de búsqueda, manejo de resultados vacíos y páginas fuera de rango, y estructura del envoltorio `{items, total, page, size, pages}`.

## ADDED Requirements

### Requirement: Parámetros de página y tamaño validados en la entrada
Todo listado paginado SHALL recibir `page` (entero mayor o igual a 1, por defecto 1) y `size` (entero entre 1 y 100 inclusive, por defecto 20), y SHALL rechazar con `422 Unprocessable Entity` cualquier valor fuera de esos rangos.

#### Scenario: Desplazamiento calculado a partir de página y tamaño
- **WHEN** se indican combinaciones válidas de `(page, size)` como `(1, 20)`, `(2, 20)` y `(3, 5)`
- **THEN** el desplazamiento (`offset`) calculado es `0`, `20` y `10` respectivamente

#### Scenario: Tamaño o número de página fuera de rango
- **WHEN** un cliente solicita un listado con `size=500` o con `page=0`
- **THEN** la API responde `422` sin ejecutar la consulta de listado

### Requirement: Envoltorio uniforme y cálculo de páginas con resultados vacíos
Todo listado paginado SHALL responder con el envoltorio `{items, total, page, size, pages}`, donde `total` se cuenta aplicando exactamente los mismos filtros que el listado y `pages` es `max(1, ceil(total / size))`, de modo que cuando `total` es `0` existe una única página vacía (`pages = 1`, `items = []`).

#### Scenario: Cantidad de páginas con elementos y sin elementos
- **WHEN** se arma una página para `6` elementos de a `2`, para `6` elementos de a `4` y para `0` elementos
- **THEN** `pages` vale `3`, `2` y `1` respectivamente

#### Scenario: Listado filtrado con resultados y sin resultados
- **WHEN** se consulta un listado aplicando un filtro que deja `1` resultado con `size=1`, o un filtro sin coincidencias (`total = 0`) en `page=1`
- **THEN** en el primer caso responde `200` con `total = 1, pages = 1`, y en el segundo responde `200` con `total = 0, pages = 1, items = []`

### Requirement: Rechazo con 422 de una página más allá de la última
Cuando el número de página solicitado (`page`) supera la cantidad total de páginas disponibles (`pages`), la API SHALL responder `422 Unprocessable Entity` con el detalle `"La página <page> no existe: hay <pages>"`.

#### Scenario: Última página válida y primera página sin resultados
- **WHEN** se pide la página `3` habiendo `6` elementos de a `2` (`pages = 3`), o la página `1` habiendo `0` resultados (`pages = 1`)
- **THEN** la validación acepta la página sin lanzar error

#### Scenario: Página posterior a la última
- **WHEN** existen `6` elementos con `size=2` (`pages = 3`) y se solicita `page=4`, o existe `1` elemento filtrado con `size=1` (`pages = 1`) y se solicita `page=2`
- **THEN** la API responde `422` con `"La página 4 no existe: hay 3"` y `"La página 2 no existe: hay 1"` respectivamente
