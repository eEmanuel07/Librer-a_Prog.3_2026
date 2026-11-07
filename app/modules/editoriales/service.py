from app.core.errors import NoEncontrado
from app.core.paginacion import Pagina, ParametrosPagina
from app.modules.editoriales.models import Editorial
from app.modules.editoriales.schemas import (
    EditorialCreate,
    EditorialRead,
    EditorialUpdate,
    LibroDeEditorial,
)
from app.modules.editoriales.unit_of_work import EditorialUnitOfWork

_DETALLE_UNIQUE = "Ya existe una editorial con ese nombre"
_DETALLE_NO_EXISTE = "La editorial no existe"


async def _buscar(uow: EditorialUnitOfWork, editorial_id: int) -> Editorial:
    # auxiliar: se llama dentro de un bloque ya abierto, no abre el suyo
    editorial = await uow.editoriales.obtener(editorial_id)
    if editorial is None:
        raise NoEncontrado(_DETALLE_NO_EXISTE)
    return editorial


async def crear_editorial(uow: EditorialUnitOfWork, datos: EditorialCreate) -> EditorialRead:
    editorial = Editorial(**datos.model_dump())
    # el nombre repetido lo rechaza el UNIQUE de la base al confirmar (409)
    async with uow.con_mensajes(unique=_DETALLE_UNIQUE):
        uow.editoriales.agregar(editorial)
    return EditorialRead.model_validate(editorial, from_attributes=True)


async def listar_editoriales(
    uow: EditorialUnitOfWork, params: ParametrosPagina
) -> Pagina[EditorialRead]:
    async with uow:
        editoriales, total = await uow.editoriales.listar_pagina(params)
        return Pagina.armar(
            [EditorialRead.model_validate(e, from_attributes=True) for e in editoriales],
            total,
            params,
        )


async def obtener_editorial(uow: EditorialUnitOfWork, editorial_id: int) -> EditorialRead:
    async with uow:
        editorial = await _buscar(uow, editorial_id)
        return EditorialRead.model_validate(editorial, from_attributes=True)


async def actualizar_editorial(
    uow: EditorialUnitOfWork, editorial_id: int, datos: EditorialUpdate
) -> EditorialRead:
    async with uow.con_mensajes(unique=_DETALLE_UNIQUE):
        editorial = await _buscar(uow, editorial_id)
        for campo, valor in datos.model_dump(exclude_unset=True).items():
            setattr(editorial, campo, valor)
    return EditorialRead.model_validate(editorial, from_attributes=True)


async def listar_libros_de_editorial(
    uow: EditorialUnitOfWork, editorial_id: int, params: ParametrosPagina
) -> Pagina[LibroDeEditorial]:
    async with uow:
        # primero se confirma que exista para poder dar 404 en vez de una lista vacia
        await _buscar(uow, editorial_id)
        libros, total = await uow.editoriales.listar_libros_pagina(editorial_id, params)
        return Pagina.armar(
            [LibroDeEditorial.model_validate(libro, from_attributes=True) for libro in libros],
            total,
            params,
        )
