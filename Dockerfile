# Imagen del TP de la librería (capítulos 1 a 4) para el despliegue en el VPS.
#
# Base python:3.12-alpine (74,7 MB, por debajo del límite de 100 MB): cada
# megabyte se descarga y se guarda en el servidor en cada despliegue, y cada
# paquete del sistema que no se usa es superficie de ataque. Las dependencias
# del TP (asyncpg, pydantic-core y el resto de requirements.txt) traen wheels
# para musl, así que se instalan sin compilador.
FROM python:3.12-alpine

# Sin archivos .pyc en la imagen, y la salida de Python sin buffer: los
# mensajes (incluido el aviso del comprobante) aparecen en docker logs en el
# momento y no cuando se llena el buffer.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# 1) Dependencias antes que el código: mientras requirements.txt no cambie,
#    esta capa sale de la caché y un cambio en el código no reinstala todo.
#    --no-cache-dir: la caché de pip no queda guardada dentro de la imagen.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 2) Usuario sin privilegios (addgroup/adduser de BusyBox, en Alpine).
RUN addgroup -S app && adduser -S -G app app

# 3) El código. Queda de root y el usuario de la aplicación sólo lo puede leer:
#    si alguien vulnera la aplicación, no puede modificarla ni es dueño del
#    contenedor. El .dockerignore deja afuera .env, .venv, .git y __pycache__,
#    y ni la dirección de la base ni su contraseña están en este archivo:
#    entran como variables de entorno al correr el contenedor (--env-file).
COPY . .

USER app

EXPOSE 8000

# 4) Salud: GET /health/ready, que ejecuta SELECT 1 contra la base. Sin
#    Compose, es la propia imagen la que dice si está sana (docker ps).
#    Va 127.0.0.1 y no localhost: en Alpine no hay curl, y wget resuelve
#    localhost primero a ::1 (IPv6), donde uvicorn no escucha.
HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
    CMD wget -q -O /dev/null http://127.0.0.1:8000/health/ready || exit 1

# 5) Al arrancar: migraciones y después el servidor.
#    - Si la base no responde (o falta DATABASE_URL), alembic falla, el &&
#      corta y el contenedor termina con error en lugar de quedar atendiendo.
#    - exec deja a uvicorn como proceso principal, para que reciba la señal
#      de parada de Docker y cierre bien.
#    - 0.0.0.0: dentro del contenedor, 127.0.0.1 sólo se alcanza desde el
#      propio contenedor y el puerto publicado nunca respondería.
CMD ["sh", "-c", "alembic upgrade head && exec uvicorn app.main:app --host 0.0.0.0 --port 8000"]
