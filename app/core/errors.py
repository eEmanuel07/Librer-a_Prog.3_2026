"""Traducción de errores de integridad a respuestas HTTP propias (RN-12).

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
    sqlstate = getattr(getattr(exc, "orig", None), "sqlstate", None)
    if sqlstate == _SQLSTATE_UNIQUE:
        detail = detalle_unique
    elif sqlstate == _SQLSTATE_FOREIGN_KEY:
        detail = detalle_fk
    elif sqlstate == _SQLSTATE_CHECK:
        detail = detalle_check
    else:
        # Sin sqlstate reconocible: mensaje genérico, nunca ``str(exc)``.
        detail = "No se pudo completar la escritura."
    return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=detail)
