from fastapi import APIRouter, Depends, HTTPException, status

from app.core.errors import Conflicto, NoEncontrado
from app.core.pagination import Paginacion, paginacion
from app.core.uow import UnitOfWork, get_uow
from app.modules.clientes import service
from app.modules.clientes.schemas import ClienteCreate, ClienteRead, ClienteUpdate, PerfilCreate, PerfilRead
from app.modules.ventas.schemas import VentaRead

router = APIRouter(prefix="/clientes", tags=["clientes"])


@router.post("/", response_model=ClienteRead, status_code=status.HTTP_201_CREATED)
async def crear_cliente(
    datos: ClienteCreate,
    uow: UnitOfWork = Depends(get_uow),
) -> ClienteRead:
    try:
        return await service.crear_cliente(uow, datos)
    except Conflicto as error:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=error.mensaje) from None


@router.get("/{cliente_id}", response_model=ClienteRead)
async def obtener_cliente(
    cliente_id: int,
    uow: UnitOfWork = Depends(get_uow),
) -> ClienteRead:
    try:
        return await service.obtener_cliente(uow, cliente_id)
    except NoEncontrado as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=error.mensaje) from None


@router.patch("/{cliente_id}", response_model=ClienteRead)
async def actualizar_cliente(
    cliente_id: int,
    datos: ClienteUpdate,
    uow: UnitOfWork = Depends(get_uow),
) -> ClienteRead:
    try:
        return await service.actualizar_cliente(uow, cliente_id, datos)
    except NoEncontrado as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=error.mensaje) from None
    except Conflicto as error:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=error.mensaje) from None


@router.post("/{cliente_id}/perfil", response_model=PerfilRead, status_code=status.HTTP_201_CREATED)
async def crear_perfil(
    cliente_id: int,
    datos: PerfilCreate,
    uow: UnitOfWork = Depends(get_uow),
) -> PerfilRead:
    try:
        return await service.crear_perfil(uow, cliente_id, datos)
    except NoEncontrado as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=error.mensaje) from None
    except Conflicto as error:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=error.mensaje) from None


@router.get("/{cliente_id}/ventas", response_model=list[VentaRead])
async def listar_ventas_de_cliente(
    cliente_id: int,
    pag: Paginacion = Depends(paginacion),
    uow: UnitOfWork = Depends(get_uow),
) -> list[VentaRead]:
    try:
        return await service.listar_ventas_de_cliente(
            uow, cliente_id, limit=pag.limit, offset=pag.offset
        )
    except NoEncontrado as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=error.mensaje) from None
