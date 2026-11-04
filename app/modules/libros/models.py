from datetime import datetime, timezone
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from sqlalchemy import CheckConstraint, Column, DateTime, Index, Numeric, text
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.modules.autores.models import Autor
    from app.modules.editoriales.models import Editorial
    from app.modules.generos.models import Genero
    from app.modules.usuarios.models import Usuario
    from app.modules.ventas.models import RenglonVenta, Venta

# lazy="raise": si alguien lee una relación sin precargarla (joinedload /
# selectinload) salta un error en vez de disparar una consulta por fila (N+1).
_RAISE = {"lazy": "raise"}


def ahora_utc() -> datetime:
    return datetime.now(timezone.utc)


class LibroAutor(SQLModel, table=True):
    """Objeto de asociación del muchos a muchos Libro <-> Autor.

    Guarda lo que no es ni del libro ni del autor: el rol y el orden en la tapa.
    """

    __tablename__ = "libro_autor"
    __table_args__ = (
        CheckConstraint("orden >= 1", name="ck_libro_autor_orden"),
        CheckConstraint(
            "rol IN ('autor', 'coautor', 'traductor', 'ilustrador')",
            name="ck_libro_autor_rol",
        ),
    )

    libro_id: int = Field(foreign_key="libro.id", primary_key=True, index=True)
    autor_id: int = Field(foreign_key="autor.id", primary_key=True, index=True)
    rol: str
    orden: int

    libro: "Libro" = Relationship(back_populates="autorias", sa_relationship_kwargs=_RAISE)
    autor: "Autor" = Relationship(back_populates="autorias", sa_relationship_kwargs=_RAISE)


class Libro(SQLModel, table=True):
    __tablename__ = "libro"
    __table_args__ = (
        CheckConstraint("precio > 0", name="ck_libro_precio"),
        CheckConstraint("stock >= 0", name="ck_libro_stock"),
        # El ISBN es único sólo entre los libros vigentes: uno dado de baja
        # (borrado_en con fecha) libera su ISBN para volver a cargarlo. Es un
        # índice único parcial y no un UNIQUE común, que lo bloquearía para siempre.
        Index(
            "uq_libro_isbn_vigente",
            "isbn",
            unique=True,
            postgresql_where=text("borrado_en IS NULL"),
        ),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    isbn: str
    titulo: str
    precio: Decimal = Field(sa_column=Column(Numeric(10, 2), nullable=False))
    stock: int
    editorial_id: int = Field(foreign_key="editorial.id", index=True)
    # Agregación opcional: un libro puede no tener género. Llega en la segunda migración.
    genero_id: Optional[int] = Field(default=None, foreign_key="genero.id", index=True)
    # Borrado lógico: la fila dada de baja queda en la tabla porque las ventas
    # viejas la apuntan, pero deja de aparecer en el catálogo.
    borrado_en: Optional[datetime] = Field(default=None, sa_type=DateTime(timezone=True))

    editorial: "Editorial" = Relationship(back_populates="libros", sa_relationship_kwargs=_RAISE)
    genero: Optional["Genero"] = Relationship(back_populates="libros", sa_relationship_kwargs=_RAISE)
    autorias: list["LibroAutor"] = Relationship(back_populates="libro", sa_relationship_kwargs=_RAISE)
    renglones: list["RenglonVenta"] = Relationship(back_populates="libro", sa_relationship_kwargs=_RAISE)
    movimientos: list["MovimientoStock"] = Relationship(back_populates="libro", sa_relationship_kwargs=_RAISE)


class MovimientoStock(SQLModel, table=True):
    """Libro mayor del stock: de sólo agregado, nunca se corrige (RN-12).

    libro.stock es la suma de las cantidades de sus movimientos. Una corrección
    se compensa con otro movimiento. La base lo impone con un disparador (migración 4).
    """

    __tablename__ = "movimiento_stock"
    __table_args__ = (CheckConstraint("cantidad <> 0", name="ck_movimiento_stock_cantidad_no_cero"),)

    id: Optional[int] = Field(default=None, primary_key=True)
    libro_id: int = Field(foreign_key="libro.id", index=True)
    # Nulo en las reposiciones y el stock inicial: no nacen de una venta.
    venta_id: Optional[int] = Field(default=None, foreign_key="venta.id", index=True)
    usuario_id: int = Field(foreign_key="usuario.id", index=True)
    cantidad: int  # positiva entra stock, negativa sale
    motivo: str
    cuando: datetime = Field(default_factory=ahora_utc, sa_type=DateTime(timezone=True))

    libro: "Libro" = Relationship(back_populates="movimientos", sa_relationship_kwargs=_RAISE)
    venta: Optional["Venta"] = Relationship(back_populates="movimientos", sa_relationship_kwargs=_RAISE)
    usuario: "Usuario" = Relationship(back_populates="movimientos", sa_relationship_kwargs=_RAISE)
