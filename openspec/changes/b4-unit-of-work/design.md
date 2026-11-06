# Design: b4-unit-of-work

## Context

Ver `proposal.md` (Why). Estado actual, observado en el código:

- `app/core/uow.py`:
  - `UnitOfWork(session)` construye los 6 repositorios;
  - `__aexit__` solo revierte si hubo error;
  - `commit(detalle_unique=..., detalle_fk=..., detalle_check=...)` confirma y traduce `IntegrityError` con `conflicto_por_integridad` (`app/core/errors.py`, por `sqlstate`);
  - `get_uow` abre el UoW dentro de la dependencia.
- **Repositorios:** casi todos los `agregar(...)` de los módulos solo hacen `session.add` (sin flush). `BaseRepository.add/update/delete` y `SoftDeleteRepository.soft_delete` hacen `flush()`. Por eso un `IntegrityError` puede saltar **dentro** del bloque (por un flush explícito, o por el autoflush al hacer una consulta) o recién **en el commit**.
- **Services:** hoy confirman y **después leen**, con el id ya generado:
  - `crear_cliente` → `obtener_cliente(uow, cliente.id)`;
  - `crear_libro` → `obtener_libro(uow, libro.id)`;
  - `crear_venta` → `obtener_venta(uow, venta.id)`.

  Los demás devuelven `XRead.model_validate(entidad)`. La fábrica usa `expire_on_commit=False`, así que los objetos siguen usables después del commit.
- **Usuarios** (H4): `UsuarioUnitOfWork(UnitOfWork)` hereda hoy los 6 repositorios sin usarlos. `get_usuario_uow` ya construye sin abrir, y `login` abre el mismo UoW dos veces.
- **Tests:** los 12 tests (`tests/`) usan `_AsyncSessionAdapter` sobre una sesión sync de SQLite, con `add`, `flush`, `commit`, `rollback`, `exec` y `get`.
- **Sesión:** `get_session` hace una sesión por petición desde `app.state.session_factory`. FastAPI cachea cada dependencia **por petición**, así que todas las dependencias que piden `get_session` reciben el mismo objeto.

## Goals / Non-Goals

**Goals:**
- Cumplir el Ej. 6 y la estructura de la pág. 8 sin cambiar ningún contrato HTTP.
- Que la app funcione y los tests pasen **en cada commit** (migración gradual, un módulo por vez).

**Non-Goals:**
- Implementar `get_usuario_actual` o la verificación de rol (tarea R1, de Bruno).
- Cambiar repositorios, modelos, schemas o mensajes de error.
- Tocar `registrar_intento_acceso` (sesión propia a propósito, Ej. 7).

## Decisions

### 1. Comportamiento del `UnitOfWork` base (`app/core/unit_of_work.py`)

```python
class UnitOfWork:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self._mensajes = _MENSAJES_POR_DEFECTO

    def con_mensajes(self, *, unique=None, fk=None, check=None) -> Self: ...

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(self, tipo, error, traza) -> bool:
        # 1. error dentro del bloque  -> rollback; si era IntegrityError, se lanza Conflicto
        # 2. sin error               -> commit; si el commit da IntegrityError -> rollback + Conflicto
        # 3. siempre: vuelve a los mensajes por defecto; NUNCA cierra la sesión
```

- **No cierra la sesión** porque no la creó: la cierra `get_session` al terminar la petición.
- **Se puede abrir más de una vez:** no guarda estado de "abierto". Cada bloque es una transacción: confirma al salir y la próxima consulta empieza otra. Es lo que ya hace el login de usuarios.
- **No se anida:** abrir un bloque dentro de otro con el mismo UoW queda prohibido por convención (se documenta en el docstring). No se agrega un control en tiempo de ejecución.
- **`IntegrityError` dentro del bloque:** `__aexit__` lo reemplaza por `Conflicto` con `raise ... from None`, el mismo patrón de hoy. Así no aparece la traza de la base.
- **Alternativa descartada:** mantener `commit()` como método público. Contradice "confirma al salir del bloque" y deja dos formas de confirmar.

### 2. Mensajes del 409: `con_mensajes(...)` devuelve `self`

```python
async with uow.con_mensajes(unique=_DETALLE_UNIQUE):
    uow.editoriales.agregar(editorial)
```

- Son los mismos tres parámetros de hoy (`unique`, `fk`, `check`). Si falta alguno, se usa el mensaje por defecto de `conflicto_por_integridad`.
- **Se reinician al salir** del bloque, para que una segunda apertura (por ejemplo, la lectura) no herede mensajes ajenos.
- **Alternativas descartadas:**
  - *pasar los mensajes al construir el UoW*: el router los tendría que conocer, pero son del service;
  - *atributos que se asignan a mano*: es fácil olvidarse de reiniciarlos.

### 3. Escribir en un bloque y leer en otro

Los services que leen después de escribir abren el UoW **dos veces**:

```python
async def crear_cliente(uow: ClienteUnitOfWork, datos: ClienteCreate) -> ClienteRead:
    cliente = Cliente(**datos.model_dump())
    async with uow.con_mensajes(unique=_DETALLE_UNIQUE_EMAIL):
        uow.clientes.agregar(cliente)
    return await obtener_cliente(uow, cliente.id)   # obtener_cliente abre su propio bloque
```

- **Cada escritura va entera en un solo bloque `async with`.** Todo lo que la operación escribe (filas, renglones, movimientos o registros de auditoría que tienen que quedar juntos) se agrega dentro del **mismo** bloque, y se confirma o se revierte todo junto. Esto vale en particular para las escrituras que nombra el Ej. 6, con la numeración de la tabla de reglas del **parcial** (consigna, págs. 6-7). El código todavía tiene los números del TP viejo; por ejemplo, el RN-10 de `app/core/pagination.py` es otra regla.
  - **RN-02** (tarea H3, Hernán): el auto-registro crea el usuario, su rol `CLIENTE` y su ficha de cliente. O quedan las tres filas o ninguna. Si ya existe un cliente con ese correo, responde 409 sin apropiarse de la ficha.
  - **RN-10** (tarea J3, Joaquín): registrar una venta descuenta el stock de cada libro y deja un movimiento por renglón. Si un libro no alcanza, no queda ninguna escritura.
  - **RN-16** (tareas R4 y R5, Bruno): cada alta de personal, cambio de rol y cambio de contraseña deja una línea en `evento_seguridad` en la misma transacción.

  **B4 no implementa esas operaciones:** deja el UoW listo para que cada una se escriba en **un solo** bloque `async with`, sin repartirse en dos. El segundo bloque solo **lee** lo que ya se confirmó; no escribe nada, así que no parte la escritura en dos transacciones. Si una operación tiene que escribir algo más, ese algo va en el primer bloque, nunca en el de lectura.
- **Por qué:** se mantiene el comportamiento de hoy. Recién se lee, y se arma el 201, cuando el commit funcionó. Además el id ya existe (con `agregar` solo, sin flush, `cliente.id` sería `None` dentro del bloque).
- **Regla para cada service:** toda función pública abre su propio `async with uow`. Las auxiliares privadas (`_buscar`, `_buscar_cliente`) no lo abren: se llaman dentro de un bloque. Una pública puede llamar a otra pública solo **después** de cerrar su bloque, nunca adentro.
- **Lecturas puras (GET):** también abren `async with uow`. Al salir se confirma una transacción que solo leyó, lo que no tiene efectos.
- **Alternativa descartada:** hacer `flush()` dentro del bloque y leer ahí mismo. Si el commit fallara al salir, se habría armado la respuesta para nada. Además cambiaría el momento en que salta el 409 en cada service.

### 4. Un Unit of Work por módulo

`app/modules/<módulo>/unit_of_work.py`, siguiendo el formato del de usuarios:

| Módulo | Clase | Repositorios |
|---|---|---|
| editoriales | `EditorialUnitOfWork` | `editoriales` |
| generos | `GeneroUnitOfWork` | `generos` |
| autores | `AutorUnitOfWork` | `autores` |
| libros | `LibroUnitOfWork` | `libros` |
| clientes | `ClienteUnitOfWork` | `clientes` |
| ventas | `VentaUnitOfWork` | `ventas`, `libros` (lee los precios) |

Cada uno tiene `get_<módulo>_uow(session = Depends(get_session))`, que lo **construye sin abrirlo** (función común, no generador). Los nombres de atributo (`uow.clientes`, `uow.libros`, …) son los de hoy, así que las consultas dentro de los services no cambian.

### 5. Sesión compartida (y lo que queda preparado para R1)

- No hace falta código nuevo: alcanza con que **toda** dependencia que necesite la base pida `Depends(get_session)` y nunca abra la fábrica por su cuenta. FastAPI resuelve `get_session` una sola vez por petición y le entrega el mismo objeto al `get_<módulo>_uow` y a `get_usuario_actual`.
- **R1 (`get_usuario_actual`) es de Bruno: este change no escribe código de esa dependencia ni de la verificación de rol.** Solo deja una nota en el **docstring de `get_session`** (`app/core/database.py`): *"`get_usuario_actual` (y la verificación de rol) tiene que pedir `session: AsyncSession = Depends(get_session)`. Así FastAPI le da la misma sesión que al Unit of Work y la petición usa una sola conexión."*
- **Cómo se prueba sin R1:** un test arma una app con una ruta que recibe `get_editorial_uow` y una dependencia de prueba que pide `get_session`. Verifica dos cosas: que `uow.session is session`, y que una `session_factory` falsa que cuenta sus llamadas fue llamada **una sola vez** en la petición.

### 6. El 409 por CHECK se prueba con un test unitario del base

Desde la API no se puede provocar un rechazo por CHECK: el schema valida antes (por ejemplo, `precio > 0`) y responde **422** sin llegar a la base. Por eso el 409 por CHECK se prueba con un **test unitario del `UnitOfWork` base**. El test lanza un `IntegrityError` con `sqlstate` 23514 dentro del bloque y en el commit, y comprueba que sale un `Conflicto` con el mensaje `check` pedido. La unicidad y la clave foránea sí se prueban además desde la API (`.http`).
- **Alternativa descartada:** saltear el schema solo para provocar el CHECK. Habría que cambiar un contrato que no es parte de este change.

### 7. Orden de commits: la app funciona en cada uno

Durante la migración conviven los dos archivos: `app/core/uow.py` (viejo) y `app/core/unit_of_work.py` (nuevo). Cada módulo pasa al nuevo en su propio commit. El viejo se borra al final, cuando nadie lo importa. El orden y lo que se prueba en cada commit están en `tasks.md`.

## Risks / Trade-offs

- **[Riesgo] Quedan llamadas a `uow.commit` o a `get_uow`** → al borrar `uow.py` falla el import y la app no arranca. **Mitigación:** antes del último commit, `grep -rn "uow.commit\|get_uow\|app.core.uow" app tests` tiene que dar vacío.
- **[Riesgo] La lectura se mueve adentro del bloque de escritura** → se arma la respuesta antes de confirmar, o `id` queda en `None`. **Mitigación:** la regla de la decisión 3 y un test por service con alta.
- **[Riesgo] Se anida `async with uow` (una pública llamada dentro del bloque de otra)** → el bloque interno confirmaría a mitad de la operación. **Mitigación:** queda prohibido por convención (decisión 3) y se revisa en cada commit de módulo.
- **[Trade-off] Los GET confirman una transacción vacía al salir** → no tiene costo apreciable, y a cambio hay una sola forma de usar el UoW.
- **[Riesgo] Los tests de usuarios dependen de `_AsyncSessionAdapter`** → el base nuevo solo usa `commit` y `rollback`, que el adaptador ya tiene. **Mitigación:** correr los 12 tests en el commit del base y en el de usuarios.
- **[Trade-off] El CHECK no se puede provocar desde la API** → se cubre con el test unitario del base (decisión 6).

## Migration Plan

Commits en el orden de `tasks.md`. **Rollback:** como cada commit deja la app funcionando, alcanza con revertir el último commit con problemas (`git revert`). No hay cambios en la base de datos.

## UI Mockups

- Decision: no (no UI) — 2026-11-05. El change solo reorganiza la capa de transacciones.
