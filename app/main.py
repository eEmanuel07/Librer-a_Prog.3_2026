from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.core.config import get_settings
from app.core.database import crear_fabrica_sesiones, crear_motor
from app.core.paginacion import PaginaInexistente
from app.core.security import calcular_hash_ficticio
from app.modules.autores.router import router as autores_router
from app.modules.clientes.router import router as clientes_router
from app.modules.editoriales.router import router as editoriales_router
from app.modules.generos.router import router as generos_router
from app.modules.health.router import router as health_router
from app.modules.libros.router import router as libros_router
from app.modules.usuarios.router import router as auth_router
from app.modules.ventas.router import router as ventas_router

# SQLAlchemy resuelve las relaciones por nombre ("Cliente", "RenglonVenta"...): todos los
# modelos tienen que estar importados antes del primer uso, aunque el módulo
# dueño todavía no registre su router.
import app.modules.clientes.models  # noqa: F401
import app.modules.usuarios.models  # noqa: F401
import app.modules.ventas.models  # noqa: F401


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    motor = crear_motor(
        settings.database_url,
        echo=settings.sql_echo,
        pool_size=settings.db_pool_size,
        max_overflow=settings.db_max_overflow,
    )
    app.state.settings = settings
    app.state.engine = motor
    app.state.session_factory = crear_fabrica_sesiones(motor)
    app.state.hash_ficticio = await calcular_hash_ficticio(settings)
    yield
    await motor.dispose()


app = FastAPI(title="Librería", lifespan=lifespan)


@app.exception_handler(PaginaInexistente)
async def pagina_inexistente(request: Request, error: PaginaInexistente) -> JSONResponse:
    # Una página más allá de la última es un parámetro que no cumple el
    # contrato: 422, igual que size=500. Vale para todos los listados.
    return JSONResponse(status_code=422, content={"detail": error.mensaje})


app.include_router(health_router)
app.include_router(auth_router)
app.include_router(editoriales_router)
app.include_router(generos_router)
app.include_router(autores_router)
app.include_router(libros_router)
app.include_router(clientes_router)
app.include_router(ventas_router)

# Cada integrante registra acá el router de su módulo:
# from app.modules.editoriales.router import router as editoriales_router
# app.include_router(editoriales_router)
# ... generos, autores, libros, clientes, ventas
