from app.core.errors import NoEncontrado
from app.core.paginacion import Pagina, ParametrosPagina
from app.modules.clientes.models import Cliente, PerfilCliente
from app.modules.clientes.schemas import ClienteCreate, ClienteRead, ClienteUpdate, PerfilCreate, PerfilRead
from app.modules.clientes.unit_of_work import ClienteUnitOfWork
from app.modules.ventas.schemas import VentaRead

# RN-12: mensajes propios para el 409; nunca el texto de la base.
_DETALLE_UNIQUE_EMAIL = "El email ya está en uso"
_DETALLE_UNIQUE_PERFIL = "El cliente ya tiene un perfil"
_DETALLE_NO_EXISTE = "El cliente no existe"


# ---------- Lecturas con precarga (sin N+1) ----------


async def obtener_cliente(uow: ClienteUnitOfWork, cliente_id: int) -> ClienteRead:
    async with uow:
        cliente = await uow.clientes.obtener_con_perfil(cliente_id)
        if cliente is None:
            raise NoEncontrado(_DETALLE_NO_EXISTE)
        return ClienteRead.desde_modelo(cliente)


async def listar_ventas_de_cliente(
    uow: ClienteUnitOfWork, cliente_id: int, params: ParametrosPagina
) -> Pagina[VentaRead]:
    async with uow:
        # Primero se confirma que exista para poder dar 404 en vez de una página vacía.
        await _buscar_cliente(uow, cliente_id)
        ventas, total = await uow.clientes.listar_ventas_pagina(cliente_id, params)
        return Pagina.armar([VentaRead.desde_modelo(v) for v in ventas], total, params)


# ---------- Escrituras ----------


async def crear_cliente(uow: ClienteUnitOfWork, datos: ClienteCreate) -> ClienteRead:
    cliente = Cliente(**datos.model_dump())
    # el email repetido lo rechaza el UNIQUE de la base, no se consulta antes
    async with uow.con_mensajes(unique=_DETALLE_UNIQUE_EMAIL):
        uow.clientes.agregar(cliente)
    # la lectura va después de cerrar el bloque de escritura (no se anidan)
    return await obtener_cliente(uow, cliente.id)


async def actualizar_cliente(
    uow: ClienteUnitOfWork, cliente_id: int, datos: ClienteUpdate
) -> ClienteRead:
    async with uow.con_mensajes(unique=_DETALLE_UNIQUE_EMAIL):
        cliente = await _buscar_cliente(uow, cliente_id)

        # PATCH: sólo los campos enviados.
        for campo, valor in datos.model_dump(exclude_unset=True).items():
            setattr(cliente, campo, valor)

    # la lectura va después de cerrar el bloque de escritura (no se anidan)
    return await obtener_cliente(uow, cliente_id)


async def crear_perfil(uow: ClienteUnitOfWork, cliente_id: int, datos: PerfilCreate) -> PerfilRead:
    # la búsqueda (404) y el alta del perfil van en el mismo bloque
    async with uow.con_mensajes(unique=_DETALLE_UNIQUE_PERFIL):
        # Se confirma que el cliente exista para dar 404 (si no, la FK daría 409).
        await _buscar_cliente(uow, cliente_id)

        perfil = PerfilCliente(cliente_id=cliente_id, **datos.model_dump())
        # el UNIQUE de cliente_id garantiza un solo perfil por cliente (RN-09)
        uow.clientes.agregar_perfil(perfil)
    return PerfilRead.desde_modelo(perfil)


# ---------- Auxiliares ----------


async def _buscar_cliente(uow: ClienteUnitOfWork, cliente_id: int) -> Cliente:
    cliente = await uow.clientes.obtener(cliente_id)
    if cliente is None:
        raise NoEncontrado(_DETALLE_NO_EXISTE)
    return cliente
