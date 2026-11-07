from collections.abc import Sequence

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.paginacion import ParametrosPagina, paginar
from app.modules.editoriales.models import Editorial
from app.modules.libros.models import Libro


class EditorialRepository:
    """Solo consultas sobre editoriales. No hace commit: eso es del UoW."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def obtener(self, editorial_id: int) -> Editorial | None:
        return await self.session.get(Editorial, editorial_id)

    async def listar(self, limit: int, offset: int) -> Sequence[Editorial]:
        consulta = select(Editorial).order_by(Editorial.id).limit(limit).offset(offset)
        return (await self.session.exec(consulta)).all()

    async def listar_pagina(
        self, params: ParametrosPagina
    ) -> tuple[Sequence[Editorial], int]:
        consulta = select(Editorial).order_by(Editorial.id)
        return await paginar(self.session, consulta, params)

    def agregar(self, editorial: Editorial) -> None:
        self.session.add(editorial)

    async def listar_libros(self, editorial_id: int, limit: int, offset: int) -> Sequence[Libro]:
        consulta = (
            select(Libro)
            .where(Libro.editorial_id == editorial_id, Libro.borrado_en.is_(None))
            .order_by(Libro.id)
            .limit(limit)
            .offset(offset)
        )
        return (await self.session.exec(consulta)).all()

    async def listar_libros_pagina(
        self, editorial_id: int, params: ParametrosPagina
    ) -> tuple[Sequence[Libro], int]:
        consulta = (
            select(Libro)
            .where(Libro.editorial_id == editorial_id, Libro.borrado_en.is_(None))
            .order_by(Libro.id)
        )
        return await paginar(self.session, consulta, params)
