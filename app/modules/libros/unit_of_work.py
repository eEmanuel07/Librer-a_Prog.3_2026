from fastapi import Depends
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.database import get_session
from app.core.unit_of_work import UnitOfWork
from app.modules.libros.repository import LibroRepository


class LibroUnitOfWork(UnitOfWork):
    """Unit of Work del módulo libros."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)
        self.libros = LibroRepository(session)


def get_libros_uow(session: AsyncSession = Depends(get_session)) -> LibroUnitOfWork:
    """Construye el Unit of Work del módulo sin abrirlo: lo abre el service."""
    return LibroUnitOfWork(session)
