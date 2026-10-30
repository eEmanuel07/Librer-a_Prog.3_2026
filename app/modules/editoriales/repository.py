from collections.abc import Sequence

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

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

    def agregar(self, editorial: Editorial) -> None:
        self.session.add(editorial)

    async def listar_libros(self, editorial_id: int, limit: int, offset: int) -> Sequence[Libro]:
        consulta = (
            select(Libro)
            .where(Libro.editorial_id == editorial_id)
            .order_by(Libro.id)
            .limit(limit)
            .offset(offset)
        )
        return (await self.session.exec(consulta)).all()
