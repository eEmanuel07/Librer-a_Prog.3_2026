from collections.abc import Sequence

from sqlalchemy.orm import joinedload, selectinload
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.modules.libros.models import Libro, LibroAutor


class LibroRepository:
    """Solo consultas sobre libros. No hace commit: eso es del UoW."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def obtener(self, libro_id: int) -> Libro | None:
        return await self.session.get(Libro, libro_id)

    async def obtener_con_relaciones(self, libro_id: int) -> Libro | None:
        # Cantidad fija de consultas, sin importar cuántos autores tenga (C-07):
        #   1) libro JOIN editorial JOIN género -> joinedload (relaciones a uno)
        #   2) autorías JOIN autor              -> selectinload (colección) + joinedload (a uno)
        consulta = (
            select(Libro)
            .where(Libro.id == libro_id)
            .options(
                joinedload(Libro.editorial),
                joinedload(Libro.genero),
                selectinload(Libro.autorias).joinedload(LibroAutor.autor),
            )
            # Si el libro ya está en la sesión (recién creado o modificado), lo
            # recarga con sus relaciones en lugar de devolver la copia sin precargar.
            .execution_options(populate_existing=True)
        )
        return (await self.session.exec(consulta)).first()

    async def listar(
        self, limit: int, offset: int, titulo: str | None, genero_id: int | None
    ) -> Sequence[Libro]:
        # Una sola consulta: libro JOIN editorial JOIN género.
        consulta = select(Libro).options(joinedload(Libro.editorial), joinedload(Libro.genero))
        if genero_id is not None:
            consulta = consulta.where(Libro.genero_id == genero_id)
        if titulo:
            # RN-11: parámetro ligado, sin distinguir mayúsculas. autoescape hace
            # que % y _ del texto buscado se tomen literalmente.
            consulta = consulta.where(Libro.titulo.icontains(titulo, autoescape=True))
        consulta = consulta.order_by(Libro.id).limit(limit).offset(offset)
        return (await self.session.exec(consulta)).all()

    def agregar(self, libro: Libro) -> None:
        self.session.add(libro)
