from fastapi import Depends
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.database import get_session
from app.core.unit_of_work import UnitOfWork
from app.modules.editoriales.repository import EditorialRepository


class EditorialUnitOfWork(UnitOfWork):
    """Unit of Work del módulo editoriales."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)
        self.editoriales = EditorialRepository(session)


def get_editoriales_uow(session: AsyncSession = Depends(get_session)) -> EditorialUnitOfWork:
    """Construye el Unit of Work del módulo sin abrirlo: lo abre el service."""
    return EditorialUnitOfWork(session)
