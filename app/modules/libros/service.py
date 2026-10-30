from app.core.errors import NoEncontrado
from app.core.uow import UnitOfWork
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
_DETALLE_NO_EXISTE = "El libro no existe"


async def _commit(uow: UnitOfWork) -> None:
    await uow.commit(
        detalle_unique=_DETALLE_UNIQUE,  # RN-01 / C-02
        detalle_fk=_DETALLE_FK,
        detalle_check=_DETALLE_CHECK,
    )


# ---------- Lecturas con precarga (sin N+1) ----------


async def obtener_libro(uow: UnitOfWork, libro_id: int) -> LibroRead:
    libro = await uow.libros.obtener_con_relaciones(libro_id)
    if libro is None:
        raise NoEncontrado(_DETALLE_NO_EXISTE)
    return LibroRead.desde_modelo(libro)


async def listar_libros(
    uow: UnitOfWork,
    limit: int,
    offset: int,
    titulo: str | None,
    genero_id: int | None = None,
) -> list[LibroResumen]:
    libros = await uow.libros.listar(limit, offset, titulo, genero_id)
    return [LibroResumen.desde_modelo(libro) for libro in libros]


# ---------- Escrituras ----------


async def crear_libro(uow: UnitOfWork, datos: LibroCreate) -> LibroRead:
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

    uow.libros.agregar(libro)
    await _commit(uow)
    return await obtener_libro(uow, libro.id)


async def actualizar_libro(uow: UnitOfWork, libro_id: int, datos: LibroUpdate) -> LibroRead:
    libro = await uow.libros.obtener(libro_id)
    if libro is None:
        raise NoEncontrado(_DETALLE_NO_EXISTE)

    # PATCH: sólo los campos enviados; los autores no se tocan.
    for campo, valor in datos.model_dump(exclude_unset=True).items():
        setattr(libro, campo, valor)

    await _commit(uow)
    return await obtener_libro(uow, libro_id)
