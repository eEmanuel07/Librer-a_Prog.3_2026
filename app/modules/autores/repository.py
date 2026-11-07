from collections.abc import Sequence

from sqlalchemy.orm import joinedload
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.paginacion import ParametrosPagina, paginar
from app.modules.autores.models import Autor
from app.modules.libros.models import Libro, LibroAutor


class AutorRepository:
    """Solo consultas sobre autores. No hace commit: eso es del UoW."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def obtener(self, autor_id: int) -> Autor | None:
        return await self.session.get(Autor, autor_id)

    def agregar(self, autor: Autor) -> None:
        self.session.add(autor)

    async def listar_autorias(self, autor_id: int, limit: int, offset: int) -> Sequence[LibroAutor]:
        # se parte de libro_autor porque el rol y el orden son de la relacion;
        # joinedload trae el libro en la misma consulta (sin N+1)
        consulta = (
            select(LibroAutor)
            .join(Libro, Libro.id == LibroAutor.libro_id)
            .where(LibroAutor.autor_id == autor_id, Libro.borrado_en.is_(None))
            .options(joinedload(LibroAutor.libro))
            .order_by(LibroAutor.libro_id)
            .limit(limit)
            .offset(offset)
        )
        return (await self.session.exec(consulta)).all()

    async def listar_autorias_pagina(
        self, autor_id: int, params: ParametrosPagina
    ) -> tuple[Sequence[LibroAutor], int]:
        consulta = (
            select(LibroAutor)
            .join(Libro, Libro.id == LibroAutor.libro_id)
            .where(LibroAutor.autor_id == autor_id, Libro.borrado_en.is_(None))
            .options(joinedload(LibroAutor.libro))
            .order_by(LibroAutor.libro_id)
        )
        return await paginar(self.session, consulta, params)
