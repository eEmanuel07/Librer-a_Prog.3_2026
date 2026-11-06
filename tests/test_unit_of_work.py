"""Tests del UnitOfWork base (app/core/unit_of_work.py), issue #33 / Ej. 6.

Se usa una sesión falsa que solo anota qué se llamó: el UnitOfWork base no
consulta nada, solo confirma, revierte y traduce errores.
"""

import sys
import unittest

from sqlalchemy.exc import IntegrityError

sys.path.insert(0, ".")

from app.core.errors import Conflicto, NoEncontrado  # noqa: E402
from app.core.unit_of_work import UnitOfWork  # noqa: E402

_UNIQUE, _FK, _CHECK = "23505", "23503", "23514"


class _ErrorDelDriver(Exception):
    """Imita el error de asyncpg: lo único que mira la traducción es ``sqlstate``."""

    def __init__(self, sqlstate: str) -> None:
        super().__init__("texto interno de la base: tabla libro, restricción uq_libro_isbn_vigente")
        self.sqlstate = sqlstate


def _integrity_error(sqlstate: str) -> IntegrityError:
    return IntegrityError("INSERT INTO libro ...", {}, _ErrorDelDriver(sqlstate))


class _SesionFalsa:
    def __init__(self, error_en_commit: IntegrityError | None = None) -> None:
        self.commits = 0
        self.rollbacks = 0
        self.cierres = 0
        self._error_en_commit = error_en_commit

    async def commit(self) -> None:
        self.commits += 1
        if self._error_en_commit is not None:
            raise self._error_en_commit

    async def rollback(self) -> None:
        self.rollbacks += 1

    async def close(self) -> None:
        self.cierres += 1


class TestUnitOfWorkBase(unittest.IsolatedAsyncioTestCase):
    async def test_01_sin_error_confirma_una_vez_y_no_revierte(self):
        sesion = _SesionFalsa()
        async with UnitOfWork(sesion):
            pass
        self.assertEqual((sesion.commits, sesion.rollbacks), (1, 0))

    async def test_02_error_de_dominio_revierte_no_confirma_y_lo_deja_pasar(self):
        sesion = _SesionFalsa()
        with self.assertRaises(NoEncontrado):
            async with UnitOfWork(sesion):
                raise NoEncontrado("El libro no existe")
        self.assertEqual((sesion.commits, sesion.rollbacks), (0, 1))

    async def test_03_integrity_error_en_el_bloque_es_conflicto_segun_sqlstate(self):
        casos = [(_UNIQUE, "ISBN repetido"), (_FK, "Editorial inexistente"), (_CHECK, "Regla violada")]
        for sqlstate, esperado in casos:
            with self.subTest(sqlstate=sqlstate):
                sesion = _SesionFalsa()
                uow = UnitOfWork(sesion).con_mensajes(
                    unique="ISBN repetido", fk="Editorial inexistente", check="Regla violada"
                )
                with self.assertRaises(Conflicto) as ctx:
                    async with uow:
                        raise _integrity_error(sqlstate)  # como si saltara en un flush
                self.assertEqual(ctx.exception.mensaje, esperado)
                self.assertEqual((sesion.commits, sesion.rollbacks), (0, 1))

    async def test_04_integrity_error_en_el_commit_revierte_y_es_conflicto(self):
        # El CHECK no se puede provocar desde la API (el schema da 422 antes):
        # este test es la prueba del 409 por CHECK (decisión 6 de design.md).
        casos = [(_UNIQUE, "Email repetido"), (_FK, "Cliente inexistente"), (_CHECK, "Regla violada")]
        for sqlstate, esperado in casos:
            with self.subTest(sqlstate=sqlstate):
                sesion = _SesionFalsa(error_en_commit=_integrity_error(sqlstate))
                uow = UnitOfWork(sesion).con_mensajes(
                    unique="Email repetido", fk="Cliente inexistente", check="Regla violada"
                )
                with self.assertRaises(Conflicto) as ctx:
                    async with uow:
                        pass
                self.assertEqual(ctx.exception.mensaje, esperado)
                self.assertEqual((sesion.commits, sesion.rollbacks), (1, 1))

    async def test_05_el_conflicto_no_arrastra_el_error_de_la_base(self):
        sesion = _SesionFalsa(error_en_commit=_integrity_error(_UNIQUE))
        with self.assertRaises(Conflicto) as ctx:
            async with UnitOfWork(sesion).con_mensajes(unique="Ya existe"):
                pass
        self.assertNotIn("uq_libro_isbn_vigente", ctx.exception.mensaje)
        self.assertIsNone(ctx.exception.__cause__)
        self.assertTrue(ctx.exception.__suppress_context__)

    async def test_06_nunca_cierra_la_sesion(self):
        sesion = _SesionFalsa()
        async with UnitOfWork(sesion):
            pass
        with self.assertRaises(NoEncontrado):
            async with UnitOfWork(sesion):
                raise NoEncontrado("no")
        self.assertEqual(sesion.cierres, 0)

    async def test_07_se_puede_abrir_dos_veces_y_confirma_las_dos(self):
        sesion = _SesionFalsa()
        uow = UnitOfWork(sesion)
        async with uow:
            pass
        async with uow:
            pass
        self.assertEqual((sesion.commits, sesion.rollbacks), (2, 0))

    async def test_08_los_mensajes_se_reinician_al_salir(self):
        uow = UnitOfWork(_SesionFalsa())
        async with uow.con_mensajes(unique="Mensaje del alta"):
            pass
        # segunda apertura sin con_mensajes: vuelve al mensaje por defecto
        with self.assertRaises(Conflicto) as ctx:
            async with uow:
                raise _integrity_error(_UNIQUE)
        self.assertEqual(ctx.exception.mensaje, "El registro ya existe.")

    async def test_09_los_mensajes_tambien_se_reinician_despues_de_un_error(self):
        uow = UnitOfWork(_SesionFalsa())
        with self.assertRaises(Conflicto):
            async with uow.con_mensajes(fk="Mensaje del alta"):
                raise _integrity_error(_FK)
        with self.assertRaises(Conflicto) as ctx:
            async with uow:
                raise _integrity_error(_FK)
        self.assertEqual(ctx.exception.mensaje, "La operación referencia un recurso inexistente.")

    async def test_10_con_mensajes_devuelve_el_mismo_unit_of_work(self):
        uow = UnitOfWork(_SesionFalsa())
        self.assertIs(uow.con_mensajes(unique="x"), uow)

    async def test_11_aenter_devuelve_el_mismo_unit_of_work(self):
        uow = UnitOfWork(_SesionFalsa())
        async with uow as abierto:
            self.assertIs(abierto, uow)

    async def test_12_solo_guarda_la_sesion(self):
        sesion = _SesionFalsa()
        uow = UnitOfWork(sesion)
        self.assertIs(uow.session, sesion)
        repos = [n for n in vars(uow) if not n.startswith("_") and n != "session"]
        self.assertEqual(repos, [])


if __name__ == "__main__":
    unittest.main()
