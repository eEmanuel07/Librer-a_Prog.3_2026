from datetime import datetime, timezone
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, DateTime, UniqueConstraint
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.modules.clientes.models import Cliente
    from app.modules.libros.models import Libro


def ahora_utc() -> datetime:
    return datetime.now(timezone.utc)


class Venta(SQLModel, table=True):
    """Registra un hecho: no se modifica después de creada (RN-08)."""

    __tablename__ = "venta"
    __table_args__ = (
        CheckConstraint("total >= 0", name="ck_venta_total_no_negativo"),
    )

    id: int | None = Field(default=None, primary_key=True)

    # Asociación con Cliente: la FK va del lado de la venta porque cada venta
    # tiene un solo cliente y un cliente tiene muchas ventas (lado "muchos").
    cliente_id: int = Field(foreign_key="cliente.id", index=True)

    fecha: datetime = Field(
        default_factory=ahora_utc,
        sa_type=DateTime(timezone=True),
        nullable=False,
    )

    # Lo calcula el servidor (RN-07); nunca viaja en el DTO.
    total: Decimal = Field(max_digits=12, decimal_places=2)

    cliente: "Cliente" = Relationship(
        back_populates="ventas",
        sa_relationship_kwargs={"lazy": "raise"},
    )

    # Composición: los renglones nacen y mueren con la venta.
    renglones: list["RenglonVenta"] = Relationship(
        back_populates="venta",
        sa_relationship_kwargs={
            "lazy": "raise",
            "cascade": "all, delete-orphan",
            "order_by": "RenglonVenta.id",
        },
    )


class RenglonVenta(SQLModel, table=True):
    __tablename__ = "renglon_venta"
    __table_args__ = (
        CheckConstraint("cantidad > 0", name="ck_renglon_venta_cantidad_positiva"),
        CheckConstraint("precio_unitario > 0", name="ck_renglon_venta_precio_positivo"),
        # RN-05 se valida en el DTO (422); la base lo garantiza igual por si
        # algún día se inserta por otro camino.
        UniqueConstraint("venta_id", "libro_id", name="uq_renglon_venta_venta_libro"),
    )

    id: int | None = Field(default=None, primary_key=True)

    # Composición: la FK va en la parte (el renglón) y se borra con el todo.
    venta_id: int = Field(foreign_key="venta.id", index=True, ondelete="CASCADE")

    # Asociación: el renglón nombra un libro que ya existe.
    libro_id: int = Field(foreign_key="libro.id", index=True)

    cantidad: int

    # Copiado del libro al registrar la venta (RN-06): no cambia aunque
    # después cambie libro.precio.
    precio_unitario: Decimal = Field(max_digits=10, decimal_places=2)

    venta: Venta = Relationship(
        back_populates="renglones",
        sa_relationship_kwargs={"lazy": "raise"},
    )
    libro: "Libro" = Relationship(
        back_populates="renglones",
        sa_relationship_kwargs={"lazy": "raise"},
    )
