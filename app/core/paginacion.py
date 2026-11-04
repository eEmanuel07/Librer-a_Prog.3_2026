"""Paginación de los listados: el envoltorio {items, total, page, size, pages} (Ej. 3)."""

from collections.abc import Sequence
from dataclasses import dataclass
from math import ceil
from typing import Annotated, Any, Generic, TypeVar

from fastapi import Query
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.sql import Select
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.errors import ErrorDeDominio

T = TypeVar("T")

SIZE_POR_DEFECTO = 20
SIZE_MAXIMO = 100


class PaginaInexistente(ErrorDeDominio):
    """Se pidió una página más allá de la última. main.py la responde con 422."""


@dataclass(frozen=True)
class ParametrosPagina:
    page: int = 1
    size: int = SIZE_POR_DEFECTO

    @property
    def offset(self) -> int:
        """Cuántas filas saltear: la página 1 empieza en 0, la 2 en size, etc."""
        return (self.page - 1) * self.size


def parametros_pagina(
    page: Annotated[int, Query(ge=1, description="Número de página, desde 1")] = 1,
    size: Annotated[
        int, Query(ge=1, le=SIZE_MAXIMO, description="Elementos por página, de 1 a 100")
    ] = SIZE_POR_DEFECTO,
) -> ParametrosPagina:
    """Dependencia común de todos los listados: valida page y size (422 si no cumplen)."""
    return ParametrosPagina(page=page, size=size)


def calcular_paginas(total: int, size: int) -> int:
    """Cantidad de páginas. Con cero resultados hay una, vacía."""
    return max(1, ceil(total / size))


def validar_pagina(params: ParametrosPagina, total: int) -> None:
    """Lanza PaginaInexistente si page pasa de la última página."""
    paginas = calcular_paginas(total, params.size)
    if params.page > paginas:
        raise PaginaInexistente(f"La página {params.page} no existe: hay {paginas}")


async def paginar(
    session: AsyncSession, consulta: Select[Any], params: ParametrosPagina
) -> tuple[Sequence[Any], int]:
    """Cuenta y trae una página de la consulta: devuelve (items, total).

    La consulta tiene que traer order_by: sin orden, dos páginas se pueden pisar.
    Son siempre dos consultas, sin importar el tamaño de la página.
    """
    subconsulta = consulta.order_by(None).subquery()
    total = (await session.exec(select(func.count()).select_from(subconsulta))).one()
    validar_pagina(params, total)
    items = (await session.exec(consulta.offset(params.offset).limit(params.size))).all()
    return items, total


class Pagina(BaseModel, Generic[T]):
    """El envoltorio de todos los listados."""

    items: list[T]
    total: int
    page: int
    size: int
    pages: int

    @classmethod
    def armar(cls, items: Sequence[T], total: int, params: ParametrosPagina) -> "Pagina[T]":
        return cls(
            items=list(items),
            total=total,
            page=params.page,
            size=params.size,
            pages=calcular_paginas(total, params.size),
        )
