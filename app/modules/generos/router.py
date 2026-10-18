from fastapi import APIRouter, Depends, status
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.database import get_session
from app.core.pagination import Paginacion, paginacion
from app.modules.generos import service
from app.modules.generos.schemas import GeneroCreate, GeneroRead, LibroDeGenero

router = APIRouter(prefix="/generos", tags=["generos"])


@router.post("/", response_model=GeneroRead, status_code=status.HTTP_201_CREATED)
async def crear_genero(
    datos: GeneroCreate,
    session: AsyncSession = Depends(get_session),
) -> GeneroRead:
    return await service.crear_genero(session, datos)


@router.get("/", response_model=list[GeneroRead])
async def listar_generos(
    pag: Paginacion = Depends(paginacion),
    session: AsyncSession = Depends(get_session),
) -> list[GeneroRead]:
    return await service.listar_generos(session, limit=pag.limit, offset=pag.offset)


@router.get("/{genero_id}/libros", response_model=list[LibroDeGenero])
async def listar_libros_de_genero(
    genero_id: int,
    pag: Paginacion = Depends(paginacion),
    session: AsyncSession = Depends(get_session),
) -> list[LibroDeGenero]:
    return await service.listar_libros_de_genero(session, genero_id, limit=pag.limit, offset=pag.offset)
