from typing import TYPE_CHECKING, Optional

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    # Venta la declara Joaquín en app/modules/ventas/models.py.
    # Se importa solo para tipado: evita el import circular y, como en
    # libros/models.py, la relación se resuelve por nombre al mapear.
    from app.modules.usuarios.models import Usuario
    from app.modules.ventas.models import Venta

# lazy="raise": si alguien lee una relación sin precargarla (joinedload /
# selectinload) salta un error en vez de disparar una consulta por fila (N+1).
_RAISE = {"lazy": "raise"}
# Uno a uno: Cliente.perfil y Cliente.usuario devuelven un objeto y no una lista (Ej. 2).
_RAISE_UNO_A_UNO = {"lazy": "raise", "uselist": False}


class PerfilCliente(SQLModel, table=True):
    """Perfil opcional de un cliente (uno a uno con Cliente)."""

    __tablename__ = "perfil_cliente"

    id: Optional[int] = Field(default=None, primary_key=True)
    # UNIQUE: un cliente tiene como máximo un perfil (RN-09).
    # La FK lleva índice: PostgreSQL no lo crea solo (sección 4.10).
    cliente_id: int = Field(foreign_key="cliente.id", unique=True, index=True)
    telefono: str
    direccion: str

    cliente: "Cliente" = Relationship(back_populates="perfil", sa_relationship_kwargs=_RAISE)


class Cliente(SQLModel, table=True):
    __tablename__ = "cliente"

    id: Optional[int] = Field(default=None, primary_key=True)
    nombre: str
    # UNIQUE: el email de un cliente es único (RN-01).
    email: str = Field(unique=True)
    # Acceso opcional por la web: nulo permitido y UNIQUE (como máximo un cliente
    # por usuario). La FK lleva índice porque PostgreSQL no lo crea solo (sección 4.10).
    usuario_id: Optional[int] = Field(
        default=None, foreign_key="usuario.id", unique=True, index=True
    )

    perfil: Optional["PerfilCliente"] = Relationship(
        back_populates="cliente", sa_relationship_kwargs=_RAISE_UNO_A_UNO
    )
    usuario: Optional["Usuario"] = Relationship(
        back_populates="cliente", sa_relationship_kwargs=_RAISE_UNO_A_UNO
    )
    ventas: list["Venta"] = Relationship(back_populates="cliente", sa_relationship_kwargs=_RAISE)
