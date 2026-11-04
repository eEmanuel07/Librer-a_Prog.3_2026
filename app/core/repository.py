from collections.abc import Sequence
from datetime import datetime, timezone
from typing import Any, Generic, TypeVar

from sqlalchemy import func
from sqlmodel import SQLModel, select
from sqlmodel.ext.asyncio.session import AsyncSession

T = TypeVar("T", bound=SQLModel)


class BaseRepository(Generic[T]):
    """Operaciones comunes a todas las entidades. Nunca confirma: eso es del UoW."""

    def __init__(self, session: AsyncSession, modelo: type[T]) -> None:
        self.session = session
        self.modelo = modelo

    async def get_by_id(self, id: int) -> T | None:
        """La fila con ese id, o None si no existe."""
        return await self.session.get(self.modelo, id)

    async def get_all(self, *, offset: int = 0, limit: int | None = None) -> Sequence[T]:
        """Todas las filas, ordenadas por id para que la paginación sea estable."""
        consulta = select(self.modelo).order_by(self.modelo.id).offset(offset)
        if limit is not None:
            consulta = consulta.limit(limit)
        return (await self.session.exec(consulta)).all()

    async def count(self) -> int:
        """Cantidad de filas, contadas en la base sin traerlas."""
        consulta = select(func.count()).select_from(self.modelo)
        return (await self.session.exec(consulta)).one()

    async def add(self, entidad: T) -> T:
        """Agrega la entidad y hace flush(): al volver ya tiene su id. Nunca confirma."""
        self.session.add(entidad)
        await self.session.flush()
        return entidad

    async def update(self, entidad: T, datos: dict[str, Any]) -> T:
        """Copia los datos sobre la entidad y hace flush(). Nunca confirma.

        Para un PATCH, datos sale de schema.model_dump(exclude_unset=True).
        """
        for campo, valor in datos.items():
            setattr(entidad, campo, valor)
        self.session.add(entidad)
        await self.session.flush()
        return entidad

    async def delete(self, entidad: T) -> None:
        """Borra la fila de verdad y hace flush(). Nunca confirma.

        Para el borrado lógico de Libro está SoftDeleteRepository.
        """
        await self.session.delete(entidad)
        await self.session.flush()


class SoftDeleteRepository(BaseRepository[T]):
    """BaseRepository para modelos con borrado lógico (columna ``borrado_en``).

    Las filas dadas de baja siguen en la tabla (las ventas viejas las apuntan),
    pero ``get_by_id``, ``get_all`` y ``count`` ya no las ven. Las dos operaciones
    que la clase base no tiene son ``get_by_id_including_deleted`` y
    ``soft_delete``. Igual que la base, nunca confirma: eso es del UoW.
    """

    async def get_by_id(self, id: int) -> T | None:
        """La fila vigente con ese id; None si no existe o está dada de baja."""
        consulta = select(self.modelo).where(self.modelo.id == id, self.modelo.borrado_en.is_(None))
        return (await self.session.exec(consulta)).first()

    async def get_by_id_including_deleted(self, id: int) -> T | None:
        """La fila con ese id, esté vigente o dada de baja."""
        return await self.session.get(self.modelo, id)

    async def get_all(self, *, offset: int = 0, limit: int | None = None) -> Sequence[T]:
        """Las filas vigentes, ordenadas por id para que la paginación sea estable."""
        consulta = (
            select(self.modelo)
            .where(self.modelo.borrado_en.is_(None))
            .order_by(self.modelo.id)
            .offset(offset)
        )
        if limit is not None:
            consulta = consulta.limit(limit)
        return (await self.session.exec(consulta)).all()

    async def count(self) -> int:
        """Cantidad de filas vigentes, contadas en la base sin traerlas."""
        consulta = select(func.count()).select_from(self.modelo).where(self.modelo.borrado_en.is_(None))
        return (await self.session.exec(consulta)).one()

    async def soft_delete(self, entidad: T) -> T:
        """Da de baja la fila: escribe ``borrado_en`` y hace flush(). Nunca confirma."""
        entidad.borrado_en = datetime.now(timezone.utc)
        self.session.add(entidad)
        await self.session.flush()
        return entidad
