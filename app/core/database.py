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
    """Una sesión por petición, tomada de la fábrica guardada en app.state."""
    fabrica: async_sessionmaker[AsyncSession] = request.app.state.session_factory
    async with fabrica() as session:
        yield session
