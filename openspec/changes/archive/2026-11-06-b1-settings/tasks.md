# Tasks: b1-settings

> Change retroactivo: todas las tareas se implementaron y verificaron en el PR #63 (commits `46ce27e`, `74efc62`, `8fb241c`, `8514b76`). Además, se volvieron a verificar en memoria el 2026-11-06 sin tocar la base de datos.

## 1. Configuración con `pydantic-settings` y `env.example`

- [x] 1.1 Agregar `pydantic-settings` en `requirements.txt`, definir `Settings` en `app/core/config.py` con las variables `POSTGRES_*`, `DB_POOL_SIZE`, `DB_MAX_OVERFLOW`, `SQL_ECHO`, `JWT_SECRET`, `JWT_EXPIRA_MINUTOS`, `COOKIE_SECURE`, `BCRYPT_COSTO` y `BCRYPT_CONCURRENCIA` (sin valores por defecto en `POSTGRES_PASSWORD` ni `JWT_SECRET`), armar `database_url` con `@computed_field(repr=False)` usando `URL.create` de `sqlalchemy.engine` con `render_as_string(hide_password=False)`, y actualizar `env.example` y `README.md`.
  - **Evidencia:** `requirements.txt` (`46ce27e`), `app/core/config.py` (`74efc62`), `env.example` (`8fb241c`) y `README.md` (`8514b76`) en el PR #63.
- [x] 1.2 Envolver la carga en `get_settings()` para traducir `ValidationError` a un `RuntimeError` que liste únicamente los nombres de las variables faltantes o inválidas sin mostrar valores.
  - **Evidencia (PR #63 y re-verificación 2026-11-06):**
    - Sin `JWT_SECRET`: `RuntimeError: Configuración incompleta o inválida: JWT_SECRET. Copiá env.example como .env y completalo (ver README).` (sin mostrar valores).
    - Con clave corta (`JWT_SECRET="corta"`) y contraseña vacía (`POSTGRES_PASSWORD=""`): `RuntimeError: Configuración incompleta o inválida: POSTGRES_PASSWORD, JWT_SECRET. Copiá env.example como .env y completalo (ver README).` (nombra las dos variables).
- [x] 1.3 Verificar el escapado de caracteres especiales en `database_url` y la conectividad con `.env` completo.
  - **Evidencia (PR #63 y re-verificación 2026-11-06):**
    - Contraseña con `@` y `/` (`a@b/c`): `database_url` sale escapada como `postgresql+asyncpg://postgres:a%40b%2Fc@localhost:5432/libreria` (driver `postgresql+asyncpg`).
    - Con el `.env` completo: `alembic current` devuelve la última migración y `GET /health/ready` devuelve `200 {"estado": "listo", "base": "ok"}`.
