"""Tests del aviso del comprobante (issue #57 / J4, Ej. 8).

El aviso se agenda con BackgroundTasks al registrar una venta, corre después de
enviar la respuesta y sólo si la venta se confirmó. Se escribe con el logger de
uvicorn para que se vea con el arranque normal del servidor.

Los tests HTTP montan el router de ventas sobre una base SQLite en memoria y
envuelven la app para anotar el momento en que termina de enviarse la
respuesta: así se ve el orden real entre la respuesta y el aviso.
"""

import unittest
from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, patch

from fastapi import FastAPI
from fastapi.testclient import TestClient
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
from app.core.database import get_session
from app.core.dependencies import get_usuario_actual
from app.modules.clientes.models import Cliente
from app.modules.editoriales.models import Editorial
from app.modules.libros.models import Libro
from app.modules.usuarios.models import AsignacionRol, Usuario
from app.modules.ventas import service
from app.modules.ventas.models import Venta
from app.modules.ventas.router import router as ventas_router
from app.modules.ventas.unit_of_work import VentaUnitOfWork, get_ventas_uow

_RESPUESTA_ENVIADA = "respuesta enviada"


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
    conexion.execute("PRAGMA foreign_keys=ON")


class TestAvisoDelComprobante(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine(
            "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
        )
        event.listen(self.engine, "connect", _activar_claves_foraneas)
        SQLModel.metadata.create_all(self.engine)
        with Session(self.engine) as s:
            editorial = Editorial(nombre="Sudamericana", pais="Argentina")
            s.add(editorial)
            s.flush()
            for titulo, precio, stock in [("Rayuela", "25000.00", 10), ("Bestiario", "18000.00", 1)]:
                s.add(Libro(isbn=f"isbn-{titulo}", titulo=titulo, precio=Decimal(precio),
                            stock=stock, editorial_id=editorial.id))
            s.add(Cliente(nombre="Lucía Fernández", email="lucia@example.com"))
            vendedor = Usuario(email="vendedor@example.com", nombre="Vendedor", password_hash="x")
            s.add(vendedor)
            s.flush()
            # POST /ventas pide VENDEDOR o ADMIN (requiere_rol lee la base).
            s.add(AsignacionRol(usuario_id=vendedor.id, rol="VENDEDOR", desde=datetime.now(timezone.utc)))
            s.commit()
            self.ids = {libro.titulo: libro.id for libro in s.exec(select(Libro)).all()}
            self.cliente_id = s.exec(select(Cliente.id)).one()
            self.vendedor_id = vendedor.id

        self.eventos = []

        app = FastAPI()
        app.include_router(ventas_router)

        def _uow():
            with Session(self.engine) as s:
                yield VentaUnitOfWork(_AsyncSessionAdapter(s))

        def _usuario():
            return Usuario(id=self.vendedor_id, email="vendedor@example.com", nombre="Vendedor",
                           password_hash="x")

        def _sesion():
            with Session(self.engine) as s:
                yield _AsyncSessionAdapter(s)

        app.dependency_overrides[get_session] = _sesion
        app.dependency_overrides[get_ventas_uow] = _uow
        app.dependency_overrides[get_usuario_actual] = _usuario

        async def app_que_anota_la_respuesta(scope, receive, send):
            async def send_y_anotar(mensaje):
                await send(mensaje)
                if mensaje["type"] == "http.response.body" and not mensaje.get("more_body"):
                    self.eventos.append(_RESPUESTA_ENVIADA)

            await app(scope, receive, send_y_anotar)

        self.client = TestClient(app_que_anota_la_respuesta)

        async def aviso_que_anota(venta_id, email, total):
            self.eventos.append(("aviso", venta_id, email, total))

        parche = patch.object(service, "avisar_comprobante", aviso_que_anota)
        parche.start()
        self.addCleanup(parche.stop)

    def tearDown(self):
        self.engine.dispose()

    def _vender(self, renglones, cliente_id=None):
        return self.client.post("/ventas/", json={
            "cliente_id": cliente_id if cliente_id is not None else self.cliente_id,
            "renglones": [{"libro_id": libro_id, "cantidad": cantidad} for libro_id, cantidad in renglones],
        })

    def _ventas_guardadas(self):
        with Session(self.engine) as s:
            return s.exec(select(func.count()).select_from(Venta)).one()

    def test_venta_confirmada_agenda_un_aviso_que_corre_despues_de_la_respuesta(self):
        respuesta = self._vender([(self.ids["Rayuela"], 2)])

        self.assertEqual(respuesta.status_code, 201)
        venta = respuesta.json()
        # Primero termina de enviarse la respuesta y recién después corre el aviso,
        # una sola vez y con los datos de la venta confirmada.
        self.assertEqual(
            self.eventos,
            [_RESPUESTA_ENVIADA, ("aviso", venta["id"], "lucia@example.com", Decimal("50000.00"))],
        )

    def test_venta_rechazada_no_agenda_aviso(self):
        casos = {
            "stock insuficiente": ([(self.ids["Rayuela"], 1), (self.ids["Bestiario"], 2)], None),
            "libro inexistente": ([(9999, 1)], None),
            "cliente inexistente": ([(self.ids["Rayuela"], 1)], 9999),
        }
        for nombre, (renglones, cliente_id) in casos.items():
            with self.subTest(nombre):
                self.eventos.clear()
                respuesta = self._vender(renglones, cliente_id)
                self.assertEqual(respuesta.status_code, 409)
                # Se envió la respuesta y nada más: no hubo aviso.
                self.assertEqual(self.eventos, [_RESPUESTA_ENVIADA])
                self.assertEqual(self._ventas_guardadas(), 0)

    def test_cuerpo_invalido_no_agenda_aviso(self):
        respuesta = self.client.post("/ventas/", json={"cliente_id": self.cliente_id, "renglones": []})
        self.assertEqual(respuesta.status_code, 422)
        self.assertEqual(self.eventos, [_RESPUESTA_ENVIADA])


class TestAvisarComprobante(unittest.IsolatedAsyncioTestCase):
    async def test_espera_sin_bloquear_y_escribe_en_el_registro_de_uvicorn(self):
        espera = AsyncMock()
        # "uvicorn.error" es el logger que uvicorn ya deja configurado en INFO: con el
        # arranque normal, el mensaje sale en la consola. Uno propio sin configurar no.
        with patch.object(service.asyncio, "sleep", espera), \
                self.assertLogs("uvicorn.error", level="INFO") as registro:
            await service.avisar_comprobante(7, "lucia@example.com", Decimal("72000.00"))

        espera.assert_awaited_once_with(0.5)  # asyncio.sleep, no time.sleep
        self.assertEqual(
            registro.output,
            ["INFO:uvicorn.error:Comprobante de la venta 7 enviado a lucia@example.com (total $72000.00)"],
        )


if __name__ == "__main__":
    unittest.main()
