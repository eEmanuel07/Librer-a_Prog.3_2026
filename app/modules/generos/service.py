from app.core.errors import NoEncontrado
from app.modules.generos.models import Genero
from app.modules.generos.schemas import GeneroCreate, GeneroRead, LibroDeGenero
from app.modules.generos.unit_of_work import GeneroUnitOfWork

_DETALLE_UNIQUE = "Ya existe un género con ese nombre"
_DETALLE_NO_EXISTE = "El género no existe"


async def crear_genero(uow: GeneroUnitOfWork, datos: GeneroCreate) -> GeneroRead:
    genero = Genero(**datos.model_dump())
    # el nombre repetido lo rechaza el UNIQUE de la base al confirmar (409)
    async with uow.con_mensajes(unique=_DETALLE_UNIQUE):
        uow.generos.agregar(genero)
    return GeneroRead.model_validate(genero, from_attributes=True)


async def listar_generos(uow: GeneroUnitOfWork, limit: int, offset: int) -> list[GeneroRead]:
    async with uow:
        generos = await uow.generos.listar(limit, offset)
        return [GeneroRead.model_validate(g, from_attributes=True) for g in generos]


async def listar_libros_de_genero(
    uow: GeneroUnitOfWork, genero_id: int, limit: int, offset: int
) -> list[LibroDeGenero]:
    async with uow:
        if await uow.generos.obtener(genero_id) is None:
            raise NoEncontrado(_DETALLE_NO_EXISTE)
        libros = await uow.generos.listar_libros(genero_id, limit, offset)
        return [LibroDeGenero.model_validate(libro, from_attributes=True) for libro in libros]
