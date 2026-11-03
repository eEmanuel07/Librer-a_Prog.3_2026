# Forma de trabajo del grupo — Parcial Cap. 1 a 6

Tablero: [Parcial Cap. 1 a 6 — Librería](https://github.com/users/eEmanuel07/projects/1)
Consigna: `Parcial_Cap1a6_Consigna.pdf` (la copia del grupo no se versiona).

## Quién hace qué

| Integrante | Frente | Ejercicios |
|---|---|---|
| Belén (`belcalvo93`) | Núcleo: `Settings`, lifespan, `BaseRepository`, `UnitOfWork`, paginación, migración 3, README | 1, 6, parte del 2 |
| Hernán (`mhernangonzalez32-gif`) | Autenticación: modelos de usuarios, bcrypt, JWT, login, registro; revisión final e integración | 4, parte del 7 |
| Bruno (`BrunoFiouchetta`) | Autorización: 401 y 403, roles con vigencia, rutas protegidas, eventos; `seed.py` | 5, parte del 3 |
| Elías (`eEmanuel07`) | Libros y stock, disparador de solo agregado, VPS y `DEPLOY.md`, armado del `.zip` | 3, 7, 10 |
| Joaquín (`joaquinmo1`) | Ventas y clientes, aviso del comprobante, Dockerfile e imagen | 8, 9, parte del 3 |

Cada tarea es una **issue** con un código (`[B3]`, `[H4]`…): la letra es de quien la hace. La issue dice qué hay que hacer, cuándo está hecha y de qué depende.

## Fases

1. **Fundamentos** (en paralelo, sin depender de nadie): `Settings`, repositorios y Unit of Work base, paginación, Dockerfile, acuerdo de nombres de relaciones.
2. **Modelos y migraciones** (compuerta): cuando estén los modelos de usuarios y de libros en `main`, Belén genera la migración 3 y después Elías escribe la 4 (el disparador). **Nadie más genera migraciones**: la cadena de Alembic es una sola.
3. **Funcionalidad**: autenticación, autorización, stock y ventas, en paralelo.
4. **Cierre**: `seed.py`, archivos `.http`, evidencias, README, integración y el `.zip`.

El campo **Fase** del tablero muestra en cuál está cada tarea.

## Flujo de una tarea

1. Tomá una issue tuya del tablero y pasala a **In Progress**.
2. Creá una rama desde `main` actualizado: `feat/<código>-<descripción>` (por ejemplo `feat/b3-base-repository`). Las de documentación y entrega, `docs/…`.
3. Commits chicos, en español y con ámbito: `feat(libros): …`, `fix(auth): …`, `docs: …`. Un commit por idea.
4. Abrí el PR a `main` con `Closes #<n>` en la descripción, así la issue se cierra sola.
5. **Otro integrante revisa y aprueba** antes de mergear. No se mergea el propio PR sin una aprobación (salvo un cambio trivial de documentación).
6. Se mergea con **merge común** (no squash), para que el historial muestre quién hizo qué.
7. Al mergear, la issue pasa a **Done**.

## Reglas del grupo

- **Una issue, una rama, un PR.** Si una tarea creció, se parte en dos issues.
- **`app/main.py` es el único archivo que todos tocan** (registro de routers). Si hay conflicto, se resuelve dejando las líneas de todos.
- **Migraciones**: se lee cada una antes de aplicarla y lleva un comentario que lo diga. Si hubo que corregir la generada, el comentario lo explica. Antes de subirla se prueba `upgrade head`, `downgrade base` y `upgrade head`.
- **Sin secretos en el repositorio**: nunca `.env`, contraseñas ni la clave de firma, ni siquiera como valor por defecto. Si algo se subió por error, avisar: sigue en el historial y hay que cambiarlo.
- **Bloqueos**: si una issue depende de otra que no está, comentalo en la issue y avisá en el grupo. No se adelanta trabajo ajeno sin acordarlo.

## Una tarea está hecha cuando

- El código cumple lo que dice la issue, con sus códigos HTTP y sin devolver texto interno de la base.
- Tiene su caso en un archivo `.http` en `test/`, con la respuesta esperada en un comentario, y corre después de `python seed.py`.
- Ningún handler bloquea (`async def`, bcrypt fuera del bucle) y ninguna entrada inválida termina en un 500.
- Pasó la revisión de otro integrante y está mergeada en `main`.

## Entrega

Un solo `.zip` por grupo, `Parcial_Cap1a6_<Grupo>.zip`, con dos carpetas: `parcial/` (el proyecto ampliado) y `despliegue/` (el TP de los capítulos 1 a 4 con su Dockerfile). Sin `.venv`, `__pycache__` ni `.env`. Lo arma Elías; lo sube un solo integrante al campus. La fecha límite la publica el campus: anotarla en el tablero cuando se conozca.
