# Arquitectura Propuesta

## Patrones aplicados

| Patrón | Dónde se usa | Por qué (consigna) |
|---|---|---|
| Capas Router → Service → UoW → Repository → Model | Todos los módulos | Cada capa sabe lo suyo y nada más (pág. 1) |
| Repository genérico (`BaseRepository[T]`, `SoftDeleteRepository[T]`) | `app/core/repository.py` | Operaciones comunes; los genéricos se borran en ejecución, así que se pasa la clase del modelo (pág. 12) |
| Unit of Work | `app/core/unit_of_work.py` y uno por módulo | Una transacción por operación de negocio (pág. 12) |
| Borrado lógico + índice único parcial | `libro` | Conservar las ventas viejas y poder recargar el ISBN (pág. 6) |
| Sólo agregado con disparador | `movimiento_stock` | El stock no se corrige: se compensa (págs. 3, 12) |
| Punto único de escritura | Stock (`mover_stock`) | Mantener el invariante stock = suma de movimientos (pág. 12) |
| Dependencias compartidas por petición | `get_session`, usuario actual y roles | Una conexión por petición (pág. 12) |
| Recursos en el lifespan | Motor, fábrica de sesiones y hash ficticio | Se crean con el bucle de eventos ya en marcha (pág. 9) |

## Estructura obligatoria del proyecto (págs. 8-9) y estado del repo

Organización por módulo funcional, con las mismas capas en todos. ✅ coincide · ⚠️ no coincide hoy · ⏳ todavía no existe en `main`.

| Ruta (consigna) | Contenido esperado | En el repo (`main`) |
|---|---|---|
| `main.py` (**raíz**) | Aplicación, lifespan y los dos grupos de rutas | ⚠️ Está en `app/main.py`, con un solo grupo de rutas (los dos grupos son R3) |
| `seed.py` (**raíz**) | Deja la base en el estado inicial conocido | ⚠️ Está en `scripts/seed.py` y es el del TP; deja de andar con la migración 3. El nuevo es R8, "seed.py en la raíz" |
| `app/core/config.py` | `Settings` con pydantic-settings | ✅ |
| `app/core/database.py` | Motor y fábrica (los llama el lifespan) y `get_session` | ✅ |
| `app/core/security.py` | bcrypt fuera del bucle, emisión y verificación del token | ✅ (H2) |
| `app/core/dependencies.py` | Usuario actual, roles vigentes, control del cambio obligatorio, `requiere_rol` | ⏳ R1, R2, R3 |
| `app/core/repository.py` | `BaseRepository[T]` y `SoftDeleteRepository[T]` | ✅ (B3, E2) |
| `app/core/paginacion.py` | Envoltorio de los listados y cálculo de páginas | ✅ (B5). ⚠️ Convive con `app/core/pagination.py` (limit/offset del TP), que todavía usan los routers |
| `app/core/unit_of_work.py` | UoW base: confirma o revierte al salir del bloque | ⏳ B4, PR #77. En `main` sigue `app/core/uow.py` |
| `app/modules/<m>/models.py` | Modelos, restricciones y relaciones | ✅ |
| `app/modules/<m>/schemas.py` | Contratos de entrada y salida | ✅ |
| `app/modules/<m>/repository.py` | Repositorios de cada entidad del módulo | ✅ |
| `app/modules/<m>/unit_of_work.py` | UoW del módulo con sus repositorios | ⏳ Sólo `usuarios` en `main`; los otros seis, en B4 (PR #77) |
| `app/modules/<m>/service.py` | Reglas de negocio; recibe el UoW y lo abre | ⚠️ En `main` todavía llaman a `uow.commit()` (lo corrige B4) |
| `app/modules/<m>/router.py` | Construye el UoW, llama al servicio, traduce errores | ⚠️ En `main` usan `get_uow` (lo corrige B4) |
| `migrations/` | Alembic y sus versiones | ✅ (2 migraciones en `main`; la 3 en PR #76) |
| `test/` | Archivos `.http` y `solo_agregado.sql` | ⚠️ Están los `.http` del TP; faltan `auth.http`, `seguridad.http` y `solo_agregado.sql` |

**Módulos mínimos** (pág. 9): `health` (sólo `router.py`; ⚠️ hoy también tiene `service.py`), `usuarios`, `editoriales`, `generos`, `autores`, `libros`, `clientes` y `ventas`. `AsignacionRol`, `IntentoAcceso` y `EventoSeguridad` viven en `usuarios`; `MovimientoStock` y `LibroAutor`, en `libros`; `PerfilCliente`, en `clientes`; `RenglonVenta`, en `ventas`.

**Extras del repo que la consigna no pide:** `tests/` (tests de `unittest`), `evidencia/` (la pide la entrega), `docs/`, `openspec/`, `knowledge-base/`. El despliegue **no** forma parte de esta estructura: va en otra carpeta, desde el TP 1-4 (pág. 9).

## Seguridad

- **Autenticación:** bcrypt con costo configurable y semáforo; JWT firmado en la cookie `access_token` (`HttpOnly`, `SameSite=Lax`, `Max-Age`, `Secure` configurable). Nunca en el cuerpo ni en `Authorization` (págs. 11, 20).
- **Autorización:** roles vigentes consultados en la base en cada petición (pág. 11).
- **Validación de entrada:** contratos con `extra="forbid"`, 72 bytes como máximo en campos de bcrypt, parámetros ligados en SQL (págs. 10-11, 20).
- **Secretos:** la clave de firma y la contraseña de la base salen del entorno y **no tienen valor por defecto**; si faltan, la app no arranca. Una clave inventada al arrancar no sirve: cambia en cada reinicio y dos procesos no se entienden (pág. 4). `.env` fuera del repo; `env.example` sin secretos.

## Variables de entorno (las de `env.example`)

| Variable | Descripción | Sensible |
|---|---|---|
| `POSTGRES_USER`, `POSTGRES_DB`, `POSTGRES_HOST`, `POSTGRES_PORT` | Arman la URL `postgresql+asyncpg` (pág. 4) | N |
| `POSTGRES_PASSWORD` | Contraseña de la base; obligatoria, sin valor por defecto | **S** |
| `DB_POOL_SIZE`, `DB_MAX_OVERFLOW` | Tamaño del pool (pág. 9) | N |
| `SQL_ECHO` | Muestra las consultas (evidencia C-15) | N |
| `JWT_SECRET` | Clave de firma; obligatoria, de 32 caracteres como mínimo | **S** |
| `JWT_EXPIRA_MINUTOS` | Duración del token y `Max-Age` de la cookie | N |
| `COOKIE_SECURE` | `true` sólo detrás de HTTPS | N |
| `BCRYPT_COSTO`, `BCRYPT_CONCURRENCIA` | Costo del hash y cuántos corren a la vez | N |

El contenedor del **TP 1-4** usa otras variables: `DATABASE_URL` y `SQL_ECHO` (pág. 15). Ver [11](11_entrega_y_despliegue.md).
