from fastapi import HTTPException, status
from sqlalchemy.orm import joinedload
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.modules.autores.models import Autor
from app.modules.autores.schemas import AutorCreate, AutorRead, AutorUpdate, LibroDeAutor
from app.modules.libros.models import LibroAutor


def _no_existe() -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="El autor no existe")


async def _buscar(session: AsyncSession, autor_id: int) -> Autor:
    autor = await session.get(Autor, autor_id)
    if autor is None:
        raise _no_existe()
    return autor


# autor no tiene UNIQUE ni CHECK, por eso aca no hace falta traducir IntegrityError
async def crear_autor(session: AsyncSession, datos: AutorCreate) -> AutorRead:
    autor = Autor(**datos.model_dump())
    session.add(autor)
    await session.commit()
    return AutorRead.model_validate(autor, from_attributes=True)


async def obtener_autor(session: AsyncSession, autor_id: int) -> AutorRead:
    autor = await _buscar(session, autor_id)
    return AutorRead.model_validate(autor, from_attributes=True)


async def actualizar_autor(session: AsyncSession, autor_id: int, datos: AutorUpdate) -> AutorRead:
    autor = await _buscar(session, autor_id)
    for campo, valor in datos.model_dump(exclude_unset=True).items():
        setattr(autor, campo, valor)
    session.add(autor)
    await session.commit()
    return AutorRead.model_validate(autor, from_attributes=True)


async def listar_libros_de_autor(
    session: AsyncSession, autor_id: int, limit: int, offset: int
) -> list[LibroDeAutor]:
    await _buscar(session, autor_id)
    # se parte de libro_autor porque el rol y el orden son de la relacion;
    # joinedload trae el libro en la misma consulta (sin N+1)
    consulta = (
        select(LibroAutor)
        .where(LibroAutor.autor_id == autor_id)
        .options(joinedload(LibroAutor.libro))
        .order_by(LibroAutor.libro_id)
        .limit(limit)
        .offset(offset)
    )
    autorias = (await session.exec(consulta)).all()
    return [LibroDeAutor.desde_modelo(a) for a in autorias]
