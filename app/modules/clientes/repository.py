from collections.abc import Sequence

from sqlalchemy.orm import joinedload, selectinload
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.paginacion import ParametrosPagina, paginar
from app.modules.clientes.models import Cliente, PerfilCliente
from app.modules.ventas.models import RenglonVenta, Venta


class ClienteRepository:
    """Solo consultas sobre clientes y su perfil. No hace commit: eso es del UoW."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def obtener(self, cliente_id: int) -> Cliente | None:
        return await self.session.get(Cliente, cliente_id)

    async def obtener_con_perfil(self, cliente_id: int) -> Cliente | None:
        # Cantidad fija de consultas (C-07): una sola consulta con JOIN a perfil.
        consulta = (
            select(Cliente)
            .where(Cliente.id == cliente_id)
            .options(joinedload(Cliente.perfil))
            # Si el cliente ya está en la sesión (recién creado o modificado), lo
            # recarga con sus relaciones en lugar de devolver la copia sin precargar.
            .execution_options(populate_existing=True)
        )
        return (await self.session.exec(consulta)).first()

    async def listar_ventas_pagina(
        self, cliente_id: int, params: ParametrosPagina
    ) -> tuple[Sequence[Venta], int]:
        """Una página de las ventas del cliente y el total: ``(items, total)``.

        Cantidad fija de consultas, tenga 1 o muchos renglones, sin N+1 (C-07):
        el conteo, venta JOIN cliente (joinedload, relación a uno) y renglones
        JOIN libro (selectinload, colección). PaginaInexistente si page pasa de la última.
        """
        consulta = (
            select(Venta)
            .where(Venta.cliente_id == cliente_id)
            .options(
                joinedload(Venta.cliente),
                selectinload(Venta.renglones).joinedload(RenglonVenta.libro),
            )
            .order_by(Venta.id)
        )
        return await paginar(self.session, consulta, params)

    def agregar(self, cliente: Cliente) -> None:
        self.session.add(cliente)

    def agregar_perfil(self, perfil: PerfilCliente) -> None:
        self.session.add(perfil)
