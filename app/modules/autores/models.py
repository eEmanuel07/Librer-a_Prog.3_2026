from typing import TYPE_CHECKING, Optional

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.modules.libros.models import LibroAutor


class Autor(SQLModel, table=True):
    __tablename__ = "autor"

    id: Optional[int] = Field(default=None, primary_key=True)
    nombre: str
    nacionalidad: str

    # se llega a los libros por libro_autor porque ahi estan el rol y el orden
    autorias: list["LibroAutor"] = Relationship(back_populates="autor", sa_relationship_kwargs={"lazy": "raise"})
