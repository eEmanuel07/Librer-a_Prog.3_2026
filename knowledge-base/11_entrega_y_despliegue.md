# Entrega y Despliegue

## Formato de entrega (pág. 24)

- **Una entrega por grupo**, en un único `.zip` que sube **un solo** integrante a la tarea del campus. Nombre: `Parcial_Cap1a6_<NombreDelGrupo>.zip`. La fecha límite la publica el campus.
- El `.zip` tiene **dos carpetas**, porque son dos proyectos distintos:

| Carpeta | Qué es | Qué lleva |
|---|---|---|
| `parcial/` | Este repo: el proyecto ampliado, **sin** el despliegue | Código completo, `requirements.txt`, `env.example`, `alembic.ini`, `migrations/`, `test/`. `README.md` con nombres y apellidos de los integrantes y los pasos para levantarlo desde cero: entorno virtual, dependencias, `.env` y cómo generar la clave de firma, `alembic upgrade head`, `python seed.py` y arranque. `evidencia/` con C-15 (consultas del detalle con 2 y con 4 renglones) y la captura de psql de C-14. |
| `despliegue/` | El **TP de los capítulos 1 a 4 tal como se entregó** | El TP más `Dockerfile`, `.dockerignore`, `env.example` con las variables del contenedor (la forma de `DATABASE_URL`, sin valores reales) y `DEPLOY.md`. `evidencia/` con la salida de cada caso D. |

- **Nunca** en el `.zip`: `.venv`, `__pycache__` (en ninguna de las dos carpetas) ni `.env`. Si va la carpeta `.git`, también se revisa su historial: una contraseña que se subió y después se borró sigue ahí, y hay que cambiarla.
- Lo arma Elías (E10) (`docs/flujo-de-trabajo.md`).

## De dónde sale `despliegue/`

- El TP 1-4 entregado está en el tag **`entrega-final`**. La rama **`despliegue`** sale de ese tag y **nunca se mezcla con `main`**: no lleva ningún cambio del parcial (págs. 2, 14).
- Al TP sólo se le agregan `Dockerfile` y `.dockerignore`; su lógica no se toca. Si no arranca en el contenedor por un defecto propio, se corrige y se anota en `DEPLOY.md` (pág. 14).

## La imagen (Ej. 9, págs. 14-15) · J1, J2

- Base `python:3.12-alpine`, que pesa menos de 100 MB (`slim` no cumple). El límite es para la imagen base, no para la del proyecto.
- `requirements.txt` se copia e instala **antes** que el código, con `--no-cache-dir`, para aprovechar la caché de capas.
- Corre con un usuario **sin privilegios** (`USER`).
- **Sin secretos:** `.dockerignore` excluye `.env`, `.venv`, `.git` y `__pycache__`. La URL y la contraseña de la base entran como variables al correr el contenedor.
- Al arrancar aplica `alembic upgrade head` y levanta `uvicorn app.main:app` en `0.0.0.0`. Si la base no responde, el contenedor termina con error, que es lo buscado.
- `HEALTHCHECK` sobre `GET /health/ready` con `127.0.0.1`, no con `localhost`: en Alpine, `wget` resuelve primero a IPv6 y uvicorn escucha en IPv4.
- **Sin Docker Compose:** la base ya está en el servidor.

## Cómo se corre (pág. 15)

`docker run -d --name libreria -p <puerto>:8000 --restart unless-stopped --env-file <archivo> libreria`
- El puerto lo asigna la cátedra. El archivo de variables vive en el servidor, fuera del repo y de la imagen, con `DATABASE_URL` (driver `postgresql+asyncpg`) y `SQL_ECHO=false`.
- Dentro del contenedor, `localhost` es el propio contenedor. Si la base corre en el servidor, se usa `host.docker.internal` con `--add-host=host.docker.internal:host-gateway`.

## Despliegue en el VPS (Ej. 10, pág. 16) · E8, E9

- Se construye la imagen en el servidor, o en otro lado y se la lleva, y se corre con `docker run`. El grupo elige y lo documenta.
- Los datos iniciales se cargan con `docker exec libreria …`, según el README del TP.
- Tiene que seguir **en línea hasta que se publiquen las notas**.
- `DEPLOY.md` incluye: la URL pública; el día y la hora del despliegue; los comandos `docker build` y `docker run` completos (con el nombre del archivo de variables, nunca su contenido); los cambios hechos al TP; y cómo se actualiza (reconstruir la imagen, borrar el contenedor y volver a correrlo; los datos siguen porque viven en la base del servidor).
- Si el despliegue no está accesible al corregir, se evalúa sólo lo que dicen `DEPLOY.md` y `evidencia/`, y los casos D que no se puedan comprobar no suman (pág. 24).
