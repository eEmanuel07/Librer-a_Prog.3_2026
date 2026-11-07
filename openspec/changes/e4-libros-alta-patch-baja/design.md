# Design: e4-libros-alta-patch-baja

## Context

Ya están en `main` las piezas que E4 necesita: `mover_stock` como único punto de escritura del stock (E3), `SoftDeleteRepository` con `soft_delete` (E2), el índice único parcial del ISBN (E1), el Unit of Work con `con_mensajes` (B4), la paginación con envoltorio (B5) y `get_usuario_actual` (R1, PR #85). Falta usarlas desde el módulo de libros.

## Goals / Non-Goals

**Goals**
- Alta, PATCH, baja y listado con el contrato del parcial.
- Que el alta respete RN-11: el stock nace de un movimiento, no de una asignación.
- Todo error de la base, traducido a 409 con mensaje propio (RN-15).

**Non-Goals**
- El control de rol ADMIN (R2, #46): se suma cuando esté.
- Reposición y movimientos (E5) y los `.http` (E7).
- Tocar el listado de libros por editorial, género o autor: son de otros módulos.

## Decisions

### 1. El alta, en un solo bloque `async with`

Se agrega el libro con `stock=0` y sus autorías, se hace `flush()` para que tenga id (`LibroRepository.add`) y se llama a `mover_stock(libro, stock_inicial, "Stock inicial", usuario.id)`. Las tres escrituras van en el mismo bloque: si la base rechaza cualquiera (ISBN repetido, editorial inexistente), el UoW revierte todo y responde 409. No queda un libro sin su movimiento ni un movimiento sin libro.

- **Por qué no `stock=stock_inicial` directo:** rompería la igualdad `stock = suma de movimientos` (RN-11), que es lo que comprueba `ids_con_stock_inconsistente`.
- **`stock_inicial = 0`:** se permite y no deja movimiento. La tabla tiene `CHECK cantidad <> 0`, y un libro sin ejemplares tiene stock 0 = suma vacía, así que la igualdad se cumple igual.

### 2. Sin consultas previas de existencia

Como en el TP, no se pregunta antes si la editorial, el género o los autores existen. Se escribe, y si la base rechaza la clave foránea o el único, `con_mensajes` lo traduce a 409. Evita una consulta por cada id y la carrera entre la consulta y la escritura.

### 3. PATCH con un contrato que sólo tiene título y precio

`LibroUpdate` declara sólo `titulo` y `precio` con `extra="forbid"`: mandar `stock` (o cualquier otro campo) da 422 en la validación, antes de llegar al servicio. Se conserva la validación que rechaza un `null` explícito, porque las dos columnas son obligatorias y la base respondería con un error opaco.

### 4. La baja reusa `soft_delete`

`DELETE` busca el libro **vigente** (`obtener`) y, si existe, llama a `soft_delete`, que escribe `borrado_en` y hace `flush()`. Un libro ya dado de baja da 404, igual que uno que nunca existió: para el catálogo no está. El ISBN queda libre por el índice único parcial (`WHERE borrado_en IS NULL`).

### 5. Listado con `paginar` de B5

El repositorio arma la consulta con los filtros y la precarga (editorial y género con `joinedload`), ordenada por id, y se la pasa a `paginar`, que hace dos consultas: el total con los mismos filtros y la página. `PaginaInexistente` la responde `main.py` con 422.

### 6. Sesión: `get_usuario_actual` ahora, `requiere_rol` después

Alta, PATCH y baja dependen de `get_usuario_actual`, que comparte la sesión de la petición con el Unit of Work (`Depends(get_session)`, regla 14). Cuando entre R2, cada endpoint cambia `Depends(get_usuario_actual)` por la dependencia de rol ADMIN, sin tocar el servicio.

### 7. `sqlite_where` en el índice del ISBN

Los tests corren contra SQLite en memoria (sin PostgreSQL), igual que los de autenticación. SQLite sólo entiende un índice parcial si se declara con `sqlite_where`; con `postgresql_where` solo, lo crearía como único común y la reutilización del ISBN no se podría probar. PostgreSQL ignora la opción de SQLite, así que el esquema real no cambia y no hace falta migración.

## Risks / Trade-offs

- **[Riesgo] Escrituras sin control de rol hasta R2** → cualquier usuario con sesión puede dar de alta, editar o dar de baja. Se mitiga pidiendo sesión (401) desde ya y dejándolo anotado en el PR y en la issue #23.
- **[Trade-off] Tests en SQLite** → no prueban el disparador ni los códigos de error de PostgreSQL. Se complementa con una prueba manual contra PostgreSQL (una base temporal) antes de abrir el PR, y con los `.http` de E7.
