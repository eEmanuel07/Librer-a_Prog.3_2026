from fastapi import Depends
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.database import get_session
from app.core.unit_of_work import UnitOfWork
from app.modules.clientes.repository import ClienteRepository


class ClienteUnitOfWork(UnitOfWork):
    """Unit of Work del módulo clientes."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)
        self.clientes = ClienteRepository(session)


def get_clientes_uow(session: AsyncSession = Depends(get_session)) -> ClienteUnitOfWork:
    """Construye el Unit of Work del módulo sin abrirlo: lo abre el service."""
    return ClienteUnitOfWork(session)
