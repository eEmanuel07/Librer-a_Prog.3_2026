from collections.abc import Sequence

from sqlalchemy.orm import joinedload, selectinload
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.modules.ventas.models import RenglonVenta, Venta


class VentaRepository:
    """Solo consultas sobre ventas. No hace commit: eso es del UoW."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def obtener_con_detalle(self, venta_id: int) -> Venta | None:
        # Cantidad fija de consultas, sin importar cuántos renglones tenga (C-07):
        #   1) venta JOIN cliente          -> joinedload (relación a uno)
        #   2) renglones JOIN libro        -> selectinload (colección) + joinedload (a uno)
        consulta = (
            select(Venta)
            .where(Venta.id == venta_id)
            .options(
                joinedload(Venta.cliente),
                selectinload(Venta.renglones).joinedload(RenglonVenta.libro),
            )
            # Si la venta ya está en la sesión (recién creada), la recarga con
            # sus relaciones en lugar de devolver la copia sin precargar.
            .execution_options(populate_existing=True)
        )
        return (await self.session.exec(consulta)).first()

    async def listar(self, limit: int, offset: int) -> Sequence[Venta]:
        # Una sola consulta: venta JOIN cliente.
        consulta = (
            select(Venta)
            .options(joinedload(Venta.cliente))
            .order_by(Venta.id)
            .limit(limit)
            .offset(offset)
        )
        return (await self.session.exec(consulta)).all()

    def agregar(self, venta: Venta) -> None:
        # La cascada de Venta.renglones agrega también los renglones.
        self.session.add(venta)
