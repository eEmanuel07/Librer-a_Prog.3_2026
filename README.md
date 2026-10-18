# Librería — TP Programación III

API REST de una librería: editoriales, géneros, autores, libros, clientes y ventas.
Hecha con **FastAPI** (handlers `async`), **SQLModel**, **PostgreSQL** y **Alembic**.

**Grupo:** Belén, Bruno, Elías, Hernán y Joaquín.

## Requisitos

- Python 3.12 o superior.
- Docker, para correr PostgreSQL.

## Instalación

```bash
git clone https://github.com/eEmanuel07/Librer-a_Prog.3_2026.git
cd Librer-a_Prog.3_2026
python -m venv .venv
```

Activar el entorno virtual:

```bash
# Git Bash
source .venv/Scripts/activate
```

```powershell
# PowerShell
.venv\Scripts\Activate.ps1
```

```cmd
:: CMD
.venv\Scripts\activate.bat
```

Instalar las dependencias:

```bash
pip install -r requirements.txt
```

## Configuración

Copiar `env.example` como `.env` (el `.env` no se sube al repositorio):

```bash
cp env.example .env
```

| Variable | Para qué sirve |
|---|---|
| `DATABASE_URL` | Conexión a PostgreSQL con el driver async: `postgresql+asyncpg://USUARIO:CONTRASEÑA@localhost:5432/libreria`. El puerto tiene que coincidir con el del contenedor (por defecto 5432, igual que en env.example). Si ya tenés otro PostgreSQL usando el 5432, mapeá el contenedor a otro puerto (por ejemplo 5433) y poné ese mismo puerto en tu .env. |
| `SQL_ECHO` | `true` muestra en la consola cada consulta SQL (sirve para la evidencia del caso C-07). Por defecto `false`. |

## Base de datos

El repo no trae `docker-compose`. Se levanta un PostgreSQL 16 en un contenedor, con el
puerto 5432 de la máquina apuntando al 5432 del contenedor:

```bash
docker run --name libreria-db -e POSTGRES_USER=postgres -e POSTGRES_PASSWORD=<tu_contraseña> -e POSTGRES_DB=libreria -p 5432:5432 -d postgres:16
```

Si el puerto 5432 de tu máquina está ocupado, usá `-p 5433:5432` y ajustá el puerto en el .env.

Las veces siguientes alcanza con `docker start libreria-db`.

## Migraciones

```bash
alembic upgrade head
```

Alembic toma la URL de `DATABASE_URL` (`.env`), nunca de `alembic.ini`.

## Datos iniciales

```bash
python -m scripts.seed
```

> ⚠️ **Borra TODOS los datos** de las tablas del proyecto (`TRUNCATE ... RESTART IDENTITY CASCADE`)
> y vuelve a cargar los datos de la consigna. Los ids arrancan otra vez en 1, así que
> correrlo varias veces deja siempre lo mismo.

## Correr el servidor

```bash
uvicorn app.main:app --reload
```

- Documentación interactiva: http://localhost:8000/docs
- Chequeo rápido: http://localhost:8000/health/live

## Estructura

```
app/
  core/          configuración, sesión de base, errores 409 y paginación comunes
  modules/
    <modulo>/    models.py (tablas), schemas.py (DTO), service.py (lógica), router.py (endpoints)
  main.py        crea la app y registra los routers
migrations/      migraciones de Alembic
scripts/seed.py  datos iniciales
test/            pedidos .http por módulo
evidencia/       salidas de consultas SQL (caso C-07)
```

## Módulos y endpoints

Los listados se paginan con `limit` (1 a 100, por defecto 20) y `offset` (desde 0).

| Módulo | Método | Ruta |
|---|---|---|
| health | GET | `/health/live`, `/health/ready` |
| editoriales | POST, GET | `/editoriales/` |
| | GET, PATCH | `/editoriales/{id}` |
| | GET | `/editoriales/{id}/libros` |
| géneros | POST, GET | `/generos/` |
| | GET | `/generos/{id}/libros` |
| autores | POST | `/autores/` |
| | GET, PATCH | `/autores/{id}` |
| | GET | `/autores/{id}/libros` |
| libros | POST | `/libros/` |
| | GET | `/libros/` (filtros `titulo` y `genero_id`) |
| | GET, PATCH | `/libros/{id}` |
| clientes | POST | `/clientes/` |
| | GET, PATCH | `/clientes/{id}` |
| | POST | `/clientes/{id}/perfil` |
| | GET | `/clientes/{id}/ventas` |
| ventas | POST, GET | `/ventas/` |
| | GET | `/ventas/{id}` |

## Cómo probar

En `test/` hay un archivo `.http` por módulo. Se abren en VS Code con la extensión
**REST Client** y se ejecuta cada pedido con *Send Request*. Usan `@host = http://localhost:8000`
y los ids de los datos iniciales, así que conviene correr `python -m scripts.seed` antes.

## Nota para Windows

- `requirements.txt` fija **SQLAlchemy en `<2.1`** a propósito: en Windows el archivo
  compilado de la 2.1 puede quedar bloqueado y la instalación falla. No lo cambien.
- Si existe una variable de entorno `DATABASE_URL` del sistema, **pisa al `.env`**
  (`python-dotenv` no sobrescribe variables ya definidas). Si la API se conecta a otra
  base, revisá y borrá esa variable.

## Evidencia de consultas (C-07)

La cantidad fija de consultas (sin N+1) está documentada en la carpeta [`evidencia/`](evidencia/).
