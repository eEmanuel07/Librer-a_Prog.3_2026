import asyncio
import logging
from decimal import Decimal

from app.core.errors import Conflicto, NoEncontrado
from app.core.uow import UnitOfWork
from app.modules.ventas.models import RenglonVenta, Venta
from app.modules.ventas.schemas import VentaCreate, VentaRead, VentaResumen

# Se usa el logger de uvicorn para que el aviso salga en la misma consola que
# el servidor, sin tocar la configuración global de logging (que duplicaría
# las líneas de SQL_ECHO).
logger = logging.getLogger("uvicorn.error")

_DETALLE_NO_EXISTE = "La venta no existe"


# ---------- Lecturas con precarga (sin N+1) ----------


async def obtener_venta(uow: UnitOfWork, venta_id: int) -> VentaRead:
    venta = await uow.ventas.obtener_con_detalle(venta_id)
    if venta is None:
        raise NoEncontrado(_DETALLE_NO_EXISTE)
    return VentaRead.desde_modelo(venta)


async def listar_ventas(uow: UnitOfWork, limit: int, offset: int) -> list[VentaResumen]:
    ventas = await uow.ventas.listar(limit, offset)
    return [VentaResumen.desde_modelo(v) for v in ventas]


# ---------- Alta ----------


async def crear_venta(uow: UnitOfWork, datos: VentaCreate) -> VentaRead:
    # RN-06: el precio se copia del libro, así que hay que leerlo de la base.
    # Esta consulta es necesaria para obtener el precio; de paso detecta los
    # libros que no existen (C-05).
    ids_libros = [r.libro_id for r in datos.renglones]
    precios = await uow.libros.precios(ids_libros)

    faltantes = [i for i in ids_libros if i not in precios]
    if faltantes:
        raise Conflicto(f"No existe el libro con id {', '.join(map(str, faltantes))}")

    # El cliente no se consulta antes: si no existe, la base rechaza la clave
    # foránea y se traduce a 409 (C-05).
    venta = Venta(cliente_id=datos.cliente_id, total=Decimal("0.00"))

    # RN-04: composición. Los renglones se crean con la venta y se agregan a
    # venta.renglones; se insertan en el mismo commit.
    for r in datos.renglones:
        venta.renglones.append(
            RenglonVenta(
                libro_id=r.libro_id,
                cantidad=r.cantidad,
                precio_unitario=precios[r.libro_id],
            )
        )

    # RN-07: el total lo calcula el servidor.
    venta.total = sum((r.cantidad * r.precio_unitario for r in venta.renglones), Decimal("0.00"))

    uow.ventas.agregar(venta)
    # RN-12: mensaje propio, nunca el texto de la base. Los libros ya se
    # validaron arriba, así que una FK rechazada acá sólo puede ser la del cliente.
    await uow.commit(
        detalle_fk="El cliente indicado no existe",
        detalle_unique="Un mismo libro no puede aparecer en dos renglones",
        detalle_check="La venta no cumple las reglas de la librería",
    )

    return await obtener_venta(uow, venta.id)


# ---------- Tarea en segundo plano ----------


async def avisar_comprobante(venta_id: int, email: str, total: Decimal) -> None:
    """Simula el envío del comprobante. Corre después de enviar la respuesta.

    Recibe datos simples (no objetos del ORM) y no usa la sesión ni el UoW de
    la petición: así no depende de que sigan abiertos.
    """
    await asyncio.sleep(0.5)  # no bloquea: el servidor sigue atendiendo
    logger.info("Comprobante de la venta %s enviado a %s (total $%s)", venta_id, email, total)
