from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import joinedload, selectinload
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.errors import http_409_por_integridad
from app.modules.libros.models import Libro, LibroAutor
from app.modules.libros.schemas import (
    LibroCreate,
    LibroRead,
    LibroResumen,
    LibroUpdate,
)

# RN-12: mensajes propios para el 409; nunca el texto de la base.
_DETALLE_UNIQUE = "El ISBN ya existe o un autor figura dos veces en el libro"
_DETALLE_FK = "La editorial, el género o algún autor indicado no existe"
_DETALLE_CHECK = "Los datos del libro no cumplen las reglas del catálogo"


def _no_existe() -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="El libro no existe")


# ---------- Lecturas con precarga (sin N+1) ----------


async def obtener_libro(session: AsyncSession, libro_id: int) -> LibroRead:
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
    libro = (await session.exec(consulta)).first()
    if libro is None:
        raise _no_existe()
    return LibroRead.desde_modelo(libro)


async def listar_libros(
    session: AsyncSession,
    limit: int,
    offset: int,
    titulo: str | None,
    genero_id: int | None = None,
) -> list[LibroResumen]:
    # Una sola consulta: libro JOIN editorial JOIN género.
    consulta = select(Libro).options(joinedload(Libro.editorial), joinedload(Libro.genero))
    if genero_id is not None:
        consulta = consulta.where(Libro.genero_id == genero_id)
    if titulo:
        # RN-11: parámetro ligado, sin distinguir mayúsculas. autoescape hace
        # que % y _ del texto buscado se tomen literalmente.
        consulta = consulta.where(Libro.titulo.icontains(titulo, autoescape=True))
    consulta = consulta.order_by(Libro.id).limit(limit).offset(offset)
    libros = (await session.exec(consulta)).all()
    return [LibroResumen.desde_modelo(libro) for libro in libros]


# ---------- Escrituras ----------


async def crear_libro(session: AsyncSession, datos: LibroCreate) -> LibroRead:
    # Agregación: viajan los ids de la editorial, del género (opcional) y de cada autor. No se
    # consulta antes si existen: se escribe y, si la base rechaza la clave
    # foránea, se responde 409 (C-04).
    libro = Libro(
        isbn=datos.isbn,
        titulo=datos.titulo,
        precio=datos.precio,
        stock=datos.stock,
        editorial_id=datos.editorial_id,
        genero_id=datos.genero_id,
    )
    for autoria in datos.autores:
        libro.autorias.append(
            LibroAutor(autor_id=autoria.autor_id, rol=autoria.rol, orden=autoria.orden)
        )

    session.add(libro)
    try:
        await session.commit()
    except IntegrityError as error:
        await session.rollback()
        raise http_409_por_integridad(
            error,
            detalle_unique=_DETALLE_UNIQUE,  # RN-01 / C-02
            detalle_fk=_DETALLE_FK,
            detalle_check=_DETALLE_CHECK,
        ) from None

    return await obtener_libro(session, libro.id)


async def actualizar_libro(session: AsyncSession, libro_id: int, datos: LibroUpdate) -> LibroRead:
    libro = await session.get(Libro, libro_id)
    if libro is None:
        raise _no_existe()

    # PATCH: sólo los campos enviados.
    for campo, valor in datos.model_dump(exclude_unset=True).items():
        setattr(libro, campo, valor)

    session.add(libro)
    try:
        await session.commit()
    except IntegrityError as error:
        await session.rollback()
        raise http_409_por_integridad(
            error,
            detalle_unique=_DETALLE_UNIQUE,
            detalle_fk=_DETALLE_FK,
            detalle_check=_DETALLE_CHECK,
        ) from None

    return await obtener_libro(session, libro_id)
