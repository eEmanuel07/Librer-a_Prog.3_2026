# Proposal: b2-lifespan-health

> Issue: #31 (B2 — Lifespan, `get_session` y `health`). Consigna: `Parcial_Cap1a6_Consigna.pdf`, Ejercicio 1 (pág. 9), estructura obligatoria (págs. 8-9) y RN-15 (pág. 7).
> Este change se escribe **antes** del código: no se implementa nada hasta que se apruebe el plan.

## Why

La mayor parte del Ejercicio 1 ya está en `main`: el motor, la fábrica de sesiones (`expire_on_commit=False`) y el hash ficticio del login (H4) se crean en el `lifespan` y se guardan en `app.state` (nunca al importar), el motor se cierra con `dispose()` al apagar, `GET /health/live` responde sin tocar la base y `GET /health/ready` ejecuta `SELECT 1` y devuelve 503 con mensaje propio si la base no responde.

Sin embargo, al revisar el código contra la consigna (págs. 8-9) y la issue #31 quedan tres puntos pendientes para dar por cerrada B2:

1. `crear_motor` (`app/core/database.py`) y el `lifespan` (`app/main.py`) no pasan `settings.db_pool_size` ni `settings.db_max_overflow` a `create_async_engine`, a pesar de que `Settings` ya los declara y valida desde B1.
2. La estructura obligatoria (págs. 8-9, IN-04 en `knowledge-base/10_preguntas_abiertas.md`) establece que el módulo `health` sólo tiene `router.py`, pero hoy tiene `router.py` y `service.py`.
3. No hay tests automáticos (`unittest`) que verifiquen la configuración del pool en el motor, el ciclo de vida ni el comportamiento de `/health/live` (200 aún con la base caída) y `/health/ready` (200 con la base disponible y 503 sin texto interno cuando la base falla).

## What Changes

- **Pool configurable en el motor (`app/core/database.py` y `app/main.py`):**
  - `crear_motor` recibe `pool_size: int = 5` y `max_overflow: int = 10` y los pasa a `create_async_engine`.
  - El `lifespan` de `app/main.py` invoca `crear_motor` pasándole `pool_size=settings.db_pool_size` y `max_overflow=settings.db_max_overflow`.
- **Estructura del módulo `health` (`app/modules/health/`):**
  - Se lleva la consulta `await session.execute(text("SELECT 1"))` y las respuestas `{"estado": "vivo"}` / `{"estado": "listo", "base": "ok"}` directamente a `app/modules/health/router.py`.
  - Se actualiza el comentario de la regla de negocio en `router.py` a la numeración del parcial (**RN-15**, en lugar de RN-12 del TP).
  - Se elimina `app/modules/health/service.py` para cumplir la estructura obligatoria de la pág. 8.
- **Pruebas automáticas con `unittest` (`tests/test_lifespan_health.py`):**
  - Verificación de que `crear_motor` aplica `pool_size` y `max_overflow` y que el `lifespan` puebla `app.state` (`settings`, `engine`, `session_factory`, `hash_ficticio`) y llama a `dispose()` al cerrar.
  - Verificación de `GET /health/live` (200 sin usar la base, incluso cuando la base está caída) y `GET /health/ready` (200 cuando `SELECT 1` responde y 503 con mensaje de dominio sin filtrar detalles internos cuando la sesión lanza `SQLAlchemyError` u `OSError`).

## Capabilities

### New Capabilities

- `ciclo-de-vida-y-salud`: inicialización y cierre de recursos compartidos en el `lifespan` de la aplicación (motor con pool configurable, fábrica de sesiones con `expire_on_commit=False`, hash ficticio en `app.state` y cierre con `dispose()`), entrega de sesión por petición (`get_session`) y endpoints de diagnóstico `GET /health/live` y `GET /health/ready`.

### Modified Capabilities

(ninguna)

## Impact

- **Código:**
  - `app/core/database.py` (`crear_motor` recibe y pasa `pool_size` y `max_overflow`);
  - `app/main.py` (el `lifespan` pasa `settings.db_pool_size` y `settings.db_max_overflow` a `crear_motor`);
  - `app/modules/health/router.py` (absorbe las 2 funciones de `service.py` y corrige el comentario a RN-15);
  - `app/modules/health/service.py` (se borra);
  - `tests/test_lifespan_health.py` (nuevo archivo de tests con `unittest`).
- **API:** sin cambios en contratos, rutas, códigos de estado ni cuerpos de respuesta de `/health/live` y `/health/ready`.
- **Compatibilidad interna:** `crear_motor` conserva valores por defecto (`pool_size=5`, `max_overflow=10`), por lo que `scripts/seed.py` sigue funcionando sin cambios hasta que R8 lo reemplace.
