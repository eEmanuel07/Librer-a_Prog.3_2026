from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from sqlalchemy import CheckConstraint, Column, Numeric
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.modules.autores.models import Autor
    from app.modules.editoriales.models import Editorial
    from app.modules.ventas.models import RenglonVenta

# lazy="raise": si alguien lee una relación sin precargarla (joinedload /
# selectinload) salta un error en vez de disparar una consulta por fila (N+1).
_RAISE = {"lazy": "raise"}


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
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    isbn: str = Field(unique=True)
    titulo: str
    precio: Decimal = Field(sa_column=Column(Numeric(10, 2), nullable=False))
    stock: int
    editorial_id: int = Field(foreign_key="editorial.id", index=True)
    # genero_id y la relación genero se agregan en la segunda migración
    # (la consigna pide que la tabla genero llegue después de la primera).

    editorial: "Editorial" = Relationship(back_populates="libros", sa_relationship_kwargs=_RAISE)
    autorias: list["LibroAutor"] = Relationship(back_populates="libro", sa_relationship_kwargs=_RAISE)
    renglones: list["RenglonVenta"] = Relationship(back_populates="libro", sa_relationship_kwargs=_RAISE)
