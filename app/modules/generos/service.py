from app.core.errors import NoEncontrado
from app.core.paginacion import Pagina, ParametrosPagina
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


async def listar_generos(
    uow: GeneroUnitOfWork, params: ParametrosPagina
) -> Pagina[GeneroRead]:
    async with uow:
        generos, total = await uow.generos.listar_pagina(params)
        return Pagina.armar(
            [GeneroRead.model_validate(g, from_attributes=True) for g in generos],
            total,
            params,
        )


async def listar_libros_de_genero(
    uow: GeneroUnitOfWork, genero_id: int, params: ParametrosPagina
) -> Pagina[LibroDeGenero]:
    async with uow:
        if await uow.generos.obtener(genero_id) is None:
            raise NoEncontrado(_DETALLE_NO_EXISTE)
        libros, total = await uow.generos.listar_libros_pagina(genero_id, params)
        return Pagina.armar(
            [LibroDeGenero.model_validate(libro, from_attributes=True) for libro in libros],
            total,
            params,
        )
