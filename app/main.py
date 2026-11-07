from contextlib import asynccontextmanager

from fastapi import APIRouter, Depends, FastAPI, Request
from fastapi.responses import JSONResponse

from app.core.config import get_settings
from app.core.database import crear_fabrica_sesiones, crear_motor
from app.core.dependencies import verificar_cambio_password_pendiente
from app.core.paginacion import PaginaInexistente
from app.core.security import calcular_hash_ficticio
from app.modules.autores.router import (
    router_protegido as autores_protegido_router,
    router_publico as autores_publico_router,
)
from app.modules.clientes.router import router as clientes_router
from app.modules.editoriales.router import (
    router_protegido as editoriales_protegido_router,
    router_publico as editoriales_publico_router,
)
from app.modules.generos.router import (
    router_protegido as generos_protegido_router,
    router_publico as generos_publico_router,
)
from app.modules.health.router import router as health_router
from app.modules.libros.router import (
    router_protegido as libros_protegido_router,
    router_publico as libros_publico_router,
)
from app.modules.usuarios.router import router as auth_router
from app.modules.usuarios.router import router_eventos, router_usuarios
from app.modules.ventas.router import router as ventas_router
from app.modules.ventas.router import router_mis_ventas

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


# Dos grupos de rutas (Ej. 5 / [R3], RN-06):
# - grupo_abierto: salud, /auth y todas las lecturas públicas del catálogo.
# - grupo_protegido: lleva montado una sola vez el control del cambio obligatorio
#   de contraseña (RN-06, 403 si debe_cambiar_password es True).
grupo_abierto = APIRouter()
grupo_abierto.include_router(health_router)
grupo_abierto.include_router(auth_router)
grupo_abierto.include_router(editoriales_publico_router)
grupo_abierto.include_router(generos_publico_router)
grupo_abierto.include_router(autores_publico_router)
grupo_abierto.include_router(libros_publico_router)

grupo_protegido = APIRouter(
    dependencies=[Depends(verificar_cambio_password_pendiente)],
)
grupo_protegido.include_router(router_usuarios)
grupo_protegido.include_router(router_eventos)
grupo_protegido.include_router(editoriales_protegido_router)
grupo_protegido.include_router(generos_protegido_router)
grupo_protegido.include_router(autores_protegido_router)
grupo_protegido.include_router(libros_protegido_router)
grupo_protegido.include_router(clientes_router)
grupo_protegido.include_router(ventas_router)
grupo_protegido.include_router(router_mis_ventas)

app.include_router(grupo_abierto)
app.include_router(grupo_protegido)
