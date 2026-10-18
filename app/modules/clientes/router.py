from fastapi import APIRouter, Depends, status
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.database import get_session
from app.core.pagination import Paginacion, paginacion
from app.modules.clientes import service
from app.modules.clientes.schemas import ClienteCreate, ClienteRead, ClienteUpdate, PerfilCreate, PerfilRead
from app.modules.ventas.schemas import VentaRead

router = APIRouter(prefix="/clientes", tags=["clientes"])


@router.post("/", response_model=ClienteRead, status_code=status.HTTP_201_CREATED)
async def crear_cliente(
    datos: ClienteCreate,
    session: AsyncSession = Depends(get_session),
) -> ClienteRead:
    return await service.crear_cliente(session, datos)


@router.get("/{cliente_id}", response_model=ClienteRead)
async def obtener_cliente(
    cliente_id: int,
    session: AsyncSession = Depends(get_session),
) -> ClienteRead:
    return await service.obtener_cliente(session, cliente_id)


@router.patch("/{cliente_id}", response_model=ClienteRead)
async def actualizar_cliente(
    cliente_id: int,
    datos: ClienteUpdate,
    session: AsyncSession = Depends(get_session),
) -> ClienteRead:
    return await service.actualizar_cliente(session, cliente_id, datos)


@router.post("/{cliente_id}/perfil", response_model=PerfilRead, status_code=status.HTTP_201_CREATED)
async def crear_perfil(
    cliente_id: int,
    datos: PerfilCreate,
    session: AsyncSession = Depends(get_session),
) -> PerfilRead:
    return await service.crear_perfil(session, cliente_id, datos)


@router.get("/{cliente_id}/ventas", response_model=list[VentaRead])
async def listar_ventas_de_cliente(
    cliente_id: int,
    pag: Paginacion = Depends(paginacion),
    session: AsyncSession = Depends(get_session),
) -> list[VentaRead]:
    return await service.listar_ventas_de_cliente(
        session, cliente_id, limit=pag.limit, offset=pag.offset
    )
