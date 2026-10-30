from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status

from app.core.errors import Conflicto, NoEncontrado
from app.core.pagination import Paginacion, paginacion
from app.core.uow import UnitOfWork, get_uow
from app.modules.ventas import service
from app.modules.ventas.schemas import VentaCreate, VentaRead, VentaResumen

router = APIRouter(prefix="/ventas", tags=["ventas"])

# No hay PATCH ni DELETE: las ventas registran un hecho y no se modifican (RN-08).


@router.post("/", response_model=VentaRead, status_code=status.HTTP_201_CREATED)
async def crear_venta(
    datos: VentaCreate,
    tareas: BackgroundTasks,
    uow: UnitOfWork = Depends(get_uow),
) -> VentaRead:
    try:
        venta = await service.crear_venta(uow, datos)
    except Conflicto as error:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=error.mensaje) from None
    # El service ya hizo commit. Se agenda el aviso con datos simples (no la
    # sesión ni el UoW); corre después de enviar la respuesta.
    tareas.add_task(service.avisar_comprobante, venta.id, venta.cliente.email, venta.total)
    return venta


@router.get("/", response_model=list[VentaResumen])
async def listar_ventas(
    pag: Paginacion = Depends(paginacion),  # RN-10: helper común
    uow: UnitOfWork = Depends(get_uow),
) -> list[VentaResumen]:
    return await service.listar_ventas(uow, limit=pag.limit, offset=pag.offset)


@router.get("/{venta_id}", response_model=VentaRead)
async def obtener_venta(
    venta_id: int,
    uow: UnitOfWork = Depends(get_uow),
) -> VentaRead:
    try:
        return await service.obtener_venta(uow, venta_id)
    except NoEncontrado as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=error.mensaje) from None
