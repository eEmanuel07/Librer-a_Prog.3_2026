# Librería — Parcial Programación III (Capítulos 1 a 6)

API REST asincrónica de una librería con catálogo público, gestión de clientes y ventas, autenticación con contraseñas en `bcrypt` y token JWT en cookie `HttpOnly`, autorización por roles con vigencia en la base de datos (`ADMIN`, `VENDEDOR`, `CLIENTE`), auditoría de seguridad, movimientos de stock de sólo agregado, borrado lógico y arquitectura en capas con repositorios y Unit of Work.

**Integrantes:**
- Belén Calvo
- Elías Tello
- Hernán González
- Bruno Fiouchetta
- Joaquín Moran

---

## Requisitos

| Componente | Versión mínima | Uso |
|---|---|---|
| Python | 3.12 | Lenguaje |
| FastAPI | 0.111 (`fastapi[standard]`) | Framework web asincrónico (`async def`) y servidor ASGI `uvicorn` |
| SQLModel | 0.0.24 | Modelos de tabla |
| SQLAlchemy | 2.0 asincrónico (`>=2.0,<2.1`) | Motor, sesión asincrónica y carga anticipada |
| asyncpg | 0.30 | Controlador asincrónico de PostgreSQL |
| PostgreSQL | 16 | Base de datos (contenedor local `libreria-db`) |
| Alembic | 1.13 | Migraciones del esquema (plantilla asincrónica) |
| pydantic-settings | 2.0 | Configuración tipada leída desde el entorno o `.env` |
| bcrypt | 4.0 | Hash de contraseñas fuera del bucle de eventos |
| PyJWT | 2.8 | Emisión y verificación de tokens firmados |
| Docker | 20.10 | Contenedor de PostgreSQL 16 para desarrollo local |

---

## Pasos para levantar el proyecto desde cero

### 1. Clonar el repositorio y crear el entorno virtual

```bash
git clone https://github.com/eEmanuel07/Librer-a_Prog.3_2026.git
cd Librer-a_Prog.3_2026
python -m venv .venv
```

Activar el entorno virtual según la terminal:

```bash
# Git Bash (Windows)
source .venv/Scripts/activate
```

```powershell
# PowerShell (Windows)
.venv\Scripts\Activate.ps1
```

```cmd
:: CMD (Windows)
.venv\Scripts\activate.bat
```

```bash
# Linux / macOS
source .venv/bin/activate
```

Instalar las dependencias:

```bash
pip install -r requirements.txt
```

### 2. Configurar las variables de entorno (`.env`)

Copiar la plantilla `env.example` como `.env` (el archivo `.env` está en `.gitignore` y **nunca** se sube al repositorio):

```bash
cp env.example .env
```

Generar una clave aleatoria de al menos 32 caracteres para `JWT_SECRET`:

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Completar en `.env` al menos `POSTGRES_PASSWORD` y `JWT_SECRET`. La configuración la valida la clase `Settings` (`app/core/config.py`, con `pydantic-settings`) al arrancar:

| Variable | Por defecto | Descripción |
|---|---|---|
| `POSTGRES_USER` | `postgres` | Usuario de PostgreSQL. |
| `POSTGRES_PASSWORD` | *(sin valor por defecto)* | **Obligatoria.** Contraseña de PostgreSQL (debe coincidir con la del contenedor `libreria-db`). |
| `POSTGRES_DB` | `libreria` | Nombre de la base de datos. |
| `POSTGRES_HOST` | `localhost` | Host donde escucha PostgreSQL. |
| `POSTGRES_PORT` | `5432` | Puerto de PostgreSQL en la máquina local (usar `5433` si se mapeó el contenedor a ese puerto). |
| `DB_POOL_SIZE` | `5` | Conexiones permanentes del pool del motor asincrónico (`>= 1`). |
| `DB_MAX_OVERFLOW` | `10` | Conexiones adicionales permitidas en picos de carga (`>= 0`). |
| `SQL_ECHO` | `false` | Con `true` imprime en consola cada consulta SQL ejecutada (útil para verificar el caso C-15). |
| `JWT_SECRET` | *(sin valor por defecto)* | **Obligatoria (mínimo 32 caracteres).** Clave de firma de los tokens JWT. |
| `JWT_EXPIRA_MINUTOS` | `30` | Duración del token JWT y `Max-Age` de la cookie `access_token`, en minutos. |
| `COOKIE_SECURE` | `false` | `true` sólo detrás de HTTPS; en desarrollo local (`http://localhost`) debe ser `false`. |
| `BCRYPT_COSTO` | `12` | Factor de costo de `bcrypt` (`4` a `31`). |
| `BCRYPT_CONCURRENCIA` | `4` | Máximo de hashes `bcrypt` ejecutándose en paralelo bajo el semáforo. |

La dirección de conexión (`database_url`) se construye automáticamente en `Settings` con un `@computed_field(repr=False)` y el driver `postgresql+asyncpg` a partir de las variables `POSTGRES_*`. Si falta `POSTGRES_PASSWORD` o `JWT_SECRET` (o si `JWT_SECRET` tiene menos de 32 caracteres), la aplicación no arranca e informa qué variable falta sin exponer valores leídos.

### 3. Levantar PostgreSQL 16 en Docker

Crear y arrancar el contenedor `libreria-db` con PostgreSQL 16 (usando en `POSTGRES_PASSWORD` el mismo valor configurado en `.env`):

```bash
docker run --name libreria-db -e POSTGRES_USER=postgres -e POSTGRES_PASSWORD=<tu_contraseña> -e POSTGRES_DB=libreria -p 5432:5432 -d postgres:16
```

Si el puerto `5432` local ya está ocupado por otra instancia de PostgreSQL, mapear otro puerto (por ejemplo `-p 5433:5432`) y colocar `POSTGRES_PORT=5433` en `.env`.

En los inicios siguientes basta con arrancar el contenedor existente:

```bash
docker start libreria-db
```

### 4. Aplicar las migraciones con Alembic

```bash
alembic upgrade head
```

Alembic toma la URL de conexión directamente desde `Settings` (`migrations/env.py`), nunca desde `alembic.ini`. El comando aplica las 4 migraciones de `migrations/versions/`:
1. `24071e705bcf` — esquema inicial del TP (`editorial`, `autor`, `libro`, `libro_autor`, `cliente`, `perfil_cliente`, `venta`, `renglon_venta`).
2. `0efd84a6de03` — tabla `genero` y clave foránea `libro.genero_id`.
3. `4a775b04f730` — tablas de acceso (`usuario`, `asignacion_rol`, `intento_acceso`, `evento_seguridad`), tabla `movimiento_stock`, columnas `cliente.usuario_id` y `libro.borrado_en`, e índices únicos parciales (`asignacion_rol` activa y `libro.isbn` entre vigentes).
4. `314ce2736bff` — función y disparador `trg_movimiento_stock_solo_agregado` que rechaza cualquier `UPDATE` o `DELETE` sobre `movimiento_stock` (RN-12).

### 5. Cargar los datos iniciales (`seed.py`)

Desde la raíz del repositorio:

```bash
python seed.py
```

> **Atención:** `seed.py` vacía todas las tablas del proyecto con `TRUNCATE TABLE ... RESTART IDENTITY CASCADE` (los `id` vuelven a empezar en `1`) y carga el estado inicial conocido de la consigna (págs. 19-20). Correrlo varias veces deja siempre el mismo resultado.

Datos que carga `python seed.py`:

- **Usuarios iniciales y asignaciones de rol vigentes:**

  | ID | Correo | Nombre | Rol vigente | `debe_cambiar_password` |
  |---|---|---|---|---|
  | 1 | `admin@example.com` | Administrador Principal | `ADMIN` | `false` |
  | 2 | `admin2@example.com` | Administrador Secundario | `ADMIN` | `false` |
  | 3 | `vendedor@example.com` | Vendedor Mostrador | `VENDEDOR` | `false` |
  | 4 | `ana@example.com` | Ana Paz | `CLIENTE` (vinculada a la clienta 3) | `false` |
  | 5 | `nuevo@example.com` | Vendedor Nuevo | `VENDEDOR` | `true` (cambio obligatorio pendiente) |

  Las contraseñas de prueba son ficticias y viven únicamente en `seed.py` (diccionario `CONTRASENAS_PRUEBA`), tal como pide la consigna (pág. 19). Los archivos `test/auth.http` y `test/seguridad.http` ya las tienen configuradas en sus pedidos de login.

- **Catálogo:** 3 editoriales (`Sudamericana`, `Alfaguara`, `Emecé`), 3 géneros (`Novela`, `Cuento`, `Ensayo`), 6 autores (`Julio Cortázar`, `Ricardo Piglia`, `Silvina Ocampo`, `Adolfo Bioy Casares`, `Jorge Luis Borges`, `Ernesto Sabato`) y 5 libros con su stock final: `Rayuela` (`10`), `Ficciones` (`8`), `Bestiario` (`1`), `Respiración artificial` (`3`) y `Antología de la literatura fantástica` (`5`).
- **Clientes:** `Lucía Fernández` (id 1, con `PerfilCliente`, sin usuario), `Tomás Ríos` (id 2, sin perfil ni usuario) y `Ana Paz` (id 3, vinculada al usuario `ana@example.com`).
- **Venta inicial y movimientos de stock:** 5 movimientos de entrada `"Stock inicial"` (`+11`, `+10`, `+1`, `+3`, `+5`) y la **venta 1** de Lucía Fernández registrada por `vendedor@example.com` (1 `Rayuela` y 2 `Ficciones`, total `$69000.00`) con sus 2 movimientos de salida (`-1` y `-2`), cumpliendo que para cada libro `stock` es igual a la suma de `cantidad` de sus movimientos (RN-11).
- **Historial de seguridad:** 1 fila inicial en `evento_seguridad` con `actor="SISTEMA"` y `accion="Carga de los datos iniciales"` (RN-16).

### 6. Arrancar el servidor

```bash
uvicorn app.main:app --reload
```

- Documentación interactiva (Swagger UI): http://localhost:8000/docs
- Chequeo de vida (no toca la base): http://localhost:8000/health/live
- Chequeo de disponibilidad (`SELECT 1` contra PostgreSQL): http://localhost:8000/health/ready

---

## Cómo correr las pruebas

### 1. Suite de pruebas automáticas (`unittest`)

El proyecto usa `unittest` de la biblioteca estándar (`IsolatedAsyncioTestCase` y `fastapi.testclient.TestClient`, sin depender de `pytest`):

```bash
python -m unittest discover -s tests
```

Cubre configuración (`Settings`), ciclo de vida (`lifespan`), endpoints `/health/live` y `/health/ready`, `BaseRepository[T]`, `SoftDeleteRepository[T]`, `UnitOfWork` y sesión compartida por petición, paginación con envoltorio, `bcrypt` y JWT, `registrar_intento_acceso` en sesión propia, registro (`RN-02`), login con límite de intentos (`RN-07`) y hash ficticio (`RN-08`), logout / `/auth/yo` / cambio de contraseña (`RN-16`), `get_usuario_actual`, `requiere_rol` (`RN-04`), dos grupos de rutas y cambio obligatorio (`RN-06`), alta de personal (`RN-16`), roles con vigencia y autoprotección (`RN-03`, `RN-05`, `RN-16`), `/eventos`, protección del catálogo (`ADMIN`), libros (`mover_stock`, alta, `PATCH`, baja lógica e ISBN reutilizable `RN-11`, `RN-13`), ventas con descuento de stock (`RN-09`, `RN-10`), aviso en segundo plano (`BackgroundTasks`), detalle de venta sin N+1 y control de dueño (`RN-14`), `/mis-ventas` y `/ventas`, y `seed.py`.

### 2. Casos de prueba en `test/` (`.http` y `.sql`)

Los archivos `.http` de la carpeta `test/` se abren en VS Code con la extensión **REST Client** y se ejecutan con *Send Request* sobre `http://localhost:8000`. Antes de correr cada archivo conviene restablecer el estado inicial:

```bash
python seed.py
```

En `test/seguridad.http`, cada login se nombra con `# @name` (`loginAdmin`, `loginVendedor`, `loginAna`, `loginNuevo`) y los pedidos siguientes usan `# @no-cookie-jar` con el encabezado `Cookie: {{loginX.response.headers.Set-Cookie}}` para mantener varias sesiones abiertas al mismo tiempo (pág. 23 de la consigna).

El caso **C-14** (`test/solo_agregado.sql`) se ejecuta directamente con `psql` contra la base local:

```bash
psql -X -e -v ON_ERROR_STOP=0 -h localhost -U postgres -d libreria -f test/solo_agregado.sql
```

| Archivo | Casos de la consigna | Qué verifica en `main` |
|---|---|---|
| `test/auth.http` | **C-01 a C-05** (y flujo H6) | **C-01:** validación de contrato estricto (`422` por email inválido, contraseña `> 72` bytes UTF-8 en `bcrypt` y campos extra con `extra="forbid"`). **C-02:** auto-registro en `POST /auth/registro` (`201`) y rechazo con `409` y mensaje propio ante email repetido de usuario o de cliente sin dejar filas sueltas ni apropiarse de la ficha (`RN-02`). **C-03:** `POST /auth/login` emite la cookie `access_token` con `HttpOnly`, `SameSite=lax` y `Max-Age` sin enviar el token en el cuerpo JSON. **C-04:** `401` con el mismo cuerpo y tiempo parejo para contraseña incorrecta y para correo inexistente (hash ficticio, `RN-08`). **C-05:** después de 5 intentos fallidos en 60 s, el 6.º intento responde `429` con `Retry-After` sin calcular `bcrypt` (`RN-07`). Incluye además `GET /auth/yo`, `POST /auth/cambiar-password` y `POST /auth/logout`. |
| `test/seguridad.http` | **C-06 a C-09** | **C-06:** `401` sin sesión vs. `403` autenticado sin el rol requerido (`VENDEDOR` intentando escrituras de `ADMIN` o `GET /eventos`), y acceso a lo propio (`RN-14`): `ana@example.com` consulta `GET /mis-ventas` (`200`) y recibe `403` en `GET /ventas/1` (que es de Lucía), mientras que el vendedor sí la ve (`200`). **C-07:** revocación de rol con sesión abierta (`DELETE /usuarios/3/roles/VENDEDOR` → `200`); en el pedido siguiente la misma cookie recibe `403` (`RN-04`) y `GET /auth/yo` muestra `"roles": []` vs. `"roles_token": ["VENDEDOR"]`. **C-08:** autoprotección de `ADMIN` (`DELETE /usuarios/1/roles/ADMIN` → `409`, `RN-05`), rol vigente duplicado (`409`, `RN-03`) y vencimientos inválidos sin zona horaria o en el pasado (`422`). **C-09:** `nuevo@example.com` con cambio obligatorio pendiente recibe `403` en el grupo protegido (`GET /ventas/`, `GET /mis-ventas`), puede usar `/auth/yo` y `POST /auth/cambiar-password` (`200`), y con la misma cookie pasa a acceder a las rutas protegidas (`200`, `RN-06`); consulta final de `GET /eventos` paginado (`RN-16`). |
| `test/solo_agregado.sql` | **C-14** | Verifica en `psql` que el disparador `trg_movimiento_stock_solo_agregado` está instalado, permite `INSERT` en `movimiento_stock` y rechaza tanto `UPDATE` como `DELETE` con `SQLSTATE 23001` (`RN-12`). Corre dentro de una transacción con `SAVEPOINT` y termina en `ROLLBACK` sin alterar los datos del `seed.py`. |
| `test/ventas.http` | Base del TP · **C-10 a C-12: pendiente (J8)** | Hoy contiene los pedidos del TP (alta de venta con dos renglones copiando precios y calculando el total en el servidor, detalle sin N+1, listado, `409` por cliente o libro inexistente, `422` por renglones vacíos, libro repetido, `precio_unitario` o `total` en el cuerpo, cantidad `<= 0`, id no entero y `405` ante `PATCH`). La actualización de este archivo con la sesión autenticada y los casos **C-10, C-11 y C-12** del parcial está **pendiente (J8)**. |
| `test/libros.http` | Base del TP (`C-01` de ruta) · **C-13 y C-16: pendiente (E7)** | Hoy contiene los pedidos del TP (alta con autores y género, `409` por ISBN repetido o FK inexistente, `422` por precio/stock/rol inválidos, detalle sin N+1, `C-01` de parámetro de ruta no entero con `422`, búsqueda por título sin distinguir mayúsculas, intento de inyección SQL `' OR '1'='1` con parámetros ligados y `PATCH` parcial). La actualización de este archivo con sesión `ADMIN`, envoltorio de paginación y los casos **C-13 y C-16** completos del parcial está **pendiente (E7)**. |
| `test/clientes.http` | Pruebas del módulo clientes (**protección y envoltorio: pendiente J7**) | Alta y detalle de clientes, unicidad de email (`409` normalizado a minúsculas), `PATCH` parcial, creación de `PerfilCliente` (`409` si ya tiene perfil, `404` si el cliente no existe) y ventas de un cliente (`GET /clientes/{id}/ventas`). |
| `test/editoriales.http` | Pruebas del módulo editoriales | Alta, unicidad de nombre (`409`), listado, detalle, `C-01` de id no entero (`422`), `PATCH` parcial y listado de libros de una editorial. |
| `test/generos.http` | Pruebas del módulo géneros | Alta, unicidad de nombre (`409`), listado, libros por género y `C-01` de id no entero (`422`). |
| `test/autores.http` | Pruebas del módulo autores | Alta, validaciones `422`, detalle, `C-01` de id no entero (`422`), `PATCH` parcial y libros de un autor con rol y orden de autoría. |
| `test/health.http` | Salud de la aplicación | `GET /health/live` (`200 {"estado": "vivo"}`) y `GET /health/ready` (`200 {"estado": "listo", "base": "ok"}`). |

---

## Estructura del proyecto

```text
app/
  core/
    config.py          Settings con pydantic-settings y @computed_field database_url
    database.py        crear_motor (con pool), crear_fabrica_sesiones y get_session
    security.py        bcrypt fuera del bucle (to_thread + semáforo), hash ficticio y JWT
    dependencies.py    get_usuario_actual (401), verificar_cambio_password_pendiente (403) y requiere_rol (403)
    repository.py      BaseRepository[T] y SoftDeleteRepository[T] (flush, nunca commit)
    paginacion.py      Envoltorio Pagina[T] ({items, total, page, size, pages}) y cálculo de páginas (422)
    pagination.py      Paginación limit/offset del TP (usada aún por clientes hasta cerrar J7)
    unit_of_work.py    UnitOfWork base: confirma al salir, revierte ante error y traduce IntegrityError
    errors.py          Errores de dominio (NoEncontrado, Conflicto, SinPermiso) y traducción de restricciones
  modules/
    health/
      router.py        GET /health/live y GET /health/ready (único archivo del módulo)
    usuarios/          Usuario, AsignacionRol, IntentoAcceso y EventoSeguridad
    editoriales/       Editorial
    generos/           Genero
    autores/           Autor
    libros/            Libro, LibroAutor y MovimientoStock (con mover_stock como punto único)
    clientes/          Cliente y PerfilCliente
    ventas/            Venta y RenglonVenta
      models.py        Modelos SQLModel, restricciones e índices
      schemas.py       Contratos DTO de entrada (extra="forbid") y de salida (sin password_hash)
      repository.py    Repositorios por entidad con carga anticipada declarada en cada método
      unit_of_work.py  Unit of Work del módulo y dependencia get_<módulo>_uow
      service.py       Reglas de negocio: recibe el UoW y lo abre con async with
      router.py        Rutas HTTP: construyen el UoW con Depends y traducen errores de dominio
  main.py              Aplicación FastAPI, lifespan y montaje de los dos grupos de rutas (abierto y protegido)
migrations/            Configuración asincrónica de Alembic y las 4 versiones del esquema
seed.py                Carga idempotente de los datos iniciales del parcial desde la raíz
test/                  Casos de prueba .http (REST Client) y solo_agregado.sql (psql)
tests/                 Suite de pruebas automáticas con unittest (IsolatedAsyncioTestCase y TestClient)
evidencia/             Salidas y capturas de verificación de los casos de prueba
env.example            Plantilla de variables de entorno sin secretos
alembic.ini            Configuración de Alembic (sin credenciales)
requirements.txt       Dependencias del proyecto con versiones mínimas
```

> **Nota sobre `app/main.py`:** el punto de entrada se mantiene en `app/main.py` (arranque con `uvicorn app.main:app --reload`) según lo confirmado por el profesor en la clase de consulta del viernes 6/11 (decisión `DD-08` en `knowledge-base/09_decisiones_y_supuestos.md`). `seed.py` vive en la raíz (`python seed.py`).

### Arquitectura en capas

Cada petición recorre las capas en este orden:

```text
Router  ──►  Service  ──►  Unit of Work (async with)  ──►  Repository  ──►  PostgreSQL
```

| Capa | Responsabilidad | Límites |
|---|---|---|
| **Router** (`router.py`) | Declara las rutas `async def`, valida contratos de entrada/salida, resuelve las dependencias (`get_usuario_actual`, `requiere_rol`) y construye el Unit of Work del módulo con `Depends(get_<módulo>_uow)` sin abrirlo. Traduce errores de dominio a HTTP (`NoEncontrado` → `404`, `Conflicto` → `409`, `SinPermiso` → `403`, `PaginaInexistente` → `422`). | No contiene reglas de negocio, no abre el UoW ni ejecuta consultas. |
| **Service** (`service.py`) | Implementa las reglas de negocio. Calcula los hashes `bcrypt` antes de abrir la transacción, configura los mensajes de restricción con `uow.con_mensajes(...)` y abre el bloque `async with uow:`. Agrupa en un único bloque las escrituras atómicas de auto-registro (`RN-02`), venta con stock y movimientos (`RN-10`) y operaciones auditadas (`RN-16`). | Nunca construye su propio UoW, no conoce detalles de HTTP ni escribe sentencias SQL. |
| **Unit of Work** (`core/unit_of_work.py` y `<módulo>/unit_of_work.py`) | Gestor de contexto asincrónico que comparte la `AsyncSession` de la petición entre todos los repositorios que compone. Confirma (`commit`) al salir normalmente del bloque `async with`, revierte (`rollback`) si sale con excepción, traduce `IntegrityError` a `Conflicto` con mensaje propio del dominio (`RN-15`) y **no cierra la sesión** (la cierra `get_session`). | No contiene lógica de negocio ni consultas. |
| **Repository** (`core/repository.py` y `<módulo>/repository.py`) | Hereda de `BaseRepository[T]` (o `SoftDeleteRepository[T]` en `LibroRepository`). Ejecuta consultas con parámetros ligados y carga anticipada (`selectinload` / `joinedload`) declarada dentro del método que la necesita (`lazy="raise"` en todas las relaciones). Sus escrituras hacen únicamente `flush()`, **nunca `commit()`**. `LibroRepository.mover_stock` es el único punto de escritura de `libro.stock` (`RN-11`). | No confirma transacciones ni toma decisiones de negocio. |

Las dependencias `get_usuario_actual`, `verificar_cambio_password_pendiente` y `requiere_rol` (`app/core/dependencies.py`) reciben `Depends(get_session)`, por lo que comparten la misma sesión y conexión del pool con el Unit of Work de la petición. La única escritura con sesión y transacción propias es `registrar_intento_acceso` (`app/modules/usuarios/service.py`), para que el conteo de intentos fallidos sobreviva al rollback de un login rechazado (`RN-07`, Ejercicio 7).

---

## Endpoints

En `app/main.py` las rutas se montan en dos grupos:
- **Grupo abierto:** no exige sesión (salvo `/auth/yo` y `/auth/cambiar-password`, que piden estar autenticado pero permiten operar a quien tiene `debe_cambiar_password=true`).
- **Grupo protegido:** lleva montada una sola vez la dependencia `verificar_cambio_password_pendiente`, que responde `403` en cualquier ruta del grupo mientras el usuario autenticado tenga el cambio de contraseña obligatorio pendiente (`RN-06`).

Los listados paginados con `app/core/paginacion.py` reciben `page` (desde `1`, por defecto `1`) y `size` (`1` a `100`, por defecto `20`), devuelven el envoltorio `{items, total, page, size, pages}` y responden `422` si se pide una página más allá de la última.

### Grupo abierto

| Módulo | Método | Ruta | Quién accede | Códigos |
|---|---|---|---|---|
| `health` | `GET` | `/health/live` | Cualquiera | `200` |
| `health` | `GET` | `/health/ready` | Cualquiera | `200`, `503` |
| `usuarios` (`auth`) | `POST` | `/auth/registro` | Cualquiera | `201`, `409`, `422` |
| `usuarios` (`auth`) | `POST` | `/auth/login` | Cualquiera | `200`, `401`, `422`, `429` |
| `usuarios` (`auth`) | `POST` | `/auth/logout` | Cualquiera | `200` |
| `usuarios` (`auth`) | `GET` | `/auth/yo` | Autenticado | `200`, `401` |
| `usuarios` (`auth`) | `POST` | `/auth/cambiar-password` | Autenticado | `200`, `401`, `422` |
| `libros` | `GET` | `/libros/` (`page`, `size`, `titulo`, `genero_id`) | Cualquiera | `200`, `422` |
| `libros` | `GET` | `/libros/{libro_id}` | Cualquiera | `200`, `404`, `422` |
| `editoriales` | `GET` | `/editoriales/` (`page`, `size`) | Cualquiera | `200`, `422` |
| `editoriales` | `GET` | `/editoriales/{editorial_id}` | Cualquiera | `200`, `404`, `422` |
| `editoriales` | `GET` | `/editoriales/{editorial_id}/libros` (`page`, `size`) | Cualquiera | `200`, `404`, `422` |
| `generos` | `GET` | `/generos/` (`page`, `size`) | Cualquiera | `200`, `422` |
| `generos` | `GET` | `/generos/{genero_id}/libros` (`page`, `size`) | Cualquiera | `200`, `404`, `422` |
| `autores` | `GET` | `/autores/{autor_id}` | Cualquiera | `200`, `404`, `422` |
| `autores` | `GET` | `/autores/{autor_id}/libros` (`page`, `size`) | Cualquiera | `200`, `404`, `422` |

### Grupo protegido

| Módulo | Método | Ruta | Quién accede | Códigos |
|---|---|---|---|---|
| `usuarios` | `POST` | `/usuarios` (alta de personal con clave provisoria) | `ADMIN` | `201`, `401`, `403`, `409`, `422` |
| `usuarios` | `GET` | `/usuarios/{usuario_id}/roles` | `ADMIN` | `200`, `401`, `403`, `404` |
| `usuarios` | `POST` | `/usuarios/{usuario_id}/roles` | `ADMIN` | `201`, `401`, `403`, `404`, `409`, `422` |
| `usuarios` | `DELETE` | `/usuarios/{usuario_id}/roles/{rol}` | `ADMIN` | `200`, `401`, `403`, `404`, `409` |
| `usuarios` (`eventos`) | `GET` | `/eventos` (`page`, `size`) | `ADMIN` | `200`, `401`, `403`, `422` |
| `editoriales` | `POST` | `/editoriales/` | `ADMIN` | `201`, `401`, `403`, `409`, `422` |
| `editoriales` | `PATCH` | `/editoriales/{editorial_id}` | `ADMIN` | `200`, `401`, `403`, `404`, `409`, `422` |
| `generos` | `POST` | `/generos/` | `ADMIN` | `201`, `401`, `403`, `409`, `422` |
| `autores` | `POST` | `/autores/` | `ADMIN` | `201`, `401`, `403`, `422` |
| `autores` | `PATCH` | `/autores/{autor_id}` | `ADMIN` | `200`, `401`, `403`, `404`, `422` |
| `libros` | `POST` | `/libros/` (con `autores` y `stock_inicial`) | `ADMIN` | `201`, `401`, `403`, `409`, `422` |
| `libros` | `PATCH` | `/libros/{libro_id}` (`titulo`, `precio`; cualquier otro campo, incluido `stock`, responde `422`) | `ADMIN` | `200`, `401`, `403`, `404`, `409`, `422` |
| `libros` | `DELETE` | `/libros/{libro_id}` (borrado lógico) | `ADMIN` | `204`, `401`, `403`, `404` |
| `libros` | `POST` | `/libros/{libro_id}/reponer` | `ADMIN` | `200`, `401`, `403`, `404`, `409`, `422` |
| `libros` | `GET` | `/libros/{libro_id}/movimientos` (`page`, `size`) | `ADMIN` | `200`, `401`, `403`, `404`, `422` |
| `ventas` | `POST` | `/ventas/` (con `renglones`, descuento de stock y aviso en `BackgroundTasks`) | `VENDEDOR`, `ADMIN` según la consigna (pág. 17); hoy sólo exige sesión: pendiente (Joaquín) | `201`, `401`, `403`, `409`, `422` |
| `ventas` | `GET` | `/ventas/` (`page`, `size`) | `VENDEDOR`, `ADMIN` | `200`, `401`, `403`, `422` |
| `ventas` | `GET` | `/ventas/{venta_id}` (sin `requiere_rol`: decide el servicio por personal o cliente dueño, `RN-14`) | `VENDEDOR`, `ADMIN` o cliente dueño | `200`, `401`, `403`, `404` |
| `ventas` | `GET` | `/mis-ventas` (`page`, `size`, `RN-14`) | Autenticado | `200`, `401`, `403`, `422` |
| `clientes` | `POST`, `GET`, `PATCH` | `/clientes/`, `/clientes/{cliente_id}`, `/clientes/{cliente_id}/perfil`, `/clientes/{cliente_id}/ventas` | En el grupo protegido (`requiere_rol("VENDEDOR", "ADMIN")` y envoltorio: **pendiente J7**) | `200`, `201`, `404`, `409`, `422` |

---

## Carpeta `evidencia/`

La carpeta [`evidencia/`](evidencia/) contiene las salidas y capturas de verificación:

| Archivo | Caso | Contenido |
|---|---|---|
| `evidencia/C-14_psql.png` y `evidencia/C-14_solo_agregado.txt` | **C-14** | Captura de pantalla y salida completa de `psql` ejecutando `test/solo_agregado.sql`: muestra el disparador `trg_movimiento_stock_solo_agregado` activo, el `INSERT` permitido y los rechazos de `UPDATE` y `DELETE` sobre `movimiento_stock` (`RN-12`). |
| *(pendiente J8)* | **C-15** | Fragmento de consola con `SQL_ECHO=true` mostrando la misma cantidad fija de consultas `SELECT` en `GET /ventas/{id}` para una venta con 2 renglones y otra con 4 renglones (**pendiente (J8)**). |
| `evidencia/C-07_ventas.txt`, `evidencia/C-07_libros.txt` y `evidencia/C-07_consultas.txt` | Base TP (sin N+1) | Registro de consultas `SELECT` fijas con `SQL_ECHO=true` en el detalle de ventas, libros y ventas por cliente del TP. |
| `evidencia/integracion.txt` | Integración | Salida de la prueba integral sobre base limpia del TP (la corrida integral final del parcial sobre base nueva corresponde a la tarea **I1**). |

---

## Notas para Windows

- `requirements.txt` fija **SQLAlchemy en `<2.1`** (`sqlalchemy[asyncio]>=2.0,<2.1`): en Windows el binario compilado de la versión 2.1 puede quedar bloqueado al instalar y hacer fallar `pip install`.
- Las variables de entorno definidas en el sistema operativo tienen prioridad sobre las del archivo `.env`. Si la aplicación intenta conectarse a otro puerto o base de datos, verificar que no existan variables `POSTGRES_HOST`, `POSTGRES_DB` o `POSTGRES_PORT` definidas en el entorno del sistema.
