from fastapi import APIRouter, BackgroundTasks, Depends, status
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.database import get_session
from app.core.pagination import Paginacion, paginacion
from app.modules.ventas import service
from app.modules.ventas.schemas import VentaCreate, VentaRead, VentaResumen

router = APIRouter(prefix="/ventas", tags=["ventas"])

# No hay PATCH ni DELETE: las ventas registran un hecho y no se modifican (RN-08).


@router.post("/", response_model=VentaRead, status_code=status.HTTP_201_CREATED)
async def crear_venta(
    datos: VentaCreate,
    tareas: BackgroundTasks,
    session: AsyncSession = Depends(get_session),
) -> VentaRead:
    venta = await service.crear_venta(session, datos)
    # Se agenda el aviso; corre después de enviar la respuesta.
    tareas.add_task(service.avisar_comprobante, venta.id, venta.cliente.email, venta.total)
    return venta


@router.get("/", response_model=list[VentaResumen])
async def listar_ventas(
    pag: Paginacion = Depends(paginacion),  # RN-10: helper común
    session: AsyncSession = Depends(get_session),
) -> list[VentaResumen]:
    return await service.listar_ventas(session, limit=pag.limit, offset=pag.offset)


@router.get("/{venta_id}", response_model=VentaRead)
async def obtener_venta(
    venta_id: int,
    session: AsyncSession = Depends(get_session),
) -> VentaRead:
    return await service.obtener_venta(session, venta_id)
