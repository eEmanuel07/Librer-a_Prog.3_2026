from pydantic import ConfigDict, model_validator
from sqlmodel import Field, SQLModel

from app.modules.libros.models import LibroAutor


class AutorCreate(SQLModel):
    model_config = ConfigDict(extra="forbid")

    nombre: str = Field(min_length=1)
    nacionalidad: str = Field(min_length=1)


class AutorUpdate(SQLModel):
    model_config = ConfigDict(extra="forbid")

    nombre: str | None = Field(default=None, min_length=1)
    nacionalidad: str | None = Field(default=None, min_length=1)

    @model_validator(mode="after")
    def sin_nulos_explicitos(self) -> "AutorUpdate":
        for campo in self.model_fields_set:
            if getattr(self, campo) is None:
                raise ValueError(f"'{campo}' no puede ser null")
        return self


class AutorRead(SQLModel):
    id: int
    nombre: str
    nacionalidad: str


class LibroDeAutor(SQLModel):
    """Libro visto desde el autor, con el rol y el orden de esa autoria."""

    libro_id: int
    isbn: str
    titulo: str
    rol: str
    orden: int

    @classmethod
    def desde_modelo(cls, autoria: LibroAutor) -> "LibroDeAutor":
        return cls(
            libro_id=autoria.libro_id,
            isbn=autoria.libro.isbn,
            titulo=autoria.libro.titulo,
            rol=autoria.rol,
            orden=autoria.orden,
        )
