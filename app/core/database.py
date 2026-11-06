from collections.abc import AsyncGenerator

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, create_async_engine
from sqlmodel.ext.asyncio.session import AsyncSession


def crear_motor(database_url: str, echo: bool = False) -> AsyncEngine:
    return create_async_engine(database_url, echo=echo)


def crear_fabrica_sesiones(motor: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    # expire_on_commit=False: después del commit los objetos siguen usables
    # sin disparar una recarga (que en async sería una carga perezosa).
    return async_sessionmaker(motor, class_=AsyncSession, expire_on_commit=False)


async def get_session(request: Request) -> AsyncGenerator[AsyncSession, None]:
    """Una sesión por petición, tomada de la fábrica guardada en app.state.

    FastAPI resuelve esta dependencia una sola vez por petición: todo el que
    pida ``Depends(get_session)`` recibe la misma sesión, y la petición usa
    una sola conexión del pool.

    Nota para R1: ``get_usuario_actual`` (y la verificación de rol) tiene que
    pedir ``session: AsyncSession = Depends(get_session)``, nunca abrir la
    fábrica por su cuenta. Así FastAPI le da la misma sesión que al Unit of
    Work del módulo y una petición autenticada toma una sola conexión.
    """
    fabrica: async_sessionmaker[AsyncSession] = request.app.state.session_factory
    async with fabrica() as session:
        yield session
