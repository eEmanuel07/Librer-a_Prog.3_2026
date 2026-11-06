from fastapi import Depends
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.database import get_session
from app.core.unit_of_work import UnitOfWork
from app.modules.generos.repository import GeneroRepository


class GeneroUnitOfWork(UnitOfWork):
    """Unit of Work del módulo generos."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)
        self.generos = GeneroRepository(session)


def get_generos_uow(session: AsyncSession = Depends(get_session)) -> GeneroUnitOfWork:
    """Construye el Unit of Work del módulo sin abrirlo: lo abre el service."""
    return GeneroUnitOfWork(session)
