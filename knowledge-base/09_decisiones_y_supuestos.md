# Decisiones y Supuestos

Decisiones que ya tomó el grupo o que fija la consigna. Las de cada change están con más detalle en `openspec/changes/archive/*/design.md`.

## Decisiones documentadas

### DD-01 — Una sola cadena de migraciones
**Decisión:** sólo B6 genera la migración 3 (autogenerada) y E6 escribe la 4 (el disparador, a mano). Nadie más genera migraciones.
**Contexto:** con dos personas generando a la vez, Alembic queda con dos cabezas (`docs/flujo-de-trabajo.md`).
**Justificación:** la consigna pide exactamente dos migraciones nuevas sobre las del TP (pág. 10).
**Trade-offs aceptados:** los modelos de usuarios y de libros tienen que estar en `main` antes de B6.

### DD-02 — La FK `cliente.usuario_id` con nombre explícito
**Decisión:** la migración 3 nombra la FK `cliente_usuario_id_fkey`.
**Contexto:** autogenerate la dejó sin nombre y el downgrade no podía borrarla.
**Justificación:** es el nombre que PostgreSQL le pondría solo, así que la base queda igual.
**Trade-offs aceptados:** el downgrade de la 3 recrea el UNIQUE común del ISBN y falla si quedaron dos libros con el mismo ISBN (uno dado de baja). Change `b6-migracion-3`, PR #76.

### DD-03 — Unit of Work: confirma al salir y mensajes con `con_mensajes()`
**Decisión:** el UoW base no tiene `commit()` público. Al salir del bloque confirma, o revierte y traduce el `IntegrityError` a 409, con los mensajes que el servicio pasa con `uow.con_mensajes(unique=…, fk=…, check=…)`.
**Contexto:** el Ej. 6 (pág. 12) pide que el UoW confirme al salir del bloque.
**Alternativas consideradas:** pasar los mensajes al construir el UoW, que obliga al router a conocerlos.
**Justificación:** los mensajes son del servicio, y se reinician en cada bloque.
**Trade-offs aceptados:** las escrituras que después leen abren el UoW dos veces: un bloque para escribir y otro para leer. Change `b4-unit-of-work`, PR #77.

### DD-04 — El intento de acceso en su propia sesión
**Decisión:** `registrar_intento_acceso` abre sesión y transacción propias y confirma siempre.
**Contexto:** el fallo de login que hay que contar es el mismo que revierte la transacción de la petición (pág. 12).
**Trade-offs aceptados:** toma una conexión más y deja filas aunque la petición falle. Es la **única** excepción a la regla de una sesión por petición (change `h4-auth-login`, H5).

### DD-05 — Tests con `unittest`
**Decisión:** los tests automáticos van con `unittest` (`IsolatedAsyncioTestCase`, `TestClient`).
**Justificación:** pytest no está en `requirements.txt`, y el grupo no agrega dependencias por los tests.

### DD-06 — OpenSpec para cada tarea
**Decisión:** cada tarea arranca con `/opsx:propose` y se cierra con `/opsx:archive`. Las specs sincronizadas viven en `openspec/specs/`.
**Contexto:** OpenSpec se inicializó después de algunas tareas, así que `b6-migracion-3` es un change retroactivo y lo dice en su propuesta.

### DD-07 — Despliegue desde el tag `entrega-final`
**Decisión:** la rama `despliegue` sale del tag `entrega-final` (el TP 1-4 tal como se entregó) y nunca se mezcla con `main`.
**Justificación:** la consigna pide desplegar el TP sin las modificaciones del parcial (págs. 2, 14).

### DD-08 — `main.py` en `app/main.py` durante el desarrollo y movimiento a la raíz al cierre
**Decisión:** durante el desarrollo todos siguen registrando sus routers en `app/main.py`, y al final, antes de entregar, se mueve a `main.py` en la raíz como muestra el árbol de la estructura obligatoria (pág. 8). `seed.py` va en la raíz desde R8 (`python seed.py`, pág. 21).
**Motivo:** no generar conflictos en las ramas abiertas mientras el grupo desarrolla en paralelo.
**Checklist del movimiento final:**
1. Mover `app/main.py` a `main.py` en la raíz.
2. El arranque pasa a `uvicorn main:app`.
3. Todos los `import app.modules...` quedan **arriba**, antes de `app = FastAPI(...)`, porque la variable `app` y el paquete `app/` se llaman igual.
4. Actualizar todo lo que importe `app.main` (tests, scripts, `README.md`).
5. Correr los tests (`python -m unittest discover -s tests`) y los `.http` completos después de moverlo.

## Supuestos inferidos

### SU-01 — Las páginas citadas son las del pie del PDF
**Supuesto:** "pág. N" es la de "Página N de 24".
**Origen:** el PDF tiene 24 páginas numeradas.
**Riesgo si es falso:** una cita mal ubicada.
**Cómo validar:** abrir el PDF en la página.

### SU-02 — Quién implementa cada regla
**Supuesto:** la columna "Quién" de [05](05_reglas_de_negocio.md) sale del título y del cuerpo de cada issue. Las que no nombran la regla (por ejemplo, RN-09 con J3) se asignaron por el contenido de la issue.
**Riesgo si es falso:** que una regla quede sin responsable.
**Cómo validar:** revisarlo en la reunión del grupo.

### SU-03 — `tests/` no viola la estructura obligatoria
**Supuesto:** agregar la carpeta `tests/` (unittest) es válido, porque la consigna permite agregar y sólo exige `test/` con los `.http`.
**Cómo validar:** preguntarlo a la cátedra si hay dudas.
