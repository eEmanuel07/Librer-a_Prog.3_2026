# Despliegue en el VPS — TP de los capítulos 1 a 4

> **Borrador.** Lo marcado con ⏳ se completa al desplegar en el VPS (E8).

Este documento describe cómo está desplegado el TP de los capítulos 1 a 4 (la librería, tal como se entregó en el tag `entrega-final`) en el VPS de la cátedra, con Docker y sin Docker Compose (Ej. 10 del parcial).

## Dónde está

| | |
|---|---|
| **URL pública** | ⏳ `http://<IP_O_DOMINIO>:<PUERTO>` |
| **Día y hora del despliegue** | ⏳ `AAAA-MM-DD HH:MM` (hora de Argentina) |
| **Rama y commit desplegados** | `despliegue` · ⏳ commit |
| **Responsable** | Elías Tello |

Para comprobar que está en línea:

- `GET <URL>/health/ready` → 200
- `GET <URL>/libros/` → 200 con la lista de libros

El despliegue queda en línea hasta que se publiquen las notas.

## Qué se despliega

- El TP de los capítulos 1 a 4 **tal como se entregó** (tag `entrega-final`). La rama `despliegue` sale de ese tag y no se mezcla con `main`, donde está el parcial.
- Al TP sólo se le agregaron:
  - `Dockerfile`: imagen sobre `python:3.12-alpine`, usuario sin privilegios, `HEALTHCHECK` sobre `/health/ready` y, al arrancar, `alembic upgrade head` y después `uvicorn`.
  - `.dockerignore`: deja afuera `.env`, `.venv`, `.git`, `__pycache__`, `test/` y `evidencia/`.
  - En `env.example`, la sección del contenedor, con la forma de `DATABASE_URL` y sin valores reales.

### Cambios al TP para que corra en el contenedor

**Ninguno.** La lógica del TP no se tocó: `git diff entrega-final despliegue` muestra sólo los archivos de arriba y la evidencia.

⏳ Si en el VPS aparece algún defecto propio del TP que impida arrancar, se corrige en la rama `despliegue` y se anota acá: qué fallaba, qué se cambió y en qué commit.

## Requisitos del servidor

- Docker instalado (⏳ versión: `docker --version`).
- PostgreSQL con la base que provee la cátedra. La base **no** va en el contenedor.
- El puerto asignado por la cátedra (⏳ `<PUERTO>`), abierto desde afuera.

## Archivo de variables

El contenedor no lee un `.env`: recibe las variables con `--env-file` desde un archivo que vive **en el servidor**, fuera del repositorio y de la imagen.

- **Archivo:** `~/libreria.env`, con permisos `600` (sólo lo lee el usuario del servidor).
- **Variables** (sólo los nombres; los valores no se publican):
  - `DATABASE_URL`: con el driver asincrónico, de la forma `postgresql+asyncpg://USUARIO:CONTRASEÑA@HOST:5432/BASE`.
  - `SQL_ECHO=false`.
- **`HOST`:** dentro del contenedor, `localhost` es el propio contenedor. Si PostgreSQL corre en el mismo servidor, se usa `host.docker.internal` (y el `docker run` lleva `--add-host`, ver abajo). Si la cátedra da otra dirección, va esa.

```bash
chmod 600 ~/libreria.env
```

## Construcción y arranque

La imagen se construye **en el servidor**, a partir de la rama `despliegue` (el repositorio es público).

```bash
git clone --branch despliegue --single-branch https://github.com/eEmanuel07/Librer-a_Prog.3_2026.git libreria
```

```bash
cd libreria
```

```bash
docker build -t libreria .
```

```bash
docker run -d --name libreria -p <PUERTO>:8000 --restart unless-stopped --add-host=host.docker.internal:host-gateway --env-file ~/libreria.env libreria
```

- `-p <PUERTO>:8000`: el puerto público asignado por la cátedra apunta al 8000 del contenedor, donde escucha uvicorn.
- `--restart unless-stopped`: el contenedor vuelve a arrancar si se cae o si se reinicia el servidor.
- `--add-host=host.docker.internal:host-gateway`: sólo hace falta si PostgreSQL corre en el mismo servidor.
- `--env-file ~/libreria.env`: las variables entran al correr el contenedor; la imagen no tiene ninguna dirección de base ni contraseña.

### Datos iniciales

Una sola vez, en el primer despliegue, con el comando del README del TP ejecutado dentro del contenedor:

```bash
docker exec libreria python -m scripts.seed
```

> El seed vacía las tablas antes de cargar. **No** se vuelve a correr al actualizar: los datos viven en la base del servidor y se conservan.

### Comprobación

```bash
docker ps
```

```bash
docker logs libreria
```

El contenedor tiene que figurar como `healthy`, y en los logs tienen que verse las migraciones aplicadas al arrancar y uvicorn escuchando en `0.0.0.0:8000`.

## Cómo se actualiza

Cuando cambia el código de la rama `despliegue`: se construye la imagen de nuevo, se elimina el contenedor y se lo vuelve a correr con el mismo comando.

```bash
cd libreria && git pull
```

```bash
docker build -t libreria .
```

```bash
docker rm -f libreria
```

```bash
docker run -d --name libreria -p <PUERTO>:8000 --restart unless-stopped --add-host=host.docker.internal:host-gateway --env-file ~/libreria.env libreria
```

Los datos **no se pierden**, porque viven en la base del servidor y no en el contenedor. Al arrancar, `alembic upgrade head` no repite las migraciones ya aplicadas (D-04).

## Evidencia de los casos D

La salida de cada caso está en `evidencia/`.

| Caso | Qué se demuestra | Dónde | Estado |
|---|---|---|---|
| D-01 | `python:3.12-alpine` por debajo de los 100 MB, y el Dockerfile parte de ella | `evidencia/imagen-local.txt` (prueba local) · ⏳ VPS | Local ✅ · VPS ⏳ |
| D-02 | Servidor limpio: `docker build` y `docker run`; el contenedor `healthy` y las migraciones aplicadas en `docker logs` | ⏳ `evidencia/D-02_build_y_run.txt` | ⏳ |
| D-03 | Desde afuera del VPS: `/health/ready` 200, `/libros/` 200 con los libros, `POST /ventas/` 201 con los precios copiados y el total calculado | ⏳ `evidencia/D-03_desde_afuera.txt` | ⏳ |
| D-04 | `docker rm -f libreria` y el mismo `docker run`: vuelve a estar `healthy`, los datos siguen y las migraciones no se repiten | ⏳ `evidencia/D-04_reinicio.txt` | ⏳ |
| D-05 | Sin `DATABASE_URL`, el contenedor termina con error en lugar de quedar sirviendo | `evidencia/imagen-local.txt` (prueba local) · ⏳ VPS | Local ✅ · VPS ⏳ |
| D-06 | La imagen no tiene `.env`, y su entorno no muestra `DATABASE_URL` ni contraseñas | `evidencia/imagen-local.txt` (prueba local) · ⏳ VPS | Local ✅ · VPS ⏳ |
| D-07 | `docker exec libreria id` no es root | `evidencia/imagen-local.txt` (prueba local) · ⏳ VPS | Local ✅ · VPS ⏳ |
| D-08 | El aviso del comprobante de la venta de D-03 aparece en `docker logs libreria` después de la línea de la respuesta | ⏳ `evidencia/D-08_aviso_en_logs.txt` | ⏳ |

Las pruebas locales de D-01, D-05, D-06 y D-07 son de J2 (Joaquín, 2026-11-05).
