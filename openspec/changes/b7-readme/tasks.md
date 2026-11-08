# Tasks: b7-readme

> Rama: `feat/b7-readme`. Cada grupo numerado (1 y 2) puede ser un commit o integrarse según indique Belén al aplicar.
> Commits en español, sin `Co-Authored-By` ni atribución de IA. Cada commit lo ejecuta Belén cuando aprueba el paso.

## 1. Reescribir `README.md` del parcial revisado contra el código real de `main`

- [x] 1.1 Actualizar el encabezado, integrantes y pasos desde cero en `README.md` y verificar que no quede ninguna referencia a `python -m scripts.seed`, `DATABASE_URL` ni el contenido de `.env`:
  - Título del parcial y descripción de las capacidades (capítulos 1 a 6);
  - Nombres y apellidos de los 5 integrantes: Belén Calvo, Elías Tello, Hernán González, Bruno Fiouchetta, Joaquín Moran;
  - Requisitos técnicos (Python 3.12+ con versiones mínimas de `requirements.txt` y Docker para PostgreSQL 16);
  - Instalación (clonado, creación y activación de `.venv` en Git Bash, PowerShell y CMD, `pip install -r requirements.txt`);
  - Configuración de `.env` desde `env.example` (variables `POSTGRES_*` con `POSTGRES_PASSWORD` obligatoria, generación de `JWT_SECRET` de al menos 32 caracteres con `python -c "import secrets; print(secrets.token_urlsafe(32))"`, `DB_POOL_SIZE`, `DB_MAX_OVERFLOW`, `SQL_ECHO`, `JWT_EXPIRA_MINUTOS`, `COOKIE_SECURE`, `BCRYPT_COSTO`, `BCRYPT_CONCURRENCIA`, sin el contenido de `.env`);
  - Contenedor PostgreSQL 16 (`docker run --name libreria-db ...` y `docker start libreria-db`);
  - Migraciones con `alembic upgrade head` (las 4 migraciones de `migrations/versions/`);
  - Carga de datos iniciales desde la raíz con `python seed.py` y tabla de los 5 usuarios iniciales (`admin@example.com`, `admin2@example.com`, `vendedor@example.com`, `ana@example.com`, `nuevo@example.com` con su rol vigente y `debe_cambiar_password`, indicando que las contraseñas de prueba viven sólo en `seed.py`);
  - Arranque del servidor con `uvicorn app.main:app --reload`.
- [x] 1.2 Actualizar las secciones de pruebas, estructura, arquitectura en capas, endpoints y `evidencia/` en `README.md` y verificar cada ruta y nombre de archivo contra el árbol real de `main`:
  - Cómo correr la suite automática con `unittest`: `python -m unittest discover -s tests`;
  - Cómo correr los archivos `.http` (extensión REST Client de VS Code, `python seed.py` previo, sesiones múltiples con `# @name` y `# @no-cookie-jar`) y `test/solo_agregado.sql` con `psql`, con tabla que detalle qué casos de la consigna cubre cada archivo (`auth.http` C-01..C-05, `seguridad.http` C-06..C-09, `ventas.http`, `libros.http`, `solo_agregado.sql` C-14, `clientes.http`, `editoriales.http`, `generos.http`, `autores.http`, `health.http`);
  - Árbol de estructura del proyecto (`app/main.py`, `seed.py`, `app/core/*`, `app/modules/<módulo>/*` con `unit_of_work.py`, `app/modules/health/router.py`, `migrations/`, `test/`, `tests/`, `evidencia/`) sin `app/core/uow.py` ni `scripts/seed.py`;
  - Tabla de arquitectura en capas (`Router → Service → UoW → Repository → Model`) reflejando `async with uow`, `uow.con_mensajes(...)`, `BaseRepository[T]` / `SoftDeleteRepository[T]` (`flush()` sin `commit()`) y sesión compartida con `Depends(get_session)`;
  - Tabla de endpoints dividida en **Grupo abierto** y **Grupo protegido** según `app/main.py`, con paginación por envoltorio `{items, total, page, size, pages}`;
  - Descripción de la carpeta `evidencia/` (C-14 en `psql`, C-15 / C-07 de consultas sin N+1 e integración) y nota para Windows sin menciones a `DATABASE_URL`.

## 2. Actualizar decisión DD-08 (`app/main.py`) y estado de changes en `knowledge-base/`, `AGENTS.md` y `CHANGES.md`

- [ ] 2.1 Actualizar `DD-08` en `knowledge-base/09_decisiones_y_supuestos.md`, `IN-01` en `knowledge-base/10_preguntas_abiertas.md` y la nota en `AGENTS.md`, verificando que quede asentado que `main.py` permanece en `app/main.py` por confirmación del profesor en la clase de consulta del viernes 6/11 (sin checklist de movimiento a la raíz ni pregunta abierta pendiente).
- [ ] 2.2 Actualizar `CHANGES.md` y verificar la consistencia de la tabla de changes, el árbol, las secciones y el resumen:
  - En `### Changes de OpenSpec ya creados`: actualizar `b2-lifespan-health` con PR [#81](https://github.com/eEmanuel07/Librer-a_Prog.3_2026/pull/81) (`Mergeado y archivado`) y agregar las filas de `b1-settings` (B1, PR #63 / change en [#82](https://github.com/eEmanuel07/Librer-a_Prog.3_2026/pull/82)), `b3-base-repository` (B3, PR #65 / change en [#82](https://github.com/eEmanuel07/Librer-a_Prog.3_2026/pull/82)) y `b5-paginacion` (B5, PR #66 / change en [#82](https://github.com/eEmanuel07/Librer-a_Prog.3_2026/pull/82));
  - Marcar `B2` como `[x]` mergeado (PR #81) en el árbol de dependencias, en `### [B2] b2-lifespan-health · #31` y en la tabla `## Resumen`;
  - En `### [B7] readme-parcial · #36`: cambiar `uvicorn main:app` por `uvicorn app.main:app --reload` y eliminar el bloque `> **Paso previo a E10 — Mover app/main.py a main.py en la raíz (DD-08):**`.

## 3. Verificación final (sin commit)

- [ ] 3.1 Ejecutar `python -m unittest discover -s tests` y `openspec validate b7-readme --strict`, y comprobar con búsqueda en `README.md` que no figuren `scripts.seed`, `scripts/seed.py`, `uow.py`, `DATABASE_URL` ni contraseñas fuera de lugar.

## Workflow follow-up

- Archivar el change con `/opsx:archive b7-readme` una vez aprobado y verificado para sincronizar `openspec/specs/documentacion-entrega/spec.md` y marcar `[B7]` en `CHANGES.md`.
