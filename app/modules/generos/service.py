from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.errors import http_409_por_integridad
from app.modules.generos.models import Genero
from app.modules.generos.schemas import GeneroCreate, GeneroRead, LibroDeGenero
from app.modules.libros.models import Libro


async def crear_genero(session: AsyncSession, datos: GeneroCreate) -> GeneroRead:
    genero = Genero(**datos.model_dump())
    session.add(genero)
    try:
        await session.commit()
    except IntegrityError as error:
        await session.rollback()
        raise http_409_por_integridad(error, detalle_unique="Ya existe un género con ese nombre") from None
    return GeneroRead.model_validate(genero, from_attributes=True)


async def listar_generos(session: AsyncSession, limit: int, offset: int) -> list[GeneroRead]:
    consulta = select(Genero).order_by(Genero.id).limit(limit).offset(offset)
    generos = (await session.exec(consulta)).all()
    return [GeneroRead.model_validate(g, from_attributes=True) for g in generos]


async def listar_libros_de_genero(
    session: AsyncSession, genero_id: int, limit: int, offset: int
) -> list[LibroDeGenero]:
    if await session.get(Genero, genero_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="El género no existe")
    consulta = (
        select(Libro)
        .where(Libro.genero_id == genero_id)
        .order_by(Libro.id)
        .limit(limit)
        .offset(offset)
    )
    libros = (await session.exec(consulta)).all()
    return [LibroDeGenero.model_validate(libro, from_attributes=True) for libro in libros]
