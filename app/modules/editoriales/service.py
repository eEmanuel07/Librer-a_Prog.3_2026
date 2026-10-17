from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.errors import http_409_por_integridad
from app.modules.editoriales.models import Editorial
from app.modules.editoriales.schemas import EditorialCreate, EditorialRead, EditorialUpdate, LibroDeEditorial
from app.modules.libros.models import Libro

_DETALLE_UNIQUE = "Ya existe una editorial con ese nombre"


def _no_existe() -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="La editorial no existe")


async def _buscar(session: AsyncSession, editorial_id: int) -> Editorial:
    editorial = await session.get(Editorial, editorial_id)
    if editorial is None:
        raise _no_existe()
    return editorial


async def _guardar(session: AsyncSession, editorial: Editorial) -> None:
    session.add(editorial)
    try:
        await session.commit()
    except IntegrityError as error:
        await session.rollback()
        # el nombre repetido lo rechaza el UNIQUE de la base, no se consulta antes
        raise http_409_por_integridad(error, detalle_unique=_DETALLE_UNIQUE) from None


async def crear_editorial(session: AsyncSession, datos: EditorialCreate) -> EditorialRead:
    editorial = Editorial(**datos.model_dump())
    await _guardar(session, editorial)
    return EditorialRead.model_validate(editorial, from_attributes=True)


async def listar_editoriales(session: AsyncSession, limit: int, offset: int) -> list[EditorialRead]:
    consulta = select(Editorial).order_by(Editorial.id).limit(limit).offset(offset)
    editoriales = (await session.exec(consulta)).all()
    return [EditorialRead.model_validate(e, from_attributes=True) for e in editoriales]


async def obtener_editorial(session: AsyncSession, editorial_id: int) -> EditorialRead:
    editorial = await _buscar(session, editorial_id)
    return EditorialRead.model_validate(editorial, from_attributes=True)


async def actualizar_editorial(
    session: AsyncSession, editorial_id: int, datos: EditorialUpdate
) -> EditorialRead:
    editorial = await _buscar(session, editorial_id)
    for campo, valor in datos.model_dump(exclude_unset=True).items():
        setattr(editorial, campo, valor)
    await _guardar(session, editorial)
    return EditorialRead.model_validate(editorial, from_attributes=True)


async def listar_libros_de_editorial(
    session: AsyncSession, editorial_id: int, limit: int, offset: int
) -> list[LibroDeEditorial]:
    # primero se confirma que exista para poder dar 404 en vez de una lista vacia
    await _buscar(session, editorial_id)
    consulta = (
        select(Libro)
        .where(Libro.editorial_id == editorial_id)
        .order_by(Libro.id)
        .limit(limit)
        .offset(offset)
    )
    libros = (await session.exec(consulta)).all()
    return [LibroDeEditorial.model_validate(libro, from_attributes=True) for libro in libros]
