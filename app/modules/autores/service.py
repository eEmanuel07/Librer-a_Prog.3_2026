from app.core.errors import NoEncontrado
from app.core.uow import UnitOfWork
from app.modules.autores.models import Autor
from app.modules.autores.schemas import AutorCreate, AutorRead, AutorUpdate, LibroDeAutor

_DETALLE_NO_EXISTE = "El autor no existe"


async def _buscar(uow: UnitOfWork, autor_id: int) -> Autor:
    autor = await uow.autores.obtener(autor_id)
    if autor is None:
        raise NoEncontrado(_DETALLE_NO_EXISTE)
    return autor


# autor no tiene UNIQUE ni CHECK: el commit no tiene un 409 propio que dar
async def crear_autor(uow: UnitOfWork, datos: AutorCreate) -> AutorRead:
    autor = Autor(**datos.model_dump())
    uow.autores.agregar(autor)
    await uow.commit()
    return AutorRead.model_validate(autor, from_attributes=True)


async def obtener_autor(uow: UnitOfWork, autor_id: int) -> AutorRead:
    autor = await _buscar(uow, autor_id)
    return AutorRead.model_validate(autor, from_attributes=True)


async def actualizar_autor(uow: UnitOfWork, autor_id: int, datos: AutorUpdate) -> AutorRead:
    autor = await _buscar(uow, autor_id)
    for campo, valor in datos.model_dump(exclude_unset=True).items():
        setattr(autor, campo, valor)
    await uow.commit()
    return AutorRead.model_validate(autor, from_attributes=True)


async def listar_libros_de_autor(
    uow: UnitOfWork, autor_id: int, limit: int, offset: int
) -> list[LibroDeAutor]:
    await _buscar(uow, autor_id)
    autorias = await uow.autores.listar_autorias(autor_id, limit, offset)
    return [LibroDeAutor.desde_modelo(a) for a in autorias]
