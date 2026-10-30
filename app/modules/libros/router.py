from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.errors import Conflicto, NoEncontrado
from app.core.pagination import Paginacion, paginacion
from app.core.uow import UnitOfWork, get_uow
from app.modules.libros import service
from app.modules.libros.schemas import LibroCreate, LibroRead, LibroResumen, LibroUpdate

router = APIRouter(prefix="/libros", tags=["libros"])


@router.post("/", response_model=LibroRead, status_code=status.HTTP_201_CREATED)
async def crear_libro(
    datos: LibroCreate,
    uow: UnitOfWork = Depends(get_uow),
) -> LibroRead:
    try:
        return await service.crear_libro(uow, datos)
    except Conflicto as error:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=error.mensaje) from None


@router.get("/", response_model=list[LibroResumen])
async def listar_libros(
    titulo: str | None = Query(default=None, description="Parte del título, sin distinguir mayúsculas"),
    genero_id: int | None = Query(default=None, description="Sólo los libros de este género"),
    pag: Paginacion = Depends(paginacion),  # RN-10: helper común
    uow: UnitOfWork = Depends(get_uow),
) -> list[LibroResumen]:
    return await service.listar_libros(
        uow, limit=pag.limit, offset=pag.offset, titulo=titulo, genero_id=genero_id
    )


@router.get("/{libro_id}", response_model=LibroRead)
async def obtener_libro(
    libro_id: int,
    uow: UnitOfWork = Depends(get_uow),
) -> LibroRead:
    try:
        return await service.obtener_libro(uow, libro_id)
    except NoEncontrado as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=error.mensaje) from None


@router.patch("/{libro_id}", response_model=LibroRead)
async def actualizar_libro(
    libro_id: int,
    datos: LibroUpdate,
    uow: UnitOfWork = Depends(get_uow),
) -> LibroRead:
    try:
        return await service.actualizar_libro(uow, libro_id, datos)
    except NoEncontrado as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=error.mensaje) from None
    except Conflicto as error:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=error.mensaje) from None
