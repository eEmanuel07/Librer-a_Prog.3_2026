from fastapi import APIRouter, Depends, status
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.database import get_session
from app.core.pagination import Paginacion, paginacion
from app.modules.editoriales import service
from app.modules.editoriales.schemas import EditorialCreate, EditorialRead, EditorialUpdate, LibroDeEditorial

router = APIRouter(prefix="/editoriales", tags=["editoriales"])


@router.post("/", response_model=EditorialRead, status_code=status.HTTP_201_CREATED)
async def crear_editorial(
    datos: EditorialCreate,
    session: AsyncSession = Depends(get_session),
) -> EditorialRead:
    return await service.crear_editorial(session, datos)


@router.get("/", response_model=list[EditorialRead])
async def listar_editoriales(
    pag: Paginacion = Depends(paginacion),
    session: AsyncSession = Depends(get_session),
) -> list[EditorialRead]:
    return await service.listar_editoriales(session, limit=pag.limit, offset=pag.offset)


@router.get("/{editorial_id}", response_model=EditorialRead)
async def obtener_editorial(
    editorial_id: int,
    session: AsyncSession = Depends(get_session),
) -> EditorialRead:
    return await service.obtener_editorial(session, editorial_id)


@router.patch("/{editorial_id}", response_model=EditorialRead)
async def actualizar_editorial(
    editorial_id: int,
    datos: EditorialUpdate,
    session: AsyncSession = Depends(get_session),
) -> EditorialRead:
    return await service.actualizar_editorial(session, editorial_id, datos)


@router.get("/{editorial_id}/libros", response_model=list[LibroDeEditorial])
async def listar_libros_de_editorial(
    editorial_id: int,
    pag: Paginacion = Depends(paginacion),
    session: AsyncSession = Depends(get_session),
) -> list[LibroDeEditorial]:
    return await service.listar_libros_de_editorial(
        session, editorial_id, limit=pag.limit, offset=pag.offset
    )
