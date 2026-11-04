from collections.abc import Sequence
from decimal import Decimal

from sqlalchemy.orm import joinedload, selectinload
from sqlmodel import func, select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.errors import Conflicto
from app.core.repository import SoftDeleteRepository
from app.modules.libros.models import Libro, LibroAutor, MovimientoStock


class LibroRepository(SoftDeleteRepository[Libro]):
    """Consultas sobre libros. No hace commit: eso es del UoW.

    Un libro dado de baja deja de aparecer en el catálogo (listado, detalle) y
    no se puede vender. Sus datos se conservan: las ventas viejas lo siguen
    mostrando porque lo cargan por la relación, no por este repositorio.
    """

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Libro)

    async def obtener(self, libro_id: int) -> Libro | None:
        """El libro vigente con ese id."""
        return await self.get_by_id(libro_id)

    async def obtener_con_relaciones(self, libro_id: int) -> Libro | None:
        # Cantidad fija de consultas, sin importar cuántos autores tenga (C-07):
        #   1) libro JOIN editorial JOIN género -> joinedload (relaciones a uno)
        #   2) autorías JOIN autor              -> selectinload (colección) + joinedload (a uno)
        consulta = (
            select(Libro)
            .where(Libro.id == libro_id, Libro.borrado_en.is_(None))
            .options(
                joinedload(Libro.editorial),
                joinedload(Libro.genero),
                selectinload(Libro.autorias).joinedload(LibroAutor.autor),
            )
            # Si el libro ya está en la sesión (recién creado o modificado), lo
            # recarga con sus relaciones en lugar de devolver la copia sin precargar.
            .execution_options(populate_existing=True)
        )
        return (await self.session.exec(consulta)).first()

    async def listar(
        self, limit: int, offset: int, titulo: str | None, genero_id: int | None
    ) -> Sequence[Libro]:
        # Una sola consulta: libro JOIN editorial JOIN género.
        consulta = (
            select(Libro)
            .where(Libro.borrado_en.is_(None))
            .options(joinedload(Libro.editorial), joinedload(Libro.genero))
        )
        if genero_id is not None:
            consulta = consulta.where(Libro.genero_id == genero_id)
        if titulo:
            # RN-11: parámetro ligado, sin distinguir mayúsculas. autoescape hace
            # que % y _ del texto buscado se tomen literalmente.
            consulta = consulta.where(Libro.titulo.icontains(titulo, autoescape=True))
        consulta = consulta.order_by(Libro.id).limit(limit).offset(offset)
        return (await self.session.exec(consulta)).all()

    async def precios(self, libro_ids: list[int]) -> dict[int, Decimal]:
        """Precio de cada libro vigente pedido; los inexistentes o dados de baja no aparecen."""
        filas = await self.session.exec(
            select(Libro.id, Libro.precio).where(Libro.id.in_(libro_ids), Libro.borrado_en.is_(None))
        )
        return dict(filas.all())

    def agregar(self, libro: Libro) -> None:
        self.session.add(libro)

    # ---------- Stock: un único punto de escritura (RN-11) ----------

    async def mover_stock(
        self,
        libro: Libro,
        cantidad: int,
        motivo: str,
        usuario_id: int,
        venta_id: int | None = None,
    ) -> MovimientoStock:
        """Cambia el stock de un libro y deja el movimiento, en el mismo paso.

        **Es el único código del sistema que escribe ``libro.stock``.** Lo usan el
        alta del libro (el «Stock inicial»), la reposición y el registro de ventas;
        nadie más. Así se cumple siempre que ``stock`` sea la suma de las cantidades
        de los movimientos del libro: una escritura sin movimiento rompería la igualdad.

        ``cantidad`` positiva entra stock y negativa lo descuenta. No hace commit,
        sólo flush: si la operación de negocio falla después, el UoW revierte el
        libro y el movimiento juntos. Para un libro recién creado, agregarlo con
        ``stock=0``, hacer flush para que tenga id, y luego mover el stock inicial.
        """
        if cantidad == 0:
            # Un movimiento nulo no dice nada (y el CHECK de la base lo rechaza).
            raise ValueError("Un movimiento de stock no puede ser de cantidad cero")
        if libro.borrado_en is not None:
            # RN-13: un libro dado de baja no se puede vender ni reponer.
            raise Conflicto("El libro está dado de baja")
        nuevo_stock = libro.stock + cantidad
        if nuevo_stock < 0:
            raise Conflicto(
                f"No hay stock suficiente de «{libro.titulo}»: hay {libro.stock} y se piden {-cantidad}"
            )

        libro.stock = nuevo_stock
        movimiento = MovimientoStock(
            libro_id=libro.id,
            venta_id=venta_id,
            usuario_id=usuario_id,
            cantidad=cantidad,
            motivo=motivo,
        )
        self.session.add(libro)
        self.session.add(movimiento)
        await self.session.flush()
        return movimiento

    async def ids_con_stock_inconsistente(self) -> list[int]:
        """Los libros cuyo stock no es la suma de sus movimientos (debería ser ninguno).

        Es la comprobación del caso C-11: tras cada caso de venta, la igualdad vale
        para todos los libros. Cuenta también los libros dados de baja.
        """
        suma = (
            select(MovimientoStock.libro_id, func.sum(MovimientoStock.cantidad).label("total"))
            .group_by(MovimientoStock.libro_id)
            .subquery()
        )
        consulta = (
            select(Libro.id)
            .outerjoin(suma, suma.c.libro_id == Libro.id)
            .where(Libro.stock != func.coalesce(suma.c.total, 0))
            .order_by(Libro.id)
        )
        return list((await self.session.exec(consulta)).all())
