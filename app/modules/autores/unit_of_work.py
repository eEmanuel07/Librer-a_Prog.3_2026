from fastapi import Depends
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.database import get_session
from app.core.unit_of_work import UnitOfWork
from app.modules.autores.repository import AutorRepository


class AutorUnitOfWork(UnitOfWork):
    """Unit of Work del módulo autores."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)
        self.autores = AutorRepository(session)


def get_autores_uow(session: AsyncSession = Depends(get_session)) -> AutorUnitOfWork:
    """Construye el Unit of Work del módulo sin abrirlo: lo abre el service."""
    return AutorUnitOfWork(session)
