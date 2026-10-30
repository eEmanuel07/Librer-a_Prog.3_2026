from fastapi import APIRouter, Depends, HTTPException, status

from app.core.errors import Conflicto, NoEncontrado
from app.core.pagination import Paginacion, paginacion
from app.core.uow import UnitOfWork, get_uow
from app.modules.editoriales import service
from app.modules.editoriales.schemas import EditorialCreate, EditorialRead, EditorialUpdate, LibroDeEditorial

router = APIRouter(prefix="/editoriales", tags=["editoriales"])


@router.post("/", response_model=EditorialRead, status_code=status.HTTP_201_CREATED)
async def crear_editorial(
    datos: EditorialCreate,
    uow: UnitOfWork = Depends(get_uow),
) -> EditorialRead:
    try:
        return await service.crear_editorial(uow, datos)
    except Conflicto as error:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=error.mensaje) from None


@router.get("/", response_model=list[EditorialRead])
async def listar_editoriales(
    pag: Paginacion = Depends(paginacion),
    uow: UnitOfWork = Depends(get_uow),
) -> list[EditorialRead]:
    return await service.listar_editoriales(uow, limit=pag.limit, offset=pag.offset)


@router.get("/{editorial_id}", response_model=EditorialRead)
async def obtener_editorial(
    editorial_id: int,
    uow: UnitOfWork = Depends(get_uow),
) -> EditorialRead:
    try:
        return await service.obtener_editorial(uow, editorial_id)
    except NoEncontrado as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=error.mensaje) from None


@router.patch("/{editorial_id}", response_model=EditorialRead)
async def actualizar_editorial(
    editorial_id: int,
    datos: EditorialUpdate,
    uow: UnitOfWork = Depends(get_uow),
) -> EditorialRead:
    try:
        return await service.actualizar_editorial(uow, editorial_id, datos)
    except NoEncontrado as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=error.mensaje) from None
    except Conflicto as error:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=error.mensaje) from None


@router.get("/{editorial_id}/libros", response_model=list[LibroDeEditorial])
async def listar_libros_de_editorial(
    editorial_id: int,
    pag: Paginacion = Depends(paginacion),
    uow: UnitOfWork = Depends(get_uow),
) -> list[LibroDeEditorial]:
    try:
        return await service.listar_libros_de_editorial(
            uow, editorial_id, limit=pag.limit, offset=pag.offset
        )
    except NoEncontrado as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=error.mensaje) from None
