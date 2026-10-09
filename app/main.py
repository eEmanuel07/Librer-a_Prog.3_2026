from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.config import get_settings
from app.core.database import crear_fabrica_sesiones, crear_motor
from app.modules.health.router import router as health_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    motor = crear_motor(settings.database_url, echo=settings.sql_echo)
    app.state.engine = motor
    app.state.session_factory = crear_fabrica_sesiones(motor)
    yield
    await motor.dispose()


app = FastAPI(title="Librería", lifespan=lifespan)

app.include_router(health_router)

# Cada integrante registra acá el router de su módulo:
# from app.modules.editoriales.router import router as editoriales_router
# app.include_router(editoriales_router)
# ... generos, autores, libros, clientes, ventas
