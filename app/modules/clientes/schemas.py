from pydantic import ConfigDict, EmailStr, model_validator
from sqlmodel import Field, SQLModel

from app.modules.clientes.models import Cliente, PerfilCliente


# extra="forbid": si el cliente manda un id u otro campo de más, se rechaza
# con 422 en lugar de ignorarse.


class ClienteCreate(SQLModel):
    model_config = ConfigDict(extra="forbid")

    nombre: str = Field(min_length=1)
    email: EmailStr


class ClienteUpdate(SQLModel):
    """PATCH: sólo los campos enviados (exclude_unset)."""

    model_config = ConfigDict(extra="forbid")

    nombre: str | None = Field(default=None, min_length=1)
    email: EmailStr | None = None

    @model_validator(mode="after")
    def sin_nulos_explicitos(self) -> "ClienteUpdate":
        # Se puede omitir un campo, pero no mandarlo en null.
        for campo in self.model_fields_set:
            if getattr(self, campo) is None:
                raise ValueError(f"'{campo}' no puede ser null")
        return self


class PerfilCreate(SQLModel):
    model_config = ConfigDict(extra="forbid")

    telefono: str = Field(min_length=1)
    direccion: str = Field(min_length=1)


# ---------- Salida ----------


class PerfilRead(SQLModel):
    id: int
    cliente_id: int
    telefono: str
    direccion: str

    @classmethod
    def desde_modelo(cls, perfil: PerfilCliente) -> "PerfilRead":
        return cls(
            id=perfil.id,
            cliente_id=perfil.cliente_id,
            telefono=perfil.telefono,
            direccion=perfil.direccion,
        )


class ClienteRead(SQLModel):
    id: int
    nombre: str
    email: str
    perfil: PerfilRead | None  # el perfil es opcional (uno a uno)

    @classmethod
    def desde_modelo(cls, cliente: Cliente) -> "ClienteRead":
        return cls(
            id=cliente.id,
            nombre=cliente.nombre,
            email=cliente.email,
            perfil=PerfilRead.desde_modelo(cliente.perfil) if cliente.perfil else None,
        )
