from fastapi import APIRouter, Depends, HTTPException, status

from app.core.errors import Conflicto, NoEncontrado
from app.core.pagination import Paginacion, paginacion
from app.core.uow import UnitOfWork, get_uow
from app.modules.autores import service
from app.modules.autores.schemas import AutorCreate, AutorRead, AutorUpdate, LibroDeAutor

router = APIRouter(prefix="/autores", tags=["autores"])


@router.post("/", response_model=AutorRead, status_code=status.HTTP_201_CREATED)
async def crear_autor(
    datos: AutorCreate,
    uow: UnitOfWork = Depends(get_uow),
) -> AutorRead:
    try:
        return await service.crear_autor(uow, datos)
    except Conflicto as error:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=error.mensaje) from None


@router.get("/{autor_id}", response_model=AutorRead)
async def obtener_autor(
    autor_id: int,
    uow: UnitOfWork = Depends(get_uow),
) -> AutorRead:
    try:
        return await service.obtener_autor(uow, autor_id)
    except NoEncontrado as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=error.mensaje) from None


@router.patch("/{autor_id}", response_model=AutorRead)
async def actualizar_autor(
    autor_id: int,
    datos: AutorUpdate,
    uow: UnitOfWork = Depends(get_uow),
) -> AutorRead:
    try:
        return await service.actualizar_autor(uow, autor_id, datos)
    except NoEncontrado as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=error.mensaje) from None
    except Conflicto as error:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=error.mensaje) from None


@router.get("/{autor_id}/libros", response_model=list[LibroDeAutor])
async def listar_libros_de_autor(
    autor_id: int,
    pag: Paginacion = Depends(paginacion),
    uow: UnitOfWork = Depends(get_uow),
) -> list[LibroDeAutor]:
    try:
        return await service.listar_libros_de_autor(uow, autor_id, limit=pag.limit, offset=pag.offset)
    except NoEncontrado as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=error.mensaje) from None
