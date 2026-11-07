"""Tests del detalle de una venta para el personal o el cliente dueño (issue #58 / J5).

La ruta no lleva requiere_rol: decide el service con los roles vigentes en la
base (RN-04) y la relación con la venta (RN-14). El detalle se arma con un
número fijo de consultas, aunque la venta tenga más renglones o algún libro
esté dado de baja (Ej. 8, C-15).

Base SQLite en memoria con el mismo adaptador asincrónico que el resto de los
tests. Las consultas se cuentan con el evento ``before_cursor_execute``.
"""

import unittest
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import event
from sqlmodel import Session, SQLModel, create_engine, select
from sqlmodel.pool import StaticPool

import app.modules.autores.models  # noqa: F401
import app.modules.clientes.models  # noqa: F401
import app.modules.editoriales.models  # noqa: F401
import app.modules.generos.models  # noqa: F401
import app.modules.libros.models  # noqa: F401
import app.modules.usuarios.models  # noqa: F401
import app.modules.ventas.models  # noqa: F401
from app.core.database import get_session
from app.core.dependencies import get_usuario_actual
from app.core.errors import NoEncontrado, SinPermiso
from app.modules.clientes.models import Cliente
from app.modules.editoriales.models import Editorial
from app.modules.libros.models import Libro
from app.modules.usuarios.models import AsignacionRol, Usuario
from app.modules.ventas.models import RenglonVenta, Venta
from app.modules.ventas.router import router as ventas_router
from app.modules.ventas.service import ver_venta
from app.modules.ventas.unit_of_work import VentaUnitOfWork, get_ventas_uow


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


def _crear_base():
    """Base con personal, clientes y dos ventas: una de Ana (2 renglones) y una de Lucía (4)."""
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    SQLModel.metadata.create_all(engine)
    ahora = datetime.now(timezone.utc)
    ids = {}
    with Session(engine) as s:
        editorial = Editorial(nombre="Sudamericana", pais="Argentina")
        s.add(editorial)
        s.flush()
        libros = {}
        for titulo, precio in [("Rayuela", "25000.00"), ("Ficciones", "22000.00"), ("Bestiario", "18000.00"),
                               ("Respiración artificial", "27000.00"), ("Antología", "30000.00")]:
            libro = Libro(isbn=f"isbn-{titulo}", titulo=titulo, precio=Decimal(precio), stock=10,
                          editorial_id=editorial.id)
            s.add(libro)
            libros[titulo] = libro

        usuarios = {}
        for clave, roles in [
            ("admin", [("ADMIN", None, None)]),
            ("vendedor", [("VENDEDOR", None, None)]),
            ("ana", [("CLIENTE", None, None)]),
            ("tomas", [("CLIENTE", None, None)]),
            # Fue vendedor: el rol está revocado o vencido en la base (el token podría seguir diciendo VENDEDOR).
            ("ex_vendedor", [("VENDEDOR", None, ahora - timedelta(days=1))]),
            ("vendedor_vencido", [("VENDEDOR", ahora - timedelta(days=1), None)]),
        ]:
            usuario = Usuario(email=f"{clave}@example.com", nombre=clave, password_hash="x")
            s.add(usuario)
            s.flush()
            for rol, vence_en, revocada_en in roles:
                s.add(AsignacionRol(usuario_id=usuario.id, rol=rol, desde=ahora - timedelta(days=30),
                                    vence_en=vence_en, revocada_en=revocada_en))
            usuarios[clave] = usuario

        ana = Cliente(nombre="Ana Paz", email="ana@example.com", usuario_id=usuarios["ana"].id)
        tomas = Cliente(nombre="Tomás Ríos", email="tomas@example.com", usuario_id=usuarios["tomas"].id)
        lucia = Cliente(nombre="Lucía Fernández", email="lucia@example.com")  # sin acceso web
        s.add_all([ana, tomas, lucia])
        s.flush()

        def _venta(cliente, titulos):
            venta = Venta(cliente_id=cliente.id, total=Decimal("0.00"))
            for titulo in titulos:
                venta.renglones.append(RenglonVenta(libro_id=libros[titulo].id, cantidad=1,
                                                    precio_unitario=libros[titulo].precio))
            venta.total = sum((r.precio_unitario for r in venta.renglones), Decimal("0.00"))
            s.add(venta)
            s.flush()
            return venta.id

        ids["venta_ana"] = _venta(ana, ["Rayuela", "Ficciones"])
        ids["venta_lucia"] = _venta(lucia, ["Rayuela", "Ficciones", "Bestiario", "Respiración artificial"])
        s.commit()
        ids["libros"] = {t: libro.id for t, libro in libros.items()}
        ids["usuarios"] = {c: u.id for c, u in usuarios.items()}
    return engine, ids


class TestVerVenta(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.engine, self.ids = _crear_base()

    async def asyncTearDown(self):
        self.engine.dispose()

    def _usuario(self, clave):
        with Session(self.engine) as s:
            return s.get(Usuario, self.ids["usuarios"][clave])

    async def _ver(self, venta_id, clave, usuario=None):
        usuario = usuario or self._usuario(clave)
        with Session(self.engine) as s:
            return await ver_venta(VentaUnitOfWork(_AsyncSessionAdapter(s)), venta_id, usuario)

    # ---------- Quién puede verla (C-06) ----------

    async def test_el_personal_ve_cualquier_venta(self):
        for clave in ("vendedor", "admin"):
            with self.subTest(clave):
                venta = await self._ver(self.ids["venta_lucia"], clave)
                self.assertEqual(venta.id, self.ids["venta_lucia"])
                self.assertEqual(len(venta.renglones), 4)

    async def test_la_cliente_ve_su_venta(self):
        venta = await self._ver(self.ids["venta_ana"], "ana")
        self.assertEqual(venta.cliente.email, "ana@example.com")
        self.assertEqual([r.titulo for r in venta.renglones], ["Rayuela", "Ficciones"])
        self.assertEqual(venta.total, Decimal("47000.00"))

    async def test_un_cliente_no_ve_la_venta_ajena(self):
        for venta in ("venta_lucia", "venta_ana"):
            with self.subTest(venta), self.assertRaises(SinPermiso) as error:
                await self._ver(self.ids[venta], "tomas")
            self.assertEqual(error.exception.mensaje, "No tenés permiso para ver esta venta")

    async def test_venta_inexistente_da_404_al_personal_y_al_cliente(self):
        for clave in ("vendedor", "ana"):
            with self.subTest(clave), self.assertRaises(NoEncontrado) as error:
                await self._ver(9999, clave)
            self.assertEqual(error.exception.mensaje, "La venta no existe")

    async def test_un_rol_revocado_o_vencido_en_la_base_ya_no_es_personal(self):
        # RN-04: vale lo que dice la base en esta petición, no el token.
        for clave in ("ex_vendedor", "vendedor_vencido"):
            with self.subTest(clave), self.assertRaises(SinPermiso):
                await self._ver(self.ids["venta_lucia"], clave)

    # ---------- Libro dado de baja ----------

    async def test_la_venta_vieja_sigue_mostrando_el_titulo_del_libro_dado_de_baja(self):
        with Session(self.engine) as s:
            libro = s.get(Libro, self.ids["libros"]["Bestiario"])
            libro.borrado_en = datetime.now(timezone.utc)
            s.add(libro)
            s.commit()
        venta = await self._ver(self.ids["venta_lucia"], "vendedor")
        self.assertIn("Bestiario", [r.titulo for r in venta.renglones])

    # ---------- Número fijo de consultas (C-15) ----------

    async def _contar_consultas(self, venta_id, clave):
        # El usuario lo trae get_usuario_actual antes del service: no se cuenta.
        usuario = self._usuario(clave)
        consultas = []

        def anotar(conn, cursor, sql, parametros, contexto, varias):
            consultas.append(sql)

        event.listen(self.engine, "before_cursor_execute", anotar)
        try:
            await self._ver(venta_id, clave, usuario)
        finally:
            event.remove(self.engine, "before_cursor_execute", anotar)
        return len(consultas)

    async def test_el_detalle_usa_las_mismas_consultas_con_2_y_con_4_renglones(self):
        con_2 = await self._contar_consultas(self.ids["venta_ana"], "vendedor")
        con_4 = await self._contar_consultas(self.ids["venta_lucia"], "vendedor")
        self.assertEqual(con_2, con_4)
        # roles + venta JOIN cliente + renglones JOIN libro
        self.assertEqual(con_2, 3)

    async def test_el_dueno_suma_una_sola_consulta_fija(self):
        # roles + dueño de la venta + venta JOIN cliente + renglones JOIN libro
        self.assertEqual(await self._contar_consultas(self.ids["venta_ana"], "ana"), 4)

    async def test_un_libro_dado_de_baja_no_agrega_consultas(self):
        antes = await self._contar_consultas(self.ids["venta_lucia"], "vendedor")
        with Session(self.engine) as s:
            libro = s.get(Libro, self.ids["libros"]["Rayuela"])
            libro.borrado_en = datetime.now(timezone.utc)
            s.add(libro)
            s.commit()
        self.assertEqual(await self._contar_consultas(self.ids["venta_lucia"], "vendedor"), antes)


class TestRutaDetalleVenta(unittest.TestCase):
    """Los códigos HTTP de GET /ventas/{id}: 401, 403, 404 y 200."""

    def setUp(self):
        self.engine, self.ids = _crear_base()
        app = FastAPI()
        app.include_router(ventas_router)

        def _sesion():
            with Session(self.engine) as s:
                yield _AsyncSessionAdapter(s)

        def _uow():
            with Session(self.engine) as s:
                yield VentaUnitOfWork(_AsyncSessionAdapter(s))

        app.dependency_overrides[get_session] = _sesion
        app.dependency_overrides[get_ventas_uow] = _uow
        self.app = app
        self.client = TestClient(app)

    def tearDown(self):
        self.engine.dispose()

    def _como(self, clave):
        with Session(self.engine) as s:
            usuario = s.get(Usuario, self.ids["usuarios"][clave])
        self.app.dependency_overrides[get_usuario_actual] = lambda: usuario

    def test_sin_sesion_401(self):
        respuesta = self.client.get(f"/ventas/{self.ids['venta_ana']}")
        self.assertEqual(respuesta.status_code, 401)

    def test_la_duena_200_y_otro_cliente_403(self):
        self._como("ana")
        self.assertEqual(self.client.get(f"/ventas/{self.ids['venta_ana']}").status_code, 200)
        self._como("tomas")
        respuesta = self.client.get(f"/ventas/{self.ids['venta_ana']}")
        self.assertEqual(respuesta.status_code, 403)
        self.assertEqual(respuesta.json(), {"detail": "No tenés permiso para ver esta venta"})

    def test_el_vendedor_200_y_venta_inexistente_404(self):
        self._como("vendedor")
        self.assertEqual(self.client.get(f"/ventas/{self.ids['venta_lucia']}").status_code, 200)
        respuesta = self.client.get("/ventas/9999")
        self.assertEqual(respuesta.status_code, 404)
        self.assertEqual(respuesta.json(), {"detail": "La venta no existe"})


if __name__ == "__main__":
    unittest.main()
