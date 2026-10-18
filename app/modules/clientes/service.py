from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import joinedload, selectinload
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.errors import http_409_por_integridad
from app.modules.clientes.models import Cliente, PerfilCliente
from app.modules.clientes.schemas import ClienteCreate, ClienteRead, ClienteUpdate, PerfilCreate, PerfilRead
from app.modules.ventas.models import RenglonVenta, Venta
from app.modules.ventas.schemas import VentaRead

# RN-12: mensajes propios para el 409; nunca el texto de la base.
_DETALLE_UNIQUE_EMAIL = "El email ya está en uso"
_DETALLE_UNIQUE_PERFIL = "El cliente ya tiene un perfil"


def _no_existe() -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="El cliente no existe")


# ---------- Lecturas con precarga (sin N+1) ----------


async def obtener_cliente(session: AsyncSession, cliente_id: int) -> ClienteRead:
    # Cantidad fija de consultas (C-07): una sola consulta con JOIN a perfil.
    consulta = (
        select(Cliente)
        .where(Cliente.id == cliente_id)
        .options(joinedload(Cliente.perfil))
        # Si el cliente ya está en la sesión (recién creado o modificado), lo
        # recarga con sus relaciones en lugar de devolver la copia sin precargar.
        .execution_options(populate_existing=True)
    )
    cliente = (await session.exec(consulta)).first()
    if cliente is None:
        raise _no_existe()
    return ClienteRead.desde_modelo(cliente)


async def listar_ventas_de_cliente(
    session: AsyncSession, cliente_id: int, limit: int, offset: int
) -> list[VentaRead]:
    # Primero se confirma que exista para poder dar 404 en vez de una lista vacia.
    await _buscar_cliente(session, cliente_id)

    # Una sola consulta para las ventas: venta JOIN cliente (joinedload, relación
    # a uno) + renglones JOIN libro (selectinload, colección). Cantidad fija de
    # consultas, tenga 1 o muchos renglones, sin N+1 (C-07).
    consulta = (
        select(Venta)
        .where(Venta.cliente_id == cliente_id)
        .options(
            joinedload(Venta.cliente),
            selectinload(Venta.renglones).joinedload(RenglonVenta.libro),
        )
        .order_by(Venta.id)
        .limit(limit)
        .offset(offset)
    )
    ventas = (await session.exec(consulta)).all()
    return [VentaRead.desde_modelo(v) for v in ventas]


# ---------- Escrituras ----------


async def crear_cliente(session: AsyncSession, datos: ClienteCreate) -> ClienteRead:
    cliente = Cliente(**datos.model_dump())
    session.add(cliente)
    try:
        await session.commit()
    except IntegrityError as error:
        await session.rollback()
        # el email repetido lo rechaza el UNIQUE de la base, no se consulta antes
        raise http_409_por_integridad(error, detalle_unique=_DETALLE_UNIQUE_EMAIL) from None
    return await obtener_cliente(session, cliente.id)


async def actualizar_cliente(
    session: AsyncSession, cliente_id: int, datos: ClienteUpdate
) -> ClienteRead:
    cliente = await _buscar_cliente(session, cliente_id)

    # PATCH: sólo los campos enviados.
    for campo, valor in datos.model_dump(exclude_unset=True).items():
        setattr(cliente, campo, valor)

    session.add(cliente)
    try:
        await session.commit()
    except IntegrityError as error:
        await session.rollback()
        raise http_409_por_integridad(error, detalle_unique=_DETALLE_UNIQUE_EMAIL) from None

    return await obtener_cliente(session, cliente_id)


async def crear_perfil(session: AsyncSession, cliente_id: int, datos: PerfilCreate) -> PerfilRead:
    # Se confirma que el cliente exista para dar 404 (si no, la FK daría 409).
    await _buscar_cliente(session, cliente_id)

    perfil = PerfilCliente(cliente_id=cliente_id, **datos.model_dump())
    session.add(perfil)
    try:
        await session.commit()
    except IntegrityError as error:
        await session.rollback()
        # el UNIQUE de cliente_id garantiza un solo perfil por cliente (RN-09)
        raise http_409_por_integridad(error, detalle_unique=_DETALLE_UNIQUE_PERFIL) from None
    return PerfilRead.desde_modelo(perfil)


# ---------- Auxiliares ----------


async def _buscar_cliente(session: AsyncSession, cliente_id: int) -> Cliente:
    cliente = await session.get(Cliente, cliente_id)
    if cliente is None:
        raise _no_existe()
    return cliente
