# Design: b1-settings

## Context

Ver `proposal.md` (Why y nota de change retroactivo). Implementado y mergeado en el PR #63 (commits `46ce27e`, `74efc62`, `8fb241c`, `8514b76`).

## Goals / Non-Goals

**Goals:**
- Validar toda la configuración con `pydantic-settings` desde el entorno o `.env`.
- Construir `database_url` con `@computed_field` y `sqlalchemy.engine.URL.create` escapando caracteres especiales.
- Impedir que la app arranque con secretos por defecto o claves débiles, informando sólo los nombres de las variables inválidas.

**Non-Goals:**
- Crear el motor o abrir conexiones al importar `config.py` (eso pertenece al `lifespan`, B2).
- Modificar variables del contenedor del TP 1-4 en la rama `despliegue`.

## Decisions

### 1. Construcción de `database_url` con `URL.create` y `@computed_field(repr=False)`
Se usa `sqlalchemy.engine.URL.create(drivername="postgresql+asyncpg", ...).render_as_string(hide_password=False)` en lugar de interpolar un `f-string`.
- **Por qué:** un `f-string` se rompe si la contraseña contiene `@`, `:` o `/`; `URL.create` los escapa en formato percent-encoding (`%40`, `%2F`). Además, `repr=False` junto con `SecretStr` evita que la contraseña aparezca si alguien imprime o loguea `Settings`.

### 2. Mensaje de error limpio en `get_settings()`
`get_settings()` envuelve `Settings()` en un `try / except ValidationError` y lanza `RuntimeError("Configuración incompleta o inválida: <VARIABLES>...") from None`.
- **Por qué:** el `ValidationError` crudo de Pydantic incluye `input_value` en su texto, lo que podría volcar en consola un secreto mal formado (por ejemplo, un `JWT_SECRET` de 30 caracteres).

## Risks / Trade-offs

- **[Trade-off] `@lru_cache` en `get_settings()`** → cachea la instancia tras la primera lectura; en tests que cambian variables de entorno hay que limpiar la caché (`get_settings.cache_clear()`) o instanciar `Settings` directamente.

## Migration Plan

Ya aplicado en `main` (PR #63): se agregó `pydantic-settings` en `requirements.txt` (`46ce27e`), se reescribió `app/core/config.py` con `Settings` y `get_settings()` (`74efc62`), y se actualizaron `env.example` (`8fb241c`) y `README.md` (`8514b76`) con las variables `POSTGRES_*`, `DB_POOL_*`, `JWT_*`, `COOKIE_SECURE` y `BCRYPT_*`.

## UI Mockups

- Decision: no (no UI) — 2026-11-06. Configuración interna del backend.
