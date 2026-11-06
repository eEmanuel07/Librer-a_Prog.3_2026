# Librería (Parcial Programación III, caps. 1 a 6) — Instrucciones para Agentes

> Este archivo es lo **primero** que lee cualquier agente al entrar al repo (Claude Code, OpenCode, Copilot, Codex…). `CLAUDE.md` lo importa, así que las reglas viven en un solo lugar.
> Sale de `knowledge-base/`, `CHANGES.md` y `docs/flujo-de-trabajo.md`. Si cambia una regla, se cambia acá.

---

## Stack Tecnológico

| Capa | Tecnología | Versión mínima |
|---|---|---|
| Lenguaje | Python | 3.12 |
| Backend | FastAPI (todos los handlers `async def`), SQLModel, SQLAlchemy 2 asincrónico, asyncpg | 0.111 / 0.0.24 / 2.0 / 0.30 |
| Base de datos | PostgreSQL (contenedor `libreria-db` en local) | 16 |
| Migraciones | Alembic, plantilla asincrónica | 1.13 |
| Configuración | pydantic-settings, desde el entorno o `.env` | 2.0 |
| Seguridad | bcrypt, PyJWT (token en cookie `HttpOnly`) | 4.0 / 2.8 |
| Tests | `unittest` de la biblioteca estándar, más los `.http` de `test/` | — |
| Contenedor | Docker, **sólo** para el TP de los caps. 1 a 4 (rama `despliegue`) | 20.10 |

Es una API sin pantallas: la política visual es `off` (`design-system/README.md`), así que ningún change pide mockups.

Detalle: [knowledge-base/02_descripcion_general.md](knowledge-base/02_descripcion_general.md)

---

## Base de Conocimiento

La fuente de verdad del dominio es `knowledge-base/`, que resume la consigna `Parcial_Cap1a6_Consigna.pdf`. El PDF no se versiona; lo tiene cada integrante. **Leé la ficha que corresponda antes de implementar.**

| Archivo | Cuándo leerlo |
|---|---|
| [01_vision_y_objetivos.md](knowledge-base/01_vision_y_objetivos.md) | Qué pide el parcial y qué queda afuera |
| [03_actores_y_roles.md](knowledge-base/03_actores_y_roles.md) | Autenticación, roles, 401 contra 403 |
| [04_modelo_de_datos.md](knowledge-base/04_modelo_de_datos.md) | Tablas, migraciones, datos iniciales |
| [05_reglas_de_negocio.md](knowledge-base/05_reglas_de_negocio.md) | **RN-01 a RN-16** con su garante y responsable |
| [06_funcionalidades.md](knowledge-base/06_funcionalidades.md) | Los 10 ejercicios y los casos C y D |
| [07_flujos_principales.md](knowledge-base/07_flujos_principales.md) | Login, registro, venta, libros, roles |
| [08_arquitectura_propuesta.md](knowledge-base/08_arquitectura_propuesta.md) | Capas, **estructura obligatoria**, variables de entorno |
| [10_preguntas_abiertas.md](knowledge-base/10_preguntas_abiertas.md) | ⚠️ Lo que no coincide con la consigna |
| [11_entrega_y_despliegue.md](knowledge-base/11_entrega_y_despliegue.md) | El `.zip`, la imagen y el VPS |

> ⚠️ Antes de tocar `main.py` o la estructura, leé la pregunta de prioridad **Alta** de `10_preguntas_abiertas.md` (IN-01: `main.py` y `seed.py` en la raíz).
> Las reglas usan **la numeración del parcial** (RN-01 a RN-16). Los comentarios viejos del código usan la del TP (IN-03).

---

## Skills Disponibles

El flujo OPSX (`/opsx:explore`, `/opsx:propose`, `/opsx:apply`, `/opsx:archive`, `/opsx:sync`, `/opsx:update`) está versionado en `.claude/commands/opsx/` y lo tiene cualquiera que clone el repo. Las skills de Active Stack son de quien las tenga instaladas:

| Agente | Rol | Skills que carga |
|---|---|---|
| **Orquestación** | Fundación del proyecto y docs | `active-orchestrator`, `kb-creator`, `roadmap-generator`, `agent-instruction`, `skill-registry` |
| **Implementación** | Cada tarea con OpenSpec | `/opsx:propose`, `/opsx:apply`, `/opsx:archive` (comandos del repo) |
| **Diseño** | No aplica (política `off`) | `design-system` sólo si el grupo cambia la política |

> Los compact rules de cada skill los resuelve el orquestador desde `.atl/skill-registry.md` (generado por `skill-registry`; no versionado — no está en el repo).

---

## Roadmap de Changes

El roadmap completo está en [CHANGES.md](CHANGES.md): las 44 tareas del tablero por fase, con sus dependencias y su estado real según los PR.

- **Changes de OpenSpec:** `h4-auth-login` (Hernán, mergeado, PR #75), `b6-migracion-3` (Belén, en revisión, PR #76) y `b4-unit-of-work` (Belén, en revisión, PR #77).
- **Cuellos de botella:** **B4** (Unit of Work) destraba H3, J3, R1, R4 y R5. **R2** (`requiere_rol`) destraba E4, E5, J3, J7, R4 y R7.
- **Camino crítico:** B4 → R5 → R2 → J3 → J5 → J8/J6 → B7/H8/I1 → E10.
- **Disponibles hoy:** B2 (lifespan y health), R8 (`seed.py` en la raíz) y E8 (VPS, cuando J2 esté mergeado).

---

## Reglas Duras (específicas del proyecto)

Valen para **cualquier** agente y cualquier integrante. Si tenés instrucciones globales propias (por ejemplo `~/.claude/CLAUDE.md`), estas reglas del proyecto las complementan y, si chocan, mandan estas.

### Del grupo

1. **NUNCA commitear directo a `main`** → una rama por issue (`feat/<código>-<descripción>`, o `docs/…` para documentación), un PR a `main` con `Closes #<n>`, **otro integrante aprueba** y se mergea con **merge común** (no squash).
2. **NUNCA agregar `Co-Authored-By`, `Claude-Session` ni "Generated with Claude Code"** en commits, PR ni issues → el autor es el integrante.
3. **NUNCA arrancar una tarea sin change** → empieza con `/opsx:propose` y se cierra con `/opsx:archive`. El change va antes del código.
4. **NUNCA hacer ni adelantar tareas de otros integrantes** → la letra del código de la issue dice de quién es (B Belén, H Hernán, R Bruno, E Elías, J Joaquín; I1, la integración, es de Hernán). Si te bloquea, se avisa (regla 9).
5. **NUNCA subir el `.env` ni secretos** (contraseñas, la clave de firma, ni siquiera como valor por defecto) → `env.example` sin valores reales. Si algo se subió por error, avisar: sigue en el historial y hay que cambiarlo. La consigna del PDF tampoco se sube.
6. **NUNCA mezclar la rama `despliegue` con `main`** → `despliegue` sale del tag `entrega-final` (el TP 1-4 tal como se entregó) y sólo lleva lo del contenedor y el VPS.

### De `docs/flujo-de-trabajo.md` (detalle en [docs/flujo-de-trabajo.md](docs/flujo-de-trabajo.md))

7. **`app/main.py` es el único archivo que todos tocan** (el registro de routers) → si hay conflicto, se resuelve dejando las líneas de todos.
8. **NUNCA generar una migración fuera de la cadena** → hay una sola: la 3 la genera B6 y la 4 la escribe a mano E6. Cada migración se **lee antes de aplicarla**, lleva un comentario que lo dice (y explica cualquier corrección a mano), y antes de subirla se prueba `upgrade head`, `downgrade base` y `upgrade head`.
9. **NUNCA adelantar trabajo bloqueado sin avisar** → si una issue depende de otra que no está, se comenta en la issue y se avisa en el grupo.

### Convención de tests

10. **Tests con `unittest`** (`IsolatedAsyncioTestCase`, `fastapi.testclient.TestClient`), nunca pytest, que no está en `requirements.txt`. Se corren con `python -m unittest discover -s tests`.

> **Recordatorio de la consigna** (no son reglas nuevas del grupo; están en [05](knowledge-base/05_reglas_de_negocio.md) y [08](knowledge-base/08_arquitectura_propuesta.md)): el router construye el Unit of Work y el servicio lo abre con `async with`; ningún repositorio hace `commit()`; RN-02, RN-10 y RN-16 van cada una en un solo bloque; las dependencias piden `Depends(get_session)` (la única con sesión propia es `registrar_intento_acceso`); ningún error devuelve texto de la base y ninguna entrada inválida da 500.

---

## Flujo de Trabajo

```
knowledge-base/ (dominio)  →  CHANGES.md (qué sigue)  →  /opsx:propose <código>-<nombre>
   →  /opsx:apply  →  PR a main (Closes #n, aprobación de otro)  →  /opsx:archive  →  checkbox en CHANGES.md
```

- Commits chicos, **en español y con ámbito**: `feat(libros): …`, `fix(auth): …`, `docs: …`. Un commit por idea.
- La issue se mueve en el [tablero](https://github.com/users/eEmanuel07/projects/1): *In Progress* al empezar y *Done* al mergear.
- Una tarea está hecha cuando cumple el "hecho cuando" de su issue, pasó la revisión de otro integrante y está mergeada en `main` (`docs/flujo-de-trabajo.md`).
