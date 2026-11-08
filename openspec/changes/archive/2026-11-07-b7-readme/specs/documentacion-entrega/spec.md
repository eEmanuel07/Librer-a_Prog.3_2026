# Spec Delta: documentacion-entrega

## Purpose

Define la información obligatoria que debe exponer `README.md` y la documentación de seguimiento del proyecto para que cualquier evaluador o integrante pueda levantar la API del parcial desde cero, ejecutar los datos iniciales, correr la suite de pruebas y los casos `.http`/`.sql` de `test/`, e inspeccionar la estructura real del repositorio y sus evidencias sin incluir secretos ni instrucciones obsoletas del Trabajo Práctico anterior.

## ADDED Requirements

### Requirement: Identificación completa de los integrantes y requisitos técnicos
El archivo `README.md` SHALL listar el nombre y apellido de cada integrante del grupo (Belén Calvo, Elías Tello, Hernán González, Bruno Fiouchetta y Joaquín Moran) y los requisitos mínimos para ejecutar el proyecto en local (Python 3.12 o superior y Docker para PostgreSQL 16).

#### Scenario: Consulta de integrantes y requisitos en el README
- **WHEN** un evaluador abre `README.md` en la raíz del proyecto
- **THEN** encuentra los nombres y apellidos de los cinco integrantes del grupo y los requisitos de versión de Python y PostgreSQL en contenedor

### Requirement: Pasos reproducibles para levantar el proyecto desde cero sin exponer secretos
El archivo `README.md` SHALL documentar en orden los comandos para levantar el proyecto desde cero (entorno virtual, dependencias, configuración de `.env` desde `env.example` con cómo generar `JWT_SECRET`, contenedor PostgreSQL 16, `alembic upgrade head`, `python seed.py` y `uvicorn app.main:app --reload`). El documento SHALL NOT incluir el contenido de un `.env` real ni referencias obsoletas a `DATABASE_URL` o `python -m scripts.seed`.

#### Scenario: Puesta en marcha siguiendo el README paso a paso
- **WHEN** se ejecutan en orden las instrucciones de instalación, configuración de `.env` (`POSTGRES_*` con `POSTGRES_PASSWORD` obligatoria y `JWT_SECRET` generada con `python -c "import secrets; print(secrets.token_urlsafe(32))"`), contenedor `libreria-db`, `alembic upgrade head`, `python seed.py` y `uvicorn app.main:app --reload`
- **THEN** la aplicación queda en ejecución con las 4 migraciones aplicadas y los datos iniciales cargados sin requerir pasos no documentados

#### Scenario: Ausencia de secretos y de referencias obsoletas del TP
- **WHEN** se revisa el contenido de `README.md`
- **THEN** no aparece el volcado de un archivo `.env`, no se instruye configurar `DATABASE_URL` para el proyecto del parcial ni ejecutar `python -m scripts.seed`

### Requirement: Documentación de los datos iniciales y usuarios de prueba
El archivo `README.md` SHALL describir qué carga `python seed.py` (vaciado idempotente, los 5 usuarios iniciales con sus correos, roles vigentes y estado de `debe_cambiar_password`, el catálogo, los clientes, la venta inicial con sus movimientos y la línea con actor `SISTEMA`) e indicar que las contraseñas de prueba viven únicamente en `seed.py`.

#### Scenario: Consulta de los usuarios iniciales para probar
- **WHEN** un evaluador consulta la sección de datos iniciales en `README.md`
- **THEN** identifica los correos `admin@example.com`, `admin2@example.com`, `vendedor@example.com`, `ana@example.com` y `nuevo@example.com`, sus roles (`ADMIN`, `VENDEDOR`, `CLIENTE`), que `nuevo@example.com` tiene cambio obligatorio de contraseña pendiente, y que las contraseñas de prueba están sólo en `seed.py` (sin publicarlas en `README.md`)

### Requirement: Instrucciones para ejecutar tests automáticos, casos `.http`/`.sql` y consultar evidencias
El archivo `README.md` SHALL documentar cómo correr la suite de pruebas automáticas con `unittest` (`python -m unittest discover -s tests`), cómo ejecutar cada archivo de `test/` (los `.http` con REST Client en VS Code y `test/solo_agregado.sql` con `psql`) detallando qué casos de prueba de la consigna cubre cada uno, y qué contiene la carpeta `evidencia/`.

#### Scenario: Ejecución de la suite de unittest y de los casos de prueba
- **WHEN** un evaluador busca cómo verificar el proyecto en `README.md`
- **THEN** encuentra el comando `python -m unittest discover -s tests`, la tabla de archivos en `test/` con los casos que cubre cada archivo (incluidos C-01 a C-05 en `test/auth.http`, C-06 a C-09 en `test/seguridad.http`, C-14 en `test/solo_agregado.sql` y los `.http` de catálogo, clientes, ventas y salud) y la descripción de los archivos en `evidencia/`

### Requirement: Estructura del proyecto y decisión sobre `app/main.py` alineadas con el código real
El archivo `README.md` y los documentos de arquitectura y seguimiento (`09_decisiones_y_supuestos.md`, `10_preguntas_abiertas.md`, `AGENTS.md` y `CHANGES.md`) SHALL reflejar la estructura real de `main`, manteniendo `app/main.py` en su ubicación actual (confirmado por el profesor el viernes 6/11) y `seed.py` en la raíz, junto con el estado actualizado de los changes mergeados (`B2` en PR #81 y `B1`, `B3`, `B5` en PR #82).

#### Scenario: Coherencia entre la estructura documentada y el árbol real del repositorio
- **WHEN** se contrasta la sección de estructura y arquitectura de `README.md`, `DD-08`, `IN-01`, `AGENTS.md` y `CHANGES.md` contra el árbol de archivos de `main`
- **THEN** todos los caminos documentados existen (`app/main.py`, `seed.py`, `app/core/config.py`, `app/core/database.py`, `app/core/security.py`, `app/core/dependencies.py`, `app/core/repository.py`, `app/core/paginacion.py`, `app/core/unit_of_work.py`, `app/core/errors.py`, `app/modules/<módulo>/unit_of_work.py`, `migrations/`, `test/`, `tests/`, `evidencia/`), no figura `app/core/uow.py` ni `scripts/seed.py`, y no queda ningún paso pendiente para mover `app/main.py` a la raíz
