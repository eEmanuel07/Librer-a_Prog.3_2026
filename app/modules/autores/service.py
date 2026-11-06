from app.core.errors import NoEncontrado
from app.modules.autores.models import Autor
from app.modules.autores.schemas import AutorCreate, AutorRead, AutorUpdate, LibroDeAutor
from app.modules.autores.unit_of_work import AutorUnitOfWork

_DETALLE_NO_EXISTE = "El autor no existe"


async def _buscar(uow: AutorUnitOfWork, autor_id: int) -> Autor:
    # auxiliar: se llama dentro de un bloque ya abierto, no abre el suyo
    autor = await uow.autores.obtener(autor_id)
    if autor is None:
        raise NoEncontrado(_DETALLE_NO_EXISTE)
    return autor


# autor no tiene UNIQUE, FK ni CHECK: no hay un 409 propio que dar, así que
# las escrituras no usan con_mensajes() (quedan los mensajes por defecto)
async def crear_autor(uow: AutorUnitOfWork, datos: AutorCreate) -> AutorRead:
    autor = Autor(**datos.model_dump())
    async with uow:
        uow.autores.agregar(autor)
    return AutorRead.model_validate(autor, from_attributes=True)


async def obtener_autor(uow: AutorUnitOfWork, autor_id: int) -> AutorRead:
    async with uow:
        autor = await _buscar(uow, autor_id)
        return AutorRead.model_validate(autor, from_attributes=True)


async def actualizar_autor(uow: AutorUnitOfWork, autor_id: int, datos: AutorUpdate) -> AutorRead:
    async with uow:
        autor = await _buscar(uow, autor_id)
        for campo, valor in datos.model_dump(exclude_unset=True).items():
            setattr(autor, campo, valor)
    return AutorRead.model_validate(autor, from_attributes=True)


async def listar_libros_de_autor(
    uow: AutorUnitOfWork, autor_id: int, limit: int, offset: int
) -> list[LibroDeAutor]:
    async with uow:
        await _buscar(uow, autor_id)
        autorias = await uow.autores.listar_autorias(autor_id, limit, offset)
        return [LibroDeAutor.desde_modelo(a) for a in autorias]
