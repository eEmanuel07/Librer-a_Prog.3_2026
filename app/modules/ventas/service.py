import asyncio
import logging
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import joinedload, selectinload
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.errors import http_409_por_integridad
from app.modules.libros.models import Libro
from app.modules.ventas.models import RenglonVenta, Venta
from app.modules.ventas.schemas import VentaCreate, VentaRead, VentaResumen

# Se usa el logger de uvicorn para que el aviso salga en la misma consola que
# el servidor, sin tocar la configuración global de logging (que duplicaría
# las líneas de SQL_ECHO).
logger = logging.getLogger("uvicorn.error")


# ---------- Lecturas con precarga (sin N+1) ----------


async def obtener_venta(session: AsyncSession, venta_id: int) -> VentaRead:
    # Cantidad fija de consultas, sin importar cuántos renglones tenga (C-07):
    #   1) venta JOIN cliente          -> joinedload (relación a uno)
    #   2) renglones JOIN libro        -> selectinload (colección) + joinedload (a uno)
    consulta = (
        select(Venta)
        .where(Venta.id == venta_id)
        .options(
            joinedload(Venta.cliente),
            selectinload(Venta.renglones).joinedload(RenglonVenta.libro),
        )
        # Si la venta ya está en la sesión (recién creada), la recarga con
        # sus relaciones en lugar de devolver la copia sin precargar.
        .execution_options(populate_existing=True)
    )
    venta = (await session.exec(consulta)).first()
    if venta is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="La venta no existe")
    return VentaRead.desde_modelo(venta)


async def listar_ventas(session: AsyncSession, limit: int, offset: int) -> list[VentaResumen]:
    # Una sola consulta: venta JOIN cliente.
    consulta = (
        select(Venta)
        .options(joinedload(Venta.cliente))
        .order_by(Venta.id)
        .limit(limit)
        .offset(offset)
    )
    ventas = (await session.exec(consulta)).all()
    return [VentaResumen.desde_modelo(v) for v in ventas]


# ---------- Alta ----------


async def crear_venta(session: AsyncSession, datos: VentaCreate) -> VentaRead:
    # RN-06: el precio se copia del libro, así que hay que leerlo de la base.
    # Esta consulta es necesaria para obtener el precio; de paso detecta los
    # libros que no existen (C-05).
    ids_libros = [r.libro_id for r in datos.renglones]
    filas = await session.exec(select(Libro.id, Libro.precio).where(Libro.id.in_(ids_libros)))
    precios: dict[int, Decimal] = dict(filas.all())

    faltantes = [i for i in ids_libros if i not in precios]
    if faltantes:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"No existe el libro con id {', '.join(map(str, faltantes))}",
        )

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

    session.add(venta)
    try:
        await session.commit()
    except IntegrityError as error:
        await session.rollback()
        # RN-12: mensaje propio con el helper común, nunca el texto de la base.
        # Los libros ya se validaron arriba, así que una FK rechazada acá
        # sólo puede ser la del cliente.
        raise http_409_por_integridad(
            error,
            detalle_fk="El cliente indicado no existe",
            detalle_unique="Un mismo libro no puede aparecer en dos renglones",
            detalle_check="La venta no cumple las reglas de la librería",
        ) from None

    return await obtener_venta(session, venta.id)


# ---------- Tarea en segundo plano ----------


async def avisar_comprobante(venta_id: int, email: str, total: Decimal) -> None:
    """Simula el envío del comprobante. Corre después de enviar la respuesta.

    Recibe datos simples (no objetos del ORM) y no usa la sesión de la
    petición: así no depende de que la sesión siga abierta.
    """
    await asyncio.sleep(0.5)  # no bloquea: el servidor sigue atendiendo
    logger.info("Comprobante de la venta %s enviado a %s (total $%s)", venta_id, email, total)
