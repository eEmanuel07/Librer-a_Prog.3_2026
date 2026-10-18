from fastapi import APIRouter, Depends, Query, status
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.database import get_session
from app.core.pagination import Paginacion, paginacion
from app.modules.libros import service
from app.modules.libros.schemas import LibroCreate, LibroRead, LibroResumen, LibroUpdate

router = APIRouter(prefix="/libros", tags=["libros"])


@router.post("/", response_model=LibroRead, status_code=status.HTTP_201_CREATED)
async def crear_libro(
    datos: LibroCreate,
    session: AsyncSession = Depends(get_session),
) -> LibroRead:
    return await service.crear_libro(session, datos)


@router.get("/", response_model=list[LibroResumen])
async def listar_libros(
    titulo: str | None = Query(default=None, description="Parte del título, sin distinguir mayúsculas"),
    genero_id: int | None = Query(default=None, description="Sólo los libros de este género"),
    pag: Paginacion = Depends(paginacion),  # RN-10: helper común
    session: AsyncSession = Depends(get_session),
) -> list[LibroResumen]:
    return await service.listar_libros(
        session, limit=pag.limit, offset=pag.offset, titulo=titulo, genero_id=genero_id
    )


@router.get("/{libro_id}", response_model=LibroRead)
async def obtener_libro(
    libro_id: int,
    session: AsyncSession = Depends(get_session),
) -> LibroRead:
    return await service.obtener_libro(session, libro_id)


@router.patch("/{libro_id}", response_model=LibroRead)
async def actualizar_libro(
    libro_id: int,
    datos: LibroUpdate,
    session: AsyncSession = Depends(get_session),
) -> LibroRead:
    return await service.actualizar_libro(session, libro_id, datos)
