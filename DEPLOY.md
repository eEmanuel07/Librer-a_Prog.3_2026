# Despliegue en el VPS — TP de los capítulos 1 a 4

Este documento describe cómo está desplegado el TP de los capítulos 1 a 4 (la librería, tal como se entregó en el tag `entrega-final`) en el VPS, para el Ej. 10 del parcial.

## Dónde está

| | |
|---|---|
| **URL pública** | https://grupo2-elias-apilibreria.ugpvou.easypanel.host |
| **Día y hora del despliegue** | 8 de noviembre de 2026, 19:04 (hora de Argentina) |
| **Rama y commit desplegados** | `despliegue` · `6581fcb` (Merge pull request #74) |
| **Proyecto y servicios en EasyPanel** | proyecto `grupo2-elias`: servicio App `apilibreria` y servicio Postgres `dblibreria` |
| **Responsable** | Elías Tello |

Para comprobar que está en línea:

- `GET https://grupo2-elias-apilibreria.ugpvou.easypanel.host/health/ready` → 200 con `{"estado":"listo","base":"ok"}`
- `GET https://grupo2-elias-apilibreria.ugpvou.easypanel.host/libros/` → 200 con la lista de libros

El despliegue queda en línea hasta que se publiquen las notas.

## Cómo se despliega: EasyPanel en lugar de `docker run`

La consigna pide correr la imagen con `docker run`. **El profesor autorizó usar EasyPanel**, con la forma enseñada en clase, y probar él mismo que el despliegue funcione. El VPS es uno de Hostinger que comparte un grupo de alumnos del curso y que se administra con EasyPanel.

EasyPanel hace lo mismo que los comandos de la consigna, desde el panel:

| Consigna | En EasyPanel |
|---|---|
| `docker build -t libreria .` | El servicio App construye la imagen con el `Dockerfile` de la rama `despliegue` en cada implementación |
| `docker run ... --env-file <archivo>` | Las variables del servicio (*Entorno*) entran al contenedor al arrancar; no están en la imagen ni en el repositorio |
| `-p <puerto>:8000` | El dominio del servicio apunta al puerto **8000** del contenedor, a través del proxy de EasyPanel (HTTPS) |
| `--restart unless-stopped` | EasyPanel vuelve a levantar el contenedor si se cae o se reinicia el servidor |
| `docker exec libreria ...` | La **Consola** del servicio, que abre una terminal dentro del contenedor |
| `docker rm -f libreria` y el mismo `docker run` | **Reiniciar** o **Implementar** el servicio |
| La base que ya tiene el servidor | Un servicio Postgres en el mismo proyecto, con sus datos en un volumen propio |

La imagen es la misma: el `Dockerfile` de la rama no cambió.

## Qué se despliega

- El TP de los capítulos 1 a 4 **tal como se entregó** (tag `entrega-final`). La rama `despliegue` sale de ese tag y no se mezcla con `main`, donde está el parcial.
- Al TP sólo se le agregaron:
  - `Dockerfile`: imagen sobre `python:3.12-alpine`, usuario sin privilegios, `HEALTHCHECK` sobre `/health/ready` y, al arrancar, `alembic upgrade head` y después `uvicorn` en el puerto 8000.
  - `.dockerignore`: deja afuera `.env`, `.venv`, `.git`, `__pycache__`, `test/` y `evidencia/`.
  - En `env.example`, la sección del contenedor, con la forma de `DATABASE_URL` y sin valores reales.

### Cambios al TP para que corra en el contenedor

**Ninguno.** La lógica del TP no se tocó: `git diff entrega-final despliegue` muestra sólo los archivos de arriba, la evidencia y este documento.

## Pasos del despliegue

1. **Proyecto:** en EasyPanel, un proyecto `grupo2-elias`.
2. **Base:** un servicio **Postgres** `dblibreria`. EasyPanel genera el usuario, la contraseña y el host interno (`grupo2-elias_dblibreria`, puerto 5432).
3. **Aplicación:** un servicio **App** `apilibreria`:
   - **Origen:** GitHub, repositorio `eEmanuel07/Librer-a_Prog.3_2026`, rama `despliegue`.
   - **Compilación:** Dockerfile, archivo `Dockerfile`.
   - **Entorno** (sólo los nombres; los valores no se publican):
     - `DATABASE_URL`, con el driver asincrónico, de la forma `postgresql+asyncpg://USUARIO:CONTRASEÑA@grupo2-elias_dblibreria:5432/BASE`. Es la URL de conexión interna del servicio Postgres, cambiando el `postgres://` del principio por `postgresql+asyncpg://`.
     - `SQL_ECHO=false`.
   - **Dominio:** el que asigna EasyPanel, con **puerto 8000**.
4. **Implementar.** En los registros del servicio se ven las migraciones aplicadas y `Uvicorn running on http://0.0.0.0:8000`; el chequeo de salud responde 200.
5. **Datos iniciales**, una sola vez, con el comando del README del TP en la **Consola** del servicio:

   ```bash
   python -m scripts.seed
   ```

   > El seed vacía las tablas antes de cargar. **No** se vuelve a correr al actualizar: los datos viven en la base y se conservan.

### Lo que se corrigió durante el despliegue

Problemas de configuración, no del TP:

- Sin `DATABASE_URL` el contenedor termina con error, como corresponde (D-05).
- Con el host de la base equivocado: `Name does not resolve`. Se usó el host interno del servicio Postgres.
- Con el dominio en el puerto 80 por defecto, el proxy respondía 502. Se configuró el puerto 8000.

## Cómo se actualiza

Cuando cambia el código de la rama `despliegue`, se toca **Implementar** en el servicio `apilibreria`: EasyPanel trae el último commit, construye la imagen de nuevo, elimina el contenedor anterior y levanta uno nuevo con las mismas variables.

Los datos **no se pierden**, porque viven en el servicio Postgres y no en el contenedor de la aplicación. Al arrancar, `alembic upgrade head` no repite las migraciones ya aplicadas.

## Evidencia de los casos D

La evidencia del VPS está en `evidencia/vps/`. La prueba previa en una máquina del grupo (J2) está en `evidencia/imagen-local.txt`.

| Caso | Qué se demuestra | Resultado | Evidencia |
|---|---|---|---|
| D-01 | El `Dockerfile` parte de `python:3.12-alpine`, por debajo de los 100 MB | El build del VPS parte de `python:3.12-alpine`; la base pesa 74,8 MB | `vps/D-01_build_python_alpine.png` · `imagen-local.txt` |
| D-02 | Build y arranque en el servidor; contenedor sano y migraciones al arrancar | uvicorn en `0.0.0.0:8000` y el chequeo de salud en 200 | `vps/D-02_migraciones_al_arrancar.png` · `vps/D-02_uvicorn_healthy.png` · `vps/historial_implementaciones.png` |
| D-03 | Desde afuera del VPS: `/health/ready`, `/libros/` y `POST /ventas/` | 200; 200 con los 6 libros; 201 con la venta 2 (2 × 25000 + 27000 = 77000.00) | `vps/D-03_desde_afuera.txt` |
| D-04 | Reiniciar el contenedor: vuelve sano y los datos siguen | La venta 2, registrada antes del reinicio, sigue en la base | `vps/D-04_reinicio.txt` · `vps/D-04_registros_reinicio.png` |
| D-05 | Sin `DATABASE_URL`, el contenedor no queda sirviendo | `RuntimeError: Falta la variable de entorno DATABASE_URL` | `vps/D-05_sin_database_url.png` · `imagen-local.txt` |
| D-06 | La imagen no tiene `.env` ni secretos | `/app` sin `.env`; el entorno de la imagen sin `DATABASE_URL` ni contraseñas | `vps/D-06_D-07_usuario_y_contenido.png` · `imagen-local.txt` |
| D-07 | El proceso no es root | `uid=100(app) gid=101(app)` | `vps/D-06_D-07_usuario_y_contenido.png` |
| D-08 | El aviso del comprobante de la venta de D-03 en los registros | `Comprobante de la venta 2 enviado a tomas@example.com (total $77000.00)` después del `201 Created` | `vps/D-08_aviso_comprobante.png` |

La carga de los datos iniciales está en `vps/datos_iniciales_seed.png`: la contraseña de la base sale enmascarada (`***`).
