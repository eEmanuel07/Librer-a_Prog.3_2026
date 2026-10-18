from decimal import Decimal
from typing import Literal

from pydantic import ConfigDict, model_validator
from sqlmodel import Field, SQLModel

from app.modules.libros.models import Libro, LibroAutor

Rol = Literal["autor", "coautor", "traductor", "ilustrador"]


# ---------- Entrada ----------
# extra="forbid": un campo desconocido (por ejemplo un id en el alta) se
# rechaza con 422 en lugar de ignorarse.


class AutoriaCreate(SQLModel):
    """Agregación con datos: viaja el id del autor más el rol y el orden."""

    model_config = ConfigDict(extra="forbid")

    autor_id: int
    rol: Rol
    orden: int = Field(ge=1)


class LibroCreate(SQLModel):
    model_config = ConfigDict(extra="forbid")

    isbn: str = Field(min_length=1)
    titulo: str = Field(min_length=1)
    precio: Decimal = Field(gt=0, max_digits=10, decimal_places=2)  # RN-03
    stock: int = Field(ge=0)  # RN-03
    editorial_id: int
    genero_id: int | None = None  # agregación opcional: un libro puede no tener género
    autores: list[AutoriaCreate]


class LibroUpdate(SQLModel):
    """PATCH: se aplican sólo los campos enviados (exclude_unset)."""

    model_config = ConfigDict(extra="forbid")

    isbn: str | None = Field(default=None, min_length=1)
    titulo: str | None = Field(default=None, min_length=1)
    precio: Decimal | None = Field(default=None, gt=0, max_digits=10, decimal_places=2)
    stock: int | None = Field(default=None, ge=0)
    editorial_id: int | None = None
    genero_id: int | None = None  # null quita el género (es opcional)

    @model_validator(mode="after")
    def sin_nulos_explicitos(self) -> "LibroUpdate":
        # Todas las columnas son obligatorias salvo genero_id: omitir el campo
        # está bien, mandarlo en null no (la base lo rechazaría con un error opaco).
        for campo in self.model_fields_set - {"genero_id"}:
            if getattr(self, campo) is None:
                raise ValueError(f"'{campo}' no puede ser null")
        return self


# ---------- Salida ----------


class EditorialResumen(SQLModel):
    id: int
    nombre: str
    pais: str


class GeneroResumen(SQLModel):
    id: int
    nombre: str


class AutorResumen(SQLModel):
    id: int
    nombre: str
    nacionalidad: str


class AutoriaRead(SQLModel):
    autor: AutorResumen
    rol: str
    orden: int

    @classmethod
    def desde_modelo(cls, autoria: LibroAutor) -> "AutoriaRead":
        return cls(
            autor=AutorResumen.model_validate(autoria.autor, from_attributes=True),
            rol=autoria.rol,
            orden=autoria.orden,
        )


def _genero_resumen(libro: Libro) -> GeneroResumen | None:
    if libro.genero is None:
        return None
    return GeneroResumen.model_validate(libro.genero, from_attributes=True)


class LibroResumen(SQLModel):
    """Para el listado: con editorial, sin autores."""

    id: int
    isbn: str
    titulo: str
    precio: Decimal
    stock: int
    editorial: EditorialResumen
    genero: GeneroResumen | None  # None si el libro no tiene género

    @classmethod
    def desde_modelo(cls, libro: Libro) -> "LibroResumen":
        return cls(
            id=libro.id,
            isbn=libro.isbn,
            titulo=libro.titulo,
            precio=libro.precio,
            stock=libro.stock,
            editorial=EditorialResumen.model_validate(libro.editorial, from_attributes=True),
            genero=_genero_resumen(libro),
        )


class LibroRead(LibroResumen):
    """Detalle: libro con editorial, género y autores (rol y orden)."""

    autores: list[AutoriaRead]

    @classmethod
    def desde_modelo(cls, libro: Libro) -> "LibroRead":
        autorias = sorted(libro.autorias, key=lambda a: a.orden)
        return cls(
            id=libro.id,
            isbn=libro.isbn,
            titulo=libro.titulo,
            precio=libro.precio,
            stock=libro.stock,
            editorial=EditorialResumen.model_validate(libro.editorial, from_attributes=True),
            genero=_genero_resumen(libro),
            autores=[AutoriaRead.desde_modelo(a) for a in autorias],
        )
