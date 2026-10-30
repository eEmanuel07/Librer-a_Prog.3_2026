from app.core.errors import NoEncontrado
from app.core.uow import UnitOfWork
from app.modules.generos.models import Genero
from app.modules.generos.schemas import GeneroCreate, GeneroRead, LibroDeGenero

_DETALLE_UNIQUE = "Ya existe un género con ese nombre"
_DETALLE_NO_EXISTE = "El género no existe"


async def crear_genero(uow: UnitOfWork, datos: GeneroCreate) -> GeneroRead:
    genero = Genero(**datos.model_dump())
    uow.generos.agregar(genero)
    await uow.commit(detalle_unique=_DETALLE_UNIQUE)
    return GeneroRead.model_validate(genero, from_attributes=True)


async def listar_generos(uow: UnitOfWork, limit: int, offset: int) -> list[GeneroRead]:
    generos = await uow.generos.listar(limit, offset)
    return [GeneroRead.model_validate(g, from_attributes=True) for g in generos]


async def listar_libros_de_genero(
    uow: UnitOfWork, genero_id: int, limit: int, offset: int
) -> list[LibroDeGenero]:
    if await uow.generos.obtener(genero_id) is None:
        raise NoEncontrado(_DETALLE_NO_EXISTE)
    libros = await uow.generos.listar_libros(genero_id, limit, offset)
    return [LibroDeGenero.model_validate(libro, from_attributes=True) for libro in libros]
