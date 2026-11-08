"""Tests del módulo clientes protegido (issue #60 / J7).

Todas las rutas de /clientes son del personal (VENDEDOR o ADMIN, con
requiere_rol: roles vigentes en la base). La ficha muestra usuario_id (sólo
lectura) y GET /clientes/{id}/ventas devuelve el envoltorio
{items, total, page, size, pages} con consultas fijas.

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
from app.core.paginacion import PaginaInexistente
from app.main import pagina_inexistente
from app.modules.clientes.models import Cliente, PerfilCliente
from app.modules.clientes.router import router as clientes_router
from app.modules.clientes.unit_of_work import ClienteUnitOfWork, get_clientes_uow
from app.modules.editoriales.models import Editorial
from app.modules.libros.models import Libro
from app.modules.usuarios.models import AsignacionRol, Usuario
from app.modules.ventas.models import RenglonVenta, Venta

_SIN_PERMISO = {"detail": "No tiene permisos para realizar esta acción"}


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


class TestClientesProtegido(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine(
            "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
        )
        SQLModel.metadata.create_all(self.engine)
        ahora = datetime.now(timezone.utc)
        with Session(self.engine) as s:
            usuarios = {}
            for clave, rol, revocada_en in [
                ("admin", "ADMIN", None),
                ("vendedor", "VENDEDOR", None),
                ("ana", "CLIENTE", None),
                ("ex_vendedor", "VENDEDOR", ahora - timedelta(days=1)),
            ]:
                usuario = Usuario(email=f"{clave}@example.com", nombre=clave, password_hash="x")
                s.add(usuario)
                s.flush()
                s.add(AsignacionRol(usuario_id=usuario.id, rol=rol, desde=ahora - timedelta(days=30),
                                    revocada_en=revocada_en))
                usuarios[clave] = usuario.id

            lucia = Cliente(nombre="Lucía Fernández", email="lucia@example.com")
            ana = Cliente(nombre="Ana Paz", email="ana@example.com", usuario_id=usuarios["ana"])
            s.add_all([lucia, ana])
            s.flush()
            s.add(PerfilCliente(cliente_id=lucia.id, telefono="261-555-0101", direccion="San Martín 100"))

            editorial = Editorial(nombre="Sudamericana", pais="Argentina")
            s.add(editorial)
            s.flush()
            libros = []
            for i, titulo in enumerate(["Rayuela", "Ficciones", "Bestiario", "Respiración artificial"]):
                libro = Libro(isbn=f"isbn-{i}", titulo=titulo, precio=Decimal("10000.00"), stock=10,
                              editorial_id=editorial.id)
                s.add(libro)
                libros.append(libro)
            s.flush()
            # Lucía: una venta de 2 renglones y otra de 4.
            for cantidad_renglones in (2, 4):
                venta = Venta(cliente_id=lucia.id, total=Decimal(10000 * cantidad_renglones))
                for libro in libros[:cantidad_renglones]:
                    venta.renglones.append(RenglonVenta(libro_id=libro.id, cantidad=1,
                                                        precio_unitario=Decimal("10000.00")))
                s.add(venta)
            s.commit()
            self.usuarios = usuarios
            self.lucia_id, self.ana_id = lucia.id, ana.id

        app = FastAPI()
        app.include_router(clientes_router)
        app.add_exception_handler(PaginaInexistente, pagina_inexistente)  # el mismo de main.py

        def _sesion():
            with Session(self.engine) as s:
                yield _AsyncSessionAdapter(s)

        def _uow():
            with Session(self.engine) as s:
                yield ClienteUnitOfWork(_AsyncSessionAdapter(s))

        app.dependency_overrides[get_session] = _sesion
        app.dependency_overrides[get_clientes_uow] = _uow
        self.app = app
        self.client = TestClient(app)

    def tearDown(self):
        self.engine.dispose()

    def _como(self, clave):
        with Session(self.engine) as s:
            usuario = s.get(Usuario, self.usuarios[clave])
        self.app.dependency_overrides[get_usuario_actual] = lambda: usuario

    def _todas_las_rutas(self):
        return [
            ("POST", "/clientes/", {"nombre": "Pedro Gómez", "email": "pedro@example.com"}),
            ("GET", f"/clientes/{self.lucia_id}", None),
            ("PATCH", f"/clientes/{self.lucia_id}", {"nombre": "Lucía F."}),
            ("POST", f"/clientes/{self.ana_id}/perfil", {"telefono": "261-555-0202", "direccion": "Belgrano 50"}),
            ("GET", f"/clientes/{self.lucia_id}/ventas", None),
        ]

    # ---------- Quién puede usar el módulo ----------

    def test_sin_sesion_401_en_todas_las_rutas(self):
        for metodo, ruta, cuerpo in self._todas_las_rutas():
            with self.subTest(f"{metodo} {ruta}"):
                self.assertEqual(self.client.request(metodo, ruta, json=cuerpo).status_code, 401)

    def test_un_cliente_o_un_rol_revocado_403_en_todas_las_rutas(self):
        for clave in ("ana", "ex_vendedor"):
            self._como(clave)
            for metodo, ruta, cuerpo in self._todas_las_rutas():
                with self.subTest(f"{clave} {metodo} {ruta}"):
                    respuesta = self.client.request(metodo, ruta, json=cuerpo)
                    self.assertEqual(respuesta.status_code, 403)
                    self.assertEqual(respuesta.json(), _SIN_PERMISO)

    def test_el_personal_usa_todas_las_rutas(self):
        esperados = [201, 200, 200, 201, 200]
        for clave, sufijo in (("vendedor", "v"), ("admin", "a")):
            self._como(clave)
            for (metodo, ruta, cuerpo), esperado in zip(self._todas_las_rutas(), esperados):
                if metodo == "POST" and ruta == "/clientes/":
                    cuerpo = {"nombre": "Pedro Gómez", "email": f"pedro.{sufijo}@example.com"}
                if ruta.endswith("/perfil") and clave == "admin":
                    esperado = 409  # el vendedor ya le creó el perfil a Ana
                with self.subTest(f"{clave} {metodo} {ruta}"):
                    self.assertEqual(self.client.request(metodo, ruta, json=cuerpo).status_code, esperado)

    # ---------- usuario_id ----------

    def test_la_ficha_muestra_usuario_id(self):
        self._como("vendedor")
        ana = self.client.get(f"/clientes/{self.ana_id}").json()
        lucia = self.client.get(f"/clientes/{self.lucia_id}").json()
        self.assertEqual(ana["usuario_id"], self.usuarios["ana"])
        self.assertIsNone(lucia["usuario_id"])
        self.assertEqual(lucia["perfil"]["telefono"], "261-555-0101")

    def test_el_personal_no_puede_asignar_usuario_id(self):
        # Lo pone el auto-registro (RN-02): en el alta y el PATCH es un campo de más.
        self._como("vendedor")
        alta = self.client.post("/clientes/", json={"nombre": "X", "email": "x@example.com",
                                                    "usuario_id": self.usuarios["vendedor"]})
        cambio = self.client.patch(f"/clientes/{self.lucia_id}", json={"usuario_id": self.usuarios["ana"]})
        self.assertEqual((alta.status_code, cambio.status_code), (422, 422))

    # ---------- GET /clientes/{id}/ventas ----------

    def test_ventas_del_cliente_con_el_envoltorio(self):
        self._como("vendedor")
        cuerpo = self.client.get(f"/clientes/{self.lucia_id}/ventas", params={"size": 1}).json()
        self.assertEqual(set(cuerpo), {"items", "total", "page", "size", "pages"})
        self.assertEqual((cuerpo["total"], cuerpo["page"], cuerpo["size"], cuerpo["pages"]), (2, 1, 1, 2))
        self.assertEqual(len(cuerpo["items"][0]["renglones"]), 2)

    def test_cliente_sin_ventas_pagina_vacia_y_cliente_inexistente_404(self):
        self._como("vendedor")
        vacia = self.client.get(f"/clientes/{self.ana_id}/ventas").json()
        self.assertEqual((vacia["items"], vacia["total"], vacia["pages"]), ([], 0, 1))
        respuesta = self.client.get("/clientes/9999/ventas")
        self.assertEqual(respuesta.status_code, 404)
        self.assertEqual(respuesta.json(), {"detail": "El cliente no existe"})

    def test_pagina_de_mas_o_size_invalido_422(self):
        self._como("vendedor")
        respuesta = self.client.get(f"/clientes/{self.lucia_id}/ventas", params={"page": 3, "size": 1})
        self.assertEqual(respuesta.status_code, 422)
        self.assertEqual(respuesta.json(), {"detail": "La página 3 no existe: hay 2"})
        self.assertEqual(self.client.get(f"/clientes/{self.lucia_id}/ventas", params={"size": 101}).status_code, 422)

    def test_ventas_del_cliente_con_consultas_fijas(self):
        self._como("vendedor")
        cantidades = []
        for size in (1, 2):
            consultas = []

            def anotar(conn, cursor, sql, parametros, contexto, varias):
                consultas.append(sql)

            event.listen(self.engine, "before_cursor_execute", anotar)
            try:
                self.client.get(f"/clientes/{self.lucia_id}/ventas", params={"size": size})
            finally:
                event.remove(self.engine, "before_cursor_execute", anotar)
            cantidades.append(len(consultas))
        # roles + cliente (404) + conteo + página (venta JOIN cliente) + renglones JOIN libro,
        # con 1 venta de 2 renglones o con 2 ventas (2 y 4 renglones).
        self.assertEqual(cantidades, [5, 5])


if __name__ == "__main__":
    unittest.main()
