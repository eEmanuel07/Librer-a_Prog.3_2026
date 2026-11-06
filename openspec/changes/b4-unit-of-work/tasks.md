# Tasks: b4-unit-of-work

> Rama: `feat/b4-unit-of-work`. Cada grupo es **un commit**. Al cerrar cada uno, la app arranca, `python -m unittest discover -s tests` pasa y el `.http` del módulo da lo mismo que antes.
> Commits sin `Co-Authored-By` ni líneas de Claude. Cada commit se hace solo cuando Belén lo aprueba.
> Tests nuevos con **unittest** (`unittest.IsolatedAsyncioTestCase`, igual que los de Hernán), no con pytest: pytest no está en `requirements.txt`.
> TDD: el comportamiento nuevo (el base y la sesión compartida) se escribe con el test primero. Los módulos son un refactor sin cambio de comportamiento: su red de seguridad son los 12 tests y los `.http`, que se corren antes y después.

## 0. Línea de base (sin commit)

- [x] 0.1 Correr `python -m unittest discover -s tests` y anotar el resultado (se esperan 12 tests OK). Si alguno falla, parar y avisar: sería una falla previa.
  - **Resultado (2026-11-05, `feat/b4-unit-of-work` en `d01f83f`):** `Ran 12 tests in 0.611s — OK`. Solo apareció un aviso de `StarletteDeprecationWarning` (httpx), que no es una falla.
- [x] 0.2 Levantar la app y correr los 7 `.http` de `test/`. Anotar el código de cada petición que hoy da 409, 404 o 422 (es la referencia de "sin cambios").
  - **Resultado (2026-11-05):** en [linea-de-base.md](linea-de-base.md) están las 109 peticiones con su código y mensaje. Se corrieron sobre la copia `libreria_b4` (`createdb -T libreria`), recreada antes de cada archivo, con la app en `POSTGRES_DB=libreria_b4`. Las 109 dieron el código esperado: 200×32, 201×9, 404×14, 405×1, 409×16, 422×37. **Ninguna dio 500**, y el log de uvicorn no tiene errores.

## 1. UnitOfWork base nuevo — commit `feat(core): UnitOfWork base que confirma o revierte al salir del bloque`

- [x] 1.1 RED: crear `tests/test_unit_of_work.py` (unittest, `IsolatedAsyncioTestCase`) con una sesión falsa que registra `commit`, `rollback` y `close`. Escribir los casos y verificar que fallan porque `app.core.unit_of_work` no existe:
  - un bloque sin error confirma una vez y no revierte;
  - un bloque con `NoEncontrado` revierte, no confirma y deja pasar el `NoEncontrado`;
  - un `IntegrityError` dentro del bloque se convierte en `Conflicto` con el mensaje `unique`, `fk` o `check` según el `sqlstate` (23505, 23503, 23514). **El 409 por CHECK se prueba solo acá**: desde la API el schema lo frena antes con 422 (decisión 6 de `design.md`);
  - un `IntegrityError` en el `commit` revierte y se convierte en `Conflicto` con el mensaje pedido;
  - nunca se llama a `close()`;
  - se puede abrir dos veces seguidas y confirma las dos;
  - los mensajes de `con_mensajes(...)` se reinician al salir;
  - `con_mensajes(...)` devuelve el mismo objeto.
- [x] 1.2 GREEN: crear `app/core/unit_of_work.py` (decisiones 1 y 2 de `design.md`), con docstring que explique el uso. Verificar que pasan los tests nuevos y los 12 de antes.
- [x] 1.3 REFACTOR: limpiar nombres o duplicación sin cambiar el comportamiento. Verificar con todos los tests.
  - **Resultado (2026-11-05):** se revisó y quedó sin cambios. La única repetición son las dos líneas `raise conflicto_por_integridad(..., **mensajes) from None` (error en el bloque y error en el commit); extraerlas a un helper agregaba un salto sin ganar claridad. Los mensajes por defecto no se repiten: salen de `conflicto_por_integridad`. **RED:** `ModuleNotFoundError: No module named 'app.core.unit_of_work'`. **GREEN:** `tests.test_unit_of_work` da 12 OK. **Suite completa:** `Ran 24 tests — OK` (los 12 de Hernán más los 12 nuevos). `app/core/uow.py`, los módulos y los routers no se tocaron.

## 2. Editoriales — commit `refactor(editoriales): Unit of Work del módulo`

- [x] 2.1 Crear `app/modules/editoriales/unit_of_work.py` con `EditorialUnitOfWork` (repo `editoriales`) y `get_editoriales_uow`, que lo construye sin abrirlo.
- [x] 2.2 `service.py`: cambiar las 2 llamadas a `uow.commit(...)` por `async with uow.con_mensajes(unique=...)`. Cada función pública abre su bloque y el tipo pasa a `EditorialUnitOfWork`.
- [x] 2.3 `router.py`: usar `Depends(get_editoriales_uow)`. Verificar que `test/editoriales.http` da los mismos códigos y mensajes que en la línea de base, incluido el 409 por nombre repetido (unicidad), y que pasan los tests.
  - **Resultado (2026-11-05):** `python -m unittest discover -s tests` da `Ran 24 tests — OK`. `test/editoriales.http` sobre una copia nueva de `libreria_b4`: 17 peticiones con **0 diferencias** de código o mensaje respecto de [linea-de-base.md](linea-de-base.md) (200×5, 201×2, 404×3, 409×2, 422×5). Los dos 409 dan "Ya existe una editorial con ese nombre" (alta y PATCH). Sin errores en el log de uvicorn. `grep` de `uow.commit` / `app.core.uow` en `app/modules/editoriales/*.py`: vacío.

## 3. Géneros — commit `refactor(generos): Unit of Work del módulo`

- [x] 3.1 Crear `app/modules/generos/unit_of_work.py` (`GeneroUnitOfWork`, `get_generos_uow`).
- [x] 3.2 Pasar `service.py` (1 commit) y `router.py` al patrón nuevo. Verificar `test/generos.http` y los tests.
  - **Resultado (2026-11-05):** `Ran 24 tests — OK`. `test/generos.http` sobre una copia nueva de `libreria_b4`: 10 peticiones con **0 diferencias** respecto de [linea-de-base.md](linea-de-base.md) (200×3, 201×1, 404×1, 409×1, 422×4). El 409 da "Ya existe un género con ese nombre" y el 404 da "El género no existe". Sin errores en el log. `grep` de `uow.commit` / `app.core.uow` en `app/modules/generos/*.py`: vacío.

## 4. Autores — commit `refactor(autores): Unit of Work del módulo`

- [x] 4.1 Crear `app/modules/autores/unit_of_work.py` (`AutorUnitOfWork`, `get_autores_uow`).
- [x] 4.2 Pasar `service.py` (2 commits) y `router.py` al patrón nuevo. Verificar `test/autores.http` y los tests.
  - **Resultado (2026-11-05):** las 2 escrituras usan `async with uow:` **sin `con_mensajes()`**. La tabla `autor` no tiene UNIQUE, FK ni CHECK, y antes ya se llamaba a `uow.commit()` sin mensajes, así que se conservan los mensajes por defecto. `Ran 24 tests — OK`. `test/autores.http` sobre una copia nueva de `libreria_b4`: 13 peticiones con **0 diferencias** respecto de [linea-de-base.md](linea-de-base.md) (200×4, 201×1, 404×3, 422×5). Los 404 dan "El autor no existe". Sin errores en el log. `grep` de `uow.commit` / `app.core.uow` en `app/modules/autores/*.py`: vacío.

## 5. Libros — commit `refactor(libros): Unit of Work del módulo`

- [ ] 5.1 Crear `app/modules/libros/unit_of_work.py` (`LibroUnitOfWork`, `get_libros_uow`).
- [ ] 5.2 `service.py`: reemplazar `_commit(uow)` por `uow.con_mensajes(unique=..., fk=..., check=...)`. En `crear_libro` y `actualizar_libro`, escribir en un bloque y leer (`obtener_libro`) después de cerrarlo. Pasar `router.py` al patrón nuevo.
- [ ] 5.3 Verificar `test/libros.http` y los tests, incluido el 409 por editorial o autor inexistente (clave foránea) y por ISBN repetido.

## 6. Clientes — commit `refactor(clientes): Unit of Work del módulo`

- [ ] 6.1 Crear `app/modules/clientes/unit_of_work.py` (`ClienteUnitOfWork`, `get_clientes_uow`).
- [ ] 6.2 Pasar `service.py` (3 commits; escritura y lectura en bloques separados en `crear_cliente` y `actualizar_cliente`) y `router.py` al patrón nuevo.
- [ ] 6.3 Verificar `test/clientes.http` y los tests: email repetido en alta y en PATCH, perfil repetido y PATCH confirmado (otro GET devuelve el dato nuevo).

## 7. Ventas — commit `refactor(ventas): Unit of Work del módulo con el repo de libros`

- [ ] 7.1 Crear `app/modules/ventas/unit_of_work.py` (`VentaUnitOfWork` con `ventas` y `libros`, `get_ventas_uow`).
- [ ] 7.2 Pasar `service.py` (1 commit; la lectura de precios va dentro del bloque de escritura y `obtener_venta` después de cerrarlo) y `router.py` al patrón nuevo. La tarea en segundo plano sigue recibiendo datos simples.
- [ ] 7.3 Verificar `test/ventas.http` y los tests. Probar el rollback: una venta con cliente inexistente da 409, y la cantidad de ventas (con `GET /ventas` o un `SELECT count(*)` de solo lectura) es la misma antes y después.

## 8. Usuarios — commit `refactor(usuarios): importar el UnitOfWork base de app.core.unit_of_work`

- [ ] 8.1 En `app/modules/usuarios/unit_of_work.py`, cambiar solo el import a `from app.core.unit_of_work import UnitOfWork`. No tocar `registrar_intento_acceso` ni el service de login. Verificar que pasan los 12 tests y que `POST /auth/login` responde igual que antes (200 / 401 / 429).

## 9. Sesión compartida — commit `test(core): una sola sesión por petición entre el Unit of Work y las dependencias`

- [ ] 9.1 RED/GREEN: en `tests/test_unit_of_work.py` (unittest, con `fastapi.testclient.TestClient` como en `tests/test_auth_router.py`), armar una app con una ruta que recibe `get_editoriales_uow` y una dependencia de prueba que pide `get_session` (como lo hará `get_usuario_actual`). Usar una `session_factory` falsa que cuenta sus llamadas. Verificar que `uow.session is session` y que la fábrica se llamó **una sola vez** por petición. Este test tiene que pasar sin tocar código de producción. Si no pasa, parar y revisar.
- [ ] 9.2 Agregar al docstring de `get_session` (`app/core/database.py`) la nota para R1: `get_usuario_actual` (y la verificación de rol) tiene que pedir `Depends(get_session)`, así FastAPI le da la misma sesión que al UoW y la petición usa una sola conexión. **No** escribir código de `get_usuario_actual` (es de Bruno). Verificar que no cambió nada más en el archivo (`git diff app/core/database.py`: solo el docstring).

## 10. Borrar el UoW viejo — commit `refactor(core): borrar uow.py y get_uow`

- [ ] 10.1 Verificar que `grep -rn "app.core.uow\|get_uow\|uow.commit" app tests` da vacío. Borrar `app/core/uow.py`.
- [ ] 10.2 Actualizar los docstrings de ejemplo de `app/core/errors.py` y `app/core/pagination.py` (hoy muestran `uow.commit` y `get_uow`). Verificar que la app arranca y que todos los tests pasan.

## 11. Verificación integral (sin commit)

- [ ] 11.1 Correr los 7 `.http` de `test/` y comparar con la línea de base de 0.2: mismos códigos y mismos mensajes.
- [ ] 11.2 Confirmar un 409 de cada tipo: unicidad (editorial repetida), clave foránea (libro con editorial inexistente) y CHECK (test unitario de la tarea 1.1, porque los schemas lo frenan antes con 422). Ninguno devuelve texto de la base.
- [ ] 11.3 Correr `python -m unittest discover -s tests`: los 12 originales más los nuevos, todos OK.

## Workflow follow-up

- Correr `openspec validate b4-unit-of-work`, abrir el PR de la issue #33 y archivar con `/opsx:archive` cuando esté aprobado.
