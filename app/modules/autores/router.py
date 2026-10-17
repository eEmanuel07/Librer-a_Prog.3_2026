from fastapi import APIRouter, Depends, status
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.database import get_session
from app.core.pagination import Paginacion, paginacion
from app.modules.autores import service
from app.modules.autores.schemas import AutorCreate, AutorRead, AutorUpdate, LibroDeAutor

router = APIRouter(prefix="/autores", tags=["autores"])


@router.post("/", response_model=AutorRead, status_code=status.HTTP_201_CREATED)
async def crear_autor(
    datos: AutorCreate,
    session: AsyncSession = Depends(get_session),
) -> AutorRead:
    return await service.crear_autor(session, datos)


@router.get("/{autor_id}", response_model=AutorRead)
async def obtener_autor(
    autor_id: int,
    session: AsyncSession = Depends(get_session),
) -> AutorRead:
    return await service.obtener_autor(session, autor_id)


@router.patch("/{autor_id}", response_model=AutorRead)
async def actualizar_autor(
    autor_id: int,
    datos: AutorUpdate,
    session: AsyncSession = Depends(get_session),
) -> AutorRead:
    return await service.actualizar_autor(session, autor_id, datos)


@router.get("/{autor_id}/libros", response_model=list[LibroDeAutor])
async def listar_libros_de_autor(
    autor_id: int,
    pag: Paginacion = Depends(paginacion),
    session: AsyncSession = Depends(get_session),
) -> list[LibroDeAutor]:
    return await service.listar_libros_de_autor(session, autor_id, limit=pag.limit, offset=pag.offset)
