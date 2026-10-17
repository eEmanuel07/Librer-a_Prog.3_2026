from datetime import datetime
from decimal import Decimal

from pydantic import ConfigDict, field_validator
from sqlmodel import Field, SQLModel

from app.modules.ventas.models import RenglonVenta, Venta


# ---------- Entrada ----------
# extra="forbid": si el cliente manda precio_unitario, total o fecha, se
# rechaza con 422. Esos datos los pone el servidor (RN-06 y RN-07).


class RenglonCreate(SQLModel):
    model_config = ConfigDict(extra="forbid")

    libro_id: int
    cantidad: int = Field(gt=0)


class VentaCreate(SQLModel):
    """Composición: los datos de cada renglón viajan dentro del alta (RN-04)."""

    model_config = ConfigDict(extra="forbid")

    cliente_id: int
    renglones: list[RenglonCreate] = Field(min_length=1)  # RN-05: al menos uno

    @field_validator("renglones")
    @classmethod
    def sin_libros_repetidos(cls, renglones: list[RenglonCreate]) -> list[RenglonCreate]:
        # RN-05: un mismo libro no aparece en dos renglones.
        ids = [r.libro_id for r in renglones]
        if len(ids) != len(set(ids)):
            raise ValueError("Un mismo libro no puede aparecer en dos renglones")
        return renglones


# No hay VentaUpdate: las ventas no se modifican (RN-08).


# ---------- Salida ----------


class ClienteResumen(SQLModel):
    id: int
    nombre: str
    email: str


class RenglonRead(SQLModel):
    libro_id: int
    titulo: str
    cantidad: int
    precio_unitario: Decimal
    subtotal: Decimal

    @classmethod
    def desde_modelo(cls, renglon: RenglonVenta) -> "RenglonRead":
        return cls(
            libro_id=renglon.libro_id,
            titulo=renglon.libro.titulo,
            cantidad=renglon.cantidad,
            precio_unitario=renglon.precio_unitario,
            subtotal=renglon.cantidad * renglon.precio_unitario,
        )


class VentaResumen(SQLModel):
    """Para el listado: sin renglones."""

    id: int
    fecha: datetime
    total: Decimal
    cliente: ClienteResumen

    @classmethod
    def desde_modelo(cls, venta: Venta) -> "VentaResumen":
        return cls(
            id=venta.id,
            fecha=venta.fecha,
            total=venta.total,
            cliente=ClienteResumen.model_validate(venta.cliente, from_attributes=True),
        )


class VentaRead(VentaResumen):
    """Detalle: venta con cliente y renglones."""

    renglones: list[RenglonRead]

    @classmethod
    def desde_modelo(cls, venta: Venta) -> "VentaRead":
        return cls(
            id=venta.id,
            fecha=venta.fecha,
            total=venta.total,
            cliente=ClienteResumen.model_validate(venta.cliente, from_attributes=True),
            renglones=[RenglonRead.desde_modelo(r) for r in venta.renglones],
        )
