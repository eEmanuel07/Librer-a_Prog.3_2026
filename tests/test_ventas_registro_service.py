"""Tests del registro de una venta con descuento de stock (issue #56 / J3, RN-10).

Casos C-10, C-11 y C-12 de la consigna sobre el service, con una base SQLite en
memoria (claves foráneas activadas) y el mismo adaptador asincrónico que usan
los tests de autenticación. La base real (PostgreSQL) además bloquea los libros
con FOR UPDATE; SQLite ignora esa cláusula, así que acá no se prueba la
concurrencia, sólo la lógica.
"""

import unittest
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import event
from sqlmodel import Session, SQLModel, create_engine, func, select
from sqlmodel.pool import StaticPool

import app.modules.autores.models  # noqa: F401
import app.modules.clientes.models  # noqa: F401
import app.modules.editoriales.models  # noqa: F401
import app.modules.generos.models  # noqa: F401
import app.modules.libros.models  # noqa: F401
import app.modules.usuarios.models  # noqa: F401
import app.modules.ventas.models  # noqa: F401
from app.core.errors import Conflicto
from app.modules.clientes.models import Cliente
from app.modules.editoriales.models import Editorial
from app.modules.libros.models import Libro, MovimientoStock
from app.modules.usuarios.models import Usuario
from app.modules.ventas.models import RenglonVenta, Venta
from app.modules.ventas.schemas import VentaCreate
from app.modules.ventas.service import crear_venta
from app.modules.ventas.unit_of_work import VentaUnitOfWork



class _AsyncSessionAdapter:
    """Sesión sincrónica de SQLite con la interfaz asincrónica que usan los repositorios."""

    def __init__(self, sync_session: Session) -> None:
        self._s = sync_session

    def add(self, obj):
        self._s.add(obj)

    async def flush(self):
        self._s.flush()

    async def commit(self):
        self._s.commit()

    async def rollback(self):
        self._s.rollback()

    async def exec(self, statement):
        return self._s.exec(statement)

    async def get(self, entity_class, ident):
        return self._s.get(entity_class, ident)


def _activar_claves_foraneas(conexion, _registro):
    # SQLite no controla las FK si no se le pide: sin esto, un cliente
    # inexistente no daría error como en PostgreSQL.
    conexion.execute("PRAGMA foreign_keys=ON")


class TestRegistrarVenta(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.engine = create_engine(
            "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
        )
        event.listen(self.engine, "connect", _activar_claves_foraneas)
        SQLModel.metadata.create_all(self.engine)
        with Session(self.engine) as s:
            editorial = Editorial(nombre="Sudamericana", pais="Argentina")
            s.add(editorial)
            s.flush()
            # Stock de los datos iniciales del parcial que usan los casos.
            for titulo, precio, stock in [
                ("Rayuela", "25000.00", 10),
                ("Ficciones", "22000.00", 8),
                ("Bestiario", "18000.00", 1),
            ]:
                s.add(Libro(isbn=f"isbn-{titulo}", titulo=titulo, precio=Decimal(precio),
                            stock=stock, editorial_id=editorial.id))
            s.add(Libro(isbn="isbn-baja", titulo="Libro dado de baja", precio=Decimal("1000.00"),
                        stock=5, editorial_id=editorial.id, borrado_en=datetime.now(timezone.utc)))
            s.add(Cliente(nombre="Lucía Fernández", email="lucia@example.com"))
            s.add(Usuario(email="vendedor@example.com", nombre="Vendedor", password_hash="x"))
            s.commit()
            self.ids = {libro.titulo: libro.id for libro in s.exec(select(Libro)).all()}
            self.cliente_id = s.exec(select(Cliente.id)).one()
            self.vendedor_id = s.exec(select(Usuario.id)).one()

    async def asyncTearDown(self):
        self.engine.dispose()

    async def _vender(self, renglones, cliente_id=None):
        datos = VentaCreate(
            cliente_id=cliente_id if cliente_id is not None else self.cliente_id,
            renglones=[{"libro_id": libro_id, "cantidad": cantidad} for libro_id, cantidad in renglones],
        )
        with Session(self.engine) as s:
            uow = VentaUnitOfWork(_AsyncSessionAdapter(s))
            return await crear_venta(uow, datos, self.vendedor_id)

    def _stock(self, titulo):
        with Session(self.engine) as s:
            return s.get(Libro, self.ids[titulo]).stock

    def _contar(self, modelo):
        with Session(self.engine) as s:
            return s.exec(select(func.count()).select_from(modelo)).one()

    def _assert_nada_escrito(self):
        self.assertEqual(self._contar(Venta), 0)
        self.assertEqual(self._contar(RenglonVenta), 0)
        self.assertEqual(self._contar(MovimientoStock), 0)
        self.assertEqual(self._stock("Rayuela"), 10)
        self.assertEqual(self._stock("Ficciones"), 8)
        self.assertEqual(self._stock("Bestiario"), 1)

    # ---------- C-10 ----------

    async def test_c10_venta_valida_descuenta_stock_y_deja_un_movimiento_por_renglon(self):
        venta = await self._vender([(self.ids["Rayuela"], 2), (self.ids["Ficciones"], 1)])

        # 201 con los precios copiados y el total calculado
        precios = {r.titulo: r.precio_unitario for r in venta.renglones}
        self.assertEqual(precios, {"Rayuela": Decimal("25000.00"), "Ficciones": Decimal("22000.00")})
        self.assertEqual(venta.total, Decimal("72000.00"))

        # el stock de cada libro bajó
        self.assertEqual(self._stock("Rayuela"), 8)
        self.assertEqual(self._stock("Ficciones"), 7)

        # un movimiento de salida por renglón, de esta venta y de quien la registró
        with Session(self.engine) as s:
            movimientos = s.exec(select(MovimientoStock).order_by(MovimientoStock.libro_id)).all()
        self.assertEqual(
            [(m.libro_id, m.cantidad, m.venta_id, m.usuario_id, m.motivo) for m in movimientos],
            [
                (self.ids["Rayuela"], -2, venta.id, self.vendedor_id, "Venta"),
                (self.ids["Ficciones"], -1, venta.id, self.vendedor_id, "Venta"),
            ],
        )

    # ---------- C-11 ----------

    async def test_c11_un_libro_que_no_alcanza_no_deja_ninguna_escritura(self):
        # Rayuela (1, alcanza) y Bestiario (2, hay 1): Rayuela se descuenta primero
        # y el bloque tiene que revertir también ese descuento.
        with self.assertRaises(Conflicto) as error:
            await self._vender([(self.ids["Rayuela"], 1), (self.ids["Bestiario"], 2)])
        self.assertIn("Bestiario", error.exception.mensaje)
        self._assert_nada_escrito()

    # ---------- C-12 ----------

    async def test_c12_cliente_inexistente(self):
        # La base rechaza la clave foránea en el flush y el UoW la traduce a 409.
        # El mensaje propio («El cliente indicado no existe») sale del sqlstate de
        # PostgreSQL (23503), que SQLite no informa: acá se comprueba el 409 y que
        # no quede nada escrito; el texto se verifica contra PostgreSQL.
        with self.assertRaises(Conflicto):
            await self._vender([(self.ids["Rayuela"], 1)], cliente_id=9999)
        self._assert_nada_escrito()

    async def test_c12_libro_inexistente(self):
        with self.assertRaises(Conflicto) as error:
            await self._vender([(self.ids["Rayuela"], 1), (9999, 1)])
        self.assertEqual(error.exception.mensaje, "No existe el libro con id 9999")
        self._assert_nada_escrito()

    async def test_c12_libro_dado_de_baja(self):
        with self.assertRaises(Conflicto) as error:
            await self._vender([(self.ids["Rayuela"], 1), (self.ids["Libro dado de baja"], 1)])
        self.assertEqual(error.exception.mensaje, "El libro está dado de baja")
        self._assert_nada_escrito()
        self.assertEqual(self._stock("Libro dado de baja"), 5)

    # ---------- Invariante de RN-11 ----------

    async def test_el_stock_baja_lo_mismo_que_suman_los_movimientos(self):
        antes = {t: self._stock(t) for t in ("Rayuela", "Ficciones", "Bestiario")}
        await self._vender([(self.ids["Rayuela"], 3), (self.ids["Bestiario"], 1)])
        with Session(self.engine) as s:
            for titulo, stock_antes in antes.items():
                suma = s.exec(
                    select(func.coalesce(func.sum(MovimientoStock.cantidad), 0)).where(
                        MovimientoStock.libro_id == self.ids[titulo]
                    )
                ).one()
                self.assertEqual(self._stock(titulo) - stock_antes, suma, titulo)


if __name__ == "__main__":
    unittest.main()
