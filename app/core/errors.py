"""Errores de dominio y traducción de errores de integridad (RN-12).

Los services lanzan ``NoEncontrado`` y ``Conflicto``; el router de cada
módulo los pasa a 404 / 409 con el mismo mensaje. El commit del UnitOfWork
traduce el ``IntegrityError`` con ``conflicto_por_integridad``: ningún error
devuelve al cliente texto interno de la base (nombres de tablas,
restricciones o trazas).

Uso típico en un service::

    uow.editoriales.agregar(editorial)
    await uow.commit(detalle_unique="Ya existe una editorial con ese nombre")
"""

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


def conflicto_por_integridad(
    exc: IntegrityError,
    *,
    detalle_unique: str = "El registro ya existe.",
    detalle_fk: str = "La operación referencia un recurso inexistente.",
    detalle_check: str = "Los datos violan una regla de la base.",
) -> Conflicto:
    """Convierte un ``IntegrityError`` en un ``Conflicto`` con mensaje propio.

    La consigna (Ej. 4) pide 409 siempre que la base rechace la escritura:
    unicidad (RN-01, RN-02, RN-09), clave foránea (C-04, C-05) o check.
    """
    sqlstate = getattr(getattr(exc, "orig", None), "sqlstate", None)
    if sqlstate == _SQLSTATE_UNIQUE:
        return Conflicto(detalle_unique)
    if sqlstate == _SQLSTATE_FOREIGN_KEY:
        return Conflicto(detalle_fk)
    if sqlstate == _SQLSTATE_CHECK:
        return Conflicto(detalle_check)
    # Sin sqlstate reconocible: mensaje genérico, nunca ``str(exc)``.
    return Conflicto("No se pudo completar la escritura.")
