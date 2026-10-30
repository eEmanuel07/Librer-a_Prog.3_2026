from fastapi import APIRouter, Depends, HTTPException, status

from app.core.errors import Conflicto, NoEncontrado
from app.core.pagination import Paginacion, paginacion
from app.core.uow import UnitOfWork, get_uow
from app.modules.generos import service
from app.modules.generos.schemas import GeneroCreate, GeneroRead, LibroDeGenero

router = APIRouter(prefix="/generos", tags=["generos"])


@router.post("/", response_model=GeneroRead, status_code=status.HTTP_201_CREATED)
async def crear_genero(
    datos: GeneroCreate,
    uow: UnitOfWork = Depends(get_uow),
) -> GeneroRead:
    try:
        return await service.crear_genero(uow, datos)
    except Conflicto as error:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=error.mensaje) from None


@router.get("/", response_model=list[GeneroRead])
async def listar_generos(
    pag: Paginacion = Depends(paginacion),
    uow: UnitOfWork = Depends(get_uow),
) -> list[GeneroRead]:
    return await service.listar_generos(uow, limit=pag.limit, offset=pag.offset)


@router.get("/{genero_id}/libros", response_model=list[LibroDeGenero])
async def listar_libros_de_genero(
    genero_id: int,
    pag: Paginacion = Depends(paginacion),
    uow: UnitOfWork = Depends(get_uow),
) -> list[LibroDeGenero]:
    try:
        return await service.listar_libros_de_genero(uow, genero_id, limit=pag.limit, offset=pag.offset)
    except NoEncontrado as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=error.mensaje) from None
