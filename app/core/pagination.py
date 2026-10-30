"""Paginación común para todos los listados (RN-10).

RN-10: todo listado se pagina con ``limit`` (de 1 a 100, por defecto 20) y
``offset`` (desde 0). FastAPI responde 422 solo si los parámetros no cumplen
el contrato, sin ejecutar el handler.

Uso típico en un router::

    from fastapi import Depends

    from app.core.pagination import Paginacion, paginacion

    @router.get("/")
    async def listar(
        pag: Paginacion = Depends(paginacion),
        uow: UnitOfWork = Depends(get_uow),
    ) -> list[AlgoRead]:
        return await service.listar(uow, limit=pag.limit, offset=pag.offset)
"""

from dataclasses import dataclass
from typing import Annotated

from fastapi import Query


@dataclass(frozen=True)
class Paginacion:
    limit: int = 20
    offset: int = 0


def paginacion(
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> Paginacion:
    """Dependencia compartida: valida y empaqueta ``limit``/``offset``."""
    return Paginacion(limit=limit, offset=offset)
