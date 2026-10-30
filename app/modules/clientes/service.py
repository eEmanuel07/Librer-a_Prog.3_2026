from app.core.errors import NoEncontrado
from app.core.uow import UnitOfWork
from app.modules.clientes.models import Cliente, PerfilCliente
from app.modules.clientes.schemas import ClienteCreate, ClienteRead, ClienteUpdate, PerfilCreate, PerfilRead
from app.modules.ventas.schemas import VentaRead

# RN-12: mensajes propios para el 409; nunca el texto de la base.
_DETALLE_UNIQUE_EMAIL = "El email ya está en uso"
_DETALLE_UNIQUE_PERFIL = "El cliente ya tiene un perfil"
_DETALLE_NO_EXISTE = "El cliente no existe"


# ---------- Lecturas con precarga (sin N+1) ----------


async def obtener_cliente(uow: UnitOfWork, cliente_id: int) -> ClienteRead:
    cliente = await uow.clientes.obtener_con_perfil(cliente_id)
    if cliente is None:
        raise NoEncontrado(_DETALLE_NO_EXISTE)
    return ClienteRead.desde_modelo(cliente)


async def listar_ventas_de_cliente(
    uow: UnitOfWork, cliente_id: int, limit: int, offset: int
) -> list[VentaRead]:
    # Primero se confirma que exista para poder dar 404 en vez de una lista vacia.
    await _buscar_cliente(uow, cliente_id)
    ventas = await uow.clientes.listar_ventas(cliente_id, limit, offset)
    return [VentaRead.desde_modelo(v) for v in ventas]


# ---------- Escrituras ----------


async def crear_cliente(uow: UnitOfWork, datos: ClienteCreate) -> ClienteRead:
    cliente = Cliente(**datos.model_dump())
    uow.clientes.agregar(cliente)
    # el email repetido lo rechaza el UNIQUE de la base, no se consulta antes
    await uow.commit(detalle_unique=_DETALLE_UNIQUE_EMAIL)
    return await obtener_cliente(uow, cliente.id)


async def actualizar_cliente(
    uow: UnitOfWork, cliente_id: int, datos: ClienteUpdate
) -> ClienteRead:
    cliente = await _buscar_cliente(uow, cliente_id)

    # PATCH: sólo los campos enviados.
    for campo, valor in datos.model_dump(exclude_unset=True).items():
        setattr(cliente, campo, valor)

    await uow.commit(detalle_unique=_DETALLE_UNIQUE_EMAIL)
    return await obtener_cliente(uow, cliente_id)


async def crear_perfil(uow: UnitOfWork, cliente_id: int, datos: PerfilCreate) -> PerfilRead:
    # Se confirma que el cliente exista para dar 404 (si no, la FK daría 409).
    await _buscar_cliente(uow, cliente_id)

    perfil = PerfilCliente(cliente_id=cliente_id, **datos.model_dump())
    uow.clientes.agregar_perfil(perfil)
    # el UNIQUE de cliente_id garantiza un solo perfil por cliente (RN-09)
    await uow.commit(detalle_unique=_DETALLE_UNIQUE_PERFIL)
    return PerfilRead.desde_modelo(perfil)


# ---------- Auxiliares ----------


async def _buscar_cliente(uow: UnitOfWork, cliente_id: int) -> Cliente:
    cliente = await uow.clientes.obtener(cliente_id)
    if cliente is None:
        raise NoEncontrado(_DETALLE_NO_EXISTE)
    return cliente
