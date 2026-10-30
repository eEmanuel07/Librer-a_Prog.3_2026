from app.core.errors import NoEncontrado
from app.core.uow import UnitOfWork
from app.modules.editoriales.models import Editorial
from app.modules.editoriales.schemas import EditorialCreate, EditorialRead, EditorialUpdate, LibroDeEditorial

_DETALLE_UNIQUE = "Ya existe una editorial con ese nombre"
_DETALLE_NO_EXISTE = "La editorial no existe"


async def _buscar(uow: UnitOfWork, editorial_id: int) -> Editorial:
    editorial = await uow.editoriales.obtener(editorial_id)
    if editorial is None:
        raise NoEncontrado(_DETALLE_NO_EXISTE)
    return editorial


async def crear_editorial(uow: UnitOfWork, datos: EditorialCreate) -> EditorialRead:
    editorial = Editorial(**datos.model_dump())
    uow.editoriales.agregar(editorial)
    await uow.commit(detalle_unique=_DETALLE_UNIQUE)
    return EditorialRead.model_validate(editorial, from_attributes=True)


async def listar_editoriales(uow: UnitOfWork, limit: int, offset: int) -> list[EditorialRead]:
    editoriales = await uow.editoriales.listar(limit, offset)
    return [EditorialRead.model_validate(e, from_attributes=True) for e in editoriales]


async def obtener_editorial(uow: UnitOfWork, editorial_id: int) -> EditorialRead:
    editorial = await _buscar(uow, editorial_id)
    return EditorialRead.model_validate(editorial, from_attributes=True)


async def actualizar_editorial(
    uow: UnitOfWork, editorial_id: int, datos: EditorialUpdate
) -> EditorialRead:
    editorial = await _buscar(uow, editorial_id)
    for campo, valor in datos.model_dump(exclude_unset=True).items():
        setattr(editorial, campo, valor)
    await uow.commit(detalle_unique=_DETALLE_UNIQUE)
    return EditorialRead.model_validate(editorial, from_attributes=True)


async def listar_libros_de_editorial(
    uow: UnitOfWork, editorial_id: int, limit: int, offset: int
) -> list[LibroDeEditorial]:
    # primero se confirma que exista para poder dar 404 en vez de una lista vacia
    await _buscar(uow, editorial_id)
    libros = await uow.editoriales.listar_libros(editorial_id, limit, offset)
    return [LibroDeEditorial.model_validate(libro, from_attributes=True) for libro in libros]
