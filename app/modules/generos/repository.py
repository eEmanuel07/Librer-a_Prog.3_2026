from collections.abc import Sequence

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.modules.generos.models import Genero
from app.modules.libros.models import Libro


class GeneroRepository:
    """Solo consultas sobre géneros. No hace commit: eso es del UoW."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def obtener(self, genero_id: int) -> Genero | None:
        return await self.session.get(Genero, genero_id)

    async def listar(self, limit: int, offset: int) -> Sequence[Genero]:
        consulta = select(Genero).order_by(Genero.id).limit(limit).offset(offset)
        return (await self.session.exec(consulta)).all()

    def agregar(self, genero: Genero) -> None:
        self.session.add(genero)

    async def listar_libros(self, genero_id: int, limit: int, offset: int) -> Sequence[Libro]:
        consulta = (
            select(Libro)
            .where(Libro.genero_id == genero_id)
            .order_by(Libro.id)
            .limit(limit)
            .offset(offset)
        )
        return (await self.session.exec(consulta)).all()
