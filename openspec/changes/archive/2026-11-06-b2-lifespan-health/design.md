# Design: b2-lifespan-health

## Context

Ver `proposal.md` (Why) y `specs/ciclo-de-vida-y-salud/spec.md`. Estado actual observado en el código de `main`:

- `app/core/config.py` (B1): `Settings` ya define `db_pool_size: int = Field(default=5, ge=1)` y `db_max_overflow: int = Field(default=10, ge=0)`.
- `app/core/database.py`:
  - `crear_motor(database_url: str, echo: bool = False) -> AsyncEngine` llama a `create_async_engine(database_url, echo=echo)` sin pasar `pool_size` ni `max_overflow`.
  - `crear_fabrica_sesiones(motor)` ya configura `async_sessionmaker(motor, class_=AsyncSession, expire_on_commit=False)`.
  - `get_session(request)` ya toma `request.app.state.session_factory` y entrega una sesión por petición con `async with fabrica() as session: yield session`.
- `app/main.py`:
  - `lifespan(app)` obtiene `settings = get_settings()`, crea el motor con `crear_motor(settings.database_url, echo=settings.sql_echo)`, guarda `settings`, `engine`, `session_factory` y `hash_ficticio` (H4) en `app.state`, y al salir ejecuta `await motor.dispose()`.
- `app/modules/health/`:
  - Tiene `router.py` y `service.py`. En la tabla de estructura obligatoria de la consigna (págs. 8-9, y en `knowledge-base/10_preguntas_abiertas.md` IN-04), `health` es el único módulo que no tiene capas ni datos propios y consta únicamente de `router.py`.
  - En `router.py`, el comentario dice `# RN-12: mensaje propio, nunca el texto de la base.` (numeración vieja del TP; en el parcial es **RN-15**).

## Goals / Non-Goals

**Goals:**
- Conectar `settings.db_pool_size` y `settings.db_max_overflow` con `crear_motor` y el `lifespan`.
- Dejar `app/modules/health/` únicamente con `router.py` (y `__init__.py`), eliminando `service.py` sin alterar las rutas ni las respuestas de `/health/live` y `/health/ready`.
- Cubrir con `unittest` el pool del motor, el ciclo de vida y los casos de `/health/live` y `/health/ready` con la base arriba y con la base caída.

**Non-Goals:**
- Modificar `Settings` (`app/core/config.py`, ya cerrado en B1) o el cálculo del hash ficticio (`app/core/security.py`, cerrado en H2/H4).
- Mover `app/main.py` a la raíz (eso se hace al cierre según la decisión DD-08).
- Cambiar el formato de respuesta de `/health/live` o `/health/ready` (ya coinciden con `test/health.http`).

## Decisions

### 1. Firma de `crear_motor` con valores por defecto compatibles

```python
def crear_motor(
    database_url: str,
    echo: bool = False,
    pool_size: int = 5,
    max_overflow: int = 10,
) -> AsyncEngine:
    return create_async_engine(
        database_url,
        echo=echo,
        pool_size=pool_size,
        max_overflow=max_overflow,
    )
```

Y en `app/main.py`:

```python
motor = crear_motor(
    settings.database_url,
    echo=settings.sql_echo,
    pool_size=settings.db_pool_size,
    max_overflow=settings.db_max_overflow,
)
```

- **Por qué parámetros explícitos con default en vez de recibir `Settings`:** `crear_motor` se mantiene desacoplado de `Settings` (recibe tipos simples) y conserva compatibilidad hacia atrás con `scripts/seed.py`, que hoy llama a `crear_motor(ajustes.database_url, echo=ajustes.sql_echo)` sin pasar el pool.
- **Alternativa descartada:** pasar el objeto `Settings` entero a `crear_motor(settings)`. Acopla `database.py` a `config.py` y obligaría a tocar `scripts/seed.py` o los tests que construyan un motor directo.

### 2. Unificar `health` en `app/modules/health/router.py` y borrar `service.py`

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.database import get_session

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/live")
async def live() -> dict[str, str]:
    # No toca la base.
    return {"estado": "vivo"}


@router.get("/ready")
async def ready(session: AsyncSession = Depends(get_session)) -> dict[str, str]:
    try:
        await session.execute(text("SELECT 1"))
        return {"estado": "listo", "base": "ok"}
    except (SQLAlchemyError, OSError):
        # RN-15: mensaje propio, nunca el texto de la base.
        raise HTTPException(
            status_code=503,
            detail="La base de datos no está disponible",
        ) from None
```

- **Por qué:** cumple literalmente la estructura obligatoria de la pág. 8 (`health` sólo tiene `router.py`, resuelve IN-04), actualiza el comentario a **RN-15** (IN-03) y agrega `from None` para no encadenar internamente la excepción de la base.
- **Alternativa descartada:** conservar `service.py`. Contradice la pág. 9 de la consigna ("el módulo `health` sólo tiene `router.py`").

### 3. Estrategia de tests con `unittest` (`tests/test_lifespan_health.py`)

Siguiendo la regla 10 de `AGENTS.md`, todas las pruebas usan `unittest` (`IsolatedAsyncioTestCase` y `fastapi.testclient.TestClient`):

1. **Configuración del pool y fábrica (`crear_motor` y `crear_fabrica_sesiones`):**
   - Verificar que `crear_motor` pasa `pool_size` y `max_overflow` a `create_async_engine` (inspeccionando `motor.pool.size()` y `motor.pool._max_overflow` o mediante `unittest.mock.patch` sobre `create_async_engine`) y que `crear_fabrica_sesiones` configura `expire_on_commit=False`.
2. **Ciclo de vida (`lifespan`):**
   - Verificar que al entrar al `lifespan(app)` se guardan `settings`, `engine`, `session_factory` y `hash_ficticio` en `app.state`, que `crear_motor` recibe `settings.db_pool_size` y `settings.db_max_overflow`, y que al salir del contexto se llama a `await motor.dispose()`.
3. **Endpoints `/health/live` y `/health/ready` con base disponible y con base caída:**
   - Con una sesión cuya ejecución de `SELECT 1` responde bien: `/health/live` da 200 `{"estado": "vivo"}` y `/health/ready` da 200 `{"estado": "listo", "base": "ok"}`.
   - Simulando la base caída (una dependencia `get_session` cuya sesión lanza `OperationalError` / `SQLAlchemyError` u `OSError` al ejecutar `SELECT 1`, con detalles internos sensibles en el mensaje de la excepción original):
     - `GET /health/ready` responde **503** con `{"detail": "La base de datos no está disponible"}` y no filtra el texto de la excepción interna (RN-15);
     - `GET /health/live` sigue respondiendo **200** con `{"estado": "vivo"}` y ni siquiera invoca `get_session`.
   - Verificar además que `app/modules/health/service.py` no existe.

## Risks / Trade-offs

- **[Riesgo] Algún módulo o test importa `app.modules.health.service`** → **Mitigación:** se verificó con `git grep "health"` que sólo `app/modules/health/router.py` lo importaba.
- **[Riesgo] `create_async_engine` con `sqlite://` en memoria no acepta `pool_size` con `StaticPool`** → **Mitigación:** en producción se usa `postgresql+asyncpg://` (que usa `AsyncAdaptedQueuePool` y acepta `pool_size` y `max_overflow`). En los tests unitarios de `crear_motor` se prueba con una URL `postgresql+asyncpg://...` (que no abre red al construir el motor, justamente porque el motor no conecta al crearse) o verificando los argumentos pasados a `create_async_engine`.

## Migration Plan

1. Commit 1: configurar `pool_size` y `max_overflow` en `crear_motor` y en el `lifespan`, con sus tests en `tests/test_lifespan_health.py`.
2. Commit 2: llevar la lógica de `health` a `router.py`, borrar `app/modules/health/service.py` y sumar los tests de `/health/live` y `/health/ready` (con la base arriba y con la base caída).
3. Verificación manual contra la app y el contenedor `libreria-db` (`test/health.http` con la base arriba; y para probar con la base caída, sin apagar `libreria-db`, levantar la app apuntando a un puerto donde no hay nada escuchando, por ejemplo `POSTGRES_PORT=5999`, para que la conexión se rechace igual que con la base caída mientras el contenedor sigue prendido).

## UI Mockups

- Decision: no (no UI) — 2026-11-06. Es un cambio de infraestructura y endpoints de diagnóstico sin interfaz gráfica.
