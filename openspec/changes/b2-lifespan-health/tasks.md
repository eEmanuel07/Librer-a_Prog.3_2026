# Tasks: b2-lifespan-health

> Rama: `feat/b2-lifespan-health`. Cada grupo numerado (1 y 2) es **un commit**. Al cerrar cada uno, la app arranca y `python -m unittest discover -s tests` pasa.
> Commits en español, sin `Co-Authored-By` ni atribución de IA. Cada commit lo ejecuta Belén cuando aprueba el paso.
> Tests nuevos con **`unittest`** (`IsolatedAsyncioTestCase` y `fastapi.testclient.TestClient`, regla 10 de `AGENTS.md`).
> TDD: cada grupo empieza escribiendo el test que falla (RED), implementa lo mínimo para pasar (GREEN) y revisa si hace falta limpiar (REFACTOR).

## 0. Línea de base (sin commit)

- [ ] 0.1 Correr `python -m unittest discover -s tests` y anotar el resultado (se esperan los 27 tests actuales en OK). Si alguno falla, parar y avisar.

## 1. Pool configurable en `crear_motor` y en el `lifespan` — commit `feat(core): configurar pool_size y max_overflow en el motor del lifespan`

- [ ] 1.1 RED: crear `tests/test_lifespan_health.py` (`unittest.IsolatedAsyncioTestCase`) con las pruebas del motor, la fábrica y el `lifespan`, y verificar que fallan porque `crear_motor` todavía no acepta `pool_size` ni `max_overflow` ni el `lifespan` se los pasa:
  - `crear_motor` recibe `pool_size` y `max_overflow` (con valores por defecto `5` y `10`) y los pasa a `create_async_engine` (verificando también el tamaño del pool en el motor creado);
  - `crear_fabrica_sesiones` configura `expire_on_commit=False`;
  - el `lifespan` de `app/main.py` guarda `settings`, `engine`, `session_factory` y `hash_ficticio` en `app.state`, llama a `crear_motor` con `pool_size=settings.db_pool_size` y `max_overflow=settings.db_max_overflow`, y al cerrarse ejecuta `await motor.dispose()`.
- [ ] 1.2 GREEN: actualizar `crear_motor` en `app/core/database.py` para recibir `pool_size: int = 5` y `max_overflow: int = 10` y pasarlos a `create_async_engine`, y actualizar `lifespan` en `app/main.py` para pasar `pool_size=settings.db_pool_size` y `max_overflow=settings.db_max_overflow`. Correr `python -m unittest discover -s tests` y verificar que pasan todos los tests.
- [ ] 1.3 REFACTOR: revisar tipos y docstrings de `app/core/database.py` y `app/main.py` sin cambiar comportamiento y volver a correr `python -m unittest discover -s tests`.

## 2. Módulo `health` sólo con `router.py` y pruebas de `/health/live` y `/health/ready` — commit `refactor(health): mover lógica al router, borrar service.py y probar health`

- [ ] 2.1 RED: agregar en `tests/test_lifespan_health.py` la clase de pruebas de `health` y verificar que el control de estructura falla mientras exista `app/modules/health/service.py`:
  - con la base disponible (`SELECT 1` responde sin error): `GET /health/live` devuelve `200` `{"estado": "vivo"}` y `GET /health/ready` devuelve `200` `{"estado": "listo", "base": "ok"}`;
  - con la base caída (la sesión lanza `OperationalError` / `SQLAlchemyError` y `OSError` al ejecutar `SELECT 1`, incluyendo texto interno sensible en la excepción): `GET /health/ready` devuelve `503` con `{"detail": "La base de datos no está disponible"}` sin filtrar texto de la base (RN-15), mientras que `GET /health/live` sigue devolviendo `200` `{"estado": "vivo"}` sin abrir sesión;
  - verificar que `app/modules/health/service.py` no existe (estructura obligatoria, pág. 8).
- [ ] 2.2 GREEN: llevar `{"estado": "vivo"}` y `await session.execute(text("SELECT 1"))` directamente a `app/modules/health/router.py`, actualizar el comentario a `RN-15` (IN-03) y eliminar `app/modules/health/service.py`. Correr `python -m unittest discover -s tests` y verificar que pasan todos los tests.
- [ ] 2.3 REFACTOR: verificar con `git grep "health"` que no quede ningún import ni referencia a `app.modules.health.service` y volver a correr la suite de `unittest`.

## 3. Verificación integral (sin commit)

- [ ] 3.1 Probar con la aplicación real y el contenedor `libreria-db`:
  - con `libreria-db` arriba: `GET /health/live` → `200 {"estado": "vivo"}` y `GET /health/ready` → `200 {"estado": "listo", "base": "ok"}` (`test/health.http`);
  - con `libreria-db` detenido (o apuntando a un puerto sin base): `GET /health/ready` → `503 {"detail": "La base de datos no está disponible"}` y `GET /health/live` → `200 {"estado": "vivo"}` ("hecho cuando" de la issue #31).
- [ ] 3.2 Correr `python -m unittest discover -s tests` y `openspec validate b2-lifespan-health --strict`, dejando asentada la evidencia en este `tasks.md`.

## Workflow follow-up

- Archivar el change con `openspec archive b2-lifespan-health` antes de abrir el PR para que el PR a `main` (`Closes #31`) ya incluya la spec `ciclo-de-vida-y-salud` sincronizada en `openspec/specs/` y el checkbox de B2 actualizado en `CHANGES.md` (y `IN-04` marcada como resuelta en `knowledge-base/10_preguntas_abiertas.md`).
