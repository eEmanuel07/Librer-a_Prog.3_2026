from typing import TYPE_CHECKING, Optional

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.modules.libros.models import Libro


class Editorial(SQLModel, table=True):
    __tablename__ = "editorial"

    id: Optional[int] = Field(default=None, primary_key=True)
    nombre: str = Field(unique=True)
    pais: str

    # la fk esta del lado de libro, aca solo va la navegacion
    libros: list["Libro"] = Relationship(back_populates="editorial", sa_relationship_kwargs={"lazy": "raise"})
