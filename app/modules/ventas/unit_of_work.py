from fastapi import Depends
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.database import get_session
from app.core.unit_of_work import UnitOfWork
from app.modules.libros.repository import LibroRepository
from app.modules.usuarios.repository import AsignacionRolRepository
from app.modules.ventas.repository import VentaRepository


class VentaUnitOfWork(UnitOfWork):
    """Unit of Work del módulo ventas.

    Compone también el repositorio de libros: el alta de una venta lee los
    precios (RN-06) en la misma sesión y la misma transacción. Y el de roles:
    el detalle de una venta decide en el service si quien pide es personal
    (roles vigentes en la base, RN-04) o el cliente dueño (RN-14).
    """

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)
        self.ventas = VentaRepository(session)
        self.libros = LibroRepository(session)
        self.roles = AsignacionRolRepository(session)


def get_ventas_uow(session: AsyncSession = Depends(get_session)) -> VentaUnitOfWork:
    """Construye el Unit of Work del módulo sin abrirlo: lo abre el service."""
    return VentaUnitOfWork(session)
