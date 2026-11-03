from datetime import datetime, timezone
from typing import TYPE_CHECKING, Optional

from sqlalchemy import CheckConstraint, DateTime, Index, text
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.modules.clientes.models import Cliente
    from app.modules.libros.models import MovimientoStock

# lazy="raise": si alguien lee una relación sin precargarla (joinedload /
# selectinload) salta un error en vez de disparar una consulta por fila (N+1).
_RAISE = {"lazy": "raise"}
# Uno a uno: Usuario.cliente devuelve un objeto y no una lista (Ej. 2).
_RAISE_UNO_A_UNO = {"lazy": "raise", "uselist": False}
# asignacion_rol tiene dos FK a usuario (usuario_id y otorgada_por): hay que
# indicar explícitamente cuál clave foránea usa la relación Usuario.asignaciones
# para evitar AmbiguousForeignKeysError al configurar los mappers.
_RAISE_ASIGNACION_USUARIO = {
    "lazy": "raise",
    "foreign_keys": "[AsignacionRol.usuario_id]",
}


def ahora_utc() -> datetime:
    return datetime.now(timezone.utc)


class Usuario(SQLModel, table=True):
    """Cuenta de acceso al sistema (personal o cliente web).

    Los roles no viven en una columna de usuario sino en asignacion_rol, con
    vigencia y revocación sin borrar la fila (sección 5.9).
    """

    __tablename__ = "usuario"

    id: Optional[int] = Field(default=None, primary_key=True)
    # UNIQUE: el correo de un usuario es único (RN-01).
    email: str = Field(unique=True)
    nombre: str
    password_hash: str
    activo: bool = Field(default=True)
    debe_cambiar_password: bool = Field(default=False)

    asignaciones: list["AsignacionRol"] = Relationship(
        back_populates="usuario",
        sa_relationship_kwargs=_RAISE_ASIGNACION_USUARIO,
    )
    movimientos: list["MovimientoStock"] = Relationship(
        back_populates="usuario",
        sa_relationship_kwargs=_RAISE,
    )
    cliente: Optional["Cliente"] = Relationship(
        back_populates="usuario",
        sa_relationship_kwargs=_RAISE_UNO_A_UNO,
    )


class AsignacionRol(SQLModel, table=True):
    """Rol asignado a un usuario con vigencia e historial de revocaciones.

    Un usuario tiene a lo sumo una asignación abierta (revocada_en IS NULL)
    por cada rol (RN-03), garantizado por un índice único parcial.
    """

    __tablename__ = "asignacion_rol"
    __table_args__ = (
        CheckConstraint(
            "rol IN ('ADMIN', 'VENDEDOR', 'CLIENTE')",
            name="ck_asignacion_rol_rol",
        ),
        Index(
            "uq_asignacion_rol_vigente",
            "usuario_id",
            "rol",
            unique=True,
            postgresql_where=text("revocada_en IS NULL"),
        ),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    usuario_id: int = Field(foreign_key="usuario.id", index=True)
    rol: str
    desde: datetime = Field(
        default_factory=ahora_utc,
        sa_type=DateTime(timezone=True),
    )
    vence_en: Optional[datetime] = Field(
        default=None,
        sa_type=DateTime(timezone=True),
    )
    revocada_en: Optional[datetime] = Field(
        default=None,
        sa_type=DateTime(timezone=True),
    )
    # Quién otorgó el rol (nulo en el auto-registro o la carga inicial).
    # Es FK a usuario.id con índice, sin relación de navegación (acuerdo E0).
    otorgada_por: Optional[int] = Field(
        default=None,
        foreign_key="usuario.id",
        index=True,
    )

    usuario: "Usuario" = Relationship(
        back_populates="asignaciones",
        sa_relationship_kwargs=_RAISE_ASIGNACION_USUARIO,
    )


class IntentoAcceso(SQLModel, table=True):
    """Registro de cada intento de login (correcto o fallido) para RN-07.

    No se relaciona con ninguna otra tabla: también anota intentos con correos
    que no existen en usuario y sobrevive al rollback de un login rechazado.
    """

    __tablename__ = "intento_acceso"
    __table_args__ = (
        Index("ix_intento_acceso_email_ip_cuando", "email", "ip", "cuando"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    cuando: datetime = Field(
        default_factory=ahora_utc,
        sa_type=DateTime(timezone=True),
    )
    email: str
    ip: str
    exito: bool


class EventoSeguridad(SQLModel, table=True):
    """Bitácora de auditoría para altas de personal, cambios de rol y contraseña (RN-16).

    actor es texto (correo del usuario o 'SISTEMA' en la carga inicial) y no
    se relaciona con ninguna otra tabla.
    """

    __tablename__ = "evento_seguridad"

    id: Optional[int] = Field(default=None, primary_key=True)
    cuando: datetime = Field(
        default_factory=ahora_utc,
        sa_type=DateTime(timezone=True),
    )
    actor: str
    accion: str
