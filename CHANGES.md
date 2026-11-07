# CHANGES — Secuencia de Implementación

> Índice canónico de todos los changes del proyecto **Librería — Parcial Programación III (caps. 1 a 6)**.
> Cada change es una issue del [tablero](https://github.com/users/eEmanuel07/projects/1) y se trabaja en una sesión.
> **Leer este archivo antes de ejecutar cualquier `/opsx:propose`.**
>
> **IDs:** se usan los códigos de las issues (`B4`, `H3`…), donde la letra es de quien la hace, y no `C-NN`, porque la consigna ya usa `C-01…C-16` para los **casos de prueba**.
> **Estado** al 2026-11-06, según el **estado real de los PR** y no sólo el del tablero: `[x]` mergeado en `main` · `[~]` PR abierto, en revisión · `[ ]` pendiente.
> 🔓 **Destraba** marca la tarea que, al terminarse, habilita a otras.

---

## Cómo usar este documento

1. **Elegí una tarea tuya** con todas sus dependencias en `[x]`. No hagas ni adelantes tareas de otros integrantes.
2. **Leé la KB** que indica "Leer antes" (`knowledge-base/`) y la página de la consigna citada ahí.
3. **Proponé el change:** `/opsx:propose <código>-<nombre>` (por ejemplo `/opsx:propose h3-auth-registro`), en una rama `feat/<código>-<descripción>` desde `main` actualizado.
4. **Implementá, abrí el PR a `main`** con `Closes #<n>`, que lo apruebe otro integrante, y al cerrar corré `/opsx:archive`.
5. **Marcá el checkbox** de este archivo (y movés la issue en el tablero).

### Changes de OpenSpec ya creados

| Change | Tarea | Responsable | PR | Estado | Spec que deja |
|---|---|---|---|---|---|
| `h4-auth-login` | H4 | Hernán | [#75](https://github.com/eEmanuel07/Librer-a_Prog.3_2026/pull/75) | Mergeado y archivado | `openspec/specs/autenticacion` |
| `b6-migracion-3` | B6 | Belén | [#76](https://github.com/eEmanuel07/Librer-a_Prog.3_2026/pull/76) | Mergeado y archivado (change retroactivo) | `openspec/specs/esquema-base-datos` |
| `b4-unit-of-work` | B4 | Belén | [#77](https://github.com/eEmanuel07/Librer-a_Prog.3_2026/pull/77) | Mergeado y archivado | `openspec/specs/transacciones` |
| `b2-lifespan-health` | B2 | Belén | por abrir | En revisión (archivado en su rama) | `openspec/specs/ciclo-de-vida-y-salud` |
| `h3-auth-registro` | H3 | Hernán | por abrir | En revisión (archivado en su rama) | `openspec/specs/autenticacion` |
| `h6-auth-logout-yo-cambio` | H6 | Hernán | por abrir | En revisión (archivado en su rama) | `openspec/specs/autenticacion` |
| `j3-venta-con-stock` | J3 | Joaquín | [#87](https://github.com/eEmanuel07/Librer-a_Prog.3_2026/pull/87) | Mergeado y archivado | `openspec/specs/ventas` |
| `j4-aviso-comprobante` | J4 | Joaquín | [#88](https://github.com/eEmanuel07/Librer-a_Prog.3_2026/pull/88) | En revisión (archivado en su rama) | `openspec/specs/ventas` |
| `j5-detalle-venta-dueno` | J5 | Joaquín | [#89](https://github.com/eEmanuel07/Librer-a_Prog.3_2026/pull/89) | En revisión (archivado en su rama) | `openspec/specs/ventas` |
| `j6-mis-ventas-y-ventas` | J6 | Joaquín | por abrir | En revisión (archivado en su rama) | `openspec/specs/ventas` |
| `r2-requiere-rol` | R2 | Bruno | [#93](https://github.com/eEmanuel07/Librer-a_Prog.3_2026/pull/93) | En revisión (archivado en su rama) | `openspec/specs/autorizacion` |
| `r5-roles-con-vigencia` | R5 | Bruno | por abrir | En revisión (archivado en su rama) | `openspec/specs/autorizacion` |

La fundación de Active Stack (`knowledge-base/`, `CHANGES.md`, `AGENTS.md`, `CLAUDE.md`) quedó mergeada en [#78](https://github.com/eEmanuel07/Librer-a_Prog.3_2026/pull/78). Las demás tareas `[x]` (incluida E6 en [#79](https://github.com/eEmanuel07/Librer-a_Prog.3_2026/pull/79)) no tienen change en `openspec/`.

---

## Árbol de dependencias

```
FASE 0 · Fundamentos
B1 Settings [x] ──┬── B2 Lifespan y health [~]
                  └── H2 security.py [x] ───────────────┐
B3 BaseRepository [x] ──┬── E2 SoftDeleteRepository [x] │
                        └── B4 UnitOfWork [x] 🔓 ───────┼──┬── R1 get_usuario_actual ──┬── R2 requiere_rol 🔓
B5 Paginación [x]                                       │  │                           ├── R3 dos grupos de rutas
J1 Dockerfile [x] ── J2 probar imagen [x] ── E8 VPS ── E9 DEPLOY.md
                                                        │  ├── R5 roles con vigencia ──┘ (R2 depende de R1 y R5)
FASE 1 · Modelos y migraciones                          │  ├── H3 registro (también H1, H2)
E0 nombres [x] ──┬── H1 modelos usuarios [x] ──┐        │  ├── R4 alta de personal (también R2) ── H6 logout/yo/cambio
                 └── E1 modelos libros [x] ────┴── B6 Migración 3 [x] ── E6 Migración 4 (disparador) [x]
E1 + E2 ── E3 punto único de stock [x] ──┐
H1 ── H5 intento_acceso [x] ── H4 login [x] ── H6
                                         │
FASE 2 · Funcionalidad (casi todo espera B4 y R2)
R2 ──┬── E4 alta/PATCH/baja libros ──┐
     ├── E5 reposición y movimientos ┼── E7 solo_agregado.sql + .http libros [~] (también E6)
     ├── J3 venta con stock (también E3, B4) 🔓 ──┬── J4 aviso
     │                                            └── J5 detalle sin N+1 (también R1) ── J6 /mis-ventas, /ventas
     ├── J7 clientes con acceso
     ├── R4 ── R6 /eventos (también R5)
     └── R7 proteger editoriales/géneros/autores

FASE 3 · Cierre
R8 seed.py en la raíz (E1, H1, E3: ya se puede) 🔓 ──┬── H7 auth.http (H3, H4, H6)
                                                     ├── R9 seguridad.http (R2, R3, R5)
                                                     └── J8 ventas.http + C-15 (J3, J4, J5)
E7 + J8 ── B7 README ──┐
toda la fase 2 ── H8 revisión RNF, I1 integración ──┴── E10 .zip de entrega
```

### Paralelismo por fase

```
GATE 0: ya disponibles hoy (dependencias en [x])
  → B2 lifespan y health                        [Belén]
  → R8 seed.py en la raíz                       [Bruno]       ← destraba H7, R9 y J8
  → E8 despliegue en el VPS                     [Elías — si J2 ✓]

GATE 1: B4 ✓ (PR #77)                           ← PRIMER FORK
  → R1 get_usuario_actual                       [Bruno]
  → R5 roles con vigencia                       [Bruno]
  → H3 auto-registro (RN-02)                    [Hernán]

GATE 2: B6 ✓ (PR #76)
  → E6 migración 4: disparador (RN-12)          [Elías]

GATE 3: R1 ✓ + R5 ✓ → R2 ✓                      ← FORK MÁS GRANDE (6 tareas)
  → E4 alta, PATCH y baja de libros             [Elías]
  → E5 reposición y movimientos                 [Elías]
  → J3 venta con stock (RN-10)                  [Joaquín]
  → J7 clientes con acceso                      [Joaquín]
  → R4 alta de personal                         [Bruno]
  → R7 proteger catálogo                        [Bruno]
  (R3 sale con R1 ✓, no espera a R2)            [Bruno]

GATE 4: J3 ✓
  → J4 aviso del comprobante                    [Joaquín]
  → J5 detalle sin N+1 (también R1 ✓)           [Joaquín]

GATE 5: R4 ✓
  → H6 logout, /auth/yo, cambiar-password       [Hernán]
  → R6 /eventos                                 [Bruno]

GATE 6: fase 2 ✓ + R8 ✓
  → H7, R9, J8, E7 (los .http y evidencias)     [cada dueño]
  → H8 revisión de requisitos no funcionales    [Hernán]
  → I1 integración sobre base nueva             [Hernán]

GATE 7: B7 ✓ + H8 ✓ + I1 ✓
  → E10 armar el .zip                           [Elías]
```

### Camino crítico (8 tareas — mínimo irreducible)

```
B4 → R5 → R2 → J3 → J5 → J8* → B7 → E10
B4 → R5 → R2 → J3 → J5 → J6* → H8/I1 → E10
```

\* Las dos ramas tienen la misma longitud. **B4 y R2 son los cuellos de botella:** B4 habilita cinco tareas (H3, J3, R1, R4, R5) y R2 seis (E4, E5, J3, J7, R4, R7).

### Plan óptimo con 3 agentes

El grupo tiene **5 integrantes** y cada uno tiene su frente, así que la tabla es por persona y no por agente. Los pasos siguen los gates.

| Paso | Belén | Hernán | Bruno | Elías | Joaquín |
|---|---|---|---|---|---|
| 1 | B4, B6 (revisión) · B2 | — | R8 | E8 si J2 ✓ | J2 (revisión) |
| 2 | — | H3 | R1, R5 | E6 | — |
| 3 | — | — | R2, R3 | E8 / E9 | — |
| 4 | — | — | R4, R7 | E4, E5 | J3, J7 |
| 5 | — | H6 | R6 | E7 | J4, J5 |
| 6 | — | H7, H8, I1 | R9 | E9 | J6, J8 |
| 7 | B7 | — | — | E10 | — |

---

## FASE 0 — Fundamentos

> En paralelo, sin depender de nadie.

### [B1] `settings-pydantic` · #30
- **Estado**: `[x]` mergeado (PR #63)
- **Scope**: `Settings` con pydantic-settings, URL con `@computed_field` a partir de `POSTGRES_*`, sin secretos por defecto; `env.example`
- **Dependencias**: ninguna · 🔓 Destraba: B2, H2
- **Governance**: CRITICO
- **Leer antes**: `knowledge-base/08_arquitectura_propuesta.md` §Variables de entorno · `06_funcionalidades.md` §Ej. 1

### [B2] `b2-lifespan-health` · #31
- **Estado**: `[~]` en revisión (archivado en su rama)
- **Scope**:
  - motor (con el tamaño del pool), fábrica de sesiones y hash ficticio creados en el lifespan, en `app.state`; `dispose()` al apagar
  - `get_session` con `expire_on_commit=False`
  - `GET /health/live` sin base; `GET /health/ready` con `SELECT 1` y 503
  - eliminado `service.py` de `health` (queda sólo `router.py`, resuelve IN-04)
- **Dependencias**: B1
- **Governance**: MEDIO
- **Leer antes**: `06_funcionalidades.md` §Ej. 1 · `08_arquitectura_propuesta.md` · `10_preguntas_abiertas.md` IN-04

### [B3] `base-repository` · #32
- **Estado**: `[x]` mergeado (PR #65)
- **Scope**: `BaseRepository[T]` con sesión y clase del modelo; `get_by_id`, `get_all`, `count`, `add`, `update`, `delete`; `flush()` y nunca `commit()`
- **Dependencias**: ninguna · 🔓 Destraba: B4, E2
- **Governance**: ALTO
- **Leer antes**: `06_funcionalidades.md` §Ej. 6 · `08_arquitectura_propuesta.md` §Patrones

### [B4] `b4-unit-of-work` · #33
- **Estado**: `[x]` mergeado (PR #77)
- **Scope**:
  - `app/core/unit_of_work.py`: confirma al salir, revierte ante una excepción, traduce `IntegrityError` a 409 con `con_mensajes()` y no cierra la sesión
  - un `unit_of_work.py` por módulo con `get_<módulo>_uow`
  - services con `async with` y routers con la dependencia del módulo; se borra `uow.py`
  - test de sesión compartida (una conexión por petición)
- **Dependencias**: B3 · 🔓 **Destraba: H3, J3, R1, R4, R5**
- **Governance**: CRITICO
- **Leer antes**: `06_funcionalidades.md` §Ej. 6 · `05_reglas_de_negocio.md` · `07_flujos_principales.md` §Flujo 1 · `09_decisiones_y_supuestos.md` DD-03

### [B5] `paginacion-envoltorio` · #34
- **Estado**: `[x]` mergeado (PR #66)
- **Scope**: `app/core/paginacion.py` con `{items, total, page, size, pages}`, 422 para una página inexistente. Los routers todavía usan `pagination.py` (ver IN-02)
- **Dependencias**: ninguna · 🔓 Destraba: J6, J7, R6, R7
- **Governance**: BAJO
- **Leer antes**: `06_funcionalidades.md` §Ej. 3 · `10_preguntas_abiertas.md` IN-02

### [E0] `nombres-relaciones` · #18
- **Estado**: `[x]` hecho (acuerdo del grupo, sin PR)
- **Scope**: nombres de las relaciones nuevas, todas con `lazy="raise"` y declaradas en los dos extremos
- **Dependencias**: ninguna · 🔓 Destraba: E1, H1
- **Governance**: BAJO
- **Leer antes**: `04_modelo_de_datos.md` §ERD

### [E2] `soft-delete-repository` · #20
- **Estado**: `[x]` mergeado (PR #69)
- **Scope**: `SoftDeleteRepository[T]` con `get_by_id_including_deleted` y `soft_delete`; `LibroRepository`
- **Dependencias**: B3 · 🔓 Destraba: E3
- **Governance**: MEDIO
- **Leer antes**: `06_funcionalidades.md` §Ej. 6 · `05_reglas_de_negocio.md` RN-13

### [J1] `dockerfile-tp` · #54
- **Estado**: `[x]` mergeado (PR #67)
- **Scope**: `Dockerfile` (`python:3.12-alpine`, usuario sin privilegios, migraciones al arrancar, `HEALTHCHECK` con 127.0.0.1) y `.dockerignore` del **TP 1-4**
- **Dependencias**: ninguna · 🔓 Destraba: J2
- **Governance**: ALTO
- **Leer antes**: `11_entrega_y_despliegue.md` §La imagen

### [J2] `prueba-imagen` · #55
- **Estado**: `[x]` mergeado en `despliegue` (PR #74; el tablero dice *Todo*)
- **Scope**: probar la imagen en local y guardar la evidencia de D-01, D-05, D-06 y D-07
- **Dependencias**: J1 · 🔓 Destraba: E8
- **Governance**: ALTO
- **Leer antes**: `11_entrega_y_despliegue.md` · `06_funcionalidades.md` §Casos

---

## FASE 1 — Modelos y migraciones

> Compuerta: **una sola cadena de migraciones**. Sólo B6 genera la 3 y E6 escribe la 4 (DD-01).

### [E1] `movimientos-borrado-logico` · #19
- **Estado**: `[x]` mergeado (PR #68)
- **Scope**: `MovimientoStock`, `libro.borrado_en` e índice único parcial del ISBN
- **Dependencias**: E0 · 🔓 Destraba: B6, E3, R8
- **Governance**: CRITICO
- **Leer antes**: `04_modelo_de_datos.md` §movimiento_stock, §libro

### [H1] `modelos-usuarios` · #37
- **Estado**: `[x]` mergeado (PR #64)
- **Scope**: `Usuario`, `AsignacionRol`, `IntentoAcceso`, `EventoSeguridad`, `Cliente.usuario_id`
- **Dependencias**: E0 · 🔓 Destraba: B6, H3, H5, J7, R5, R8
- **Governance**: CRITICO
- **Leer antes**: `04_modelo_de_datos.md` · `03_actores_y_roles.md`

### [B6] `b6-migracion-3` · #35
- **Estado**: `[x]` mergeado (PR #76)
- **Scope**: migración 3 (`4a775b04f730`) autogenerada y leída: tablas de acceso, `movimiento_stock`, `cliente.usuario_id` y `libro.borrado_en` con los índices parciales; FK `cliente_usuario_id_fkey` nombrada a mano. Probado `upgrade head → downgrade base → upgrade head` y `alembic check`
- **Dependencias**: H1, E1 · 🔓 Destraba: E6
- **Governance**: CRITICO
- **Leer antes**: `04_modelo_de_datos.md` §Migraciones · `09_decisiones_y_supuestos.md` DD-01, DD-02

### [E6] `migracion-4-disparador` · #25
- **Estado**: `[x]` mergeado (PR #79)
- **Scope**: migración 4 **escrita a mano**: función y disparador que rechazan UPDATE y DELETE sobre `movimiento_stock` (RN-12), leída y comentada; ida y vuelta en una base vacía
- **Dependencias**: B6 · 🔓 Destraba: E7
- **Governance**: ALTO
- **Leer antes**: `05_reglas_de_negocio.md` RN-12 · `06_funcionalidades.md` §Ej. 2, §Ej. 7 · `04_modelo_de_datos.md` §Migraciones

---

## FASE 2 — Funcionalidad

> Casi todo espera **B4** (el UoW) y **R2** (`requiere_rol`). Con B4 y R2 hechos, cada frente avanza en paralelo.

### [H2] `security-bcrypt-jwt` · #38
- **Estado**: `[x]` mergeado (PR #71)
- **Scope**: bcrypt con costo configurable, `to_thread` y semáforo; emisión y verificación del JWT
- **Dependencias**: B1 · 🔓 Destraba: H3, H4, R1
- **Governance**: CRITICO
- **Leer antes**: `06_funcionalidades.md` §Ej. 4 · `08_arquitectura_propuesta.md` §Seguridad

### [H5] `intento-acceso-sesion-propia` · #41
- **Estado**: `[x]` mergeado (PR #72)
- **Scope**: `registrar_intento_acceso` con sesión y transacción propias y el comentario de las tres cosas (Ej. 7)
- **Dependencias**: H1 · 🔓 Destraba: H4
- **Governance**: CRITICO
- **Leer antes**: `09_decisiones_y_supuestos.md` DD-04 · `07_flujos_principales.md` §Flujo 2

### [H4] `h4-auth-login` · #40
- **Estado**: `[x]` mergeado (PR #75; **el tablero dice *Todo***)
- **Scope**: `POST /auth/login` con el límite de RN-07 (429 con `Retry-After`), hash ficticio de RN-08 y cookie `HttpOnly`; spec `autenticacion`
- **Dependencias**: H2, H5 · 🔓 Destraba: H6, H7
- **Governance**: CRITICO
- **Leer antes**: `07_flujos_principales.md` §Flujo 2 · `05_reglas_de_negocio.md` RN-07, RN-08

### [E3] `punto-unico-stock` · #21
- **Estado**: `[x]` mergeado (PR #70)
- **Scope**: `mover_stock` como único punto de escritura del stock, que deja el movimiento (RN-11)
- **Dependencias**: E1, E2 · 🔓 Destraba: E4, E5, J3, R8
- **Governance**: CRITICO
- **Leer antes**: `05_reglas_de_negocio.md` RN-11 · `04_modelo_de_datos.md` §Invariante

### [H3] `auth-registro` · #39
- **Estado**: `[~]` en revisión (PR listo)
- **Scope**: `POST /auth/registro`: hash antes de la transacción; usuario, rol CLIENTE y ficha en **un solo** bloque (RN-02); 409 sin filas sueltas ni apropiarse de la ficha (C-02)
- **Dependencias**: H1, H2, B4
- **Governance**: CRITICO
- **Leer antes**: `07_flujos_principales.md` §Flujo 3 · `05_reglas_de_negocio.md` RN-01, RN-02 · `06_funcionalidades.md` §Ej. 4

### [R1] `get-usuario-actual` · #45
- **Estado**: `[x]` mergeado (cubierto en PR #85)
- **Scope**: `app/core/dependencies.py`: `get_usuario_actual` desde la cookie `access_token`, con 401 (sin cookie, token inválido o vencido, usuario inexistente o inactivo); pide `Depends(get_session)` para compartir la sesión del UoW
- **Dependencias**: B4, H2 · 🔓 **Destraba: R2, R3, J5**
- **Governance**: CRITICO
- **Leer antes**: `03_actores_y_roles.md` §Cómo se decide un permiso · `07_flujos_principales.md` §Flujo 1 · `08_arquitectura_propuesta.md` §Estructura

### [R5] `roles-con-vigencia` · #49
- **Estado**: `[~]` en revisión (PR listo, change archivado en su rama)
- **Scope**: asignar (vencimiento opcional, con zona y en el futuro, si no 422) y revocar sin borrar la fila; reasignar uno vencido; autoprotección (RN-05, 409); evento en el mismo bloque (RN-16)
- **Dependencias**: H1, B4 · 🔓 Destraba: R2, R6, R9
- **Governance**: CRITICO
- **Leer antes**: `05_reglas_de_negocio.md` RN-03, RN-05, RN-16 · `07_flujos_principales.md` §Flujo 6 · `03_actores_y_roles.md`

### [R2] `requiere-rol` · #46
- **Estado**: `[~]` en revisión (PR listo, change archivado en su rama)
- **Scope**: `requiere_rol` con 403, consultando los roles vigentes en la base en cada petición (RN-04)
- **Dependencias**: R1, R5 · 🔓 **Destraba: E4, E5, J3, J7, R4, R7**
- **Governance**: CRITICO
- **Leer antes**: `05_reglas_de_negocio.md` RN-04 · `03_actores_y_roles.md` §RBAC

### [R3] `dos-grupos-de-rutas` · #47
- **Estado**: `[ ]` pendiente
- **Scope**: grupo abierto y grupo protegido en `main.py`, con el control del cambio obligatorio montado una vez (RN-06, 403); lo propio (RN-14). Ver IN-01: dónde queda `main.py`
- **Dependencias**: R1 · 🔓 Destraba: R9
- **Governance**: CRITICO
- **Leer antes**: `05_reglas_de_negocio.md` RN-06 · `02_descripcion_general.md` §API · `10_preguntas_abiertas.md` IN-01

### [R4] `alta-de-personal` · #48
- **Estado**: `[ ]` pendiente
- **Scope**: `POST /usuarios` con contraseña provisoria y `debe_cambiar_password`; evento de seguridad en el mismo bloque (RN-16)
- **Dependencias**: R2, B4 · 🔓 Destraba: H6, R6
- **Governance**: CRITICO
- **Leer antes**: `05_reglas_de_negocio.md` RN-16 · `03_actores_y_roles.md` · `07_flujos_principales.md` §Flujo 6

### [R6] `eventos-paginado` · #50
- **Estado**: `[ ]` pendiente
- **Scope**: `GET /eventos` paginado con el envoltorio (ADMIN)
- **Dependencias**: R4, R5, B5
- **Governance**: ALTO
- **Leer antes**: `04_modelo_de_datos.md` §evento_seguridad · `06_funcionalidades.md` §Ej. 3

### [R7] `proteger-catalogo` · #51
- **Estado**: `[ ]` pendiente
- **Scope**: altas y PATCH de editoriales, géneros y autores sólo para ADMIN; listados con el envoltorio
- **Dependencias**: R2, B5
- **Governance**: MEDIO
- **Leer antes**: `03_actores_y_roles.md` §RBAC · `06_funcionalidades.md` §Ej. 3 · `10_preguntas_abiertas.md` IN-02

### [H6] `auth-logout-yo-cambio` · #42
- **Estado**: `[~]` en revisión (PR listo, change archivado en su rama)
- **Scope**: `POST /auth/logout` (borra la cookie), `GET /auth/yo` (roles vigentes y los del token), `POST /auth/cambiar-password` (72 bytes; evento RN-16; no emite un token nuevo)
- **Dependencias**: H4, R4 · 🔓 Destraba: H7
- **Governance**: CRITICO
- **Leer antes**: `06_funcionalidades.md` §Ej. 4 · `05_reglas_de_negocio.md` RN-06, RN-16

### [E4] `libros-alta-patch-baja` · #23
- **Estado**: `[ ]` pendiente
- **Scope**: `POST /libros` con `stock_inicial` y su movimiento, `PATCH` sólo de título y precio, `DELETE` con borrado lógico (204), ISBN recargable (RN-13), envoltorio en el listado
- **Dependencias**: E3, R2 · 🔓 Destraba: E7
- **Governance**: MEDIO
- **Leer antes**: `07_flujos_principales.md` §Flujo 5 · `05_reglas_de_negocio.md` RN-01, RN-11, RN-13

### [E5] `reposicion-y-movimientos` · #24
- **Estado**: `[ ]` pendiente
- **Scope**: `POST /libros/{id}/reponer` (200, con su movimiento; 409 si está dado de baja) y `GET /libros/{id}/movimientos`
- **Dependencias**: E3, R2 · 🔓 Destraba: E7
- **Governance**: MEDIO
- **Leer antes**: `07_flujos_principales.md` §Flujo 5 · `05_reglas_de_negocio.md` RN-11, RN-13

### [J3] `venta-con-stock` · #56
- **Estado**: `[x]` mergeado (PR #87; falta `requiere_rol` de R2)
- **Scope**: `POST /ventas` en **un solo** bloque: precios, renglones, descuento por `mover_stock` y un movimiento por renglón (RN-09, RN-10); 409 sin escrituras si falta stock, cliente o libro (C-11, C-12)
- **Dependencias**: E3, R2, B4 · 🔓 Destraba: J4, J5, J8
- **Governance**: ALTO
- **Leer antes**: `07_flujos_principales.md` §Flujo 4 · `05_reglas_de_negocio.md` RN-09, RN-10, RN-11 · `04_modelo_de_datos.md` §Invariante

### [J4] `aviso-comprobante` · #57
- **Estado**: `[~]` en revisión (PR listo, change archivado en su rama)
- **Scope**: `BackgroundTasks` agendado sólo si la venta se confirmó, visible con el logger de uvicorn
- **Dependencias**: J3 · 🔓 Destraba: J8
- **Governance**: BAJO
- **Leer antes**: `06_funcionalidades.md` §Ej. 8 · `07_flujos_principales.md` §Flujo 4

### [J5] `detalle-venta-dueno` · #58
- **Estado**: `[~]` en revisión (PR listo, change archivado en su rama)
- **Scope**: `GET /ventas/{id}` con un número fijo de consultas (aunque el libro esté dado de baja); el servicio decide personal o dueño (403), sin `requiere_rol`
- **Dependencias**: J3, R1 · 🔓 Destraba: J6, J8
- **Governance**: ALTO
- **Leer antes**: `05_reglas_de_negocio.md` RN-14 · `02_descripcion_general.md` §API · `06_funcionalidades.md` §Ej. 8

### [J6] `mis-ventas-y-ventas` · #59
- **Estado**: `[~]` en revisión (PR listo, change archivado en su rama; falta `requiere_rol` de R2)
- **Scope**: `GET /mis-ventas` (autenticado) y `GET /ventas` (VENDEDOR o ADMIN) con el envoltorio
- **Dependencias**: J5, B5
- **Governance**: MEDIO
- **Leer antes**: `05_reglas_de_negocio.md` RN-14 · `06_funcionalidades.md` §Ej. 3

### [J7] `clientes-con-acceso` · #60
- **Estado**: `[ ]` pendiente
- **Scope**: el módulo clientes protegido (VENDEDOR o ADMIN), con `usuario_id` y el envoltorio
- **Dependencias**: H1, R2, B5
- **Governance**: MEDIO
- **Leer antes**: `03_actores_y_roles.md` §RBAC · `04_modelo_de_datos.md` §cliente

### [E8] `despliegue-vps` · #27
- **Estado**: `[ ]` pendiente
- **Scope**: el **TP 1-4** (rama `despliegue`, desde el tag `entrega-final`) en el VPS con `docker run --env-file`, en línea hasta que se publiquen las notas
- **Dependencias**: J1, J2 · 🔓 Destraba: E9
- **Governance**: ALTO
- **Leer antes**: `11_entrega_y_despliegue.md` · `09_decisiones_y_supuestos.md` DD-07

---

## FASE 3 — Cierre

### [R8] `seed-en-la-raiz` · #52
- **Estado**: `[ ]` pendiente — **disponible ahora**
- **Scope**: `seed.py` en la raíz con los datos de las págs. 19-20 (usuarios, catálogo, venta 1, movimientos que cumplen el invariante, línea `SISTEMA`); reemplaza a `scripts/seed.py`
- **Dependencias**: E1, H1, E3 · 🔓 **Destraba: H7, R9, J8**
- **Governance**: MEDIO
- **Leer antes**: `04_modelo_de_datos.md` §Seed data · `03_actores_y_roles.md` §Usuarios iniciales · `10_preguntas_abiertas.md` IN-01

### [H7] `auth-http` · #43
- **Estado**: `[ ]` pendiente
- **Scope**: `test/auth.http` con C-01 a C-05
- **Dependencias**: H3, H4, H6, R8
- **Governance**: BAJO
- **Leer antes**: `06_funcionalidades.md` §Casos

### [R9] `seguridad-http` · #53
- **Estado**: `[ ]` pendiente
- **Scope**: `test/seguridad.http` con C-06 a C-09 (varias sesiones con `# @name` y `# @no-cookie-jar`)
- **Dependencias**: R2, R3, R5, R8
- **Governance**: BAJO
- **Leer antes**: `06_funcionalidades.md` §Casos

### [J8] `ventas-http-c15` · #61
- **Estado**: `[ ]` pendiente
- **Scope**: `test/ventas.http` (C-10 a C-12) y evidencia de C-15 (las mismas consultas con 2 y con 4 renglones)
- **Dependencias**: J3, J4, J5, R8 · 🔓 Destraba: B7
- **Governance**: BAJO
- **Leer antes**: `06_funcionalidades.md` §Casos · `11_entrega_y_despliegue.md`

### [E7] `solo-agregado-y-http-libros` · #26
- **Estado**: `[~]` en revisión (PR #80, parcial: caso C-14; C-13 y C-16 van en otro PR)
- **Scope**: `test/solo_agregado.sql` (C-14), `.http` de libros (C-13, C-16) y captura de psql
- **Dependencias**: E4, E5, E6 · 🔓 Destraba: B7
- **Governance**: BAJO
- **Leer antes**: `06_funcionalidades.md` §Casos · `05_reglas_de_negocio.md` RN-12

### [E9] `deploy-md` · #28
- **Estado**: `[ ]` pendiente
- **Scope**: `DEPLOY.md` (URL, fecha, comandos sin el contenido de las variables, cambios al TP, cómo actualizar) y `evidencia/` de D-01 a D-08
- **Dependencias**: E8
- **Governance**: MEDIO
- **Leer antes**: `11_entrega_y_despliegue.md`

### [H8] `revision-rnf` · #44
- **Estado**: `[ ]` pendiente
- **Scope**: revisar los requisitos no funcionales: sin secretos, sin carga perezosa, sin 500 por entrada inválida, RN-15
- **Dependencias**: todas las de la fase 2 · 🔓 Destraba: E10
- **Governance**: ALTO
- **Leer antes**: `05_reglas_de_negocio.md` §Excepciones globales

### [I1] `integracion-base-nueva` · #62
- **Estado**: `[ ]` pendiente
- **Scope**: clon nuevo, `alembic upgrade head` sobre una base vacía, `python seed.py` y todos los `.http`
- **Dependencias**: todas las de la fase 2 · 🔓 Destraba: E10
- **Governance**: MEDIO
- **Leer antes**: `06_funcionalidades.md` §Casos · `11_entrega_y_despliegue.md`

### [B7] `readme-parcial` · #36
- **Estado**: `[ ]` pendiente
- **Scope**: `README.md` con integrantes y los pasos desde cero (entorno virtual, dependencias, `.env` y la clave de firma, migraciones, seed, arranque con `uvicorn main:app`)
- **Dependencias**: E7, J8 · 🔓 Destraba: E10
- **Governance**: BAJO
- **Leer antes**: `11_entrega_y_despliegue.md` §Formato de entrega · `09_decisiones_y_supuestos.md` DD-08

> **Paso previo a E10 — Mover `app/main.py` a `main.py` en la raíz (DD-08):**
> Una vez mergeados todos los routers de la fase 2 (y antes de cerrar I1, B7 y E10), mover `app/main.py` → `main.py` en la raíz siguiendo el checklist de `knowledge-base/09_decisiones_y_supuestos.md` (DD-08): arranque con `uvicorn main:app`, todos los `import app.modules...` arriba de `app = FastAPI(...)`, actualizar imports de `app.main` en tests/scripts/README y correr la suite de `unittest` y todos los `.http`.

### [E10] `zip-de-entrega` · #29
- **Estado**: `[ ]` pendiente
- **Scope**: `Parcial_Cap1a6_<Grupo>.zip` con `parcial/` y `despliegue/`, sin `.venv`, `__pycache__` ni `.env`
- **Dependencias**: B7, H8, I1
- **Governance**: ALTO
- **Leer antes**: `11_entrega_y_despliegue.md`

---

## Resumen

| Fase | Tareas | `[x]` | `[~]` | `[ ]` |
|---|---|---|---|---|
| 0 · Fundamentos | 9 | 8 | 1 | 0 |
| 1 · Modelos y migraciones | 4 | 4 | 0 | 0 |
| 2 · Funcionalidad | 21 | 4 | 0 | 17 |
| 3 · Cierre | 10 | 0 | 1 | 9 |
| **Total** | **44** | **16** | **2** | **26** |
