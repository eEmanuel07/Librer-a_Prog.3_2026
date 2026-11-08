# Proposal: h8-revision-rnf

## Why

La consigna del Parcial (págs. 20-21) y el roadmap en `CHANGES.md` establecen la tarea **[H8] (`revision-rnf`, #44)** como compuerta obligatoria previa al empaquetado final (`E10`). Es necesario auditar transversalmente toda la base de código tras el cierre de la Fase 2 para garantizar el cumplimiento estricto de los Requisitos No Funcionales (RNF): ausencia de secretos en el repositorio, prohibición de carga perezosa (`lazy="raise"`), prevención de errores HTTP 500 ante entradas mal formadas, no exposición de mensajes internos de base de datos (RN-15), aislamiento transaccional en Unit of Work y validez estricta de las especificaciones OpenSpec.

## What Changes

- **Auditoría transversal de RNF** sobre todos los módulos (`usuarios`, `libros`, `ventas`, `clientes`, `autores`, `editoriales`, `generos`, `health`), núcleo (`app/core/`), migraciones (`migrations/`, `alembic.ini`) y script inicial (`seed.py`).
- **Corrección de hallazgos menores de RNF / OpenSpec** detectados durante la inspección (como completar las secciones `## Purpose` pendientes en `openspec/specs/autorizacion/spec.md` y `openspec/specs/datos-iniciales/spec.md` para que `openspec validate --all --strict` pase sin advertencias ni fallos, y archivar changes remanentes si aplica).
- **Tests automatizados de verificación de RNF (`tests/test_rnf.py`)** que comprueban programáticamente las invariantes transversales:
  - Todas las relaciones SQLModel declaran `lazy="raise"`.
  - Ningún repositorio define llamadas a `.commit()`.
  - Todos los esquemas de entrada (`Create`, `Update`, `Request`) tienen `extra="forbid"`.
  - `Settings` exige `postgres_password` y `jwt_secret` sin valores por defecto.
  - Entradas inválidas en rutas y cuerpos devuelven 422 y nunca 500 ni filtran texto de SQLAlchemy/PostgreSQL (RN-15).

## Capabilities

### New Capabilities
None.

### Modified Capabilities
None. (`skip_specs: true` en `.openspec.yaml`; las correcciones de formato en specs existentes son de saneamiento documental para `openspec validate --all --strict`).

## Impact

- **Tests:** Nuevo archivo `tests/test_rnf.py` con pruebas automatizadas de arquitectura y requisitos no funcionales.
- **OpenSpec / Docs:** Saneamiento de `openspec/specs/` y actualización de estado en `CHANGES.md`.
- **Código de producción:** Sólo si la auditoría detecta algún desvío puntual respecto a RN-15 o RNF.
