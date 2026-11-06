# Proposal: b1-settings

> Issue: #30 (B1 — Settings con pydantic-settings). PR: #63 (commits `46ce27e`, `74efc62`, `8fb241c`, `8514b76`). Consigna: `Parcial_Cap1a6_Consigna.pdf`, Ejercicio 1 (págs. 4 y 9).

## Nota sobre el orden: change retroactivo

Este change se escribió **después** de la implementación. `Settings` y `env.example` ya estaban implementados, probados y mergeados en `main` (PR #63) antes de que se inicializara OpenSpec en el repositorio (PR #73). No se alteró el orden para aparentar un flujo distinto: OpenSpec todavía no estaba en el proyecto cuando se hizo B1. Este change deja documentado qué se hizo, por qué y con qué evidencia se verificó, sincronizando la spec `configuracion`.

## Why

El proyecto del TP leía una única variable `DATABASE_URL` y no tenía configuración tipada para el pool de conexiones, la firma del JWT ni el costo y la concurrencia de bcrypt. El Ejercicio 1 del parcial exige validar toda la configuración al arrancar con `pydantic-settings`, construir `database_url` mediante un `@computed_field` a partir de las variables `POSTGRES_*` y prohibir valores por defecto para los secretos (`POSTGRES_PASSWORD` y `JWT_SECRET`).

## What Changes

- **`requirements.txt`:** agrega `pydantic-settings`.
- **`app/core/config.py` (`Settings` y `get_settings`):**
  - `Settings(BaseSettings)` con `SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")`.
  - Variables de base de datos `POSTGRES_USER`, `POSTGRES_PASSWORD` (`SecretStr`, `Field(min_length=1)`, obligatoria sin valor por defecto), `POSTGRES_DB`, `POSTGRES_HOST`, `POSTGRES_PORT`, `DB_POOL_SIZE` (default 5, `ge=1`), `DB_MAX_OVERFLOW` (default 10, `ge=0`) y `SQL_ECHO`.
  - Propiedad `@computed_field(repr=False)` `database_url` que usa `URL.create` de `sqlalchemy.engine` (`drivername="postgresql+asyncpg"`) con `.render_as_string(hide_password=False)`, escapando `@`, `:` y `/` en la contraseña y ocultándola en el `repr` de `Settings`.
  - Variables de seguridad y autenticación: `JWT_SECRET` (`SecretStr`, `Field(min_length=32)`, sin valor por defecto), `JWT_EXPIRA_MINUTOS` (default 30, `ge=1`), `COOKIE_SECURE` (default `False`), `BCRYPT_COSTO` (default 12, `ge=4, le=31`) y `BCRYPT_CONCURRENCIA` (default 4, `ge=1`).
  - `get_settings()` cacheada con `@lru_cache` que captura `ValidationError` y lanza `RuntimeError` (`from None`) nombrando únicamente las variables faltantes o inválidas en mayúsculas, sin exponer ningún valor leído.
- **`env.example` y `README.md`:** plantilla con todas las variables documentadas sin secretos reales e instrucciones de configuración actualizadas.

## Capabilities

### New Capabilities

- `configuracion`: carga y validación de variables de entorno al arrancar, obligatoriedad de secretos sin valores por defecto y construcción segura de la URL de conexión a PostgreSQL.

### Modified Capabilities

(ninguna)

## Impact

- **Código:** `requirements.txt`, `app/core/config.py`, `env.example` y `README.md` (ya mergeados en `main` en el PR #63; este change no modifica código).
- **Seguridad:** la aplicación se niega a arrancar si faltan `POSTGRES_PASSWORD` o `JWT_SECRET` o si `JWT_SECRET` tiene menos de 32 caracteres, y nunca muestra los valores leídos en el mensaje de error.
