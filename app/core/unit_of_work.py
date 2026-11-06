"""UnitOfWork base: confirma o revierte al salir del bloque (Ej. 6).

Es un gestor de contexto asincrónico sobre la sesión de la petición:

* al salir del ``async with`` sin error, **confirma**;
* si se sale con una excepción, **revierte** y la deja pasar;
* si la base rechaza la escritura (``IntegrityError``), ya sea dentro del
  bloque (por un flush) o en el commit, revierte y la traduce a ``Conflicto``
  (409) con el mensaje propio de la operación, nunca con el texto de la base;
* **no cierra la sesión**, porque no la creó: la cierra ``get_session`` al
  terminar la petición.

Cada módulo tiene su Unit of Work, que hereda de este y compone los
repositorios que sus operaciones necesitan, todos con la misma sesión. El
router lo construye con una dependencia y se lo pasa al service sin abrirlo;
el service lo abre con ``async with`` y nunca lo construye::

    async with uow.con_mensajes(unique="Ya existe una editorial con ese nombre"):
        uow.editoriales.agregar(editorial)

Se puede abrir más de una vez (cada bloque es una transacción), pero no se
anida: un bloque dentro de otro con el mismo Unit of Work confirmaría a mitad
de la operación. Cada escritura va entera en un solo bloque.
"""

from types import TracebackType
from typing import Self

from sqlalchemy.exc import IntegrityError
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.errors import conflicto_por_integridad


class UnitOfWork:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self._mensajes: dict[str, str] = {}

    def con_mensajes(
        self,
        *,
        unique: str | None = None,
        fk: str | None = None,
        check: str | None = None,
    ) -> Self:
        """Fija los mensajes del 409 para el próximo bloque y devuelve el mismo UoW.

        El que no se pasa usa el mensaje por defecto de ``conflicto_por_integridad``.
        Al salir del bloque se vuelven a los mensajes por defecto.
        """
        mensajes = {"detalle_unique": unique, "detalle_fk": fk, "detalle_check": check}
        self._mensajes = {clave: texto for clave, texto in mensajes.items() if texto is not None}
        return self

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(
        self,
        tipo: type[BaseException] | None,
        error: BaseException | None,
        traza: TracebackType | None,
    ) -> None:
        mensajes, self._mensajes = self._mensajes, {}
        if error is not None:
            await self.session.rollback()
            if isinstance(error, IntegrityError):
                # rechazo de la base dentro del bloque (por ejemplo, en un flush)
                raise conflicto_por_integridad(error, **mensajes) from None
            return  # cualquier otro error sigue su camino
        try:
            await self.session.commit()
        except IntegrityError as rechazo:
            await self.session.rollback()
            # la unicidad la garantiza la base, no se consulta antes
            raise conflicto_por_integridad(rechazo, **mensajes) from None
