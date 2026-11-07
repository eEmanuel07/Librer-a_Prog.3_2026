"""Tests de GET /ventas y GET /mis-ventas con el envoltorio (issue #59 / J6).

/ventas es del personal (VENDEDOR o ADMIN, según los roles vigentes en la base);
/mis-ventas sólo pide estar autenticado y devuelve las ventas del cliente
asociado al usuario (RN-14). Los dos devuelven {items, total, page, size, pages}.

Base SQLite en memoria con el mismo adaptador asincrónico que el resto de los
tests. Las consultas se cuentan con el evento ``before_cursor_execute``.
"""

import unittest
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import event
from sqlmodel import Session, SQLModel, create_engine
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
from app.core.errors import SinPermiso
from app.core.paginacion import PaginaInexistente, ParametrosPagina
from app.main import app as app_principal
from app.main import pagina_inexistente
from app.modules.clientes.models import Cliente
from app.modules.editoriales.models import Editorial
from app.modules.libros.models import Libro
from app.modules.usuarios.models import AsignacionRol, Usuario
from app.modules.ventas.models import RenglonVenta, Venta
from app.modules.ventas.router import router as ventas_router
from app.modules.ventas.router import router_mis_ventas
from app.modules.ventas.service import listar_mis_ventas, listar_ventas
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
    """Personal, clientes y 5 ventas: 3 de Ana, 1 de Tomás y 1 de Lucía (sin acceso web)."""
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    SQLModel.metadata.create_all(engine)
    ahora = datetime.now(timezone.utc)
    with Session(engine) as s:
        editorial = Editorial(nombre="Sudamericana", pais="Argentina")
        s.add(editorial)
        s.flush()
        libro = Libro(isbn="isbn-rayuela", titulo="Rayuela", precio=Decimal("25000.00"), stock=50,
                      editorial_id=editorial.id)
        s.add(libro)

        usuarios = {}
        for clave, rol, revocada_en in [
            ("admin", "ADMIN", None),
            ("vendedor", "VENDEDOR", None),
            ("ana", "CLIENTE", None),
            ("tomas", "CLIENTE", None),
            ("ex_vendedor", "VENDEDOR", ahora - timedelta(days=1)),
        ]:
            usuario = Usuario(email=f"{clave}@example.com", nombre=clave, password_hash="x")
            s.add(usuario)
            s.flush()
            s.add(AsignacionRol(usuario_id=usuario.id, rol=rol, desde=ahora - timedelta(days=30),
                                revocada_en=revocada_en))
            usuarios[clave] = usuario.id

        ana = Cliente(nombre="Ana Paz", email="ana@example.com", usuario_id=usuarios["ana"])
        tomas = Cliente(nombre="Tomás Ríos", email="tomas@example.com", usuario_id=usuarios["tomas"])
        lucia = Cliente(nombre="Lucía Fernández", email="lucia@example.com")
        s.add_all([ana, tomas, lucia])
        s.flush()

        ventas = {}
        for cliente in [ana, tomas, ana, lucia, ana]:
            venta = Venta(cliente_id=cliente.id, total=Decimal("25000.00"))
            venta.renglones.append(RenglonVenta(libro_id=libro.id, cantidad=1,
                                                precio_unitario=Decimal("25000.00")))
            s.add(venta)
            s.flush()
            ventas.setdefault(cliente.email, []).append(venta.id)
        s.commit()
    return engine, usuarios, ventas


class TestListadosService(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.engine, self.usuarios, self.ventas = _crear_base()

    async def asyncTearDown(self):
        self.engine.dispose()

    def _usuario(self, clave):
        with Session(self.engine) as s:
            return s.get(Usuario, self.usuarios[clave])

    async def _llamar(self, funcion, clave, page=1, size=20, usuario=None):
        usuario = usuario or self._usuario(clave)
        with Session(self.engine) as s:
            uow = VentaUnitOfWork(_AsyncSessionAdapter(s))
            return await funcion(uow, ParametrosPagina(page=page, size=size), usuario)

    async def _contar_consultas(self, funcion, clave, **kwargs):
        # El usuario lo trae get_usuario_actual antes del service: no se cuenta.
        usuario = self._usuario(clave)
        consultas = []

        def anotar(conn, cursor, sql, parametros, contexto, varias):
            consultas.append(sql)

        event.listen(self.engine, "before_cursor_execute", anotar)
        try:
            await self._llamar(funcion, clave, usuario=usuario, **kwargs)
        finally:
            event.remove(self.engine, "before_cursor_execute", anotar)
        return len(consultas)

    # ---------- GET /ventas ----------

    async def test_el_personal_ve_todas_las_ventas_con_el_envoltorio(self):
        for clave in ("vendedor", "admin"):
            with self.subTest(clave):
                pagina = await self._llamar(listar_ventas, clave)
                self.assertEqual((pagina.total, pagina.page, pagina.size, pagina.pages), (5, 1, 20, 1))
                ids = [v.id for v in pagina.items]
                self.assertEqual(ids, sorted(ids))
                self.assertEqual(len(ids), 5)
                self.assertEqual(pagina.items[0].cliente.email, "ana@example.com")

    async def test_un_cliente_o_un_rol_revocado_no_ven_todas_las_ventas(self):
        for clave in ("ana", "ex_vendedor"):
            with self.subTest(clave), self.assertRaises(SinPermiso) as error:
                await self._llamar(listar_ventas, clave)
            self.assertEqual(error.exception.mensaje, "No tenés permiso para ver todas las ventas")

    async def test_paginas_de_ventas_y_pagina_de_mas(self):
        ultima = await self._llamar(listar_ventas, "vendedor", page=3, size=2)
        self.assertEqual((ultima.total, ultima.pages, len(ultima.items)), (5, 3, 1))
        with self.assertRaises(PaginaInexistente) as error:
            await self._llamar(listar_ventas, "vendedor", page=4, size=2)
        self.assertEqual(error.exception.mensaje, "La página 4 no existe: hay 3")

    async def test_el_listado_usa_las_mismas_consultas_con_cualquier_tamano(self):
        # roles + conteo + página (venta JOIN cliente)
        self.assertEqual(await self._contar_consultas(listar_ventas, "vendedor", size=2), 3)
        self.assertEqual(await self._contar_consultas(listar_ventas, "vendedor", size=5), 3)

    # ---------- GET /mis-ventas ----------

    async def test_mis_ventas_trae_solo_las_del_cliente_del_usuario(self):
        pagina = await self._llamar(listar_mis_ventas, "ana")
        self.assertEqual(pagina.total, 3)
        self.assertEqual([v.id for v in pagina.items], self.ventas["ana@example.com"])
        self.assertTrue(all(v.cliente.email == "ana@example.com" for v in pagina.items))

        pagina = await self._llamar(listar_mis_ventas, "tomas")
        self.assertEqual([v.id for v in pagina.items], self.ventas["tomas@example.com"])

    async def test_mis_ventas_sin_ficha_de_cliente_es_una_pagina_vacia(self):
        pagina = await self._llamar(listar_mis_ventas, "vendedor")
        self.assertEqual((pagina.items, pagina.total, pagina.page, pagina.pages), ([], 0, 1, 1))

    async def test_mis_ventas_paginado(self):
        pagina = await self._llamar(listar_mis_ventas, "ana", page=2, size=2)
        self.assertEqual((pagina.total, pagina.pages, [v.id for v in pagina.items]),
                         (3, 2, self.ventas["ana@example.com"][2:]))
        with self.assertRaises(PaginaInexistente):
            await self._llamar(listar_mis_ventas, "ana", page=3, size=2)

    async def test_mis_ventas_usa_dos_consultas_fijas(self):
        # conteo + página (venta JOIN cliente)
        self.assertEqual(await self._contar_consultas(listar_mis_ventas, "ana", size=1), 2)
        self.assertEqual(await self._contar_consultas(listar_mis_ventas, "ana", size=3), 2)


class TestListadosHttp(unittest.TestCase):
    """Códigos HTTP de GET /ventas y GET /mis-ventas."""

    def setUp(self):
        self.engine, self.usuarios, _ = _crear_base()
        app = FastAPI()
        app.include_router(ventas_router)
        app.include_router(router_mis_ventas)
        app.add_exception_handler(PaginaInexistente, pagina_inexistente)  # el mismo de main.py

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
            usuario = s.get(Usuario, self.usuarios[clave])
        self.app.dependency_overrides[get_usuario_actual] = lambda: usuario

    def test_mis_ventas_esta_registrada_en_la_app(self):
        rutas = set(app_principal.openapi()["paths"])
        self.assertIn("/mis-ventas", rutas)
        self.assertIn("/ventas/", rutas)

    def test_sin_sesion_401(self):
        for ruta in ("/ventas/", "/mis-ventas"):
            with self.subTest(ruta):
                self.assertEqual(self.client.get(ruta).status_code, 401)

    def test_ventas_403_para_un_cliente_y_200_para_el_vendedor(self):
        self._como("ana")
        respuesta = self.client.get("/ventas/")
        self.assertEqual(respuesta.status_code, 403)
        self.assertEqual(respuesta.json(), {"detail": "No tenés permiso para ver todas las ventas"})
        self._como("vendedor")
        respuesta = self.client.get("/ventas/", params={"size": 2})
        self.assertEqual(respuesta.status_code, 200)
        cuerpo = respuesta.json()
        self.assertEqual(set(cuerpo), {"items", "total", "page", "size", "pages"})
        self.assertEqual((cuerpo["total"], cuerpo["size"], cuerpo["pages"], len(cuerpo["items"])), (5, 2, 3, 2))

    def test_mis_ventas_200_con_el_envoltorio(self):
        self._como("ana")
        cuerpo = self.client.get("/mis-ventas").json()
        self.assertEqual((cuerpo["total"], cuerpo["page"], cuerpo["size"], cuerpo["pages"]), (3, 1, 20, 1))

    def test_parametros_invalidos_422(self):
        self._como("vendedor")
        casos = {
            "size=500": ("/ventas/", {"size": 500}),
            "page=0": ("/mis-ventas", {"page": 0}),
            "página de más": ("/ventas/", {"page": 4, "size": 2}),
        }
        for nombre, (ruta, params) in casos.items():
            with self.subTest(nombre):
                self.assertEqual(self.client.get(ruta, params=params).status_code, 422)
        respuesta = self.client.get("/ventas/", params={"page": 4, "size": 2})
        self.assertEqual(respuesta.json(), {"detail": "La página 4 no existe: hay 3"})


if __name__ == "__main__":
    unittest.main()
