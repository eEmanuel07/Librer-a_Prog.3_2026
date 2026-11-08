from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status

from app.core.dependencies import get_usuario_actual, requiere_rol
from app.core.errors import Conflicto, NoEncontrado, SinPermiso
from app.core.paginacion import Pagina, ParametrosPagina, parametros_pagina
from app.modules.usuarios.models import Usuario
from app.modules.ventas import service
from app.modules.ventas.schemas import VentaCreate, VentaRead, VentaResumen
from app.modules.ventas.unit_of_work import VentaUnitOfWork, get_ventas_uow

router = APIRouter(prefix="/ventas", tags=["ventas"])
# /mis-ventas cuelga de la raíz, no de /ventas: va en un router aparte del mismo módulo.
router_mis_ventas = APIRouter(tags=["ventas"])

# No hay PATCH ni DELETE: las ventas registran un hecho y no se modifican (RN-08).


@router.post("/", response_model=VentaRead, status_code=status.HTTP_201_CREATED)
async def crear_venta(
    datos: VentaCreate,
    tareas: BackgroundTasks,
    uow: VentaUnitOfWork = Depends(get_ventas_uow),
    # Sólo el personal registra ventas (403 para un cliente). Quien la registra
    # queda en cada movimiento de stock. requiere_rol usa la misma sesión que el
    # Unit of Work (get_session se resuelve una vez por petición).
    usuario: Usuario = Depends(requiere_rol("VENDEDOR", "ADMIN")),
) -> VentaRead:
    try:
        venta = await service.crear_venta(uow, datos, usuario.id)
    except Conflicto as error:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=error.mensaje) from None
    # Llegar acá quiere decir que la venta se confirmó: si no, el 409 ya salió
    # arriba y no se agenda nada. Se agenda con datos simples (no la sesión ni el
    # UoW) y corre después de enviar la respuesta.
    tareas.add_task(service.avisar_comprobante, venta.id, venta.cliente.email, venta.total)
    return venta


@router.get("/", response_model=Pagina[VentaResumen])
async def listar_ventas(
    params: ParametrosPagina = Depends(parametros_pagina),  # page y size: 422 si no cumplen
    uow: VentaUnitOfWork = Depends(get_ventas_uow),
    _personal: Usuario = Depends(requiere_rol("VENDEDOR", "ADMIN")),
) -> Pagina[VentaResumen]:
    return await service.listar_ventas(uow, params)


@router.get("/{venta_id}", response_model=VentaRead)
async def obtener_venta(
    venta_id: int,
    uow: VentaUnitOfWork = Depends(get_ventas_uow),
    # Sin requiere_rol: el dueño la ve sin ser personal. Decide el service (RN-14).
    usuario: Usuario = Depends(get_usuario_actual),
) -> VentaRead:
    try:
        return await service.ver_venta(uow, venta_id, usuario)
    except NoEncontrado as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=error.mensaje) from None
    except SinPermiso as error:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=error.mensaje) from None


@router_mis_ventas.get("/mis-ventas", response_model=Pagina[VentaResumen])
async def listar_mis_ventas(
    params: ParametrosPagina = Depends(parametros_pagina),
    uow: VentaUnitOfWork = Depends(get_ventas_uow),
    # Lo propio sólo pide estar autenticado (RN-14).
    usuario: Usuario = Depends(get_usuario_actual),
) -> Pagina[VentaResumen]:
    return await service.listar_mis_ventas(uow, params, usuario)
