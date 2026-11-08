# Design: b7-readme

## Context

Ver `proposal.md` (Why) y `specs/documentacion-entrega/spec.md`. Estado observado en `main`:

- **`README.md` actual:** quedó del Trabajo Práctico de los capítulos 1 a 4. Aunque B1 actualizó la sección de `Settings` y `env.example`, el resto del archivo tiene información obsoleta o incompleta:
  - Título `"Librería — TP Programación III"` e integrantes sólo con nombre de pila (`Belén, Bruno, Elías, Hernán y Joaquín`).
  - En la nota para Windows todavía menciona `DATABASE_URL`.
  - En "Datos iniciales" y "Cómo probar" indica `python -m scripts.seed` (cuando R8 ya movió el script a `seed.py` en la raíz y borró `scripts/`).
  - No lista los 5 usuarios iniciales que carga `seed.py` ni explica cómo probar las rutas autenticadas.
  - No explica cómo correr la suite de `unittest` (`python -m unittest discover -s tests`) ni cómo correr `test/solo_agregado.sql` con `psql`, ni qué casos `C-01..C-16` cubre cada archivo de `test/`.
  - En "Estructura" y "Arquitectura en capas" sigue nombrando `app/core/uow.py` (borrado en B4), `app/core/pagination.py` con `limit`/`offset`, `scripts/seed.py` y `await uow.commit(...)` manual, omitiendo `app/core/unit_of_work.py` (`async with`), `app/core/repository.py` (`BaseRepository[T]` y `SoftDeleteRepository[T]`), `app/core/paginacion.py` (envoltorio `Pagina[T]`), `app/core/security.py`, `app/core/dependencies.py`, `app/modules/usuarios/` y `unit_of_work.py` en cada módulo.
  - En "Módulos y endpoints" faltan todas las rutas de `/auth`, `/usuarios`, `/eventos`, la baja lógica (`DELETE /libros/{id}`), la reposición (`POST /libros/{id}/reponer`), los movimientos (`GET /libros/{id}/movimientos`), `/mis-ventas` y la separación entre grupo abierto y grupo protegido (`app/main.py`).
  - En `evidencia/` sólo menciona C-07 del TP, cuando ya están `evidencia/C-14_solo_agregado.txt` y `evidencia/C-14_psql.png` (y se sumará C-15 con J8).
- **Decisión sobre `main.py` (viernes 6/11):** en la clase de consulta del viernes 6/11 el profesor confirmó que `main.py` puede quedar en `app/main.py` (con arranque `uvicorn app.main:app --reload`). Por lo tanto, se descarta moverlo a la raíz antes de E10 y hay que actualizar `DD-08` (`knowledge-base/09_decisiones_y_supuestos.md`), `IN-01` (`knowledge-base/10_preguntas_abiertas.md`), `AGENTS.md` y `CHANGES.md`.
- **Seguimiento en `CHANGES.md`:** B2 ya fue mergeado en `main` (PR #81) y los 3 changes retroactivos (`b1-settings`, `b3-base-repository`, `b5-paginacion`) ya fueron mergeados en `main` (PR #82), pero la tabla y el estado de B2 en `CHANGES.md` habían quedado desactualizados tras merges posteriores.

## Goals / Non-Goals

**Goals:**
- Dejar `README.md` 100 % fiel al código real de `main` y a lo que exige la página 24 de `Parcial_Cap1a6_Consigna.pdf` para la carpeta `parcial/`.
- Registrar en `DD-08`, `IN-01`, `AGENTS.md` y `CHANGES.md` la confirmación del profesor (6/11) de que `app/main.py` se mantiene en su lugar.
- Dejar `CHANGES.md` al día con `B2` (`[x]` mergeado, PR #81) y con las filas de `b1-settings`, `b2-lifespan-health`, `b3-base-repository` y `b5-paginacion` (PR #81 y PR #82).

**Non-Goals:**
- Tocar código de aplicación (`app/`, `seed.py`, `migrations/`, `tests/`).
- Documentar el despliegue del TP en el VPS dentro de `README.md` como si fuera parte de `parcial/` (eso va en `despliegue/DEPLOY.md` en la tarea E9; en `README.md` sólo se aclara que el contenedor local es para PostgreSQL 16).
- Incluir en `README.md` el contenido de `.env` o contraseñas de usuarios que la consigna indica que viven sólo en `seed.py` (pág. 19).

## Decisions

### 1. Estructura y contenido de `README.md`

Se organiza `README.md` en secciones claras que siguen el orden exacto que pide la consigna (pág. 24) y reflejan el código actual de `main`:

1. **Encabezado e integrantes:**
   - Título: `# Librería — Parcial Programación III (Capítulos 1 a 6)`.
   - Resumen: API REST asincrónica en capas (`Router → Service → UoW → Repository → Model`) con autenticación por cookie `HttpOnly` (bcrypt + JWT), autorización RBAC con vigencia en la base, transacciones con Unit of Work, movimientos de stock de sólo agregado y borrado lógico.
   - **Integrantes:** Belén Calvo, Elías Tello, Hernán González, Bruno Fiouchetta, Joaquín Moran.
2. **Requisitos:**
   - Python 3.12 o superior, FastAPI 0.111+, SQLModel 0.0.24+, SQLAlchemy 2.0 asincrónico (`<2.1`), asyncpg 0.30+, Alembic 1.13+, pydantic-settings 2.0+, bcrypt 4.0+, PyJWT 2.8+.
   - Docker 20.10+ (para correr PostgreSQL 16 en el contenedor local `libreria-db`).
3. **Pasos para levantar el proyecto desde cero:**
   - **Paso 1 — Clonar y crear el entorno virtual (`.venv`):** comandos para Git Bash (`source .venv/Scripts/activate`), PowerShell (`.venv\Scripts\Activate.ps1`), CMD (`.venv\Scripts\activate.bat`) y Linux/macOS (`source .venv/bin/activate`), seguido de `pip install -r requirements.txt`.
   - **Paso 2 — Configurar el archivo `.env`:** copiar `env.example` a `.env` (`cp env.example .env`). Explicar todas las variables que lee `Settings` (`app/core/config.py`):
     - `POSTGRES_USER`, `POSTGRES_PASSWORD` (**obligatoria**, sin valor por defecto), `POSTGRES_DB`, `POSTGRES_HOST`, `POSTGRES_PORT` (con las que `@computed_field` arma `database_url` usando el driver `postgresql+asyncpg`).
     - `JWT_SECRET` (**obligatoria**, mínimo 32 caracteres, sin valor por defecto) y cómo generarla con `python -c "import secrets; print(secrets.token_urlsafe(32))"`.
     - `DB_POOL_SIZE` (default 5), `DB_MAX_OVERFLOW` (default 10), `SQL_ECHO` (default `false`; `true` para ver las consultas SQL en consola en C-15), `JWT_EXPIRA_MINUTOS` (default 30), `COOKIE_SECURE` (default `false` en HTTP local), `BCRYPT_COSTO` (default 12) y `BCRYPT_CONCURRENCIA` (default 4).
     - Aclarar que si falta `POSTGRES_PASSWORD` o `JWT_SECRET` (o si `JWT_SECRET` tiene menos de 32 caracteres), la aplicación no arranca e informa qué variable falta sin exponer valores. Nunca incluir el contenido de un `.env` ni mencionar `DATABASE_URL`.
   - **Paso 3 — Levantar la base de datos PostgreSQL 16 en Docker:** comando `docker run --name libreria-db -e POSTGRES_USER=postgres -e POSTGRES_PASSWORD=<tu_contraseña> -e POSTGRES_DB=libreria -p 5432:5432 -d postgres:16` (y `docker start libreria-db` para las veces siguientes, con la nota de `-p 5433:5432` si el puerto 5432 local ya está en uso).
   - **Paso 4 — Aplicar las migraciones con Alembic:** `alembic upgrade head` (aplica las 4 migraciones: las 2 del TP, la 3 `4a775b04f730` con tablas de acceso, `movimiento_stock`, `cliente.usuario_id`, `libro.borrado_en` e índices únicos parciales, y la 4 `314ce2736bff` escrita a mano con el disparador `trg_movimiento_stock_solo_agregado` de RN-12).
   - **Paso 5 — Cargar los datos iniciales (`seed.py`):**
     - Comando desde la raíz: `python seed.py`.
     - Explicar qué hace: vacía todas las tablas con `TRUNCATE TABLE ... RESTART IDENTITY CASCADE` (reiniciando secuencias a 1, por lo que es idempotente) y carga los datos de las págs. 19-20:
       - **5 usuarios iniciales:**
         | ID | Email | Nombre | Rol vigente | Cambio de contraseña obligatorio |
         |---|---|---|---|---|
         | 1 | `admin@example.com` | Administrador Principal | `ADMIN` | No (`false`) |
         | 2 | `admin2@example.com` | Administrador Secundario | `ADMIN` | No (`false`) |
         | 3 | `vendedor@example.com` | Vendedor Mostrador | `VENDEDOR` | No (`false`) |
         | 4 | `ana@example.com` | Ana Paz | `CLIENTE` (vinculada a cliente 3) | No (`false`) |
         | 5 | `nuevo@example.com` | Vendedor Nuevo | `VENDEDOR` | Sí (`true`) |
       - Aclarar que las contraseñas de prueba son ficticias y están definidas únicamente en `seed.py` (`CONTRASENAS_PRUEBA`) y en los encabezados de `test/seguridad.http`, tal como pide la consigna (pág. 19: *"Las contraseñas son de mentira y viven sólo en ese archivo"*).
       - **Catálogo:** 3 editoriales, 3 géneros, 6 autores y 5 libros con sus movimientos `"Stock inicial"` (`Rayuela` 11, `Ficciones` 10, `Bestiario` 1, `Respiración artificial` 3, `Antología de la literatura fantástica` 5).
       - **Clientes:** Lucía Fernández (con perfil, sin usuario), Tomás Ríos (sin usuario) y Ana Paz (vinculada a `ana@example.com`).
       - **Venta 1:** de Lucía Fernández, registrada por `vendedor@example.com` (1 `Rayuela` y 2 `Ficciones`, total `$69000.00`), con sus dos movimientos de salida (`-1` y `-2`), dejando el stock final en `10, 8, 1, 3, 5` igual a la suma de movimientos de cada libro (RN-11).
       - **Historial de seguridad:** 1 fila inicial con `actor="SISTEMA"` y `accion="Carga de los datos iniciales"` (RN-16).
   - **Paso 6 — Arrancar el servidor:**
     - Comando: `uvicorn app.main:app --reload`.
     - URLs: `http://localhost:8000/docs`, `http://localhost:8000/health/live`, `http://localhost:8000/health/ready`.
4. **Cómo correr las pruebas:**
   - **Tests automáticos (`unittest`):** `python -m unittest discover -s tests` (con la biblioteca estándar `unittest` y `IsolatedAsyncioTestCase` / `TestClient`, sin necesitar pytest).
   - **Casos de prueba en `test/` (`.http` y `.sql`):** explicar cómo usarlos con la extensión **REST Client** de VS Code (ejecutando `python seed.py` antes de cada archivo, y notando el uso de `# @name` y `# @no-cookie-jar` para múltiples sesiones simultáneas) y cómo correr `test/solo_agregado.sql` con `psql`:
     ```bash
     psql -X -e -v ON_ERROR_STOP=0 -h localhost -U postgres -d libreria -f test/solo_agregado.sql
     ```
     Incluir tabla con cada archivo de `test/` y qué casos demuestra:
     - `test/auth.http`: **C-01 a C-05** (validación de contratos 422 y límite de 72 bytes en bcrypt, auto-registro atómico RN-02 y 409 por email repetido o ficha de cliente existente sin apropiación, login con cookie `HttpOnly` sin token en el cuerpo, anti-enumeración con hash ficticio RN-08, rate limit 429 con `Retry-After` al 6.º intento RN-07, más `/auth/yo`, `/auth/cambiar-password` y `/auth/logout`).
     - `test/seguridad.http`: **C-06 a C-09** (401 sin sesión vs. 403 por rol insuficiente y acceso a lo propio en `/mis-ventas` y `/ventas/{id}` RN-14; revocación de rol en caliente con sesión abierta RN-04 y contraste en `/auth/yo`, vencimientos inválidos 422; autoprotección de ADMIN 409 RN-05 y unicidad de rol abierto 409 RN-03; bloqueo 403 por cambio obligatorio de contraseña RN-06 salvo `/auth`, desbloqueo con la misma cookie tras cambiarla y auditoría en `GET /eventos` RN-16).
     - `test/ventas.http`: casos de ventas (alta con cálculo de total y copia de precios RN-09, detalle sin N+1, validaciones 409 y 422, inmutabilidad 405; y **C-10 a C-12** con descuento de stock y movimientos en un solo UoW RN-10).
     - `test/libros.http`: catálogo de libros, validaciones de alta/PATCH, búsqueda con parámetros ligados e intento de inyección SQL, paginación y casos **C-13 y C-16** (reposición, baja lógica 204, reutilización de ISBN dado de baja RN-13, paginación con filtro y rechazo de `stock` en PATCH RN-11).
     - `test/solo_agregado.sql`: **C-14** (`UPDATE` y `DELETE` sobre `movimiento_stock` en `psql` rechazados por el disparador `trg_movimiento_stock_solo_agregado` de RN-12, dentro de una transacción con `SAVEPOINT` y `ROLLBACK`).
     - `test/editoriales.http`, `test/generos.http`, `test/autores.http`, `test/clientes.http`, `test/health.http`: pruebas por módulo de catálogo, clientes con perfil y endpoints `/health/live` y `/health/ready`.
5. **Estructura del proyecto y arquitectura en capas:**
   - Árbol real de archivos (`app/main.py`, `seed.py`, `app/core/config.py`, `app/core/database.py`, `app/core/security.py`, `app/core/dependencies.py`, `app/core/repository.py`, `app/core/paginacion.py`, `app/core/unit_of_work.py`, `app/core/errors.py`, `app/modules/<módulo>/` con `models.py`, `schemas.py`, `repository.py`, `unit_of_work.py`, `service.py`, `router.py`, `app/modules/health/router.py`, `migrations/`, `test/`, `tests/`, `evidencia/`).
   - Tabla de responsabilidades de cada capa (`Router → Service → UoW → Repository → Model`) explicando que el router construye el UoW con `Depends(get_<módulo>_uow)`, el servicio lo abre con `async with uow:` (y configura `uow.con_mensajes(...)`), los repositorios heredan de `BaseRepository[T]` / `SoftDeleteRepository[T]` y sólo hacen `flush()`, y las dependencias de autenticación/autorización comparten la misma sesión de la petición (`Depends(get_session)`), con la única excepción de `registrar_intento_acceso` (DD-04).
   - Tabla de endpoints dividida en **Grupo abierto** y **Grupo protegido** (tal como están montados en `app/main.py`).
6. **Carpeta `evidencia/` y notas para Windows:**
   - Explicar los archivos en `evidencia/` (`C-14_solo_agregado.txt` y `C-14_psql.png` para el caso C-14 del disparador en `psql`, las capturas/salidas de consultas fijas sin N+1 para C-15 / C-07 y `integracion.txt`).
   - Conservar la nota para Windows sobre `sqlalchemy[asyncio]>=2.0,<2.1` y sobre variables de entorno del sistema que puedan pisar `POSTGRES_*` del `.env` (sin mencionar `DATABASE_URL`).

### 2. Actualización de DD-08 e IN-01 (`app/main.py` queda en `app/`)

- **Por qué:** En la clase de consulta del viernes 6/11 el profesor confirmó que `main.py` puede permanecer en `app/main.py` (arranque `uvicorn app.main:app --reload`). Mantenerlo ahí evita romper todos los imports de `tests/`, `README.md` y ramas en curso antes del cierre.
- **Dónde impacta:**
  1. `knowledge-base/09_decisiones_y_supuestos.md` (DD-08): cambiar el título a `### DD-08 — main.py se mantiene en app/main.py y seed.py va en la raíz`, explicar que el profesor confirmó en la clase de consulta del viernes 6/11 que `app/main.py` queda donde está (con arranque `uvicorn app.main:app --reload`) mientras que `seed.py` vive en la raíz (`python seed.py`, R8), y eliminar el checklist de 5 pasos del movimiento final.
  2. `knowledge-base/10_preguntas_abiertas.md` (IN-01 y tabla de Preguntas abiertas): actualizar la resolución de IN-01 indicando que `seed.py` ya está en la raíz (R8, PR #100) y que `app/main.py` queda en `app/main.py` por confirmación del profesor en la consulta del viernes 6/11 (DD-08); además, quitar de la tabla de preguntas abiertas la fila sobre quién ejecuta el movimiento final de `app/main.py` (y marcar IN-04 e IN-06 como resueltas si corresponde, o mantener el foco en IN-01 y la fila de la tabla).
  3. `AGENTS.md` (línea 40): reemplazar `> main.py se mantiene en app/main.py hasta el cierre; al final se mueve a la raíz (ver decisión DD-08 en 09).` por `> main.py queda en app/main.py (confirmado por el profesor en la consulta del 6/11; ver decisión DD-08 en 09).`
  4. `CHANGES.md`: en `[B7]` cambiar `uvicorn main:app` por `uvicorn app.main:app --reload` y eliminar el bloque `> **Paso previo a E10 — Mover app/main.py a main.py en la raíz (DD-08):** ...`.

### 3. Actualización de `CHANGES.md` (B2 y changes retroactivos B1, B3, B5)

- En la tabla `### Changes de OpenSpec ya creados`:
  - Agregar las filas de `b1-settings` (B1, Belén, código en [#63](https://github.com/eEmanuel07/Librer-a_Prog.3_2026/pull/63) / change en [#82](https://github.com/eEmanuel07/Librer-a_Prog.3_2026/pull/82), `Mergeado y archivado (change retroactivo)`, `openspec/specs/configuracion`), `b3-base-repository` (B3, Belén, [#65](https://github.com/eEmanuel07/Librer-a_Prog.3_2026/pull/65) / [#82](https://github.com/eEmanuel07/Librer-a_Prog.3_2026/pull/82), `Mergeado y archivado (change retroactivo)`, `openspec/specs/repositorios`) y `b5-paginacion` (B5, Belén, [#66](https://github.com/eEmanuel07/Librer-a_Prog.3_2026/pull/66) / [#82](https://github.com/eEmanuel07/Librer-a_Prog.3_2026/pull/82), `Mergeado y archivado (change retroactivo)`, `openspec/specs/paginacion`).
  - Actualizar la fila de `b2-lifespan-health`: PR [#81](https://github.com/eEmanuel07/Librer-a_Prog.3_2026/pull/81) y estado `Mergeado y archivado`.
- En el árbol de dependencias (línea 56): `B2 Lifespan y health [x]`.
- En `### [B2] b2-lifespan-health · #31`: `- **Estado**: [x] mergeado (PR #81)`.
- En la tabla `## Resumen`: Fase 0 pasa de `8 [x] / 1 [~] / 0 [ ]` a `9 [x] / 0 [~] / 0 [ ]` (ajustando el total de `[x]` y `[~]`).

## Risks / Trade-offs

- **[Riesgo] Diferencias entre lo que tienen `test/libros.http`, `test/ventas.http` y `test/clientes.http` hoy en `main` y lo que sumarán J7, J8 y la segunda parte de E7** → **Mitigación:** describir cada archivo de `test/` de modo que refleje tanto las pruebas ya presentes en `main` como los casos C asignados por la consigna (C-01 a C-16), e indicar siempre ejecutar `python seed.py` antes de correr cada archivo.
- **[Riesgo] Exponer contraseñas en `README.md` que la consigna pide dejar sólo en `seed.py`** → **Mitigación:** en la tabla de usuarios iniciales de `README.md` se listan los correos, nombres, roles y `debe_cambiar_password`, y se indica explícitamente que las contraseñas de prueba están en el diccionario `CONTRASENAS_PRUEBA` de `seed.py` (y ya configuradas en los `.http`).

## Migration Plan

1. En `/opsx:apply`, actualizar primero `README.md` verificando cada comando, ruta y archivo contra el repositorio real.
2. Actualizar `knowledge-base/09_decisiones_y_supuestos.md` (DD-08), `knowledge-base/10_preguntas_abiertas.md` (IN-01), `AGENTS.md` y `CHANGES.md` (DD-08, B2 en PR #81, retroactivos B1/B3/B5 en PR #82).
3. Verificar que `python -m unittest discover -s tests` sigue pasando y que `openspec validate b7-readme --strict` da válido.

## UI Mockups

- Decision: no (no UI) — 2026-11-07. Es un change de documentación (`README.md`, `knowledge-base/`, `AGENTS.md` y `CHANGES.md`) en una API sin pantallas.
