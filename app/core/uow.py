"""Unit of Work: el único lugar donde se hace commit o rollback.

Flujo: Router -> Service -> UoW -> Repository. El UoW tiene la sesión de la
petición y expone los repositorios (``uow.editoriales``). Si algo falla
dentro del ``async with`` hace rollback; si el commit choca con una
restricción de la base, lo traduce a ``Conflicto`` con mensaje propio.

Uso típico en un router::

    @router.post("/")
    async def crear(datos: AlgoCreate, uow: UnitOfWork = Depends(get_uow)):
        return await service.crear(uow, datos)
"""

from collections.abc import AsyncGenerator
from types import TracebackType

from fastapi import Depends
from sqlalchemy.exc import IntegrityError
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.database import get_session
from app.core.errors import conflicto_por_integridad
from app.modules.autores.repository import AutorRepository
from app.modules.editoriales.repository import EditorialRepository
from app.modules.generos.repository import GeneroRepository
from app.modules.libros.repository import LibroRepository


class UnitOfWork:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.editoriales = EditorialRepository(session)
        self.generos = GeneroRepository(session)
        self.autores = AutorRepository(session)
        self.libros = LibroRepository(session)

    async def __aenter__(self) -> "UnitOfWork":
        return self

    async def __aexit__(
        self,
        tipo: type[BaseException] | None,
        error: BaseException | None,
        traza: TracebackType | None,
    ) -> None:
        if error is not None:
            await self.session.rollback()

    async def commit(
        self,
        *,
        detalle_unique: str = "El registro ya existe.",
        detalle_fk: str = "La operación referencia un recurso inexistente.",
        detalle_check: str = "Los datos violan una regla de la base.",
    ) -> None:
        """Confirma la transacción; los ``detalle_*`` son los mensajes del 409."""
        try:
            await self.session.commit()
        except IntegrityError as error:
            await self.session.rollback()
            # la unicidad la garantiza la base, no se consulta antes
            raise conflicto_por_integridad(
                error,
                detalle_unique=detalle_unique,
                detalle_fk=detalle_fk,
                detalle_check=detalle_check,
            ) from None

    async def rollback(self) -> None:
        await self.session.rollback()


async def get_uow(session: AsyncSession = Depends(get_session)) -> AsyncGenerator[UnitOfWork, None]:
    """Un UoW por petición, sobre la misma sesión que da ``get_session``."""
    async with UnitOfWork(session) as uow:
        yield uow
