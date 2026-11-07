from fastapi import APIRouter, Depends, HTTPException, status

from app.core.dependencies import requiere_rol
from app.core.errors import Conflicto, NoEncontrado
from app.core.paginacion import Pagina, ParametrosPagina, parametros_pagina
from app.modules.clientes import service
from app.modules.clientes.schemas import ClienteCreate, ClienteRead, ClienteUpdate, PerfilCreate, PerfilRead
from app.modules.clientes.unit_of_work import ClienteUnitOfWork, get_clientes_uow
from app.modules.ventas.schemas import VentaRead

# Todo el módulo es del personal (VENDEDOR o ADMIN): sin sesión 401, sin el rol
# 403. El rol se lee de la base en cada petición (RN-04), no del token.
router = APIRouter(
    prefix="/clientes",
    tags=["clientes"],
    dependencies=[Depends(requiere_rol("VENDEDOR", "ADMIN"))],
)


@router.post("/", response_model=ClienteRead, status_code=status.HTTP_201_CREATED)
async def crear_cliente(
    datos: ClienteCreate,
    uow: ClienteUnitOfWork = Depends(get_clientes_uow),
) -> ClienteRead:
    try:
        return await service.crear_cliente(uow, datos)
    except Conflicto as error:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=error.mensaje) from None


@router.get("/{cliente_id}", response_model=ClienteRead)
async def obtener_cliente(
    cliente_id: int,
    uow: ClienteUnitOfWork = Depends(get_clientes_uow),
) -> ClienteRead:
    try:
        return await service.obtener_cliente(uow, cliente_id)
    except NoEncontrado as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=error.mensaje) from None


@router.patch("/{cliente_id}", response_model=ClienteRead)
async def actualizar_cliente(
    cliente_id: int,
    datos: ClienteUpdate,
    uow: ClienteUnitOfWork = Depends(get_clientes_uow),
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
    uow: ClienteUnitOfWork = Depends(get_clientes_uow),
) -> PerfilRead:
    try:
        return await service.crear_perfil(uow, cliente_id, datos)
    except NoEncontrado as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=error.mensaje) from None
    except Conflicto as error:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=error.mensaje) from None


@router.get("/{cliente_id}/ventas", response_model=Pagina[VentaRead])
async def listar_ventas_de_cliente(
    cliente_id: int,
    params: ParametrosPagina = Depends(parametros_pagina),  # page y size: 422 si no cumplen
    uow: ClienteUnitOfWork = Depends(get_clientes_uow),
) -> Pagina[VentaRead]:
    try:
        return await service.listar_ventas_de_cliente(uow, cliente_id, params)
    except NoEncontrado as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=error.mensaje) from None
