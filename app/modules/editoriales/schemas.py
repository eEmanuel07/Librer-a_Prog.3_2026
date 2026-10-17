from decimal import Decimal

from pydantic import ConfigDict, model_validator
from sqlmodel import Field, SQLModel


# extra="forbid" para que un id u otro campo de mas en el cuerpo de 422
class EditorialCreate(SQLModel):
    model_config = ConfigDict(extra="forbid")

    nombre: str = Field(min_length=1)
    pais: str = Field(min_length=1)


class EditorialUpdate(SQLModel):
    model_config = ConfigDict(extra="forbid")

    nombre: str | None = Field(default=None, min_length=1)
    pais: str | None = Field(default=None, min_length=1)

    @model_validator(mode="after")
    def sin_nulos_explicitos(self) -> "EditorialUpdate":
        # se puede omitir un campo, pero no mandarlo en null
        for campo in self.model_fields_set:
            if getattr(self, campo) is None:
                raise ValueError(f"'{campo}' no puede ser null")
        return self


class EditorialRead(SQLModel):
    id: int
    nombre: str
    pais: str


class LibroDeEditorial(SQLModel):
    id: int
    isbn: str
    titulo: str
    precio: Decimal
    stock: int
