# Proposal: b7-readme

> Issue: #36 (B7 — README del parcial). Consigna: `Parcial_Cap1a6_Consigna.pdf`, Formato de entrega (pág. 24), Estructura obligatoria (págs. 8-9), Datos iniciales (págs. 19-20) y Casos de prueba mínimos (págs. 21-23).
> Este change se escribe **antes** de tocar `README.md`, `knowledge-base/`, `AGENTS.md` o `CHANGES.md`.

## Why

El `README.md` actual del repositorio sigue describiendo el Trabajo Práctico de los capítulos 1 a 4: menciona nombres de pila sin apellidos, `python -m scripts.seed`, `app/core/uow.py`, `app/core/pagination.py` con `limit`/`offset`, un listado incompleto de módulos y endpoints sin autenticación ni autorización, y sólo la evidencia del caso C-07 del TP. La consigna del parcial (pág. 24) exige que `parcial/README.md` incluya los nombres y apellidos de los integrantes y los pasos completos para levantar el proyecto desde cero contra el código real de `main` (`entorno virtual`, `dependencias`, `.env` desde `env.example` con `POSTGRES_PASSWORD` y cómo generar `JWT_SECRET`, contenedor PostgreSQL, `alembic upgrade head`, `python seed.py` desde la raíz y arranque con `uvicorn app.main:app --reload`), además de reflejar la decisión confirmada por el profesor en la clase de consulta del viernes 6/11 de mantener `main.py` en `app/main.py`.

## What Changes

- **`README.md` (reescritura y actualización contra el código real de `main`):**
  - **Integrantes con nombre y apellido:** Belén Calvo, Elías Tello, Hernán González, Bruno Fiouchetta y Joaquín Moran.
  - **Requisitos:** Python 3.12+ y Docker (para correr el contenedor `libreria-db` con PostgreSQL 16).
  - **Pasos desde cero:**
    1. Creación y activación del entorno virtual (`.venv` en Git Bash, PowerShell y CMD) e instalación de dependencias (`pip install -r requirements.txt`).
    2. Configuración de `.env` a partir de `env.example` (nunca versionado ni incluido su contenido real): variables `POSTGRES_*` (`POSTGRES_PASSWORD` obligatoria), generación de `JWT_SECRET` (mínimo 32 caracteres) con `python -c "import secrets; print(secrets.token_urlsafe(32))"`, variables del pool (`DB_POOL_SIZE`, `DB_MAX_OVERFLOW`), `SQL_ECHO`, `JWT_EXPIRA_MINUTOS`, `COOKIE_SECURE`, `BCRYPT_COSTO` y `BCRYPT_CONCURRENCIA`. Eliminación de toda referencia vieja a `DATABASE_URL`.
    3. Contenedor de PostgreSQL 16 (`docker run --name libreria-db ...` y `docker start libreria-db`, con nota de mapeo de puerto si el 5432 está ocupado).
    4. Migraciones con `alembic upgrade head` (4 versiones: 2 del TP + migración 3 de acceso/movimientos/borrado lógico + migración 4 del disparador de sólo agregado).
    5. Carga de datos iniciales desde la raíz con `python seed.py` (reemplazando `python -m scripts.seed`) y tabla de los 5 usuarios iniciales (`admin@example.com`, `admin2@example.com`, `vendedor@example.com`, `ana@example.com`, `nuevo@example.com` con sus roles y estado de `debe_cambiar_password`, indicando que las contraseñas de prueba viven únicamente en `seed.py` según la pág. 19 de la consigna).
    6. Arranque del servidor con `uvicorn app.main:app --reload`.
  - **Ejecución de pruebas:**
    - Suite automática con `unittest`: `python -m unittest discover -s tests`.
    - Archivos `.http` y `.sql` en `test/` (`auth.http`, `seguridad.http`, `ventas.http`, `libros.http`, `solo_agregado.sql`, `clientes.http`, `editoriales.http`, `generos.http`, `autores.http`, `health.http`) detallando cómo se corren y qué casos de la consigna cubre cada uno.
  - **Estructura del proyecto, arquitectura en capas, endpoints (grupo abierto y grupo protegido) y carpeta `evidencia/`:** actualizados al código real de `main` (`app/main.py`, `seed.py`, `app/core/unit_of_work.py`, `app/core/repository.py`, `app/core/paginacion.py`, `app/core/security.py`, `app/core/dependencies.py`, `unit_of_work.py` por módulo, `tests/`, `test/` y `evidencia/`).
- **Actualización de la decisión DD-08 (`app/main.py` se mantiene en `app/main.py`):**
  - `knowledge-base/09_decisiones_y_supuestos.md`: actualizar **DD-08** registrando que `main.py` queda definitivamente en `app/main.py` porque el profesor lo confirmó en la clase de consulta del viernes 6/11 (quitando el checklist de movimiento a la raíz).
  - `knowledge-base/10_preguntas_abiertas.md`: actualizar **IN-01** y quitar la pregunta abierta sobre quién mueve `app/main.py` a la raíz.
  - `AGENTS.md`: actualizar la nota de `main.py` para reflejar que permanece en `app/main.py` (DD-08).
- **Actualización de `CHANGES.md`:**
  - Marcar **B2** como `[x]` mergeado (PR #81) en el árbol de dependencias, en la sección de `[B2]` y en la tabla de resumen.
  - En la tabla `Changes de OpenSpec ya creados`: actualizar `b2-lifespan-health` con el enlace al PR [#81](https://github.com/eEmanuel07/Librer-a_Prog.3_2026/pull/81) (`Mergeado y archivado`) y agregar las filas de `b1-settings` (B1, PR #63 / change en [#82](https://github.com/eEmanuel07/Librer-a_Prog.3_2026/pull/82)), `b3-base-repository` (B3, PR #65 / change en [#82](https://github.com/eEmanuel07/Librer-a_Prog.3_2026/pull/82)) y `b5-paginacion` (B5, PR #66 / change en [#82](https://github.com/eEmanuel07/Librer-a_Prog.3_2026/pull/82)) como changes retroactivos mergeados y archivados.
  - En `[B7]`: cambiar `uvicorn main:app` por `uvicorn app.main:app --reload` y eliminar el bloque `"Paso previo a E10 — Mover app/main.py a main.py en la raíz (DD-08)"`.

## Capabilities

### New Capabilities

- `documentacion-entrega`: documentación de puesta en marcha desde cero en `README.md` (integrantes, requisitos, variables de entorno y generación de clave de firma sin secretos expuestos, base de datos, migraciones, datos iniciales con `python seed.py`, arranque con `uvicorn app.main:app --reload`, ejecución de tests automáticos y casos `.http`/`.sql`, estructura real del proyecto y evidencias).

### Modified Capabilities

(ninguna)

## Impact

- **Archivos modificados en el apply:**
  - `README.md`
  - `knowledge-base/09_decisiones_y_supuestos.md`
  - `knowledge-base/10_preguntas_abiertas.md`
  - `AGENTS.md`
  - `CHANGES.md`
- **Código de la aplicación (`app/`, `seed.py`, `migrations/`, `tests/`):** sin cambios.
