"""Errores de dominio y traducción de errores de integridad (RN-12).

Los módulos con Repository + Unit of Work usan ``NoEncontrado`` y
``Conflicto``: el commit del UoW traduce el ``IntegrityError`` con
``conflicto_por_integridad`` y el router los pasa a 404 / 409.

Los módulos que todavía no migraron usan ``http_409_por_integridad``.

Todo el equipo usa este helper en sus services: ningún error devuelve al
cliente texto interno de la base (nombres de tablas, restricciones o trazas).

Uso típico en un service::

    from sqlalchemy.exc import IntegrityError

    from app.core.errors import http_409_por_integridad

    try:
        session.add(obj)
        await session.commit()
        await session.refresh(obj)
    except IntegrityError as exc:
        await session.rollback()
        raise http_409_por_integridad(
            exc,
            detalle_unique="Email en uso.",
            detalle_fk="Referencia a un recurso inexistente.",
        )
"""

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError

# Códigos de estado de PostgreSQL (los expone el driver asyncpg en
# ``exc.orig.sqlstate``). No se inspecciona el texto del error.
_SQLSTATE_UNIQUE = "23505"
_SQLSTATE_FOREIGN_KEY = "23503"
_SQLSTATE_CHECK = "23514"


class ErrorDeDominio(Exception):
    """Error de negocio con mensaje propio, sin nada de HTTP.

    Los services lanzan sus subclases y cada router las traduce a un código
    de estado (NoEncontrado -> 404, Conflicto -> 409).
    """

    def __init__(self, mensaje: str) -> None:
        super().__init__(mensaje)
        self.mensaje = mensaje


class NoEncontrado(ErrorDeDominio):
    """El recurso pedido no existe."""


class Conflicto(ErrorDeDominio):
    """La base rechazó la escritura (unicidad, clave foránea o check)."""


def _detalle_por_integridad(
    exc: IntegrityError, *, detalle_unique: str, detalle_fk: str, detalle_check: str
) -> str:
    sqlstate = getattr(getattr(exc, "orig", None), "sqlstate", None)
    if sqlstate == _SQLSTATE_UNIQUE:
        return detalle_unique
    if sqlstate == _SQLSTATE_FOREIGN_KEY:
        return detalle_fk
    if sqlstate == _SQLSTATE_CHECK:
        return detalle_check
    # Sin sqlstate reconocible: mensaje genérico, nunca ``str(exc)``.
    return "No se pudo completar la escritura."


def http_409_por_integridad(
    exc: IntegrityError,
    *,
    detalle_unique: str = "El registro ya existe.",
    detalle_fk: str = "La operación referencia un recurso inexistente.",
    detalle_check: str = "Los datos violan una regla de la base.",
) -> HTTPException:
    """Convierte un ``IntegrityError`` en un 409 con mensaje propio.

    La consigna (Ej. 4) pide 409 siempre que la base rechace la escritura:
    unicidad (RN-01, RN-02, RN-09), clave foránea (C-04, C-05) o check.
    """
    detail = _detalle_por_integridad(
        exc, detalle_unique=detalle_unique, detalle_fk=detalle_fk, detalle_check=detalle_check
    )
    return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=detail)


def conflicto_por_integridad(
    exc: IntegrityError,
    *,
    detalle_unique: str = "El registro ya existe.",
    detalle_fk: str = "La operación referencia un recurso inexistente.",
    detalle_check: str = "Los datos violan una regla de la base.",
) -> Conflicto:
    """Igual que ``http_409_por_integridad`` pero como error de dominio.

    Lo usa el commit del UnitOfWork: mismos mensajes propios, sin HTTP.
    """
    return Conflicto(
        _detalle_por_integridad(
            exc, detalle_unique=detalle_unique, detalle_fk=detalle_fk, detalle_check=detalle_check
        )
    )
